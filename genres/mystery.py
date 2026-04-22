"""ミステリー長尺チャンネル「夜の覗き窓 / Mystery Files」のジャンル設定

カバー範囲: 都市伝説 / 未解決事件 / オカルト・超常現象 / 陰謀論
動画長: 8-12分（長尺、Shortsではない）
話者: 白上虎太郎（speaker_id=29、不気味な男性）
スタイル: 暗い、シネマティック、ドキュメンタリー風
"""

NAME = "mystery"

# 長尺なので Claude の応答上限を大きく確保（50-70シーンのJSON、各150-250token）
CLAUDE_MAX_TOKENS = 18000

# ===== 動画サイズ（長尺横画面 16:9） =====
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FLUX_ASPECT_RATIO = "16:9"   # FLUX生成も横

# サムネは 16:9（YouTube 通常動画サムネ仕様）
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# 長尺はエンコード時間短縮のため高速プリセット使用
VIDEO_PRESET = "ultrafast"
VIDEO_FPS = 24    # 30→24 でフレーム数 -20%

# ===== VOICEVOX =====
VOICEVOX_SPEAKER_ID = 29   # 白上虎太郎（ふつう、男性低音、不気味）
VOICEVOX_SPEED = 0.95      # ゆっくり気味
VOICEVOX_PITCH = -0.03     # 少し低く
VOICEVOX_INTONATION = 1.15 # 抑揚やや強め（語りの起伏）

# ===== Stable Diffusion / FLUX =====
SD_STYLE_PREFIX = "dark cinematic photo, "
SD_STYLE_SUFFIX = (
    ", moody atmosphere, dim lighting, deep shadows, eerie mood, "
    "muted desaturated colors, film grain, photorealistic, high detail, "
    "moody composition, foggy, unsettling, mysterious, documentary style, "
    "no text, no letters, no watermark"
)
SD_NEGATIVE = (
    "anime, cartoon, illustration, drawing, painting, cute, bright, "
    "cheerful, colorful, saturated, smiling, comic, neon, sci-fi, "
    "deformed, lowres, blurry, watermark, logo, signature, text, letters, "
    "japanese text, chinese text, extra limbs, bad anatomy, gore, blood"
)

# ===== 固有名詞→画像オーバーライド =====
ENTITY_CANDIDATES = [
    # 場所・舞台
    "abandoned_house", "dark_alley", "japanese_shrine", "old_temple",
    "school_corridor", "tunnel", "forest", "lake", "bridge",
    "old_hospital", "old_mansion", "graveyard", "subway_station",
    # オカルト・霊
    "ghost_silhouette", "shadow_figure", "old_photo", "old_diary",
    "occult_symbol", "candle", "mirror", "window_at_night",
    # 事件
    "police_tape", "newspaper_clip", "evidence_bag", "interrogation_room",
    "courtroom", "missing_person_poster", "footprints",
    # 陰謀
    "secret_document", "hidden_room", "cipher_text", "world_map_dark",
    # その他
    "rotary_phone", "old_tv_static", "child_drawing", "footsteps_in_dust",
]

# ===== Subtitle =====
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_EMPHASIS_COLOR = "#FF4444"     # 赤の強調（怖さ・衝撃）
SUBTITLE_EMPHASIS_SHAKE = True

# ===== Thumbnail =====
THUMBNAIL_BADGE_TEXT = "閲覧注意"
THUMBNAIL_TEXT_COLOR = "#FF2222"
THUMBNAIL_STROKE_COLOR = "#000000"

# ===== BGM =====
BGM_VOLUME = 0.08    # 長尺なのでBGMは控えめに

