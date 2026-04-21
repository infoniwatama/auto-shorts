"""Claude API でジャンル別 Shorts 台本（JSON）を生成"""
import os
import json
import re
from datetime import datetime

import anthropic
from dotenv import load_dotenv

import config

load_dotenv(config.ROOT / ".env")


def _strip_to_json(text: str) -> str:
    """Claudeの応答からJSON部分だけを抽出"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"JSON not found in response: {text[:200]}")
    return text[start:end + 1]


def generate_script(theme: str, genre) -> dict:
    """テーマとジャンルから台本JSONを生成して返す。同時にファイル保存。"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment or .env")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = genre.PROMPT_TEMPLATE.format(theme=theme)

    msg = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.CLAUDE_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text
    script = json.loads(_strip_to_json(raw))

    config.ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = config.OUT_SCRIPTS / f"{genre.NAME}_{ts}.json"
    out_path.write_text(
        json.dumps(script, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    script["_meta"] = {
        "timestamp": ts,
        "path": str(out_path),
        "theme": theme,
        "genre": genre.NAME,
    }
    return script


if __name__ == "__main__":
    import sys
    from genres import load_genre
    genre_name = sys.argv[1] if len(sys.argv) > 1 else "horror"
    theme = sys.argv[2] if len(sys.argv) > 2 else "テスト"
    g = load_genre(genre_name)
    s = generate_script(theme, g)
    print(f"Generated: {s['_meta']['path']}")
    print(f"Title candidates: {s['title_candidates']}")
    print(f"Scenes: {len(s['scenes'])}")
