# コミットメッセージ profile 一覧

`commit-push` はこのファイルを読んで、コミットメッセージ生成時に使う profile を 1 つ選ぶ。

## 選択順

1. env marker で確定できる profile
2. 実行中エージェントが自分の runtime identity から確信を持てる profile
3. `generic-fallback`

## 書式

1 profile = 1 見出しとし、各 profile に以下を書く。

- 適用条件
- commit trailer
- subject/body 追加ルール
- 適用例

`generic-fallback` は必ず残す。追加 profile を作る場合も同じ書式にそろえる。

## `claude-code`

- 適用条件: 環境変数 `CLAUDECODE=1` が設定されている
- commit trailer: `Co-Authored-By: Claude Code <noreply@anthropic.com>`
- subject/body 追加ルール: なし
- 適用例: Claude Code のセッション中に `/commit-push` を実行したとき

## `gemini-cli`

- 適用条件: 環境変数 `GEMINI_CLI=1` が設定されている
- commit trailer: `Co-Authored-By: Gemini CLI <218195315+gemini-cli@users.noreply.github.com>`
- subject/body 追加ルール: なし
- 適用例: Gemini CLI から共通 skill 相当の workflow を実行したとき

## `codex`

- 適用条件: env marker では確定できないが、実行中エージェントが自分を Codex と確信できる
- commit trailer: `Co-Authored-By: Codex <codex@users.noreply.github.com>`
- subject/body 追加ルール: なし
- 適用例: Codex から共通 skill を実行したとき

## `generic-fallback`

- 適用条件: 他の profile に確信を持って一致できないとき
- commit trailer: なし
- subject/body 追加ルール: 実行環境の固有名詞を commit message に含めない
- 適用例: 実行中エージェントを明示できない runtime から呼び出したとき
