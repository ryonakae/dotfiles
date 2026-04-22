# Hermes Agent プロバイダーリファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/integrations/providers

## サポートプロバイダー一覧

| プロバイダー | 説明 | セットアップ |
|---|---|---|
| Nous Portal | サブスクリプション型 | `hermes model` で OAuth |
| OpenAI Codex | ChatGPT OAuth | `hermes model` でデバイスコード認証 |
| Anthropic | Claude モデル | `ANTHROPIC_API_KEY` |
| OpenRouter | マルチプロバイダールーティング | `OPENROUTER_API_KEY` |
| Z.AI / ZhipuAI | GLM モデル | `GLM_API_KEY` / `ZAI_API_KEY` |
| Kimi / Moonshot | コーディング・チャット | `KIMI_API_KEY` |
| Kimi / Moonshot China | 中国地域 | `KIMI_CN_API_KEY` |
| Arcee AI | Trinity モデル | `ARCEEAI_API_KEY` |
| Xiaomi MiMo | MiMo モデル | `XIAOMI_API_KEY` |
| AWS Bedrock | Claude, Nova 等 | boto3 認証 |
| Qwen Portal | Qwen 3.5 / Coder | `hermes model` で OAuth |
| MiniMax | 国際版 | `MINIMAX_API_KEY` |
| MiniMax China | 中国版 | `MINIMAX_CN_API_KEY` |
| Alibaba Cloud | DashScope Qwen | `DASHSCOPE_API_KEY` |
| Hugging Face | 20+ オープンモデル | `HF_TOKEN` |
| Kilo Code | KiloCode hosted | `KILOCODE_API_KEY` |
| OpenCode Zen | 従量課金 | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | $10/月 | `OPENCODE_GO_API_KEY` |
| DeepSeek | DeepSeek API | `DEEPSEEK_API_KEY` |
| NVIDIA NIM | Nemotron | `NVIDIA_API_KEY` |
| Ollama Cloud | マネージド Ollama | `OLLAMA_API_KEY` |
| Google Gemini | Cloud Code Assist | `hermes model` で OAuth |
| xAI (Grok) | Grok 4 | `XAI_API_KEY` |
| GitHub Copilot | GPT-5.x, Claude 等 | OAuth / `COPILOT_GITHUB_TOKEN` |
| GitHub Copilot ACP | ACP agent backend | `hermes model` |
| Vercel AI Gateway | AI Gateway | `AI_GATEWAY_API_KEY` |
| Custom Endpoint | VLLM, SGLang, Ollama 等 | ベース URL + API キー |

**要件**: 最低 64,000 トークンのコンテキストウィンドウが必要

## プロバイダー設定コマンド

```bash
hermes model              # 対話型プロバイダー・モデル選択
hermes auth               # 認証情報管理
hermes auth add openrouter --api-key sk-or-v1-xxx  # API キー追加
hermes auth list           # 認証情報一覧
```

## ローカルモデル使用

```bash
hermes model
# Custom endpoint を選択
# API base URL: http://localhost:11434/v1
# API key: ollama
# Model name: qwen3.5:27b
# Context length: 32768
```

```yaml
model:
  default: qwen3.5:27b
  provider: custom
  base_url: http://localhost:11434/v1
```

Ollama, vLLM, llama.cpp, SGLang, LocalAI 等に対応。

## フォールバックプロバイダー

プライマリモデルエラー時に自動フェイルオーバー。

## 認証情報プール

```yaml
credential_pool_strategies:
  openrouter: round_robin       # fill_first | round_robin | least_used | random
```

```bash
hermes auth add openrouter --api-key sk-or-v1-key1
hermes auth add openrouter --api-key sk-or-v1-key2
```

## セッション内モデル切替

```
/model                              # 現在のモデル表示
/model claude-sonnet-4              # モデル切替（プロバイダー自動検出）
/model zai:glm-5                    # プロバイダー:モデル指定
/model custom:qwen-2.5              # カスタムエンドポイント
/model claude-sonnet-4 --global     # 切替 + デフォルト保存
```

## 補助モデル設定

補助タスク（ビジョン、圧縮、Web 抽出等）に別モデルを指定:

```yaml
auxiliary:
  vision:
    provider: "auto"
    model: "openai/gpt-4o"
  compression:
    model: "google/gemini-3-flash-preview"
  web_extract:
    provider: "auto"
```

## 委譲モデル

サブエージェントに別モデルを使用:

```yaml
delegation:
  model: "google/gemini-3-flash-preview"
  provider: "openrouter"
```
