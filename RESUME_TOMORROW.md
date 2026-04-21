# 明日の再開手順

## 事前に起動しておくもの
1. **VOICEVOX** を起動（ポート 50021）
2. ComfyUI は不要（FLUX APIでやるので）

## 手順

### 1. Anthropic 動画の再レンダ（音量修正版）
```bash
cd C:\Users\souro\auto-shorts
python main.py --script "output/scripts/ai_news_20260421_235643.json"
```
→ キャッシュあり、画像は全部生成済み。音声のみ再生成＋動画組立（5-10分）

### 2. アップロード（サムネなし）
```bash
python youtube_upload.py output/videos/20260421_235643 --privacy private
```

### 3. 3本バッチ（Tim Cook + SpaceX + BTS）
```bash
python tools/batch_generate.py
```
→ 1本15分×3 = 45分。完了後に生成される `output/videos/<ts>/` を順次アップ:

```bash
# 各 run_dir に対して
python youtube_upload.py output/videos/<TIMESTAMP> --privacy private
```

## 状態サマリ（2026-04-22 寝落ち時点）

### 完成済み・アップ済み
- https://youtu.be/CbofddJGtPk（AI3社同盟、改行・スタイル修正済み）

### 完成済み・アップ未
- `output/videos/20260421_235643/` (Anthropic首位、**音量古い版**。再レンダしてから上げる)

### 未着手
- Tim Cook CEO 退任
- SpaceX xAI $250B 買収
- BTS HYBE 会長逮捕令状

## 設定変更リスト（寝る前に確定済み）
- BGM音量: 0.05（かすか）
- ナレーション音量: 1.3（ブースト）
- SFX音量: 0.6
- 音声末尾カット: -0.02s
- 字幕位置: 中央（Y 0.50）
- CTA撤廃（outroはチャンネル登録誘導なし、結論1文で締め）
- プロンプト: AI特化 → 全ジャンルニュース対応
- 概要欄: スタイリッシュ版
- バッジ: 「速報」

## 要注意
- **電話番号認証まだ**: https://www.youtube.com/verify
  認証しないとサムネ自動設定不可（手動ならOK）
- Replicate クレジット: 当初 $10 入れて、約 $1-1.5 使用済み（残 $8-9）
