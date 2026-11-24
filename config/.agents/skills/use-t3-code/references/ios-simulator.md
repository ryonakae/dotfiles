# iOS Simulator

- worktreeごとに `{機種名} ({リポジトリ名} / {ブランチ名})` の専用端末を使う。T3はworktreeを仮のブランチ `t3/<id>` で作り、十数秒後に意味のある名前へ変えるので、ブランチが `t3/` で始まる間は作らずに待つ。worktreeのディレクトリ名は使わない。primary checkoutも同じ形式で区別する。
- プロジェクトに専用端末の作成スクリプトや手順があれば、それに従い、`xcrun simctl create` を手で書かない。
- スクリプトがなければ `xcrun simctl create` で作り、直後に同じUDIDで `xcrun simctl boot` と `xcrun simctl shutdown` を1回実行してから `device_open` で開く。T3のDevice Hubは `device.plist` に `lastUsedAt` か `lastBootedAt` がない端末を一覧から除外し、作成直後の端末にはどちらもないため。この起動は一覧への登録だけが目的で、以降の起動・操作は `device_open` と返されたコマンドで行う。
- 端末は名前ではなくUDIDで特定する。作成時に返されたUDIDを `git rev-parse --git-path` で得られるworktreeのGitディレクトリ内のファイルか作業記録に残し、以降はUDIDで対象を指定する。ブランチ名が変わったら `xcrun simctl rename` で端末名を合わせる。他worktree・他リポジトリの端末を代用しない。スレッドを片付けるときは [thread-lifecycle.md](thread-lifecycle.md) の「付随物を片付ける」に従って消す。
- 同じworktreeの親・子エージェントは操作担当を交代し、同じ端末を並行操作しない。並行検証が必要な場合だけ、担当を識別できる専用端末を追加する。セッションの扱いはT3が返す指示に従う。
- 端末は `device_open` で開く。専用端末のIDが分からなければ先に `device_list` で確認する。
- 操作は `device_open` が返す `quickStart` に従い、`agentDevice.command` をそのままのパスで実行する。このコマンドは端末とセッションに紐付いており、`--udid` などの対象指定は付けない。実行パスとセッションは開くたびに変わるので、文書やスクリプトに固定しない。
- UI動作検証や `.ad` テストの配置・初期状態・実行方法は、対象アプリの既存規約を優先する。
