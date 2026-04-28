"""MoviePy 2.x で台本+音声+画像から 1080x1920 Shorts mp4 を組立"""
import math
import random
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ColorClip,
    concatenate_videoclips,
    afx,
    vfx,
)

import config


# ===== 字幕レンダラ（PIL、強調ワード対応） =====
_FONT_CACHE: dict = {}


def _load_font(path: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    """Variable fontなら weight をaxis経由でセット"""
    key = (path, size, weight)
    if key not in _FONT_CACHE:
        font = ImageFont.truetype(path, size)
        if weight is not None:
            try:
                font.set_variation_by_axes([weight])
            except Exception:
                pass
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]


def _parse_emphasis(text: str) -> list[tuple[str, bool]]:
    """**word** 記法をパースして [(text, is_emphasis), ...] にする"""
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    result = []
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**"):
            result.append((p[2:-2], True))
        else:
            result.append((p, False))
    return result


_TOKENIZER = None


def _get_tokenizer():
    """janome Tokenizer をシングルトンで返す（初期化に1秒程度かかるため）"""
    global _TOKENIZER
    if _TOKENIZER is None:
        from janome.tokenizer import Tokenizer
        _TOKENIZER = Tokenizer()
    return _TOKENIZER


# 自立語の品詞（新しい文節の開始トリガー）
_INDEPENDENT_POS = {"名詞", "動詞", "形容詞", "形容動詞", "副詞", "連体詞",
                    "感動詞", "接続詞"}


_OPEN_BRACKETS = set("「『([{〈《（〔")

# 短い補助動詞/補助語。これらで始まる短いチャンクは前のチャンクに吸収
_AUX_HEADS = ("しれ", "して", "でき", "なり", "あり", "いれ", "くれ",
              "もら", "なっ", "いっ", "だろ", "でしょ", "みら", "ませ",
              "ちゃ", "じゃ", "ない", "ている", "ていた")


def _is_ascii_like(s: str) -> bool:
    """ASCII文字 + 空白 + ハイフン等のみで構成されているか（日本語なし）"""
    return bool(s) and all(ord(c) < 128 or c in "―-・" for c in s)


def _bunsetsu_split(text: str) -> list[str]:
    """日本語+英数字テキストを文節（bunsetsu）に分割。
    自立語1個 + その後ろの付属語（助詞・助動詞・記号）= 1文節。
    - 接尾/非自立は前のチャンクに吸収
    - 開き括弧は末尾につけず、次のチャンクの先頭に送る
    """
    if not text:
        return []
    tokenizer = _get_tokenizer()
    chunks: list[str] = []
    cur: list[str] = []
    pending_open = ""   # 次のチャンクの先頭に付けるべき開き括弧
    last_sub = ""        # 直前トークンの細分類POS
    # サ変動詞の"し/する"パターン（活用→し+ます、検出→し+ました 等）
    SA_VERB_FORMS = {"し", "する", "せ", "さ", "しよ", "しろ"}

    for tok in tokenizer.tokenize(text):
        pos_parts = tok.part_of_speech.split(",")
        pos = pos_parts[0]
        pos_sub = pos_parts[1] if len(pos_parts) > 1 else ""
        surface = tok.surface

        # 開き括弧は現在チャンク確定→pendingに蓄積→次のチャンク冒頭へ
        if surface in _OPEN_BRACKETS:
            if cur:
                chunks.append("".join(cur))
                cur = []
            pending_open += surface
            continue

        is_independent = pos in _INDEPENDENT_POS
        # 接尾/非自立/数は前のチャンクに吸収（対抗策, 1600万件, こと, ため）
        if pos_sub in ("接尾", "非自立", "数"):
            is_independent = False
        # サ変複合: 名詞-サ変接続 + 動詞(し/する) は同じチャンク（活用する、検出します）
        if pos == "動詞" and surface in SA_VERB_FORMS and last_sub == "サ変接続":
            is_independent = False

        if is_independent:
            if cur:
                chunks.append("".join(cur))
            cur = [pending_open + surface] if pending_open else [surface]
            pending_open = ""
        else:
            if pending_open and not cur:
                cur = [pending_open + surface]
                pending_open = ""
            else:
                cur.append(surface)

        last_sub = pos_sub

    if pending_open:
        if cur:
            cur.insert(0, pending_open)
        else:
            chunks.append(pending_open)
    if cur:
        chunks.append("".join(cur))

    return _post_process_chunks(chunks)


