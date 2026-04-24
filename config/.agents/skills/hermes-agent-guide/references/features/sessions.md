# セッション管理・チェックポイント・ロールバック

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/sessions / checkpoints-and-rollback

## セッションの保存場所

- `~/.hermes/state.db` — SQLite + FTS5 でセッションメッセージ・メタデータを永続化
- `~/.hermes/sessions/` — Gateway 別の per-platform セッションキャッシュ
- `~/.hermes/checkpoints/` — シャドウ git リポジトリ（破壊的操作前のスナップショット）

## CLI

```bash
hermes sessions list                  # セッション一覧（タイトル・最終更新）
hermes sessions show <id>             # 特定セッションの詳細
hermes sessions search "<query>"      # FTS5 全文検索
hermes sessions export <id> --format json
hermes sessions delete <id>
hermes -c                             # 最新セッション再開
hermes -r <id|タイトル>               # 特定セッション再開
```

セッション内では `/sessions` で一覧、`/title <name>` でタイトル設定、`/new` または `/reset` で新規開始。

## グルーピング

```yaml
group_sessions_per_user: true        # true=ユーザー別、false=チャット別
unauthorized_dm_behavior: pair       # pair=ペアリングコード生成 / ignore=無視
```

Gateway 環境ではユーザーごとにセッションを分離するか、チャネルごとに分離するかを選択。

## 自動 prune と VACUUM (v0.11.0)

起動時に古いセッションの自動 prune と SQLite VACUUM が走る。

```yaml
sessions:
  retention_days: 90                  # これより古いセッションを自動削除
  vacuum_on_start: true
```

## アイドル / リセット時刻

```yaml
session_idle_minutes: 1440            # 不活動でセッション終了（デフォルト 24h）
session_reset_hour: 4                 # 毎日 4:00 にセッションを区切る
```

## チェックポイント・ロールバック

`write_file`, `patch`, `rm`, `mv`, `sed -i` などの破壊的操作前に、対象ファイルのスナップショットがシャドウ git に取られる。

```yaml
checkpoints:
  enabled: true
  max_snapshots: 50
```

| コマンド | 説明 |
|---------|------|
| `/rollback` | スナップショット一覧 |
| `/rollback N` | スナップショット N に復元 |
| `/rollback diff N` | 復元前に差分プレビュー |
| `/rollback N file` | 特定ファイルのみ復元 |

`hermes chat --checkpoints` でセッション開始時に有効化。Git 配下のファイルだけが対象（バイナリと `.gitignore` 対象は除外）。

## バックアップ

```bash
hermes backup ~/hermes-backup.tar.gz       # 設定・セッション・メモリを丸ごとアーカイブ
hermes import ~/hermes-backup.tar.gz       # 復元（既存設定は上書き）
```

`auth.json` と `.env` は機密のためアーカイブから除外。手動でコピーが必要。
