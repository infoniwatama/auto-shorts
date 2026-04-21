"""AIニュースShortsのジャンル設定"""

NAME = "ai_news"

# ===== VOICEVOX =====
VOICEVOX_SPEAKER_ID = 13   # 青山龍星（ニュースキャスター調・ノーマル）
VOICEVOX_SPEED = 1.10
VOICEVOX_PITCH = 0.0
VOICEVOX_INTONATION = 1.05

# ===== Stable Diffusion（写実ニュース報道写真） =====
SD_STYLE_PREFIX = "photorealistic news photography, "
SD_STYLE_SUFFIX = (
    ", real-world scene, professional press photo, cinematic lighting, "
    "documentary photography, shallow depth of field, sharp focus, "
    "high detail, 4k, journalistic style, natural colors, no text, no letters"
)
SD_NEGATIVE = (
    "anime, cartoon, illustration, drawing, painting, neon, abstract, "
    "sci-fi, futuristic, cyberpunk, glowing, deformed, lowres, blurry, "
    "watermark, logo, signature, text, letters, japanese text, "
    "chinese text, extra limbs, bad anatomy, cluttered, oversaturated"
)

# ===== 固有名詞→画像オーバーライド =====
# 台本JSON の各 scene の "entity" フィールドが下記のいずれかなら、
# assets/entities/<entity>.png/.jpg があれば SDXL生成画像の代わりに使用
ENTITY_CANDIDATES = [
    # テック企業
    "openai", "anthropic", "google", "microsoft", "meta", "apple",
    "amazon", "nvidia", "tesla", "spacex", "samsung",
    # AI 関連
    "claude", "gpt", "gemini", "chatgpt",
    "ai_chip", "datacenter", "server_room",
    # 国・地域
    "japan", "usa", "china", "eu", "korea",
    # ニュース汎用
    "breaking_news", "courtroom", "police", "press_conference",
    "stock_chart_up", "stock_chart_down", "hacker", "cyber_attack",
    "ceo_meeting", "office", "city_skyline",
    # エンタメ
    "concert", "microphone", "stage", "kpop",
]

# ===== Subtitle =====
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "#0a1f3a"        # 濃紺の縁取り
SUBTITLE_EMPHASIS_COLOR = "#FFE633"      # 強調ワードの黄色
SUBTITLE_EMPHASIS_SHAKE = True           # 強調シーンで字幕シェイク

# ===== Thumbnail =====
THUMBNAIL_BADGE_TEXT = "速報"
THUMBNAIL_TEXT_COLOR = "#FFE633"          # 黄
THUMBNAIL_STROKE_COLOR = "#000000"

# ===== BGM =====
BGM_VOLUME = 0.05   # ナレーション優先、BGMは遠くでかすかに

# ===== キャラクター立ち絵（オプショナル、画像があれば自動表示） =====
CHARACTER_DIR = "ai_news"     # assets/characters/<dir>/<expression>.png
CHARACTER_POSITION = "right"  # "left" or "right"
EMOTION_TO_EXPRESSION = {
    "hook": "surprise",
    "normal": "normal",
    "shock": "surprise",
    "silence": "normal",
    "climax": "smile",
    "outro": "smile",
}

