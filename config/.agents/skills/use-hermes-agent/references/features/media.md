# 画像生成・ブラウザ自動化・ビジョン・TTS/STT・ボイスモード

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/vision / https://hermes-agent.nousresearch.com/docs/user-guide/features/image-generation / https://hermes-agent.nousresearch.com/docs/user-guide/features/browser

## 画像生成

`image_gen` は pluggable backend（v0.15.0 で FAL は `plugins/image_gen/fal/` に移植、Krea も追加）。`FAL_KEY` または Nous サブスクリプション（Gateway 経由）で利用可能。

### 対応モデル

`flux-2/klein`, `flux-2-pro`, `z-image/turbo`, `nano-banana-pro`, `gpt-image-1.5`, `ideogram/v3`, `recraft/v4/pro`, `qwen-image`

**Krea 2**（v0.15.0、`krea-2-medium` $0.03 / `krea-2-large` $0.06）

### アスペクト比

`landscape` / `square` / `portrait` の 3 種

### 設定

```yaml
image_gen:
  model: "flux-2/klein"      # デフォルトモデル
  use_gateway: false          # Nous Gateway 経由
```

## Web 検索バックエンド

| バックエンド | 環境変数 | 検索 | 抽出 | クロール | 備考 |
|-----------|---------|:---:|:---:|:---:|-----|
| Firecrawl | `FIRECRAWL_API_KEY` | o | o | o | （v0.15.0 で `firecrawl_integration` tag が revert された経緯あり） |
| Parallel | `PARALLEL_API_KEY` | o | o | - | |
| Tavily | `TAVILY_API_KEY` | o | o | o | |
| Exa | `EXA_API_KEY` | o | o | - | |
| Brave Search | `BRAVE_API_KEY` | o | - | - | v0.14.0（free tier） |
| DuckDuckGo (DDGS) | （不要） | o | - | - | v0.14.0 |
| SearXNG | `SEARXNG_URL` | o | o | - | v0.13.0、split web tools（search/extract/browse 分離） |
| xAI Web Search | `XAI_API_KEY` | o | - | - | v0.15.0、web_search provider plugin として |

v0.13.0 で split web tools 化（search / extract / browse が分離）。

### 新ツール

- **`x_search`** — first-class X (Twitter) 検索ツール（v0.14.0、OAuth or API key）
- **`video_analyze`** — Gemini など互換マルチモーダルモデル向け native 動画理解（v0.13.0）
- **`video_generate`** — pluggable provider backend（v0.14.0）

## ブラウザ自動化

### バックエンド

cloud browser providers は v0.15.0 で `image_gen` 形式プラグインに移行（Browserbase, Anchor, Camofox, Hyperbrowser）。

| バックエンド | タイプ | 認証 |
|------------|--------|------|
| Browserbase | クラウド | `BROWSERBASE_API_KEY` |
| Browser Use | クラウド | `BROWSER_USE_API_KEY` |
| Anchor | クラウド | `ANCHOR_API_KEY`（v0.15.0） |
| Hyperbrowser | クラウド | `HYPERBROWSER_API_KEY`（v0.15.0） |
| Firecrawl | クラウド | `FIRECRAWL_API_KEY` |
| Camofox | ローカル | `CAMOFOX_URL` |
| ローカル Chrome | ローカル | `/browser connect` で CDP 接続 |
| ローカル Chromium | ローカル | agent-browser（内蔵）。LAN/localhost URL で自動起動（v0.12.0） |

### CDP supervisor（v0.12.0）

ダイアログ検出 + cross-origin iframe eval。`browser_console` の evaluation は v0.14.0 で 180x 高速化。

### ブラウザツール一覧

`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_scroll`, `browser_press`, `browser_back`, `browser_get_images`, `browser_vision`, `browser_console`, `browser_cdp`

### セッション録画

```yaml
browser:
  record_sessions: true
```

## ボイスモード

| モード | プラットフォーム | 説明 |
|--------|--------------|------|
| Interactive Voice | CLI | Ctrl+B で録音、自動無音検出 |
| Auto Voice Reply | Telegram/Discord | テキスト + 音声返信 |
| Voice Channel | Discord | VC 参加・ライブ会話 |

STT プロバイダー: local（無料）> groq > openai

### TTS プロバイダー詳細

8 プロバイダーに対応。Telegram では Opus フォーマットが必要（edge/minimax/neutts/gemini/xai は ffmpeg による変換が必要）。

| プロバイダー | 備考 |
|------------|------|
| `edge` | 無料、Microsoft Edge TTS |
| `elevenlabs` | 高品質、`ELEVENLABS_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `minimax` | `MINIMAX_API_KEY` |
| `mistral` | `MISTRAL_API_KEY` |
| `gemini` | `GEMINI_API_KEY` |
| `xai` | `XAI_API_KEY` |
| `neutts` | `NEUTTS_API_KEY` |

```yaml
tts:
  provider: "edge"
  voice: "en-US-AriaNeural"
  speed: 1.0                    # プロバイダーごとに速度制御可能
```

## ビジョン & 画像貼り付け

`/paste` コマンド、`Ctrl+V`、`Alt+V` で画像をセッションに貼り付け可能。画像は `~/.hermes/images/` に保存され、Base64 エンコードでビジョン対応モデルに送信される。プラットフォームによってサポート状況が異なる。

### ビジョン強化（v0.12.0+）

- **Native multimodal image routing** — モデルの実 vision capability に基づくルーティング（v0.12.0）
- **`vision_analyze` がビジョン対応モデルにピクセルを直接送信**（v0.14.0）
- **`computer_use` cua-driver backend** — non-Anthropic provider 対応、focus-safe ops、`hermes update` で refresh（v0.14.0）
- **`computer_use` キャプチャを `auxiliary.vision` 経由に**（v0.15.0）
- **`vision_analyze` + `browser_vision` で `model.supports_vision` を honor**（v0.16.0）

### Spotify / Google Meet（v0.12.0）

- **Spotify** — native 統合の 7 ツール、PKCE OAuth、setup wizard。bundled skill としては v0.16.0 で削除
- **Google Meet** — プラグイン（join/transcribe/speak、Realtime OpenAI transport + Node bot server）

### xAI Custom Voices（v0.13.0）

TTS provider + voice cloning。`/voice` で切替。
