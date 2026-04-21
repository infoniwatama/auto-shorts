"""サムネ自動生成（背景=代表シーン画像 + 大文字テキスト + 数字 + バッジ）

注意: 自動生成サムネは「下書き」。最終的にCanva等で人間が手調整する前提で、
最初の見た目を素早く確認するためのもの。CTRが半減するリスク回避のため、
本投稿前に手作業のサムネ作成を強く推奨。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config


THUMB_W = config.VIDEO_WIDTH      # 1080
THUMB_H = config.VIDEO_HEIGHT     # 1920


def _resize_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """アスペクト比を保ちつつ w×h をカバーする最小サイズにリサイズし、中央クロップ"""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def _draw_text_with_stroke(draw: ImageDraw.ImageDraw, xy: tuple[int, int],
                            text: str, font: ImageFont.FreeTypeFont,
                            fill: str, stroke: str, stroke_w: int) -> None:
    x, y = xy
    sw = stroke_w
    for dx in range(-sw, sw + 1):
        for dy in range(-sw, sw + 1):
            if dx == 0 and dy == 0:
                continue
            if dx * dx + dy * dy <= sw * sw:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke)
    draw.text((x, y), text, font=font, fill=fill)


def _pick_background_scene(script: dict, image_map: dict) -> Path:
    """サムネ背景に使うシーン画像を選択"""
    scenes = script["scenes"]
    # 優先順: shock > climax > hook > 最初
    for emo in ("shock", "climax", "hook"):
        for s in scenes:
            if s.get("emotion") == emo:
                return image_map[s["scene_id"]]
    return image_map[scenes[0]["scene_id"]]


def generate_thumbnail(script: dict, image_map: dict, out_path: Path, genre) -> Path:
    bg_path = _pick_background_scene(script, image_map)
    bg = Image.open(bg_path).convert("RGBA")
    bg = _resize_cover(bg, THUMB_W, THUMB_H)

    # 暗くして可読性を上げる
    dark = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 110))
    bg = Image.alpha_composite(bg, dark)

    # 上下グラデ（見やすさ）
    grad = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(THUMB_H):
        if y < THUMB_H * 0.45:
            alpha = int(160 * (1 - y / (THUMB_H * 0.45)))
        elif y > THUMB_H * 0.6:
            alpha = int(180 * ((y - THUMB_H * 0.6) / (THUMB_H * 0.4)))
        else:
            alpha = 0
        gd.line([(0, y), (THUMB_W, y)], fill=(0, 0, 0, alpha))
    bg = Image.alpha_composite(bg, grad)

    draw = ImageDraw.Draw(bg)

    text_color = getattr(genre, "THUMBNAIL_TEXT_COLOR", "#FFE633")
    stroke_color = getattr(genre, "THUMBNAIL_STROKE_COLOR", "#000000")
    badge_text = getattr(genre, "THUMBNAIL_BADGE_TEXT", "")

    # === メイン煽り文（上部、最大サイズ） ===
    main_text = script.get("thumbnail_text", "").strip()
    if main_text:
        # 文字数で動的にサイズ調整（8文字想定で200pt）
        size = 240 if len(main_text) <= 6 else 200 if len(main_text) <= 9 else 160
        font_main = ImageFont.truetype(config.SUBTITLE_FONT, size)
        bbox = font_main.getbbox(main_text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # 横が幅を超える場合さらに縮小
        max_w = THUMB_W - 80
        if tw > max_w:
            size = int(size * max_w / tw)
            font_main = ImageFont.truetype(config.SUBTITLE_FONT, size)
            bbox = font_main.getbbox(main_text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (THUMB_W - tw) // 2
        ty = 280
        _draw_text_with_stroke(draw, (tx, ty), main_text, font_main,
                                fill=text_color, stroke=stroke_color, stroke_w=14)

    # === 大数字/キーワード（中央、最大サイズ） ===
    number_text = script.get("thumbnail_number", "").strip()
    if number_text:
        size = 320 if len(number_text) <= 4 else 240 if len(number_text) <= 7 else 180
        font_num = ImageFont.truetype(config.SUBTITLE_FONT, size)
        bbox = font_num.getbbox(number_text)
        nw, nh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        max_w = THUMB_W - 60
        if nw > max_w:
            size = int(size * max_w / nw)
            font_num = ImageFont.truetype(config.SUBTITLE_FONT, size)
            bbox = font_num.getbbox(number_text)
            nw, nh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        nx = (THUMB_W - nw) // 2
        ny = 900
        _draw_text_with_stroke(draw, (nx, ny), number_text, font_num,
                                fill="white", stroke=stroke_color, stroke_w=18)

    # === バッジ（右上） ===
    if badge_text:
        font_badge = ImageFont.truetype(config.SUBTITLE_FONT, 70)
        bbox = font_badge.getbbox(badge_text)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad = 30
        bx = THUMB_W - bw - pad * 2 - 40
        by = 40
        # 黄色背景の矩形
        draw.rectangle([bx, by, bx + bw + pad * 2, by + bh + pad * 2],
                       fill=text_color)
        _draw_text_with_stroke(draw,
                                (bx + pad, by + pad - bbox[1]),
                                badge_text, font_badge,
                                fill="black", stroke="black", stroke_w=0)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(out_path, quality=92)
    return out_path
