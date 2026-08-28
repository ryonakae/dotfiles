# Read-only permission

このassignmentでは`read-only` permissionを持つ。

- repositoryのfileやdirectoryを作成、編集、rename、移動、削除しない。
- Git index、ref、commit、branch、worktree、設定を変更しない。
- formatter、generator、installer、migration、test、buildのうち、repositoryに成果物を残しうるものは実行しない。briefとrepositoryのcontractが読み取りのみだと保証している場合だけ実行できる。
- fileの読み取り、検索、diffの確認、静的な推論、副作用の残らないcommandを優先する。
- 調査を始める前にGit baselineを記録し、報告の直前にもう一度比較する。

commandやtoolがrepositoryを変更してしまった場合は、すぐに作業を止める。変更されたpathと実行したcommandを報告し、自分でrevertやcleanをしない。その後の扱いはMain Piが決める。

reviewerのassignmentはこのpermissionでのみ成立する。
