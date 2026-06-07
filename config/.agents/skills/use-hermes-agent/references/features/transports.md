# Transport ABC・プロバイダー Transport 層

> 参照元: RELEASE_v0.11.0.md / agent/transports/

v0.11.0 で `run_agent.py` に密結合していたフォーマット変換と HTTP 通信が `agent/transports/` という抽象層に切り出された。各 transport は独自の API 形式・ストリーミング処理・format conversion を持つ。

## 設計

```
Provider (anthropic, openai, openrouter, bedrock, ...)
   ↓ resolve
Transport (AnthropicTransport / ChatCompletionsTransport / ResponsesApiTransport / BedrockTransport)
   ↓ HTTP / SDK call
LLM API
```

`Transport` は ABC（抽象基底クラス）で、各実装が以下の責務を持つ:

- リクエスト形式変換（hermes 内部表現 → ベンダー API 形式）
- HTTP / SDK 呼び出し
- ストリーミング応答のパース
- レスポンス形式変換（ベンダー応答 → hermes 内部表現）

## 標準 Transport 実装

| Transport | 用途 | 主な対象プロバイダー |
|-----------|------|---------------------|
| `AnthropicTransport` | Anthropic Messages API | Anthropic, Claude over Bedrock（旧経路） |
| `ChatCompletionsTransport` | OpenAI 互換 Chat Completions API | OpenRouter, DeepSeek, Kimi, Z.AI, Together, etc. |
| `ResponsesApiTransport` | OpenAI Responses API | OpenAI native, Codex OAuth, xAI Grok（v0.11.0 で移行） |
| `BedrockTransport` | AWS Bedrock Converse API（v0.11.0 ネイティブ追加） | AWS Bedrock 全モデル |
| `CodexAppServerTransport` | Codex app-server runtime（v0.14.0） | OpenAI/Codex モデル（session reuse / wedged session retire / OAuth refresh classification） |

## AWS Bedrock ネイティブ対応 (v0.11.0)

`BedrockTransport` は Converse API を直接叩くため、boto3 認証で動く。OpenAI 互換ラッパーを介さない。

```yaml
model:
  provider: bedrock
  default: "anthropic.claude-sonnet-4-5-20250929-v2:0"

# .env
AWS_REGION=us-west-2
AWS_PROFILE=default      # boto3 が解決
```

サポート範囲: Claude (Bedrock 経由)、Nova、Llama、Mistral、Titan 系。

## Codex OAuth + Responses API

`ResponsesApiTransport` を経由して GPT-5 / GPT-5.5 を Codex OAuth で利用可能。`hermes model` の picker は live discovery で新モデルを自動表示する（カタログ更新不要）。

## per-provider / per-model timeout

```yaml
model:
  default: "anthropic/claude-sonnet-4"
  request_timeout_seconds: 1800

providers:
  openrouter:
    request_timeout_seconds: 600          # プロバイダー単位
    models:
      "anthropic/claude-opus-4-7":
        request_timeout_seconds: 3600     # モデル単位（最優先）
```

## カスタム Transport 開発

v0.13.0 で provider 自体が plugin 化（`ProviderProfile` ABC + `plugins/model-providers/`）。`register_transport()` 系 API は provider plugin の中で利用する。

## クロスセッション 1h prompt cache（v0.14.0）

Anthropic / OpenRouter / Nous Portal で Claude 系プロンプトの 1 時間キャッシュをクロスセッションで共有可能。

```yaml
prompt_caching:
  cache_ttl: 1h
```

## OpenAI 互換ローカルプロキシ（`hermes proxy`、v0.14.0+）

OAuth provider（Claude Pro / ChatGPT Pro / SuperGrok）を localhost の OpenAI 互換エンドポイントとして公開:

```bash
hermes proxy                  # デフォルト 8775 ポートで起動
hermes proxy --upstream xai   # xAI を upstream に指定（v0.15.0）
```

Codex / Aider / Cline / Continue 等から OAuth クレデンシャルを再利用可能。
