# コンテキスト圧縮・チェックポイント・コンテキスト参照

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files / https://hermes-agent.nousresearch.com/docs/user-guide/features/context-references

## コンテキスト圧縮

長い会話を自動要約。最初の3ターンと最後の4ターンを保持。

```yaml
compression:
  enabled: true
  threshold: 0.50
```

手動: `/compress`

## チェックポイント & ロールバック

破壊的操作（`write_file`, `patch`, `rm`, `mv`, `sed -i`）の実行前にファイルの自動スナップショットを取得する。シャドウ git リポジトリ `~/.hermes/checkpoints/` に保存。

### コマンド

| コマンド | 説明 |
|---------|------|
| `/rollback` | スナップショット一覧表示 |
| `/rollback N` | スナップショット N の状態に復元 |
| `/rollback diff N` | 復元前に差分プレビュー |
| `/rollback N file` | 特定ファイルのみ復元 |

### 設定

```yaml
checkpoints:
  enabled: true
  max_snapshots: 50
```

## コンテキスト参照（@記号）

`@` プレフィックスでファイル・フォルダ・差分・URL をコンテキストに注入する。CLI では Tab 補完が可能。

### 参照タイプ

| 構文 | 説明 |
|------|------|
| `@file:path` | ファイル全体を注入 |
| `@file:path:10-25` | 指定行範囲のみ注入 |
| `@folder:path` | フォルダ構造を注入 |
| `@diff` | 未コミットの変更差分 |
| `@staged` | ステージ済み変更 |
| `@git:5` | 直近5コミットの diff |
| `@url:https://...` | URL の内容を取得・注入 |

### サイズ制限

- ソフトリミット: コンテキストの 25%（超過時に警告）
- ハードリミット: コンテキストの 50%（超過時に切り詰め）

### セキュリティ

以下のパスへのアクセスは自動ブロックされる: `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.kube/`, `$HERMES_HOME/.env`
