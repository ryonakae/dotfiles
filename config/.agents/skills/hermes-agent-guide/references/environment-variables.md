# Hermes Agent 環境変数リファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/reference/environment-variables

すべての環境変数は `~/.hermes/.env` に設定する。`hermes config set VAR value` でも設定可能。

---

## LLM プロバイダー

| 変数 | 説明 |
|------|------|
| `OPENROUTER_API_KEY` | OpenRouter API キー（推奨） |
| `OPENROUTER_BASE_URL` | OpenRouter ベース URL 上書き |
| `ANTHROPIC_API_KEY` | Anthropic Console API キー |
| `OPENAI_API_KEY` | カスタム OpenAI 互換エンドポイント用 |
| `OPENAI_BASE_URL` | カスタムエンドポイントのベース URL |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Google AI Studio API キー |
| `GEMINI_BASE_URL` | Google AI Studio ベース URL 上書き |
| `GLM_API_KEY` / `ZAI_API_KEY` | z.ai / ZhipuAI API キー |
| `GLM_BASE_URL` | z.ai ベース URL |
| `KIMI_API_KEY` | Kimi / Moonshot API キー |
| `KIMI_CN_API_KEY` | Kimi 中国地域 API キー |
| `ARCEEAI_API_KEY` | Arcee AI API キー |
| `MINIMAX_API_KEY` | MiniMax API キー（グローバル） |
| `MINIMAX_CN_API_KEY` | MiniMax 中国地域 API キー |
| `KILOCODE_API_KEY` | Kilo Code API キー |
| `XIAOMI_API_KEY` | Xiaomi MiMo API キー |
| `HF_TOKEN` | Hugging Face トークン |
| `DASHSCOPE_API_KEY` | Alibaba Cloud DashScope API キー |
| `DEEPSEEK_API_KEY` | DeepSeek API キー |
| `NVIDIA_API_KEY` | NVIDIA NIM API キー |
| `OLLAMA_API_KEY` | Ollama Cloud API キー |
| `XAI_API_KEY` | xAI (Grok) API キー |
| `MISTRAL_API_KEY` | Mistral API キー |
| `OPENCODE_ZEN_API_KEY` | OpenCode Zen API キー |
| `OPENCODE_GO_API_KEY` | OpenCode Go API キー |
| `AI_GATEWAY_API_KEY` | Vercel AI Gateway API キー |
| `COPILOT_GITHUB_TOKEN` | Copilot 用 GitHub トークン（最優先） |
| `GH_TOKEN` / `GITHUB_TOKEN` | GitHub トークン（Copilot 2-3 番目の優先順位） |
| `AWS_REGION` / `AWS_PROFILE` | Bedrock 用 AWS 設定 |
| `HERMES_MODEL` | プロセスレベルのモデル名上書き |
| `HERMES_INFERENCE_PROVIDER` | プロバイダー選択上書き |

## プロバイダー認証 / OAuth

| 変数 | 説明 |
|------|------|
| `HERMES_GEMINI_CLIENT_ID` | Gemini CLI OAuth Client ID |
| `HERMES_GEMINI_CLIENT_SECRET` | Gemini CLI OAuth Client Secret |
| `HERMES_GEMINI_PROJECT_ID` | GCP Project ID（有料 Gemini） |
| `ANTHROPIC_TOKEN` | Anthropic OAuth トークン |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code トークン上書き |
| `HERMES_PORTAL_BASE_URL` | Nous Portal URL 上書き |
| `HERMES_COPILOT_ACP_COMMAND` | Copilot ACP バイナリパス |
| `HERMES_HOME` | Hermes 設定ディレクトリ（デフォルト: `~/.hermes`） |

## ツール API

| 変数 | 説明 |
|------|------|
| `FIRECRAWL_API_KEY` | Firecrawl API キー（Web 検索・スクレイピング） |
| `FIRECRAWL_API_URL` | Firecrawl セルフホスト URL |
| `PARALLEL_API_KEY` | Parallel AI API キー |
| `TAVILY_API_KEY` | Tavily 検索 API キー |
| `EXA_API_KEY` | Exa 検索 API キー |
| `BROWSERBASE_API_KEY` | Browserbase API キー |
| `BROWSERBASE_PROJECT_ID` | Browserbase Project ID |
| `BROWSER_USE_API_KEY` | Browser Use API キー |
| `BROWSER_CDP_URL` | Chrome DevTools Protocol URL |
| `FAL_KEY` | FAL.ai 画像生成 API キー |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS API キー |
| `GROQ_API_KEY` | Groq Whisper STT API キー |
| `VOICE_TOOLS_OPENAI_KEY` | OpenAI 音声ツール用キー |
| `HONCHO_API_KEY` | Honcho メモリ API キー |
| `SUPERMEMORY_API_KEY` | Supermemory API キー |
| `TINKER_API_KEY` | Tinker RL トレーニング API キー |
| `WANDB_API_KEY` | Weights & Biases API キー |
| `DAYTONA_API_KEY` | Daytona サンドボックス API キー |
| `GITHUB_TOKEN` | Skills Hub 用 GitHub トークン |

