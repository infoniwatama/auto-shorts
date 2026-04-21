"""既存の script.json に対してWeb検索を再実行し、attributionを復元。
画像はDLせず、メタデータのみ取得してクレジットを再生成する。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import json
import config
from web_image_search import unsplash_search, pexels_search, build_attribution_block


def rebuild(run_dir: Path) -> None:
    script_path = run_dir / "script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))

    attributions = []
    for scene in script["scenes"]:
        kw = scene.get("image_search_keyword")
        if not kw:
            continue
        # scene側に既にあればスキップ
        if scene.get("_attribution"):
            attributions.append(scene["_attribution"])
            continue
        info = unsplash_search(kw)
        if info is None:
            info = pexels_search(kw)
        if info is not None:
            scene["_attribution"] = info
            attributions.append(info)
            print(f"scene{scene['scene_id']:02d} [{info['source']}] '{kw}' → {info['photographer']}")
        else:
            print(f"scene{scene['scene_id']:02d} MISS '{kw}'")

    script["_attributions"] = attributions
    script_path.write_text(
        json.dumps(script, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # youtube_description.txt も更新
    desc_lines = [
        script["title_candidates"][0] if script.get("title_candidates") else "",
        "",
        f"テーマ: {script['_meta'].get('theme', '')[:200]}",
    ]
    if attributions:
        desc_lines.append(build_attribution_block(attributions))
    (run_dir / "youtube_description.txt").write_text(
        "\n".join(desc_lines), encoding="utf-8"
    )
    print(f"\n✅ 再構築: {len(attributions)}件のクレジット")


if __name__ == "__main__":
    run_dir = Path(sys.argv[1]).resolve()
    rebuild(run_dir)