def _post_process_chunks(chunks: list[str]) -> list[str]:
    """チャンクの事後調整:
    1. 連続するASCII始まりチャンク（固有名詞句）を空白で結合
    2. 短い補助動詞チャンクを前のチャンクに吸収
    """
    # 1. 連続するASCII始まりチャンクを統合（"Frontier " "Model " "Forumという" → "Frontier Model Forumという"）
    merged: list[str] = []
    for c in chunks:
        if merged:
            prev_rstrip = merged[-1].rstrip()
            if (prev_rstrip and ord(prev_rstrip[-1]) < 128
                    and (prev_rstrip[-1].isalnum() or prev_rstrip[-1] in "._-")
                    and c and ord(c[0]) < 128
                    and (c[0].isalnum() or c[0] in "._-")):
                # 既存の末尾空白 or 先頭空白があればそれを使う、なければ1つ足す
                if merged[-1].endswith(" ") or c.startswith(" "):
                    merged[-1] = merged[-1] + c
                else:
                    merged[-1] = merged[-1] + " " + c
                continue
        merged.append(c)

    # 2. 短い補助動詞チャンクを前にくっつける
    result: list[str] = []
    for c in merged:
        if result and len(c) <= 8 and any(c.startswith(p) for p in _AUX_HEADS):
            result[-1] = result[-1] + c
        else:
            result.append(c)
    return result


