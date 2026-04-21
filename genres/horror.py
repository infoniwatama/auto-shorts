"""怖い話/怪談Shortsのジャンル設定"""

NAME = "horror"

# ===== VOICEVOX =====
VOICEVOX_SPEAKER_ID = 11   # 玄野武宏（ノーマル）
VOICEVOX_SPEED = 1.05
VOICEVOX_PITCH = -0.02
VOICEVOX_INTONATION = 1.1

# ===== Stable Diffusion =====
SD_STYLE_PREFIX = "cinematic photo, "
SD_STYLE_SUFFIX = (
    ", dark horror atmosphere, dim lighting, deep shadows, eerie mood, "
    "muted desaturated colors, film grain, photorealistic, high detail, "
    "moody composition, foggy, unsettling"
)
SD_NEGATIVE = (
    "anime, cartoon, illustration, drawing, painting, cute, bright, "
    "cheerful, colorful, saturated, smiling face, text, watermark, "
    "logo, signature, lowres, blurry, deformed, extra limbs, bad anatomy"
)

# ===== Subtitle =====
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_EMPHASIS_COLOR = "#FF4444"     # 強調ワードは赤（怖い系）
SUBTITLE_EMPHASIS_SHAKE = True

# ===== Thumbnail =====
THUMBNAIL_BADGE_TEXT = "閲覧注意"
THUMBNAIL_TEXT_COLOR = "#FF2222"
THUMBNAIL_STROKE_COLOR = "#000000"

# ===== BGM =====
BGM_VOLUME = 0.15

# ===== キャラクター立ち絵（怖い話なので通常はキャラ非表示） =====
CHARACTER_DIR = "horror"
CHARACTER_POSITION = "right"
EMOTION_TO_EXPRESSION = {
    "hook": "normal",
    "normal": "normal",
    "shock": "scared",
    "silence": None,    # silenceは立ち絵も消す
    "climax": "scared",
    "outro": "normal",
}

# ===== Claude prompt =====
PROMPT_TEMPLATE = """あなたはYouTube Shorts怪談チャンネルの台本作家です。

【タスク】
以下のテーマから30秒のShorts台本を生成してください。

【出力形式】
必ず以下のJSON形式のみで出力。前後の説明文・コードフェンス禁止。

{{
  "title_candidates": ["タイトル案1", "タイトル案2", "タイトル案3"],
  "thumbnail_text": "サムネ用の8文字以内の煽り文",
  "thumbnail_number": "サムネに大きく載せる短いキーワード（例: '実話' '深夜3時' '消えた'）",
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "ナレーション文",
      "duration_sec": 3.0,
      "emotion": "hook | normal | shock | silence | climax | outro",
      "image_prompt": "FLUX/SDXL用の英語画像プロンプト。固有名詞や日本語禁止、視覚要素のみ。",
      "sfx": "heartbeat | whisper | glass_break | wind | door_creak | silence | none",
      "bgm_intensity": "low | mid | high"
    }}
  ]
}}

【タイトル候補のフォーマット（重要）】
- 形式: 「【絵文字＋強ワード】内容｜実話/怪談」
- 例: 「【⚠️実話】深夜のコンビニで起きた怪奇現象｜怪談」
- 例: 「【🕯️注意】消えた家族の謎｜未解決事件」
- 25-28字以内、最重要キーワードは左寄せ
- 絵文字は⚠️🕯️👁🌙のいずれか1個（先頭の【】内）
- 数字または時刻を1つ入れる（「深夜3時」「3人」「30年前」等）

【強調ワードのマーキング（重要）】
- ナレーション内の最重要1ワードを **ダブルアスタリスク** で囲む
- 例: "それは **絶対に** あり得ないことだった"、"そこには **誰もいない** はずだった"
- 各シーンで最大1ワード
- hook/shock/climaxシーンは必ず1ワード強調

【構成ルール】
- 全体30-35秒、scenesは7-10個
- scene_id=1は必ずemotion="hook"、duration=3秒、視聴者が即"気になる"問いを1つ
- 中盤に必ず1つ以上emotion="shock"を配置
- 最後はemotion="outro"でCTA「続きはコメント欄」or「チャンネル登録で次回」
- silenceシーンは1.5-2秒、ナレーション空文字でOK

【ループ構造（重要）】
- Shortsはループ再生される。scene_id=1 と outro シーンの image_prompt は **同じ構図・同じ場所・同じ照明** にすること
- 例: 両方とも「dark abandoned japanese alley at midnight, foggy」など
- 視聴者がループ時に気づかず2周目を見る設計

【オチの意外性（重要）】
- climaxシーンに「視聴者が想定しない一言」を入れる
- 良い例: 「実は今もそこにいるのだという」「あなたの後ろにも、ね」「それは今夜起きた話だ」
- 視聴者を不安にさせる引きで終わる

【感情ガイド】
- hook: 冒頭3秒。「これは絶対に見てはいけない動画です」等
- normal: 通常進行、淡々と事実
- shock: 衝撃の事実開示、視聴者が"えっ"となる箇所
- silence: 間を作る、無音演出
- climax: 最大の見せ場
- outro: 終わり、CTA

【ナレーションの注意】
- 1秒あたり約7文字（VOICEVOX読み上げ速度基準）
- duration_secはnarration文字数÷7で計算
- 漢字の読み仮名は不要だが難読語は避ける
- 句読点で自然な間を作る
- 怪談特有の言い回し（〜だという、〜らしい、〜と言われている）を多用

【画像プロンプトの注意】
- 全シーンで世界観を統一すること
- 人物が出る時も顔のクローズアップは避け、後ろ姿・シルエット・遠景中心
- 日本的な要素（traditional japanese house, narrow alley, abandoned shrine等）を盛り込む
- 単純な情景描写でOK、長すぎない方が良い

【テーマ】
{theme}
"""
