# Hermes Agent 設定リファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

## 概要

Hermes Agent の `config.yaml` 設定項目をカテゴリ別にまとめたリファレンス。モデル、ターミナル、表示、メモリ、音声、MCP、セキュリティなど全設定カテゴリを網羅する。

各カテゴリの詳細は `config/` 配下の個別ファイルを参照。

## カテゴリ一覧

| トピック | 参照先 | 概要 |
|---------|--------|------|
| モデル・エージェント設定 | [config/model-and-agent.md](config/model-and-agent.md) | ディレクトリ構造・設定優先順位・モデル/プロバイダー・推論制御 |
| ターミナルバックエンド | [config/terminal.md](config/terminal.md) | 6 種のバックエンド (local/docker/ssh/modal/daytona/singularity) |
| 表示・UI 設定 | [config/display-and-ui.md](config/display-and-ui.md) | 表示オプション・スキン・ストリーミング (ゲートウェイ) |
| メモリ・圧縮設定 | [config/memory-and-compression.md](config/memory-and-compression.md) | メモリ有効化・文字制限・コンテキスト圧縮・ファイル読み取り制限 |
| TTS/STT/ボイスモード | [config/tts-stt-voice.md](config/tts-stt-voice.md) | TTS プロバイダー・STT プロバイダー・ボイスモード設定 |
| MCP・スキル設定 | [config/mcp-and-skills.md](config/mcp-and-skills.md) | MCP サーバー設定・スキル外部ディレクトリ・プラットフォーム別無効化 |
| セキュリティ・承認 | [config/security-and-approvals.md](config/security-and-approvals.md) | シークレット秘匿・承認モード・Web サイトブロックリスト |
| その他の設定 | [config/other-config.md](config/other-config.md) | Quick コマンド・補助モデル・委譲・コード実行・Web 検索・ブラウザ・タイムゾーン・認証情報プール・コンテキストファイル・worktree・セッション管理 |

## 関連リファレンス

- ツール・機能の概要: [tools-and-features.md](tools-and-features.md)
- 自動化・高度機能: [automation-and-advanced.md](automation-and-advanced.md)
- 環境変数: [environment-variables.md](environment-variables.md)
