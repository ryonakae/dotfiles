# worktree の操作

worktree の作成・移動・削除は T3 Code で行い、`git worktree` や内蔵の worktree 機能（Claude Code の `EnterWorktree` など）を使わない。これらで作った worktree はスレッドに紐付かない。

- 作業中のスレッドを移す: `t3_worktree_handoff`
- 別スレッドや子タスクを worktree で動かす: `t3_thread_launch` の `workspaceStrategy`、`delegate_task` の `isolation`
- 削除: T3 Code がスレッドの削除・マージ時に片付ける
