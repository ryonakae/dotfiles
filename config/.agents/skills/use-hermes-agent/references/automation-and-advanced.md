# Hermes Agent 自動化・高度機能リファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/

## 概要

Hermes Agent の自動化機能と高度な拡張ポイントをまとめたリファレンス。スケジュール実行、サブエージェント委譲、プラグインなど、エージェントの能力を拡張する機能群を扱う。

各トピックの詳細は `automation/` 配下の個別ファイルを参照。

## トピック一覧

| トピック | 参照先 | 概要 |
|---------|--------|------|
| Cron / スケジュールタスク | [automation/cron.md](automation/cron.md) | cron 式・プリセット・CLI 管理・スキル添付・プログラマティック管理 |
| サブエージェント委譲 | [automation/delegation.md](automation/delegation.md) | 単一/並列タスク委譲・コンテキストルール・深度制限・モデルオーバーライド |
| コード実行 | [automation/code-execution.md](automation/code-execution.md) | hermes_tools モジュール・実行モード・リソース制限・セキュリティモデル |
| バッチ処理 | [automation/batch-processing.md](automation/batch-processing.md) | JSONL 入出力・並列実行・チェックポイント/リジューム・品質フィルタリング |
| イベントフック | [automation/hooks.md](automation/hooks.md) | Gateway フック (HOOK.yaml)・利用可能イベント・プラグインフック |
| プラグインシステム | [automation/plugins.md](automation/plugins.md) | ディレクトリ構造・register パターン・検出パス・CLI コマンド |
| API サーバー | [automation/api-server.md](automation/api-server.md) | OpenAI 互換エンドポイント・認証・互換フロントエンド・マルチユーザープロファイル |
| ACP / IDE 統合 | [automation/acp.md](automation/acp.md) | VS Code・Zed・JetBrains 向け ACP 設定 |
| RL トレーニング | [automation/rl-training.md](automation/rl-training.md) | 強化学習ツールセット (rl_*)・ワークフロー |
| メモリプロバイダー | [automation/memory-providers.md](automation/memory-providers.md) | 8 種のプロバイダー比較・設定・CLI コマンド |

## 関連リファレンス

- 設定項目の詳細: [configuration.md](configuration.md)
- ツール・機能の概要: [tools-and-features.md](tools-and-features.md)
- メッセージングプラットフォーム: [messaging-platforms.md](messaging-platforms.md)