# ===== Claude prompt =====
PROMPT_TEMPLATE = """あなたは YouTube Shorts ニュースチャンネルの台本作家です。
扱うジャンルは問いません（テック、経済、政治、エンタメ、国際、社会等）。

【タスク】
以下のネタから **55-60秒のShorts台本（Shorts上限ギリギリまで詳しく）** を生成してください。
視聴者は一般層。ニュース番組のアナウンサー読み上げのように、
しっかりと内容を説明します。**報道調・ニュース解説調**で書きます
（断定形、体言止め可、敬体「です・ます」も可）。
キャラクター語尾（「〜のだ」「〜なのだ」「〜だぞ」等）は **絶対に使わない** こと。

【出力形式】
必ず以下のJSON形式のみで出力。前後の説明文・コードフェンス禁止。

{{
  "title_candidates": ["タイトル案1", "タイトル案2", "タイトル案3"],
  "thumbnail_text": "サムネ用の8文字以内の煽り文",
  "thumbnail_number": "サムネに大きく載せる数字または短いキーワード（例: '1600万件' '3社同盟' '24000'）",
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "ナレーション文。重要なキーワードは **二重アスタリスク** で囲む（後述）",
      "duration_sec": 3.0,
      "emotion": "hook | normal | shock | silence | climax | outro",
      "image_prompt": "SDXL/FLUX用の英語画像プロンプト。固有名詞や日本語禁止、視覚要素のみ。",
      "image_search_keyword": "Unsplash/Pexels検索用の英語キーワード(2-4語)。例: 'data center server room', 'business handshake meeting', 'cyber security hacker', 'asian city skyline night'。FLUXフォールバックする場合に画像生成プロンプトより検索ヒット率重視。null可。",
      "entity": "openai | anthropic | google | microsoft | meta | apple | amazon | nvidia | tesla | spacex | samsung | claude | gpt | gemini | chatgpt | ai_chip | datacenter | server_room | japan | usa | china | eu | korea | breaking_news | courtroom | police | press_conference | stock_chart_up | stock_chart_down | hacker | cyber_attack | ceo_meeting | office | city_skyline | concert | microphone | stage | kpop | null",
      "sfx": "ding | whoosh | pop | notification | silence | none",
      "bgm_intensity": "low | mid | high"
    }}
  ]
}}

【タイトル候補のフォーマット（重要）】
- 形式: 「【絵文字＋強ワード】内容｜2026」
- 例: 「【🚨衝撃】Apple CEO 15年ぶり交代｜2026」
- 例: 「【💥速報】BTS事務所トップに令状｜2026」
- 25-28字以内、最重要キーワードは左寄せ
- 絵文字は🚨💥🔥のいずれか1個（先頭の【】内に入れる）
- 数字が入れやすい場合は必ず入れる（金額・人数・時期等）

【強調ワードのマーキング（重要）】
- ナレーション内の最重要1ワードを **ダブルアスタリスク** で囲む
- 例: "AI業界に **激震** "、"なんと **1600万件** が流出"
- 各シーンで最大1ワード（多すぎると効果消える）
- hook/shock/climaxシーンは必ず1ワード強調を入れる
- normal/outroは強調なしでもOK
- 強調ワードはサムネ煽り文と関連する内容にする（記憶定着）

【entityフィールドの使い方】
- ナレーションで特定企業や具体物が出るシーンは、必ず該当 entity を指定
- 例: "OpenAIが発表" → entity="openai"、 "ハッキングが発覚" → entity="hacker"
- 該当しないシーン（フックや煽り等）は entity=null

【image_search_keyword の使い方（重要）】
- 各シーンに対し、Unsplash/Pexels で検索しやすい **英語キーワード** を必ず生成
- 2-4語の短いフレーズ。一般名詞中心。固有名詞は使わない（実在企業ロゴ写真は権利問題）
- 良い例: "data center server room", "business handshake meeting", "asian city skyline night",
  "cyber security hacker", "press conference podium", "world map digital",
  "executive office building", "computer screen code dark"
- 悪い例: "OpenAI office"（固有名詞）、"the moment they shook hands"（具体的過ぎ）、"AI"（一般的過ぎ）
- フック/煽りシーンも視覚的に合うキーワードを必ず入れる（hook なら "breaking news studio", climax なら "smartphone night dark" 等）

【画像入手の優先順位（システム側で自動）】
1. assets/entities/<entity>.png（手配済みロゴ等）
2. Unsplash/Pexels で image_search_keyword 検索
3. 上記ヒットなければ image_prompt から FLUX で生成
そのため image_prompt と image_search_keyword は両方とも内容と整合する形で書く

【構成ルール】
- 全体 **55-60秒（Shorts上限ギリギリまで最大限詰め込む）**
- scenesは **15-18個**（情報密度最大化）
- scene_id=1は必ずemotion="hook"、duration=2-3秒
- フック例「AI業界に **激震** が走りました」「衝撃のニュースです」
- 中盤に必ず1つemotion="shock"（数字や衝撃の事実で）
- 最後はemotion="outro"で **結論の一言で締める**（チャンネル登録誘導・フォロー誘導は禁止）

【1シーンの長さとテンポ】
- 1シーンのナレーションは **30-45文字** 推奨（最大50文字）
- 1シーン **3-4秒**（VOICEVOX 青山龍星は5字/秒程度で読む）
- ただし hook/shock は短く強く（15-25文字、2-3秒）
- 視聴者が同じ画像で5秒以上止まらないよう、長めの説明は2シーンに分割
- **合計ナレーション文字数 500-700文字を目標**（60秒上限で情報密度MAX）

【文体（重要・厳守）】
- **報道ニュース調**で、内容をしっかり説明する
- ですます調と体言止めを混ぜる（断定感とプロ感）
- 「〜のだ」「〜なのだ」「〜だぞ」等のキャラ語尾は **絶対NG**
- 単なる単語の連発（「OpenAIが動く。」「狙いは中国AI。」）はNG。文として情報を伝える
- 良い例:
  - "AI業界に **激震** が走りました"
  - "OpenAI・Anthropic・Googleが史上初めての連携を発表"
  - "中国企業による『蒸留』という盗用技術への対抗策です"
  - "Anthropicは単独で1600万件の不正利用を検出しました"
  - "次に狙われるのは、あなたが使うAIかもしれません"
- 悪い例（短すぎ・説明不足）:
  - "OpenAIが動く"
  - "狙いは中国AI"
  - "1600万件"
  - "AI冷戦の本格化"

【内容の網羅】
- 5W1Hを動画全体でカバー: いつ・誰が・何を・なぜ・どうした
- 数字や具体例は省略せず説明（「1600万件」だけでなく「1600万件もの不正利用が検出されました」）
- 専門用語は1度言い換える（例: 「蒸留、つまりモデルをマネして安く作る技術」）
- 以下を全部カバー:
  1. **いつ**: 発表日時・経緯
  2. **誰が**: 関係する企業名・人名（ただし個人のフルネームは避ける）
  3. **何を**: 何が起きたか、具体的アクション
  4. **なぜ**: 背景・動機・原因
  5. **規模**: 数字（回数・金額・人数・期間）
  6. **仕組み**: 技術的な説明（やさしい言い換え付き）
  7. **影響**: 業界や視聴者への意味
  8. **今後**: 次に何が起きるかの予測や警告

【ループ構造（重要）】
- Shortsはループ再生されるため、最後と最初を視覚的に繋げる
- scene_id=1 (hook) と最後の scene (outro) の image_prompt は **同じ構図・同じ視覚要素** を使うこと
- 例: 両方とも「futuristic blue purple neon network with floating orbs」を含める
- 視聴者が動画ループ時に「気づかず2周目」を見るように設計

【オチの意外性（重要）】
- climaxシーンに「視聴者が想定しない一言」を入れる
- 良い例: 「次に狙われるのは、あなたが使うAIかもしれません」
         「これはまだ氷山の一角に過ぎません」
         「AI覇権争いは新たな局面に突入しました」
- 単なる事実の繰り返し（NG例:「AI3社が連携しました」）ではなく、視聴者を引き込む引き

【outro（最後のシーン）のルール】
- **チャンネル登録・フォロー誘導は禁止**
- 「登録」「フォロー」「チャンネル」「登録者」等の単語を使わない
- 未来志向の定型句（「今後も」「これからも」「引き続き」「今後とも」）も禁止
- **結論を言い切る1文**で締める。ニュース番組のエンディングのように短く。
- OK例: 「AI時代の新たな転換点です。」
        「業界は、根本から変わりつつあります。」
        「静かに、しかし確実に、AI戦争は始まった。」
        「これは、始まりに過ぎません。」
        「見えない戦線で、AIの未来が争われています。」

【感情ガイド】
- hook: 冒頭3秒で視聴者を掴む
- normal: 事実の積み上げ、淡々と
- shock: 驚きの数字/事実を強調
- silence: 1.5秒の余韻（気づきを促す）
- climax: 結論の核心
- outro: CTA

【ナレーションの注意】
- 報道キャスター調（ですます＋体言止めミックス）
- 1秒あたり約 **5文字** （VOICEVOX青山龍星の想定速度）
- 難しい専門用語は1度だけ言い換える（例: 「蒸留」→「モデルをマネして作る技術」）
- 数字は必ず文脈に埋め込む（単体で出さず、意味が伝わる文に）
- キャラ語尾（のだ、ぞ、にゃ等）は使わない
- 「〜です」「〜ます」「〜でしょう」「〜と見られます」「〜と発表」等の報道調語尾を多用

【画像プロンプトの注意（写実報道写真スタイル）】
- ニュース報道風の写実的な実写写真
- ジャンルに応じた具体シーン:
  * テック/ビジネス: 会議室、CEO登壇、オフィス、サーバールーム、記者会見
  * 政治/国際: 国会、首脳会談、国旗、街並み
  * エンタメ: ステージ、コンサート会場、マイク、観客のシルエット
  * 事件/社会: 警察署、裁判所、街の一角、新聞、夜景
- 人物が出る場合は顔が認識できないアングル（後ろ姿、シルエット、手元のクローズアップ）
- 企業ロゴ・実在人物の顔・日本語/中国語/ハングル文字は画像に入れない
- 抽象的・SF的・ネオン系・カートゥーン調は **絶対に避ける**（報道風スタイル統一）

【テロップ折返しの目安】
- 1シーン30-45文字でも、文節改行で2-3行に収まる
- 強調ワードは長くても5-6文字までに（「**激震**」「**1600万件**」など）
- 「OpenAI」「Anthropic」「Google」など英語表記の固有名詞は不必要に繰り返さない

【テーマ/ネタ】
{theme}
"""
