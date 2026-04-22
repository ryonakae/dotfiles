# 画像生成・ブラウザ自動化・ビジョン・TTS/STT・ボイスモード

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/vision / https://hermes-agent.nousresearch.com/docs/user-guide/features/image-generation / https://hermes-agent.nousresearch.com/docs/user-guide/features/browser

## 画像生成

FAL.ai 経由で 8 モデルに対応。`FAL_KEY` または Nous サブスクリプション（Gateway 経由）で利用可能。

### 対応モデル

`flux-2/klein`, `flux-2-pro`, `z-image/turbo`, `nano-banana-pro`, `gpt-image-1.5`, `ideogram/v3`, `recraft/v4/pro`, `qwen-image`

### アスペクト比

`landscape` / `square` / `portrait` の 3 種

### 設定

```yaml
image_gen:
  model: "flux-2/klein"      # デフォルトモデル
  use_gateway: false          # Nous Gateway 経由
```

## Web 検索バックエンド

| バックエンド | 環境変数 | 検索 | 抽出 | クロール |
|-----------|---------|:---:|:---:|:---:|
| Firecrawl（デフォルト） | `FIRECRAWL_API_KEY` | o | o | o |
| Parallel | `PARALLEL_API_KEY` | o | o | - |
| Tavily | `TAVILY_API_KEY` | o | o | o |
| Exa | `EXA_API_KEY` | o | o | - |

## ブラウザ自動化

### バックエンド

| バックエンド | タイプ | 認証 |
|------------|--------|------|
| Browserbase | クラウド | `BROWSERBASE_API_KEY` |
| Browser Use | クラウド | `BROWSER_USE_API_KEY` |
| Firecrawl | クラウド | `FIRECRAWL_API_KEY` |
| Camofox | ローカル | `CAMOFOX_URL` |
| ローカル Chrome | ローカル | `/browser connect` で CDP 接続 |
| ローカル Chromium | ローカル | agent-browser（内蔵） |

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