## ターミナルバックエンド

| 変数 | 説明 |
|------|------|
| `TERMINAL_ENV` | バックエンド選択（`local` / `docker` / `ssh` / `singularity` / `modal` / `daytona`） |
| `TERMINAL_DOCKER_IMAGE` | Docker イメージ |
| `TERMINAL_DOCKER_FORWARD_ENV` | Docker 環境変数転送（JSON 配列） |
| `TERMINAL_DOCKER_VOLUMES` | Docker ボリュームマウント |
| `TERMINAL_DOCKER_MOUNT_CWD_TO_WORKSPACE` | CWD を `/workspace` にマウント |
| `TERMINAL_SINGULARITY_IMAGE` | Singularity イメージ |
| `TERMINAL_TIMEOUT` | コマンドタイムアウト（秒） |
| `TERMINAL_CWD` | 作業ディレクトリ |
| `SUDO_PASSWORD` | sudo 実行用パスワード |
| `TERMINAL_SSH_HOST` | SSH ホスト名 |
| `TERMINAL_SSH_USER` | SSH ユーザー名 |
| `TERMINAL_SSH_PORT` | SSH ポート（デフォルト: 22） |
| `TERMINAL_SSH_KEY` | SSH 秘密鍵パス |
| `TERMINAL_CONTAINER_CPU` | コンテナ CPU（デフォルト: 1） |
| `TERMINAL_CONTAINER_MEMORY` | コンテナメモリ MB（デフォルト: 5120） |
| `TERMINAL_CONTAINER_DISK` | コンテナディスク MB（デフォルト: 51200） |
| `TERMINAL_CONTAINER_PERSISTENT` | 永続化（デフォルト: `true`） |

## メッセージング共通

| 変数 | 説明 |
|------|------|
| `MESSAGING_CWD` | メッセージングモード作業ディレクトリ |
| `GATEWAY_ALLOWED_USERS` | 全プラットフォーム許可ユーザー |
| `GATEWAY_ALLOW_ALL_USERS` | 全ユーザー許可（非推奨） |

## Telegram

| 変数 | 説明 |
|------|------|
| `TELEGRAM_BOT_TOKEN` | BotFather から取得したトークン |
| `TELEGRAM_ALLOWED_USERS` | 許可ユーザー ID（カンマ区切り） |
| `TELEGRAM_HOME_CHANNEL` | Cron 配信用チャット ID |
| `TELEGRAM_WEBHOOK_URL` | Webhook モード用 HTTPS URL |
| `TELEGRAM_WEBHOOK_PORT` | Webhook ポート（デフォルト: 8443） |
| `TELEGRAM_WEBHOOK_SECRET` | Webhook 検証シークレット |
| `TELEGRAM_PROXY` | プロキシ URL |
| `TELEGRAM_REACTIONS` | 絵文字リアクション（デフォルト: `false`） |

## Discord

| 変数 | 説明 |
|------|------|
| `DISCORD_BOT_TOKEN` | Bot トークン |
| `DISCORD_ALLOWED_USERS` | 許可ユーザー ID（カンマ区切り） |
| `DISCORD_ALLOWED_ROLES` | 許可ロール ID（カンマ区切り） |
| `DISCORD_HOME_CHANNEL` | Cron 配信用チャネル ID |
| `DISCORD_REQUIRE_MENTION` | @メンション必須（デフォルト: `true`） |
| `DISCORD_FREE_RESPONSE_CHANNELS` | メンション不要チャネル ID |
| `DISCORD_AUTO_THREAD` | 自動スレッド化（デフォルト: `true`） |
| `DISCORD_REACTIONS` | 絵文字リアクション（デフォルト: `true`） |
| `DISCORD_PROXY` | プロキシ URL |

## Slack

| 変数 | 説明 |
|------|------|
| `SLACK_BOT_TOKEN` | `xoxb-` Bot User OAuth Token |
| `SLACK_APP_TOKEN` | `xapp-` App-Level Token（Socket Mode 用） |
| `SLACK_ALLOWED_USERS` | 許可 Member ID（カンマ区切り） |
| `SLACK_HOME_CHANNEL` | Cron 配信用チャネル ID |

## WhatsApp

| 変数 | 説明 |
|------|------|
| `WHATSAPP_ENABLED` | WhatsApp ブリッジ有効化 |
| `WHATSAPP_MODE` | `bot`（別番号）/ `self-chat`（自分へのメッセージ） |
| `WHATSAPP_ALLOWED_USERS` | 許可電話番号（国コード付き、カンマ区切り。`*` で全許可） |

## Signal