def _split_into_units(tokens: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    """文字列を「破壊不可なユニット」に分解。
    - **emphasis** は1ユニット
    - 通常テキストは janome の文節単位で1ユニット
    """
    units: list[tuple[str, bool]] = []
    for chunk, is_emph in tokens:
        if is_emph:
            units.append((chunk, True))
            continue
        # 改行を保持しつつ文節分割
        for line in chunk.split("\n"):
            for b in _bunsetsu_split(line):
                if b:
                    units.append((b, False))
            units.append(("\n", False))
        if units and units[-1] == ("\n", False):
            units.pop()  # 末尾の余分な改行を消す
    return units


_NO_LINE_START = set("、。！？，．,.!?）)」』]｝}〉》")


def _wrap_units(units: list[tuple[str, bool]], font: ImageFont.FreeTypeFont,
                max_width: int) -> list[list[tuple[str, bool]]]:
    """ユニット単位で折返し。行頭禁則（句読点）対応。"""
    lines: list[list[tuple[str, bool]]] = [[]]
    cur_w = 0.0

    def unit_width(t: str) -> float:
        return sum(font.getlength(c) for c in t)

    for i, (text, is_emph) in enumerate(units):
        if text == "\n":
            lines.append([])
            cur_w = 0
            continue
        w = unit_width(text)
        if cur_w + w > max_width and lines[-1]:
            # 次のユニットが行頭禁則文字 or 自分が長すぎてどうしようもない場合の処理
            # 通常は新しい行へ
            lines.append([])
            cur_w = 0
        lines[-1].append((text, is_emph))
        cur_w += w

        # 行頭禁則: 次のユニットが句読点なら、そっちに送らずこの行に置く
        # （実装上、既に上で改行済みでも次回ループで「行頭がNGなら戻す」処理を入れる）

    # 行頭禁則の事後修正: 各行の先頭が NO_LINE_START だったら前の行末尾に戻す
    fixed: list[list[tuple[str, bool]]] = []
    for line in lines:
        if fixed and line and line[0][0] and line[0][0][0] in _NO_LINE_START:
            fixed[-1].append(line[0])
            line = line[1:]
        fixed.append(line)
    return fixed


def render_subtitle_image(text: str, font_path: str, font_size: int,
                          max_width: int,
                          normal_color: str, emphasis_color: str,
                          stroke_color: str, stroke_width: int,
                          line_spacing: int = 12,
                          font_weight: int | None = None) -> Image.Image:
    """強調ワード対応の字幕PNG（透過RGBA）を生成。ユニット単位で折返し。"""
    font = _load_font(font_path, font_size, font_weight)
    tokens = _parse_emphasis(text)
    units = _split_into_units(tokens)
    lines = _wrap_units(units, font, max_width)

    ascent, descent = font.getmetrics()
    line_h = ascent + descent + line_spacing
    canvas_h = max(line_h * len(lines), line_h)

    img = Image.new("RGBA", (max_width, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    sw = stroke_width
    for line_idx, line in enumerate(lines):
        line_w = sum(font.getlength(c) for unit_text, _ in line for c in unit_text)
        x = (max_width - line_w) // 2
        y = line_idx * line_h
        for unit_text, is_emph in line:
            color = emphasis_color if is_emph else normal_color
            # ユニットを文字単位で描画（縁取り＋本体）
            for ch in unit_text:
                for dx in range(-sw, sw + 1):
                    for dy in range(-sw, sw + 1):
                        if dx == 0 and dy == 0:
                            continue
                        if dx * dx + dy * dy <= sw * sw:
                            draw.text((x + dx, y + dy), ch, font=font, fill=stroke_color)
                draw.text((x, y), ch, font=font, fill=color)
                x += font.getlength(ch)

    return img


def _ken_burns_clip(image_path: Path, duration: float, zoom_in: bool = True) -> ImageClip:
    """画像を1080x1920に収め、Ken Burnsズームを適用"""
    clip = ImageClip(str(image_path)).with_duration(duration)

    # まず画面をカバーするサイズにリサイズ（短辺がVIDEO_HEIGHTに届く）
    iw, ih = clip.size
    scale = max(config.VIDEO_WIDTH / iw, config.VIDEO_HEIGHT / ih) * config.KEN_BURNS_ZOOM_END
    base_w, base_h = int(iw * scale), int(ih * scale)
    clip = clip.resized(new_size=(base_w, base_h))

    # ズーム比率を時間で変化させる
    z0 = config.KEN_BURNS_ZOOM_START / config.KEN_BURNS_ZOOM_END
    z1 = 1.0
    if not zoom_in:
        z0, z1 = z1, z0

    def scale_fn(t):
        p = t / duration if duration > 0 else 0
        return z0 + (z1 - z0) * p

    clip = clip.resized(scale_fn)

    # 中央配置、1080x1920にクロップ
    clip = clip.with_position(("center", "center"))
    composed = CompositeVideoClip(
        [clip],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    ).with_duration(duration)
    return composed


def _subtitle_clip(text: str, duration: float, genre, emotion: str = "normal"):
    """強調ワード対応の字幕クリップ。**word** で強調、シェイク有無は genre 設定。
    emotion="hook" の場合はインパクト重視のフックフォント＋拡大表示にする。"""
    if not text.strip():
        return None

    is_hook = emotion == "hook"
    font_size = (config.SUBTITLE_FONT_SIZE_HOOK
                 if is_hook else config.SUBTITLE_FONT_SIZE)
    stroke_w = (config.SUBTITLE_STROKE_WIDTH_HOOK
                if is_hook else config.SUBTITLE_STROKE_WIDTH)
    # フックは Reggae One（太い display フォント）、それ以外は Noto Sans JP
    font_path = (getattr(config, "SUBTITLE_FONT_HOOK", config.SUBTITLE_FONT)
                 if is_hook else config.SUBTITLE_FONT)
    # フックは画面上部寄り（バナーと重ならない位置）、それ以外は中央
    y_ratio = (getattr(config, "SUBTITLE_Y_RATIO_HOOK", config.SUBTITLE_Y_RATIO)
               if is_hook else config.SUBTITLE_Y_RATIO)

    # フックは特別カラーで目を引く（黄+赤縁取り）。それ以外はジャンル既定。
    if is_hook:
        normal_color = getattr(config, "HOOK_SUBTITLE_COLOR", genre.SUBTITLE_COLOR)
        stroke_color = getattr(config, "HOOK_SUBTITLE_STROKE_COLOR",
                               genre.SUBTITLE_STROKE_COLOR)
        # フック中の **強調** はさらに白で抜くと黄背景に映える
        emphasis_color = "white"
    else:
        normal_color = genre.SUBTITLE_COLOR
        stroke_color = genre.SUBTITLE_STROKE_COLOR
        emphasis_color = getattr(genre, "SUBTITLE_EMPHASIS_COLOR",
                                 genre.SUBTITLE_COLOR)

    img = render_subtitle_image(
        text=text,
        font_path=font_path,
        font_size=font_size,
        max_width=config.VIDEO_WIDTH - 80,
        normal_color=normal_color,
        emphasis_color=emphasis_color,
        stroke_color=stroke_color,
        stroke_width=stroke_w,
        # 851チカラヅヨクは固定ウェイトなので variable axis 指定は不要
        font_weight=None if is_hook else getattr(config, "SUBTITLE_FONT_WEIGHT", None),
    )
    arr = np.array(img)
    clip = ImageClip(arr).with_duration(duration)

    y_base = int(config.VIDEO_HEIGHT * y_ratio) - arr.shape[0] // 2
    has_emphasis = "**" in text
    shake_enabled = getattr(genre, "SUBTITLE_EMPHASIS_SHAKE", False)

    if has_emphasis and shake_enabled:
        # 最初の0.5秒だけシェイク（フォーカスを引く）
        x_base = (config.VIDEO_WIDTH - arr.shape[1]) // 2

        def pos_fn(t):
            if t < 0.5:
                shake_x = math.sin(t * 50) * 8
                shake_y = math.cos(t * 60) * 6
                return (x_base + shake_x, y_base + shake_y)
            return (x_base, y_base)

        clip = clip.with_position(pos_fn)
    else:
        clip = clip.with_position(("center", y_base))

    return clip


def _hook_banner_clip(duration: float):
    """hookシーン上部に重ねる「🚨 速報」赤帯バナー"""
    if not getattr(config, "HOOK_BANNER_ENABLED", False):
        return None
    from PIL import Image, ImageDraw, ImageFont
    h = int(config.VIDEO_HEIGHT * config.HOOK_BANNER_HEIGHT_RATIO)
    w = config.VIDEO_WIDTH
    img = Image.new("RGBA", (w, h), config.HOOK_BANNER_COLOR + (235,))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            getattr(config, "SUBTITLE_FONT_HOOK", config.SUBTITLE_FONT),
            config.HOOK_BANNER_FONT_SIZE,
        )
    except Exception:
        font = ImageFont.load_default()
    text = config.HOOK_BANNER_TEXT
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((w - tw) // 2 - bbox[0], (h - th) // 2 - bbox[1]),
        text,
        fill=config.HOOK_BANNER_TEXT_COLOR,
        font=font,
        stroke_width=3,
        stroke_fill="black",
    )
    arr = np.array(img)
    clip = ImageClip(arr).with_duration(duration)
    y = int(config.VIDEO_HEIGHT * config.HOOK_BANNER_Y_RATIO)

    # 最初の0.4秒で上からスライドイン
    def pos_fn(t):
        if t < 0.4:
            offset = int((1 - t / 0.4) * h)
            return (0, y - offset)
        return (0, y)

    return clip.with_position(pos_fn)


def _flash_clip(duration: float = 0.15) -> ColorClip:
    return ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=(255, 255, 255),
    ).with_duration(duration).with_opacity(0.7)


# ===== キャラクター立ち絵 =====

def _character_image_path(genre, expression: str | None) -> Path | None:
    """assets/characters/<genre.CHARACTER_DIR>/<expression>.png を返す。なければNone"""
    if expression is None:
        return None
    char_dir_name = getattr(genre, "CHARACTER_DIR", None)
    if not char_dir_name:
        return None
    base = config.CHARACTER_BASE / char_dir_name
    for ext in ("png", "PNG", "webp"):
        p = base / f"{expression}.{ext}"
        if p.exists():
            return p
    return None


def _character_clip(genre, emotion: str, duration: float):
    """シーンの emotion に応じた立ち絵 ImageClip を返す。画像なければ None"""
    expr_map = getattr(genre, "EMOTION_TO_EXPRESSION", None)
    if not expr_map:
        return None
    expr = expr_map.get(emotion)
    if expr is None:
        return None

    img_path = _character_image_path(genre, expr)
    if img_path is None:
        # ノーマル表情にfallback
        img_path = _character_image_path(genre, "normal")
        if img_path is None:
            return None

    char_clip = ImageClip(str(img_path)).with_duration(duration)
    # 幅を画面の CHARACTER_WIDTH_RATIO にリサイズ（縦は連動）
    target_w = int(config.VIDEO_WIDTH * config.CHARACTER_WIDTH_RATIO)
    iw, ih = char_clip.size
    target_h = int(ih * target_w / iw)
    char_clip = char_clip.resized(new_size=(target_w, target_h))

    # 配置: 下端からマージン、左右はgenre側設定
    y = config.VIDEO_HEIGHT - target_h - int(config.VIDEO_HEIGHT * config.CHARACTER_Y_OFFSET_RATIO)
    pos = getattr(genre, "CHARACTER_POSITION", "right")
    if pos == "left":
        x = 20
    else:
        x = config.VIDEO_WIDTH - target_w - 20

    return char_clip.with_position((x, y))


def _build_scene(scene: dict, image_path: Path, audio_path: Path, genre) -> CompositeVideoClip:
    duration = float(scene.get("actual_audio_sec") or scene.get("duration_sec", 3.0))
    emotion = scene.get("emotion", "normal")

    # entity画像があればSDXL生成画像を上書き
    entity_path = config.find_entity_image(scene.get("entity"))
    if entity_path is not None:
        image_path = entity_path

    if emotion == "silence":
        # 真っ黒は離脱を招くので、画像を暗転＋静止で繋ぎとして使う
        layers = [_ken_burns_clip(image_path, duration, zoom_in=False)]
        dim = ColorClip(
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
            color=(0, 0, 0),
        ).with_duration(duration).with_opacity(0.55)
        layers.append(dim)
    else:
        zoom_in = emotion in ("hook", "climax", "shock")
        layers = [_ken_burns_clip(image_path, duration, zoom_in=zoom_in)]
        if emotion == "shock":
            layers.append(_flash_clip(0.15).with_start(0))

    # キャラ立ち絵（任意、画像があれば）
    char = _character_clip(genre, emotion, duration)
    if char is not None:
        layers.append(char)

    sub = _subtitle_clip(scene.get("narration", ""), duration, genre, emotion=emotion)
    if sub is not None:
        layers.append(sub)

    # hookシーン上部に🚨速報バナーを重ねる（インパクト最大化）
    if emotion == "hook":
        banner = _hook_banner_clip(duration)
        if banner is not None:
            layers.append(banner)

    composite = CompositeVideoClip(
        layers,
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    ).with_duration(duration)

    # ===== 音声 =====
    # 音声実時間より僅かに短く切って読み取りEOFを回避（最小限）
    safe_dur = max(0.1, duration - 0.02)
    narration = (
        AudioFileClip(str(audio_path))
        .with_duration(safe_dur)
        .with_effects([afx.MultiplyVolume(config.NARRATION_VOLUME)])
    )
    audio_layers = [narration]

    sfx_name = scene.get("sfx", "none")
    sfx_path = _pick_sfx(sfx_name, genre)
    if sfx_path is not None:
        try:
            sfx_clip = AudioFileClip(str(sfx_path))
            # SFX 自体の長さを超えて再生しない（EOFエラー回避）
            target = max(0.1, min(duration, float(sfx_clip.duration), 2.5) - 0.05)
            sfx_audio = (
                sfx_clip.subclipped(0, target)
                .with_effects([afx.MultiplyVolume(config.SFX_VOLUME)])
            )
            audio_layers.append(sfx_audio)
        except Exception as e:
            print(f"  [warn] sfx '{sfx_name}' load failed: {e}")

    composite = composite.with_audio(CompositeAudioClip(audio_layers))
    return composite


def _silence_pad(duration: float, image_path: Path) -> CompositeVideoClip:
    """shock直前のpattern interrupt: 次シーン画像を静止表示（音だけ無音）"""
    clip = ImageClip(str(image_path)).with_duration(duration)
    iw, ih = clip.size
    scale = max(config.VIDEO_WIDTH / iw, config.VIDEO_HEIGHT / ih)
    base_w, base_h = int(iw * scale), int(ih * scale)
    clip = clip.resized(new_size=(base_w, base_h)).with_position(("center", "center"))
    return CompositeVideoClip(
        [clip],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    ).with_duration(duration)


# 各SFX名 → 候補ファイル名のリスト。実在するもののみが使われ、複数あれば毎回ランダムに選ぶ。
_SFX_ALIAS = {
    # === スキーマ標準名（プロンプトが出すもの） ===
    "impact_drum": ["se_don", "se_dodon", "se_don_1", "se_jidai_geki"],
    "breaking_alert": ["se_dora", "ショック1", "se_dondonpafupafu_2025"],
    "dramatic_riser": ["se_ga_n", "Inspiration08-1(Low)", "Inspiration08-2(Low-Delay)", "Inspiration05-3(High)"],
    "reveal_chime": ["se_VFR_jan", "se_VFR_chararira", "se_VFR_chime", "キラッ2"],
    "camera_shutter": ["se_VFR_Flash06_1"],
    "suspense_drone": ["Inspiration08-1(Low)", "Inspiration08-2(Low-Delay)", "Inspiration08-4(High)"],
    "typing_keyboard": ["se_VFR_kin", "se_VFR_syakin"],
    "swoosh_transition": ["se_VFR_swish_1", "se_VFR_swish_2", "se_VFR_swish_3", "se_VFR_swish_4",
                           "se_VFR_hyu_n1", "se_VFR_hyu_n2", "se_bamentenkan"],
    "glitch_news": ["se_VFR_kin", "se_VFR_syakin", "se_VFR_syakin2"],
    "warning_beep": ["決定ボタンを押す22", "se_VFR_chime"],
    # === 旧名（後方互換） ===
    "ding": ["se_VFR_chime", "ding"],
    "whoosh": ["se_VFR_swish_1", "se_VFR_swish_2", "se_VFR_hyu_n1", "whoosh"],
    "pop": ["se_VFR_Pop01_1", "pop"],
    "notification": ["キラッ2", "se_VFR_chime", "notification"],
    "breaking": ["se_dora", "ショック1", "breaking"],
}


def _pick_sfx(name: str, genre) -> Path | None:
    if name in ("none", "silence", None, ""):
        return None
    sfx_dir = config.genre_sfx_dir(genre.NAME)
    candidates_raw = _SFX_ALIAS.get(name, name)
    if isinstance(candidates_raw, str):
        candidates_raw = [candidates_raw]
    candidates_raw = list(candidates_raw) + [name]
    # 実在するファイルだけを集めてランダム選択（バリエーション化）
    existing = []
    for cand in candidates_raw:
        for ext in ("mp3", "wav", "ogg", "m4a"):
            p = sfx_dir / f"{cand}.{ext}"
            if p.exists() and p not in existing:
                existing.append(p)
    if not existing:
        return None
    return random.choice(existing)


def _pick_bgm(genre, script: dict | None = None) -> Path | None:
    """script._meta.bgm_mood に応じてジャンル別BGMを選定。
    _meta.json があればムードタグでフィルタ、なければ全候補からランダム。"""
    bgm_dir = config.genre_bgm_dir(genre.NAME)
    candidates = []
    for ext in ("mp3", "wav", "ogg", "m4a"):
        candidates.extend(bgm_dir.glob(f"*.{ext}"))
    candidates = [p for p in candidates if not p.name.startswith("_")]
    if not candidates:
        return None

    # ムード絞り込み
    mood = None
    if script:
        mood = (script.get("_meta", {}) or {}).get("bgm_mood") \
            or script.get("bgm_mood")
    meta_path = bgm_dir / "_meta.json"
    if mood and meta_path.exists():
        try:
            import json as _json
            meta = _json.loads(meta_path.read_text(encoding="utf-8"))
            tag_map = meta.get("tracks", {}) or {}
            matched = [
                p for p in candidates
                if mood in (tag_map.get(p.name, []) or [])
            ]
            if matched:
                print(f"  [bgm] mood='{mood}' → {len(matched)}/{len(candidates)} 候補")
                candidates = matched
            else:
                print(f"  [bgm] mood='{mood}' 該当なし→全候補から選定")
        except Exception as e:
            print(f"  [bgm] _meta.json 読込失敗: {e}")
    return random.choice(candidates)


def assemble(script: dict, audio_map: dict, image_map: dict, out_path: Path, genre) -> Path:
    """全シーン結合→BGM乗せ→書き出し。shock直前に無音パッド挿入。
    ジャンル別の VIDEO_WIDTH/HEIGHT があれば config に反映（縦/横切替対応）。"""
    # ジャンル別動画サイズの適用（mysteryなら 1920x1080 横画面）
    if hasattr(genre, "VIDEO_WIDTH"):
        config.VIDEO_WIDTH = genre.VIDEO_WIDTH
    if hasattr(genre, "VIDEO_HEIGHT"):
        config.VIDEO_HEIGHT = genre.VIDEO_HEIGHT

    scenes = script["scenes"]
    scene_clips = []
    pad_sec = config.SILENCE_PAD_BEFORE_SHOCK

    for i, scene in enumerate(scenes):
        sid = scene["scene_id"]
        img = image_map[sid]
        aud = audio_map[sid]["audio_path"]
        # entity画像があればパッド/シーン共にこちらを使う
        entity_img = config.find_entity_image(scene.get("entity"))
        pad_img = entity_img or img

        # shockの直前パッド: 当該shockシーンの画像を静止表示（黒回避）
        if (scene.get("emotion") == "shock" and pad_sec > 0
                and i > 0 and scenes[i - 1].get("emotion") != "silence"):
            scene_clips.append(_silence_pad(pad_sec, pad_img))

        clip = _build_scene(scene, img, aud, genre)
        if scene_clips:
            clip = clip.with_effects([vfx.CrossFadeIn(config.TRANSITION_DURATION)])
        scene_clips.append(clip)

    video = concatenate_videoclips(scene_clips, method="compose", padding=-config.TRANSITION_DURATION)

    bgm_path = _pick_bgm(genre, script)
    if bgm_path is not None:
        try:
            bgm = (
                AudioFileClip(str(bgm_path))
                .with_effects([
                    afx.AudioLoop(duration=video.duration),
                    afx.MultiplyVolume(genre.BGM_VOLUME),
                    afx.AudioFadeOut(1.0),
                ])
            )
            narration = video.audio
            video = video.with_audio(CompositeAudioClip([narration, bgm]))
        except Exception as e:
            print(f"  [warn] bgm load failed: {e}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fps = getattr(genre, "VIDEO_FPS", config.VIDEO_FPS)
    preset = getattr(genre, "VIDEO_PRESET", "medium")
    video.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        preset=preset,
        threads=4,
    )
    return out_path
