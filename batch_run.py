"""指定本数を連続生成（history更新→次のネタ選定を自動で繰り返す）"""
import os
import sys
import traceback

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import news_fetcher
import main

N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
GENRE = sys.argv[2] if len(sys.argv) > 2 else "ai_news"

results = []
for i in range(N):
    print(f"\n{'=' * 60}")
    print(f"===== {i + 1}/{N} =====")
    print(f"{'=' * 60}", flush=True)
    try:
        items = news_fetcher.fetch_recent_headlines()
        result = news_fetcher.select_top_topic(items, top_n=1)
        cand = result["selected"][0]
        title = cand["title"]
        theme = cand["theme_for_video"]
        print(f"PICKED: {title}", flush=True)
        out = main.run(genre_name=GENRE, theme=theme)
        results.append((i + 1, title, str(out), None))
    except Exception as e:
        print(f"❌ iter {i + 1} failed: {e}", flush=True)
        traceback.print_exc()
        results.append((i + 1, None, None, str(e)))

print("\n" + "=" * 60)
print("📊 FINAL SUMMARY")
print("=" * 60)
for idx, title, out, err in results:
    status = "✅" if out else "❌"
    print(f"{status} [{idx}] {title or err}")
    if out:
        print(f"      → {out}")
