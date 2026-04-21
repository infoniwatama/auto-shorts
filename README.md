# auto-shorts: 自動生成 YouTube Shorts パイプライン

ジャンル切替式の Shorts 自動生成ツール。
Claude API + VOICEVOX + ComfyUI(SDXL) + MoviePy で半自動。

## 対応ジャンル

| genre | 用途 | 話者 | 画像スタイル |
|---|---|---|---|
| `ai_news` | AIニュース解説 | ずんだもん(3) | 青紫ネオン、テック調 |
| `horror` | 怪談・怖い話 | 玄野武宏(11) | 暗いシネマ、写実的 |

## アーキテクチャ

```
Theme(string) + genre
  → Claude API   (script_gen.py)        → JSON 台本
  → VOICEVOX     (tts.py)               → シーンごと wav
  → ComfyUI/SDXL (image_gen.py)         → シーンごと png
  → MoviePy      (video_assemble.py)    → 1080x1920 mp4
  → PIL          (thumbnail_gen.py)     → サムネ下書き png
```

## 必要な常駐サービス

| サービス | 起動方法 | ポート |
|---|---|---|
| VOICEVOX | アプリ起動 | 50021 |
| ComfyUI | `G:\AI\ComfyUI\run_nvidia_gpu.bat` | 8188 |

## 初回セットアップ

```bash
pip install -r requirements.txt
copy .env.example .env
# .env に ANTHROPIC_API_KEY を記入
```

## 使い方

### テーマから新規生成
```bash
python main.py --genre ai_news "OpenAI が新モデル発表"
python main.py --genre horror "深夜のコンビニで起きた不可解な出来事"
```

### 既存台本から再生成（音声・画像はキャッシュ、動画だけ作り直し）
```bash
python main.py --script output/scripts/ai_news_20260421_120000.json
```

## 出力構成

```
output/scripts/<genre>_<timestamp>.json   # 全台本
output/videos/<timestamp>/
├── audio/scene_NN.wav
├── images/scene_NN.png
├── script.json
├── <timestamp>_shorts.mp4
└── <timestamp>_thumb.png        # サムネ下書き
```

## ジャンル追加方法

`genres/<name>.py` を新規作成。`horror.py` をコピペして以下を変えるだけ:
- `NAME` / `VOICEVOX_*` / `SD_STYLE_*` / `SUBTITLE_*` / `THUMBNAIL_*`
- `PROMPT_TEMPLATE`（Claude API への指示）
- `EMOTION_TO_EXPRESSION`（立ち絵の表情マッピング、任意）

## アセット追加（任意、置けば自動使用）

### BGM
`assets/bgm/<genre>/` または `assets/bgm/` に mp3/wav を配置。ジャンル別フォルダ優先。
- AI ニュース推奨: DOVA-SYNDROME（https://dova-s.jp/） 「テクノ」「シネマティック」カテゴリ
- 怖い話推奨: 同じく「ホラー・ダーク」カテゴリ

### SFX
`assets/sfx/<genre>/<name>.mp3` または `assets/sfx/<name>.mp3`。台本の `sfx` フィールドに対応:
- AI ニュース系: `ding`, `whoosh`, `pop`, `notification`
- 怪談系: `heartbeat`, `whisper`, `glass_break`, `wind`, `door_creak`

推奨: 効果音ラボ（https://soundeffect-lab.info/）

### 固有名詞画像（entity images、AI ニュース推奨）
台本JSONの各シーンの `entity` フィールドに `openai`, `anthropic`, `google` 等が入ります。
`assets/entities/<entity>.png` を置くと、SDXL生成画像の代わりにそちらが使われます。
報道写真風の SDXL 画像と組み合わせて、リアル感が大幅UP。

#### 推奨セット（AI ニュース）
`assets/entities/` に以下を配置:
- `openai.png` — OpenAI ロゴ or オフィス写真
- `anthropic.png` — Anthropic ロゴ
- `google.png` — Google ロゴ
- `microsoft.png`, `meta.png`
- `claude.png`, `gpt.png`, `gemini.png`, `chatgpt.png`
- `ai_chip.png`, `datacenter.png`, `server_room.png`
- `shield.png` — セキュリティ
- `hacker.png`, `cyber_attack.png`
- `japan.png`, `usa.png`, `china.png`, `eu.png`
- `stock_chart_up.png`, `stock_chart_down.png`
- `ceo_meeting.png`, `office.png`, `press_conference.png`