| 変数 | 説明 |
|------|------|
| `SIGNAL_HTTP_URL` | signal-cli HTTP エンドポイント |
| `SIGNAL_ACCOUNT` | ボット電話番号（E.164 形式） |
| `SIGNAL_ALLOWED_USERS` | 許可電話番号 / UUID（カンマ区切り） |
| `SIGNAL_GROUP_ALLOWED_USERS` | 監視グループ ID（`*` で全許可） |

## Email

| 変数 | 説明 |
|------|------|
| `EMAIL_ADDRESS` | メールアドレス |
| `EMAIL_PASSWORD` | パスワード / アプリパスワード |
| `EMAIL_IMAP_HOST` | IMAP ホスト |
| `EMAIL_SMTP_HOST` | SMTP ホスト |
| `EMAIL_ALLOWED_USERS` | 許可送信元アドレス（カンマ区切り） |
| `EMAIL_POLL_INTERVAL` | ポーリング間隔秒（デフォルト: 15） |

## その他プラットフォーム

| 変数 | 説明 |
|------|------|
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER` | SMS (Twilio) |
| `HASS_TOKEN` / `HASS_URL` | Home Assistant |
| `MATTERMOST_URL` / `MATTERMOST_TOKEN` | Mattermost |
| `MATRIX_HOMESERVER` / `MATRIX_ACCESS_TOKEN` / `MATRIX_USER_ID` | Matrix |
| `DINGTALK_CLIENT_ID` / `DINGTALK_CLIENT_SECRET` | DingTalk |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | Feishu/Lark |
| `WECOM_BOT_ID` / `WECOM_SECRET` | WeCom |
| `WEIXIN_ACCOUNT_ID` / `WEIXIN_TOKEN` | Weixin |
| `BLUEBUBBLES_SERVER_URL` / `BLUEBUBBLES_PASSWORD` | BlueBubbles |
| `QQ_APP_ID` / `QQ_CLIENT_SECRET` | QQ Bot |

## API サーバー / Webhook

| 変数 | 説明 |
|------|------|
| `API_SERVER_ENABLED` | API サーバー有効化（デフォルト: `false`） |
| `API_SERVER_PORT` | ポート（デフォルト: 8642） |
| `API_SERVER_HOST` | バインドアドレス（デフォルト: `127.0.0.1`） |
| `API_SERVER_KEY` | Bearer トークン認証 |
| `API_SERVER_CORS_ORIGINS` | CORS 許可オリジン |
| `WEBHOOK_ENABLED` | Webhook プラットフォーム有効化 |
| `WEBHOOK_PORT` | Webhook ポート（デフォルト: 8644） |
| `WEBHOOK_SECRET` | HMAC シークレット |

## エージェント動作

| 変数 | 説明 |
|------|------|
| `HERMES_MAX_ITERATIONS` | ツール呼び出し最大回数（デフォルト: 90） |
| `HERMES_API_TIMEOUT` | LLM API タイムアウト秒（デフォルト: 1800） |
| `HERMES_STREAM_READ_TIMEOUT` | ストリーミング読取タイムアウト秒（デフォルト: 120） |
| `HERMES_STREAM_STALE_TIMEOUT` | 古いストリーム検出秒（デフォルト: 180） |
| `HERMES_YOLO_MODE` | 危険コマンド承認スキップ |
| `HERMES_QUIET` | 非必須出力抑止 |
| `HERMES_TIMEZONE` | IANA タイムゾーン |
| `HERMES_TUI` | TUI 起動（`1` に設定） |
| `HERMES_ENABLE_PROJECT_PLUGINS` | プロジェクトローカルプラグイン有効化 |

## Cron / セッション

| 変数 | 説明 |
|------|------|
| `HERMES_CRON_TIMEOUT` | Cron ジョブ不活動タイムアウト秒（デフォルト: 600） |
| `HERMES_CRON_SCRIPT_TIMEOUT` | 事前実行スクリプトタイムアウト秒（デフォルト: 120） |
| `SESSION_IDLE_MINUTES` | 不活動後セッションリセット（デフォルト: 1440） |
| `SESSION_RESET_HOUR` | 日次リセット時刻 24h（デフォルト: 4） |

## 補助タスクオーバーライド

| 変数 | 説明 |
|------|------|
| `AUXILIARY_VISION_PROVIDER` / `_MODEL` / `_BASE_URL` / `_API_KEY` | Vision タスク |
| `AUXILIARY_WEB_EXTRACT_PROVIDER` / `_MODEL` / `_BASE_URL` / `_API_KEY` | Web 抽出タスク |

## STT オーバーライド

| 変数 | 説明 |
|------|------|
| `STT_GROQ_MODEL` | Groq STT モデル（デフォルト: `whisper-large-v3-turbo`） |
| `STT_OPENAI_MODEL` | OpenAI STT モデル（デフォルト: `whisper-1`） |
| `GROQ_BASE_URL` | Groq STT エンドポイント |
| `STT_OPENAI_BASE_URL` | OpenAI STT エンドポイント |
