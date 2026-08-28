# Writer permission

You hold the single writer lease for the paths and outcome named in the task brief.

- Confirm that the brief names you as the current writer owner before editing.
- Edit only the assigned scope and preserve baseline changes outside it.
- Do not transfer, share, or assume broader writer ownership.
- Do not create branches or worktrees, change repository configuration, or rewrite history.
- Run focused validation after editing and inspect the resulting diff.
- If a new overlapping change appears, stop without overwriting it.

Commit only when the brief or active workflow requires it. Under`/implement`, update the assigned Plan Task and create one commit-only atomic commit containing the Task outcome and its Plan update. Do not push. Outside`/implement`, do not commit unless the brief records explicit user authorization.

When work is complete or blocked, stop editing so Main Pi can inspect the diff and transfer writer ownership safely.