# ===== Claude prompt =====
PROMPT_TEMPLATE = """あなたはYouTube長尺動画チャンネル「夜の覗き窓 / Mystery Files」の台本作家です。
扱うジャンル: 都市伝説、未解決事件、オカルト・超常現象、陰謀論。
視聴者: ミステリー好きの一般層。怖がりたい、知的好奇心を満たしたい。

【タスク】
以下のネタから **8-12分の長尺動画台本** を生成してください。
低音男性（白上虎太郎）が **静かに、ゆっくりと、不気味に語る** スタイル。
ホラー・サスペンス・ドキュメンタリーの要素を混ぜた、引き込まれる構成にする。

【動画フォーマットの選択】
内容に応じて以下のいずれかの構成を採用:
1. **単発深掘り型**「八尺様の真実 / 北関東連続女児誘拐の謎」 — 1つの事件/伝説を徹底解説
2. **ランキング型**「絶対に見てはいけない都市伝説5選」 — 複数を比較しながら
3. **シリーズ風**「日本の闇 第◯話: ◯◯」 — 1つのテーマで連作風
4. **真相究明型**「30年経っても解明されない◯◯」 — 謎と推測を提示

【出力形式】
必ず以下のJSON形式のみで出力。前後の説明文・コードフェンス禁止。

{{
  "format_type": "single | ranking | series | mystery",
  "title_candidates": ["候補1", "候補2", "候補3", "候補4", "候補5"],
  "thumbnail_text": "サムネ用の8文字以内の煽り文",
  "thumbnail_number": "サムネに大きく載せる短いキーワード（例: '実話' '深夜2時' '消えた家族'）",
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "ナレーション。重要キーワードは **二重アスタリスク** で囲む",
      "duration_sec": 12.0,
      "emotion": "intro | normal | shock | silence | climax | outro | reveal",
      "image_prompt": "FLUX/SDXL用の英語プロンプト。固有名詞や日本語禁止、視覚要素のみ。",
      "image_search_keyword": "Unsplash/Pexels検索用の英語キーワード(2-4語)。例: 'abandoned japanese house dark', 'old photograph mysterious', 'foggy forest night'",
      "entity": "abandoned_house | dark_alley | japanese_shrine | ... | null（assets/entities/<entity>.png 参照）",
      "sfx": "heartbeat | whisper | door_creak | wind | footstep | glass_break | clock_tick | silence | none",
      "bgm_intensity": "low | mid | high"
    }}
  ]
}}

【構成ルール（長尺の鉄則・必須遵守）】
- 全体 **音声で8-15分（最低8分）必達**、scenes は **50-70個**
- 各シーン **10-20秒**
- **合計ナレーション文字数 4000-5000文字（厳守）** ← 8分以上の音声に必要
- 白上虎太郎は約5字/秒で読む → 4000字 = 800秒 = 13.3分、5000字 = 16.6分
- 最初の30秒（フック+導入）が最重要、視聴者を捕まえる
- 文字数が足りない場合は、 **背景説明・歴史的文脈・複数の説・現場の描写を厚くする**
- 各シーン平均60-90文字。シーン数を増やしてOK

【動画の構成テンプレート（時間と文字数の目安）】
1. **フック（0-15秒、scene 1-2、emotion="intro"、約100-150字）**
   - 衝撃の問いかけ or 結論先出し
   - 例: "あなたは、午前2時に鏡を見たことがありますか？"
2. **イントロ（15-45秒、scene 3-5、"intro"、約200-300字）**
   - 「夜の覗き窓へようこそ」のチャンネル挨拶
   - 今夜のテーマ紹介、何が起きるかの予告
3. **背景・経緯（1-4分、scene 6-15、normal複数、約800-1200字）**
   - 事件/伝説の発端、舞台、関係者、年代背景
   - 当時の社会状況、地域文化、関係する歴史
   - 客観的事実を淡々と、複数のソースから
4. **核心部分（4-9分、scene 16-40、normal+shock混在、約1500-2000字）**
   - 詳細描写、目撃証言、状況証拠、当時の警察捜査
   - 関係者の証言を順に紹介（A氏、B氏、C氏…）
   - 中盤に必ず emotion="shock" を2-3回（衝撃の事実開示）
   - silence シーンで余韻
5. **謎・考察（9-12分、scene 41-55、reveal+climax、約800-1200字）**
   - 複数の説（説1: ◯◯説、説2: ◯◯説、説3: ◯◯説）
   - 矛盾点、未解明部分、専門家の見解
   - 「真実は誰も知らない」という余韻
6. **エンディング（12-15分、scene 56-70、outro、約200-400字）**
   - 結論または問いかけで締める
   - **チャンネル登録誘導は禁止**（「フォロー」「チャンネル登録」一切なし）
   - 例: "次は、あなたの番かもしれません。"
   - 例: "夜の覗き窓は、また開きます。"

【文字数を稼ぐコツ】
- 関係者の証言を「Aさんによると…」「次にBさんが語ったのは…」と順番に詳述
- 当時の社会背景・歴史的文脈を厚く
- 複数の解釈・説を3-5個提示し、それぞれ詳細に
- 現場の風景・気候・時刻を細かく描写
- 「ここで重要なのは…」「もうひとつ忘れてはならないのは…」で論点追加

【強調ワードのマーキング】
- ナレーション内の最重要1-2ワードを **ダブルアスタリスク** で囲む
- 例: "そこには **誰もいないはず** だった。"
- shock/climax/reveal のシーンには必ず1ワード強調
- normal は強調なしでもOK

【image_search_keyword】
- 各シーンに英語キーワード（2-4語）必須
- 「abandoned japanese alley night」「old photograph mysterious」「foggy forest dark」など
- Unsplash/Pexels で当たりやすい一般名詞中心
- 固有名詞・実在人物は使わない（権利問題）

【entityフィールド】
- 場所・物体が具体的な場合は entity を指定
- 例: ナレーションで神社が出る → entity="japanese_shrine"
- assets/entities/<name>.png があれば自動でその画像が使われる
- ない場合は image_prompt から FLUX 生成

【画像プロンプトのスタイル】
- 暗いシネマティック、ドキュメンタリー風
- 例: "abandoned tatami room with single dim light, eerie atmosphere, photorealistic, dark moody"
- 人物は出すなら **顔が見えない**（後ろ姿、シルエット、手元）
- 血や暴力的描写は禁止（収益化のため）
- 文字・ロゴ・実在人物は禁止

【ナレーションの注意】
- 白上虎太郎（男性、低音、不気味）の語り。**短文を多用**、間を取る
- 1秒あたり約5文字
- 「〜だった」「〜という」「〜と言われている」「〜らしい」を使い、断定を避ける
- 怪談特有の言い回し: 「真夜中のこと」「気づけば」「確かに見た」「いや、見たはずだ」
- 漢字の読み仮名は不要。難読語は避ける

【オチ・余韻のルール】
- 最後のシーン（outro）は **チャンネル登録誘導禁止**
- 結論を断定せず、視聴者の想像を促す
- 良い例:
  - "あなたが今夜、窓の外を見たとき。"
  - "その音は、まだ続いているのかもしれません。"
  - "夜の覗き窓は、決して閉じません。"

【NG表現】
- 「チャンネル登録」「フォロー」「いいね」「コメント」 → 絶対NG
- 「衝撃」「ヤバい」「マジで」等の俗語 → NG
- 「〜のだ」「〜なのだ」等のキャラ語尾 → NG（白上は普通の男性語り）
- 個人名（被害者・容疑者の本名）→ NG（プライバシーリスク）
- 「絶対」「100%」「確実」 → NG（断定の責任を負わない）

【テーマ/ネタ】
{theme}
"""
