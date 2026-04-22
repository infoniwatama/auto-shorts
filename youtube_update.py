"""既存のYouTube動画の概要欄・タイトル・タグを更新。
Usage:
  python youtube_update.py <video_id> --run-dir output/videos/20260421_222321
  python youtube_update.py <video_id> --description-file path/to/new_description.txt
"""
import argparse
import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from googleapiclient.errors import HttpError

sys.path.insert(0, str(Path(__file__).parent))
import config
from youtube_upload import (
    get_authenticated_service, CATEGORY_SCIENCE_TECH, DEFAULT_TAGS,
)


def _build_stylish_description(run_dir: Path) -> str:
    """main.py のスタイリッシュ概要欄ロジックと同じ出力を生成"""
    import web_image_search as _wis
    script = json.loads((run_dir / "script.json").read_text(encoding="utf-8"))
    attrs = script.get("_attributions", [])
    title = script["title_candidates"][0] if script.get("title_candidates") else ""
    hook = script["scenes"][0]["narration"] if script.get("scenes") else ""
    hook_clean = re.sub(r"\*\*([^*]+?)\*\*", r"\1", hook).strip()
    theme = script["_meta"].get("theme", "")[:300]

    sep = "━━━━━━━━━━━━━━━━━━━━"
    desc_lines = [
        f"📡 {title}",
        "",
        sep,
        "  60秒ニュース速報 / Flash News",
        "  AIが届ける、世界の今を60秒で。",
        sep,
        "",
        "▼ 本日のヘッドライン",
        f"　{hook_clean}",
        "",
        "▼ 詳細",
        f"　{theme}",
        "",
        "▼ このチャンネルについて",
        "　AIが世界中のニュースを厳選・要約し、",
        "　30秒の報道調ショートにまとめてお届け。",
        "　テック、経済、政治、エンタメ、国際、社会——",
        "　ジャンル問わず、今この瞬間を速く、客観的に。",
        "",
        "#ニュース #速報 #Shorts #2026 #最新ニュース",
        "",
        sep,
    ]
    if attrs:
        desc_lines.append("📸 Photo Credits")
        attr_block = _wis.build_attribution_block(attrs)
        attr_lines = [l for l in attr_block.splitlines()
                      if l.strip() and "Image Credits" not in l]
        desc_lines.extend(attr_lines)
        desc_lines.append("")
        desc_lines.append(sep)

    return "\n".join(desc_lines)


def update_video(video_id: str, description: str,
                 title: str | None = None,
                 tags: list[str] | None = None) -> dict:
    yt = get_authenticated_service()

    # 既存の snippet を取得（update は全フィールドを送る必要があるため）
    existing = yt.videos().list(part="snippet", id=video_id).execute()
    if not existing.get("items"):
        raise RuntimeError(f"Video not found: {video_id}")
    snippet = existing["items"][0]["snippet"]

    # 更新
    snippet["description"] = description[:5000]
    if title:
        snippet["title"] = title[:100]
    if tags:
        snippet["tags"] = list(set(tags + DEFAULT_TAGS))[:500]

    body = {"id": video_id, "snippet": snippet}
    response = yt.videos().update(part="snippet", body=body).execute()
    return response


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video_id", help="YouTube video ID（URLの末尾）")
    p.add_argument("--run-dir", help="output/videos/<timestamp> から概要欄を再生成")
    p.add_argument("--description-file", help="既存テキストファイル指定")
    p.add_argument("--title", help="タイトルも更新する場合に指定")
    p.add_argument("--tags", nargs="*", default=[], help="タグ追加")
    args = p.parse_args()

    if args.description_file:
        desc = Path(args.description_file).read_text(encoding="utf-8")
    elif args.run_dir:
        desc = _build_stylish_description(Path(args.run_dir).resolve())
        # 再生成したテキストをファイルにも保存しておく（ついで）
        out_path = Path(args.run_dir).resolve() / "youtube_description.txt"
        out_path.write_text(desc, encoding="utf-8")
    else:
        raise SystemExit("--run-dir か --description-file のどちらかを指定してください")

    print(f"📝 更新内容プレビュー（先頭500字）:")
    print(desc[:500])
    print("...")
    print(f"\n📤 動画 {args.video_id} を更新中...")
    result = update_video(args.video_id, desc, title=args.title, tags=args.tags)
    print(f"✅ 更新完了: https://youtu.be/{args.video_id}")


if __name__ == "__main__":
    main()