#### 入手元（公式ブランドリソース）
- OpenAI: https://openai.com/brand
- Anthropic: https://www.anthropic.com/brand
- Google: https://about.google/brand-resource-center/
- Microsoft: https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks
- Meta: https://about.meta.com/brand/resources/
- フリー写真: Unsplash (https://unsplash.com/), Pexels (https://www.pexels.com/) で検索

ロゴの利用には各社のガイドラインがあります。報道目的・引用範囲内なら一般的にOK。
画像が無い entity は SDXL 生成画像にフォールバックするため、揃えなくても動きます。

### キャラクター立ち絵（オプション、強推奨）
`assets/characters/<genre.CHARACTER_DIR>/<expression>.png` に配置。

#### AI ニュース（ずんだもん）
`assets/characters/ai_news/` に以下を配置:
- `normal.png` — 通常表情
- `surprise.png` — 驚き表情
- `smile.png` — 笑顔

**入手方法**: 著作権の関係で自動DLできません。以下から手動DL:
1. ずんだもん公式素材（坂本アヒル氏）: https://seiga.nicovideo.jp/seiga/im11206626
   - PSD配布、説明文記載のパスワードでアップローダーから入手
   - PSDをPhotoshop等で開き、表情レイヤー切替→各PNGエクスポート
2. そざい屋ベリィ版: https://sozaberi.com/zundamon_01/
3. 個人作家版（BOOTH等）: https://booth.pm/ja/items/5585469

ライセンス: ずんずんPJガイドライン遵守（https://zunko.jp/con_ongen_kiyaku.html）

立ち絵がないと顔出しなしの「文字+音声+画像」だけになり、視聴維持率が大きく落ちます（チャンネル分析レポートより）。本格運用前に必ず追加推奨。

#### 怪談 (horror)
`assets/characters/horror/` に以下を配置:
- `normal.png`, `scared.png`

怪談系は立ち絵なしの方がシリアスに見えるため任意。

## 設定変更（config.py）

| 項目 | デフォルト | 用途 |
|---|---|---|
| `SD_CHECKPOINT` | `sd_xl_base_1.0.safetensors` | 質UP→Juggernaut XL DLして書換 |
| `SUBTITLE_FONT_SIZE` | 70 | 字幕サイズ |
| `SUBTITLE_FONT_WEIGHT` | 900 | Variable font 太さ |
| `BGM_VOLUME` (genre側) | 0.15 | 音声100:BGM15:SFX80 比率 |
| `SFX_VOLUME` | 0.8 | 上記同 |
| `SILENCE_PAD_BEFORE_SHOCK` | 0.4 | shock直前の余韻秒 |
| `CHARACTER_WIDTH_RATIO` | 0.45 | 立ち絵の画面幅比 |

## 機能

- ✅ ジャンル切替（`--genre`）
- ✅ 強調ワード字幕（`**word**` で囲むと黄色＋シェイク）
- ✅ タイトルテンプレ（【🚨衝撃】〜｜2026最新 形式）
- ✅ サムネ自動下書き生成
- ✅ ループ構造（hook と outro が同構図）
- ✅ オチの意外性（climax で twist）
- ✅ shock 直前の無音パッド（pattern interrupt）
- ✅ 音量比 100:15:80（音声:BGM:SFX）
- ✅ Ken Burns ズーム
- ✅ シーン間クロスフェード
- ✅ 音声/画像のキャッシュ（再生成時に高速）
- ✅ キャラ立ち絵オーバーレイ（アセットあれば自動）

## 人間の作業（自動化禁物）

| タスク | 所要 | 重要度 |
|---|---|---|
| サムネ最終調整（自動下書きをCanvaで） | 20-30分 | ★★★（CTR半減リスク） |
| タイトル選定（候補3つから） | 5分 | ★★★ |
| 台本の冒頭3秒チェック | 5分 | ★★★ |
| YouTube アップロード | 5分 | ★★ |

→ 1本あたり人間40分弱。
