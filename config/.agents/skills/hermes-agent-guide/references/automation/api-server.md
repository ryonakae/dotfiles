# API サーバー

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server

## エンドポイント

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/v1/chat/completions` | POST | OpenAI 互換 Chat Completions |
| `/v1/responses` | POST | OpenAI Responses API 互換 |
| `/v1/runs` | POST | 非同期タスク実行 |
| `/v1/runs/{id}` | GET | タスク状態確認 |
| `/v1/jobs` | POST | バッチジョブ投入 |
| `/v1/jobs/{id}` | GET | ジョブ状態確認 |
| `/health` | GET | ヘルスチェック |

## 起動と認証

```bash
hermes gateway start --api       # API サーバーも同時起動
# または
hermes api start --port 8080
```

```yaml
api:
  enabled: true
  port: 8080
  auth:
    type: "bearer"              # bearer / api_key / none
    token: "${API_AUTH_TOKEN}"   # 環境変数参照
  cors:
    origins: ["*"]              # CORS 許可オリジン
    methods: ["GET", "POST"]
```

## 互換フロントエンド

API サーバーは OpenAI 互換のため以下のフロントエンドと接続可能:

- **Open WebUI** (旧 Ollama WebUI)
- **LobeChat**
- **ChatGPT Next Web**
- **BetterChatGPT**
- **Chatbot UI**
- **LibreChat**

## マルチユーザープロファイル

```yaml
api:
  profiles:
    default:
      model: "anthropic/claude-sonnet-4-20250514"
      system_prompt: "汎用アシスタント"
    coder:
      model: "anthropic/claude-sonnet-4-20250514"
      system_prompt: "プログラミング専門"
      toolsets: ["terminal", "file", "web"]
```
