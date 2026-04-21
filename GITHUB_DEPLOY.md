# GitHub Actions デプロイ手順

毎日6:00 JSTに自動でニュースを取得→動画生成→YouTube投稿（private）。

## 1. GitHub プライベートリポジトリ作成（5分）

1. https://github.com/new を開く
2. 設定:
   - Owner: **infoniwatama**
   - Repository name: **auto-shorts**
   - Description: 自動ニュース動画生成パイプライン
   - **Private** を選択（必須、APIキーが含まれるため）
   - "Add README/.gitignore/license" は **チェックしない**（既存ファイルがあるため）
3. 「Create repository」

## 2. ローカルから初回push（コマンドコピペ）

```powershell
cd C:\Users\souro\auto-shorts
git init -b main
git add .
git commit -m "Initial: auto-shorts pipeline with cloud workflow"
git remote add origin https://github.com/infoniwatama/auto-shorts.git
git push -u origin main
```

初回 push で GitHub アカウントの認証画面が出ます。
- ブラウザでGitHubログイン → 「Authorize git-credential-manager」

## 3. Secrets 登録（10分）

GitHub リポジトリページ → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

以下7つを登録:

| Name | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-IcVDY63...`（既存） |
| `REPLICATE_API_TOKEN` | `r8_YuP31...`（既存） |
| `PEXELS_API_KEY` | `ELW3lZnK1...`（既存） |
| `UNSPLASH_ACCESS_KEY` | `aopdx_CoCEFXMzQH...`（既存） |
| `YOUTUBE_CLIENT_SECRET_JSON` | `client_secret.json` の中身全体（{"installed":...}全文） |
| `YOUTUBE_TOKEN_JSON` | `token.json` の中身全体 |

`.env` の各値と、ローカルの `client_secret.json` `token.json` の中身そのままコピペ。

### 値の取り出し方
```powershell
# .env の中身を表示
type C:\Users\souro\auto-shorts\.env

# client_secret.json の中身
type C:\Users\souro\auto-shorts\client_secret.json

# token.json の中身（OAuth後生成済み）
type C:\Users\souro\auto-shorts\token.json
```

JSONはコピペ時に改行・空白そのまま貼ってOK（GitHub Secretsは複数行対応）。

## 4. ワークフロー初回実行（手動トリガー）

1. GitHub リポジトリ → **Actions** タブ
2. 左メニュー「Daily AI Flash News」をクリック
3. 「Run workflow」ボタン → 「Run workflow」
4. 5-10分待つ → 緑チェック ✅ なら成功
5. https://studio.youtube.com/ で動画が private で上がってるか確認

## 5. 自動実行スケジュール

`.github/workflows/daily-news.yml` の cron を編集:

```yaml
on:
  schedule:
    - cron: "0 21 * * *"  # 毎朝6:00 JST（21:00 UTC前日）
```

頻度を変えたい場合:
- 毎日2回: `"0 9,21 * * *"` （朝6時 + 夕方6時 JST）
- 平日のみ: `"0 21 * * 0-4"` （日-木の21UTC = 月-金朝JST）
- 週1回: `"0 21 * * 0"` （日21UTC = 月朝JST）

cron文法: https://crontab.guru/

## 6. テーマを手動で指定したい時

1. Actions → 「Daily AI Flash News」→ 「Run workflow」
2. **theme** 欄にテーマ文を貼る
3. **privacy** で公開設定を選ぶ（private/unlisted/public）
4. 「Run workflow」

## 7. ログ確認とデバッグ

- **失敗時**: Actions ページで該当 run をクリック → 各ステップのログを確認
- **生成された動画**: 完了した run の下部「Artifacts」から ZIP ダウンロード可能（7日保持）
- **YouTube 上**: https://studio.youtube.com/ コンテンツ で確認

## 8. コスト試算（月額）

| 項目 | コスト | 内訳 |
|---|---|---|
| GitHub Actions | **$0** | 月2000分の無料枠内（1日15分×30=450分） |
| Anthropic Claude | $5-10 | 1動画あたり~$0.20×30 |
| Replicate FLUX | $5-15 | 画像生成（Web優先で大半は$0） |
| YouTube/Pexels/Unsplash | $0 | 全部無料 |
| **合計** | **$10-25/月** | |

## 9. 注意事項

- **client_secret.json と token.json は絶対にコミットしない**（.gitignore済み）
- Replicate のクレジットが切れたら Replicate ダッシュボードでチャージ
- YouTube アカウントの電話番号認証完了後はサムネも自動設定される
- Workflow ログにシークレットは出ない（自動でマスク）

## トラブルシュート

### "VOICEVOX did not become ready in time"
→ サービスコンテナ起動失敗。`.github/workflows/daily-news.yml` のwait部分のリトライ回数を増やす（90→120）

### "Insufficient credit" (Replicate)
→ https://replicate.com/account/billing でチャージ

### "quotaExceeded" (YouTube API)
→ 1日6本までの上限（YouTube Data APIは1upload=1600単位、無料枠10000/日）

### token.json が期限切れ
→ ローカルで `python youtube_upload.py` を1回実行 → 新しい token.json 生成 → GitHub Secret 更新