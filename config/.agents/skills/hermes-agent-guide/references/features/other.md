# Web ダッシュボード・God Mode・セキュリティモデル・メッセージングゲートウェイ概要

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/overview

## Web ダッシュボード

```bash
hermes dashboard
```

ブラウザベースの管理 UI。`pip install hermes-agent[web]` が前提条件。

### ページ構成

Status / Config / API Keys / Sessions / Logs / Analytics / Cron / Skills

REST API エンドポイントも提供。テーマ切替対応。

## God Mode (G0DM0D3)

オプションのレッドチーミングスキル。3 つの攻撃モードを搭載。

| モード | 説明 |
|--------|------|
| GODMODE CLASSIC | システムプロンプトテンプレートによる脱獄 |
| PARSELTONGUE | 33 種の入力難読化テクニック |
| ULTRAPLINIAN | 最大 55 モデルのマルチモデルレーシング |

`execute_code` 経由で `auto_jailbreak()` を呼び出して使用。

## 7層セキュリティモデル

1. ユーザー認可 -- 許可リスト・DM ペアリング
2. 危険コマンド承認 -- human-in-the-loop
3. コンテナ分離 -- Docker/Singularity/Modal
4. MCP 認証フィルタリング -- 環境変数分離
5. コンテキストファイルスキャン -- プロンプトインジェクション検出
6. クロスセッション分離 -- データ分離
7. 入力サニタイゼーション -- 作業ディレクトリ検証

## メッセージングゲートウェイ概要

17+ プラットフォーム対応: Telegram, Discord, Slack, WhatsApp, Signal, SMS, Email, Home Assistant, Mattermost, Matrix, DingTalk, Feishu/Lark, WeCom, Weixin, BlueBubbles, QQ Bot, Webhooks

### ゲートウェイサービス管理

```bash
hermes gateway                    # フォアグラウンド実行
hermes gateway install            # サービスインストール
hermes gateway start              # サービス開始
hermes gateway stop               # サービス停止
hermes gateway status             # ステータス確認
hermes gateway setup              # プラットフォーム設定
```

### セキュリティ

```bash
# ユーザー許可リスト
TELEGRAM_ALLOWED_USERS=123456789
DISCORD_ALLOWED_USERS=111222333
GATEWAY_ALLOWED_USERS=123456789   # グローバル

# DM ペアリング
hermes pairing list
hermes pairing approve telegram ABC12DEF
hermes pairing revoke telegram 123456789
```

## 委譲（サブエージェント）

最大3つの同時実行サブエージェント。独立コンテキストで実行。

```yaml
delegation:
  model: "google/gemini-3-flash-preview"
  provider: "openrouter"
```

## コード実行

```yaml
code_execution:
  mode: project    # project（セッションディレクトリ）| strict（一時ディレクトリ）
  timeout: 300
```

## バックグラウンドセッション

```
/background Analyze logs and summarize errors
```

独立セッションとして実行。メイン会話には影響しない。
