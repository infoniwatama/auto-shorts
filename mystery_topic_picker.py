"""mystery_topics.json から、過去投稿と被らないトピックを Claude に選定させる。
news_fetcher の代わりに mystery 用トピック供給。
"""
import json
import os
import random
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

import config

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(config.ROOT / ".env")

TOPICS_FILE = config.ROOT / "mystery_topics.json"
HISTORY_FILE = config.ROOT / "mystery_history.json"


CLAUDE_PROMPT = """あなたは「夜の覗き窓 / Mystery Files」のプロデューサーです。
8-12分の長尺動画ネタを以下の候補から1つ選び、台本生成用の詳細テーマ文に展開してください。

【候補トピック】
{topics_block}

【絶対NG: 過去に投稿済みのネタ】
{posted_block}

【選定基準】
- 過去投稿と **同じトピック・同じ事件・同じ伝説** は絶対NG
- ジャンルバランス: 過去5本でどのカテゴリ（都市伝説/未解決事件/オカルト/陰謀論）が偏っていたか確認、別カテゴリを優先
- 視聴者が「続きが気になる」「コメントしたくなる」要素のあるもの優先
- 訴訟リスク・名誉毀損リスクの低いもの（公開情報・歴史的事件）を選ぶ
- 個人の特定情報（被害者・容疑者の実名）は使わない、地名と事案概要のみ

【出力】
必ず以下のJSON形式のみで出力。前後の説明文・コードフェンス禁止。

{{
  "category": "都市伝説 | 未解決事件 | オカルト・超常現象 | 陰謀論",
  "topic_seed": "選んだ候補トピックの1行サマリ",
  "format_hint": "single | ranking | series | mystery のどれが向くか + 一言理由",
  "theme_for_video": "動画台本生成に渡すための、5W1Hを含む詳細なテーマ文（300-600字）。
日本語、報道調と怪談調を混ぜる、固有名詞・地名・年号・舞台を必ず含める。
複数の説や矛盾点も触れる。Claude が長尺台本（30-45シーン）を作るのに十分な情報を提供する。"
}}
"""


def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8")).get("posted", [])
    except Exception:
        return []


def _build_topics_block() -> str:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    parts = []
    for cat, topics in data["categories"].items():
        # 各カテゴリからランダム5件抽出（毎回違う候補集合になる）
        sample = random.sample(topics, min(5, len(topics)))
        parts.append(f"### {cat}")
        for t in sample:
            parts.append(f"- {t}")
        parts.append("")
    return "\n".join(parts)


def pick_topic() -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)

    history = _load_history()
    if history:
        posted_block = "\n".join(
            f"- [{h.get('posted_at','')[:10]}] [{h.get('category','')}] {h.get('topic_seed','')[:60]}"
            for h in history[-30:]
        )
    else:
        posted_block = "（まだ投稿実績なし）"

    topics_block = _build_topics_block()

    prompt = CLAUDE_PROMPT.format(
        topics_block=topics_block,
        posted_block=posted_block,
    )

    msg = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    # JSON抽出
    import re as _re
    s = _re.search(r"\{.*\}", raw, _re.DOTALL)
    if not s:
        raise RuntimeError(f"Claude応答にJSONが見つからない:\n{raw[:500]}")
    return json.loads(s.group(0))


if __name__ == "__main__":
    selected = pick_topic()
    print(json.dumps(selected, ensure_ascii=False, indent=2))
