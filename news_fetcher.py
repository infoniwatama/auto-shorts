"""RSS で当日のヘッドラインを集めて、Claude API で「最もバズ理想な1本」を選定する。

使い方:
  python news_fetcher.py            # トップネタを表示
  python news_fetcher.py --json     # JSON出力（main.py に渡す形）
  python news_fetcher.py --top 3    # 上位3本
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import feedparser
import anthropic
from dotenv import load_dotenv

import config

load_dotenv(config.ROOT / ".env")


# ===== RSS フィード（無料、APIキー不要） =====
RSS_FEEDS = {
    # 日本 総合
    "NHK 主要": "https://www.nhk.or.jp/rss/news/cat0.xml",
    "NHK 国際": "https://www.nhk.or.jp/rss/news/cat6.xml",
    "Yahoo!主要": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
    "Yahoo!国際": "https://news.yahoo.co.jp/rss/topics/world.xml",
    "Yahoo!IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "Yahoo!経済": "https://news.yahoo.co.jp/rss/topics/business.xml",
    "Yahoo!エンタメ": "https://news.yahoo.co.jp/rss/topics/entertainment.xml",
    # テック日本
    "ITmedia": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",
    "ASCII": "https://ascii.jp/rss.xml",
    # テック海外
    "TechCrunch JP": "https://jp.techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    # AI 専門
    "AI News (英語)": "https://www.artificialintelligence-news.com/feed/",
}


def fetch_recent_headlines(hours: int = 24, max_per_feed: int = 5) -> list[dict]:
    """各フィードから直近X時間のヘッドラインを集める"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"  [warn] {source} 取得失敗: {e}", file=sys.stderr)
            continue
        for entry in feed.entries[:max_per_feed]:
            published = None
            for k in ("published_parsed", "updated_parsed"):
                if getattr(entry, k, None):
                    import time
                    published = datetime.fromtimestamp(
                        time.mktime(getattr(entry, k)), tz=timezone.utc
                    )
                    break
            if published and published < cutoff:
                continue
            items.append({
                "source": source,
                "title": getattr(entry, "title", "").strip(),
                "summary": re.sub(r"<[^>]+>", "",
                                   getattr(entry, "summary", ""))[:300].strip(),
                "url": getattr(entry, "link", ""),
                "published": published.isoformat() if published else None,
            })
    return items


CLAUDE_SCORE_PROMPT = """あなたはYouTube Shortsニュースチャンネルのプロデューサーです。
以下の本日のニュースヘッドラインリストから、**最もバズる可能性が高い** トップ{top_n}本を選んでください。

【選定基準】（上から優先）
1. 数字インパクトがあるか（金額・人数・割合・規模）
2. 衝撃性・予想外性があるか
3. 一般視聴者が感情的に反応するか（怒り・驚き・笑い・感動）
4. 業界の構造を変える/重要な転換点か
5. 知名度の高い企業・人物・国が関与しているか

【避けるべきネタ】
- 個人の死亡事故（センシティブ、収益化リスク）
- 政治の党派的に分かれる内容（炎上リスク）
- 暴力・性的・差別的内容
- 単発の事件で文脈を要するもの
- すでに何度も報道されてる古い話題

【出力形式】
必ず以下のJSON形式のみで出力。前後の説明文・コードフェンス禁止。

{{
  "selected": [
    {{
      "rank": 1,
      "title": "選んだヘッドライン",
      "source": "ソース名",
      "url": "URL",
      "buzz_reason": "なぜバズるか1行説明",
      "theme_for_video": "動画台本生成に渡すための、5W1Hを含む詳細なテーマ文（200-400字）。日本語、報道調、固有名詞・数字を必ず含める。Claude が動画台本を作る際に十分な情報を提供する。"
    }}
  ]
}}

【ヘッドラインリスト】
{headlines}
"""


def select_top_topic(items: list[dict], top_n: int = 1) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)

    if not items:
        raise RuntimeError("ヘッドラインが0件。RSS取得を確認してください。")

    headlines_text = "\n".join(
        f"- [{i['source']}] {i['title']} ({i['url']})\n  {i['summary']}"
        for i in items[:80]   # トークン節約のため最大80件
    )
    prompt = CLAUDE_SCORE_PROMPT.format(top_n=top_n, headlines=headlines_text)

    msg = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    # JSON抽出（前後にコードフェンス等あれば剥がす）
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    return json.loads(raw[start:end + 1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--top", type=int, default=1, help="選定する本数")
    p.add_argument("--hours", type=int, default=24, help="何時間遡るか")
    p.add_argument("--json", action="store_true", help="JSON出力")
    args = p.parse_args()

    print(f"📰 RSS から直近 {args.hours}時間のヘッドライン取得中...", file=sys.stderr)
    items = fetch_recent_headlines(hours=args.hours)
    print(f"   → {len(items)} 件取得", file=sys.stderr)

    print(f"🤖 Claude で TOP{args.top} 選定中...", file=sys.stderr)
    result = select_top_topic(items, top_n=args.top)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for sel in result["selected"]:
            print(f"\n=== Rank {sel['rank']} ===")
            print(f"📌 {sel['title']}")
            print(f"   出典: {sel['source']}")
            print(f"   URL : {sel['url']}")
            print(f"💥 バズ理由: {sel['buzz_reason']}")
            print(f"🎬 テーマ:\n{sel['theme_for_video']}")


if __name__ == "__main__":
    main()