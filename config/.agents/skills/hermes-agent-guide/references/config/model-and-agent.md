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
```
