# メモリプロバイダー

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers

## 比較表

| プロバイダー | 種別 | ストレージ | 特徴 |
|------------|------|-----------|------|
| **Honcho** | クラウド | サーバー | セッション・メタ認知ベース。ユーザー別学習 |
| **OpenViking** | クラウド | サーバー | ベクトル検索ベース。大規模コンテキスト |
| **Mem0** | ハイブリッド | ローカル/クラウド | グラフ + ベクトル。関係性の自動抽出 |
| **Hindsight** | クラウド | サーバー | 長期記憶特化。忘却曲線モデル |
| **Holographic** | ローカル | ファイル | 軽量。ファイルベースの永続化。外部依存なし |
| **RetainDB** | セルフホスト | SQLite/PostgreSQL | 構造化メモリ。SQL クエリ可能 |
| **ByteRover** | クラウド | サーバー | 自動要約。圧縮メモリ |
| **Supermemory** | クラウド | サーバー | Web ブックマーク連携。知識ベース構築 |

## 設定

```yaml
memory:
  provider: "holographic"       # プロバイダー名
  auto_save: true               # セッション終了時に自動保存
  auto_load: true               # セッション開始時に自動読込
```

## CLI コマンド

```bash
hermes memory status             # 現在のプロバイダー状態
hermes memory list               # 保存済みメモリ一覧
hermes memory clear              # メモリクリア
hermes memory export             # エクスポート
hermes memory import <file>      # インポート
```
