# iOS Simulator

- worktreeごとに `{機種名} ({リポジトリ名} / {worktreeのディレクトリ名})` の専用端末を使う。ディレクトリ名はworktreeルートの末尾の名前をそのまま使い、ブランチ名から加工しない。primary checkoutも同じ形式で区別する。同名になる場合は短い識別子を追加する。
- 専用端末がなければ `xcrun simctl create` で作り、直後に同じUDIDで `xcrun simctl boot` と `xcrun simctl shutdown` を1回実行してから `device_open` で開く。T3のDevice Hubは `device.plist` に `lastUsedAt` か `lastBootedAt` がない端末を一覧から除外し、作成直後の端末にはどちらもないため。この起動は一覧への登録だけが目的で、以降の起動・操作は `device_open` と返されたコマンドで行う。
- 作成時に返されたUDIDを、そのworktreeの作業記録に端末名とともに残し、以降はUDIDで対象を指定する。他worktree・他リポジトリの端末を代用しない。
- 同じworktreeの親・子エージェントは操作担当を交代し、同じ端末を並行操作しない。並行検証が必要な場合だけ、担当を識別できる専用端末を追加する。セッションの扱いはT3が返す指示に従う。
- 端末は `device_open` で開く。専用端末のIDが分からなければ先に `device_list` で確認する。
- 操作は `device_open` が返す `quickStart` に従い、`agentDevice.command` をそのままのパスで実行する。このコマンドは端末とセッションに紐付いており、`--udid` などの対象指定は付けない。実行パスとセッションは開くたびに変わるので、文書やスクリプトに固定しない。
- UI動作検証や `.ad` テストの配置・初期状態・実行方法は、対象アプリの既存規約を優先する。
