# モデル設定・エージェント動作・推論制御

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#auxiliary-models

## ディレクトリ構造

```
~/.hermes/
├── config.yaml           # 設定ファイル
├── .env                  # API キーとシークレット
├── auth.json             # OAuth プロバイダー認証情報
├── SOUL.md               # エージェントアイデンティティ
├── memories/             # 永続メモリファイル
├── skills/               # スキル
├── cron/                 # スケジュールジョブ
├── sessions/             # ゲートウェイセッション
├── state.db              # SQLite セッションデータベース
└── logs/                 # ログファイル
```

## 設定の優先順位

1. CLI 引数
2. `~/.hermes/config.yaml`
3. `~/.hermes/.env`
4. ビルトインデフォルト

## モデル設定

```yaml
model:
  default: "anthropic/claude-sonnet-4"
  provider: "openrouter"        # auto | openrouter | nous | anthropic | custom 等
  base_url: ""                  # カスタムエンドポイント用
  context_length: 131072        # 自動検出をオーバーライド
```

## エージェント設定

```yaml
agent:
  max_turns: 90                 # ツール呼び出し最大回数
  reasoning_effort: ""          # none | minimal | low | medium | high | xhigh
  tool_use_enforcement: "auto"  # auto | true | false
  api_max_retries: 3            # API リトライ回数 (v0.11.0)
  request_timeout_seconds: 0    # プロバイダー/モデル別オーバーライド可 (v0.11.0)
```

## 補助モデル UI (v0.11.0)

`hermes model` に「Configure auxiliary models」専用画面が追加。タスク別（compression / vision / session_search / title_generation）に個別モデルを GUI で設定できる。

`auxiliary.*.provider: "auto"` のデフォルト挙動が変更され、メインモデルにフォールバックするようになった（旧: 集計プロバイダー固有のデフォルトに silent 切替）。意図しないモデル切替を防ぐ。
