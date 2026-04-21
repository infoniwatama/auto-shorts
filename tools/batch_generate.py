"""複数のテーマから動画を順次生成するバッチ実行スクリプト"""
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent

# ネタ一覧（タイトル, テーマ本文）
TOPICS = [
    ("tim_cook_retire",
     "Apple CEO Tim Cook が2026年9月で退任、ハードウェア担当副社長の John Ternus(50歳) が後継CEOに就任。"
     "Cookは15年間のCEO時代にApple時価総額を4兆ドル超（20倍以上）に成長させた。"
     "Ternus は25年Appleに勤務、M1/M2/M3チップ等ハード開発を主導、AI時代のAppleを託される。"
     "Cook は Executive Chairman として残留。発表は2026年4月20日、株価は小幅安 -0.5%。"),

    ("spacex_xai_250b",
     "SpaceX が xAI を総額2500億ドル（約37兆円）で買収。史上最大のAI M&A 案件。"
     "イーロン・マスクは両社のオーナーで、実質的な自社統合。"
     "xAI の Grok と SpaceX の衛星網 Starlink を統合し、宇宙規模のAI配信基盤を構築する計画。"
     "ライバル OpenAI, Anthropic, Google に対抗するスケール戦略。2026年4月、業界最大級の衝撃。"),

    ("bts_hybe_arrest",
     "BTS 所属事務所 HYBE 創業者 Bang Si-hyuk 会長に韓国警察が逮捕令状を請求。"
     "容疑は IPO を巡る約200億ウォン（約22億円）規模の不正取引。"
     "2019年の IPO 前、投資家に上場計画はないと偽り持株を売らせ、"
     "上場後に別契約で利益を受領した疑い。BTSが兵役を終えて活動再開のタイミングと重なり衝撃。"
     "2026年4月21日、ソウル警察が発表。Bang は容疑段階で未逮捕。"),
]


def run_one(name: str, theme: str):
    print(f"\n{'='*60}")
    print(f"🎬 {name}")
    print(f"{'='*60}")
    cmd = ["python", "main.py", "--genre", "ai_news", theme]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=False)
    return p.returncode


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="特定のネタだけ実行（name指定）")
    args = ap.parse_args()

    for name, theme in TOPICS:
        if args.only and name not in args.only:
            continue
        rc = run_one(name, theme)
        if rc != 0:
            print(f"⚠️  {name} 失敗 (rc={rc}), 次へ進みます")


if __name__ == "__main__":
    main()
