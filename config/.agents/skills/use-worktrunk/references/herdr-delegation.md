# herdr 委譲と fork の手順

SKILL.md が「herdr で実行する」と判定した操作の実行手順。いつ herdr 委譲になるか、承認が要るかの判定は SKILL.md が持ち、このファイルは手順だけを持つ。

## 有効化条件とフォールバック

次の両方が成立するときだけこの手順を使う。

```sh
test "$HERDR_ENV" = 1
herdr pane current --current
```

`HERDR_ENV` が不一致、または herdr CLI がエラー（stderr の JSON、exit 1/2）を返したら、このファイルの手順を使わず SKILL.md §6 の通常 shell 案内へフォールバックする。session 内で一度失敗した herdr 呼び出しを黙って再試行して押し切らない。

## ペインは sandbox 外 — 実行制限

herdr のペイン内シェルは Agent Safehouse の外で動く。これは safehouse が制限する `wt` 操作を完遂するための意図的な迂回路であり、汎用の実行経路ではない。herdr ペインで実行してよいのは次だけ。

- SKILL.md と公式 worktrunk Skill が定める `wt` コマンド
- その完了・状態確認に必要な読み取り（sentinel の echo、`git status` 等の read-only 確認）
- fork フローの Agent wrapper 起動（`herdr agent start` 経由）

それ以外のコマンドを safehouse 回避の目的でペインへ送らない。

## 共通規則

- ID は herdr の JSON レスポンスから読む（`.result.tab`、`.result.root_pane`、`.result.pane.pane_id`）。sidebar の並びや例から推測しない
- レイアウト作成は `--no-focus` を付け、ユーザーのフォーカスを動かさない。例外は「承認プロンプトへの委譲」だけ
- 自分が作っていないタブ・ペインを閉じない。`herdr server stop` を実行しない
- `pane run` は対象ペインが対話プロンプトにいるときだけ送る。直前のコマンドが残っている可能性があれば `pane read --source visible` で確認し、必要なら `pane send-keys <id> ctrl+c` で入力をクリアしてから送る。混線した入力のまま重ねて送らない
- wt コマンドの完了検知は sentinel で行う。fish 構文でコマンド末尾に `; echo __WT_DONE=$status` を付け、`pane wait-output <id> --regex '__WT_DONE=[0-9]+' --timeout <ms>` で待ち、`__WT_DONE=0` 以外は失敗として扱う。`--match __WT_DONE=` はペインにエコーされたコマンド行自体（`__WT_DONE=$status`）に即マッチするため使わない。wt の出力文言との一致には依存しない
- タブラベルと agent 名は branch 名から導出し、`[a-z][a-z0-9_-]{0,31}` へ正規化する（大文字は小文字化、その他の不許可文字は `-`、先頭が英小文字でなければ接頭辞を付ける）。agent 名は `herdr agent list` で衝突を確認し、衝突したら短いサフィックスで一意化する

## (a) fork なしの新規作成

worktree を新規作成して残す。ペインのシェルが worktree へ cd した状態で残るよう、`--no-cd` は付けない（対話シェルの `wt` 関数が cd を定着させる）。

1. `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <リポジトリルート> --label <正規化名> --no-focus` を実行し、`.result.tab` と `.result.root_pane` を読む
2. root pane で `wt switch <ユーザーの引数>; echo __WT_DONE=$status` を `pane run` し、`wait-output` で sentinel を待つ
3. `__WT_DONE=0` なら `pane get` で cwd が worktree の絶対 path へ移ったことを確認し、タブ位置と path を報告する。タブは閉じない
4. 失敗・タイムアウトは「承認プロンプトと失敗の分岐」へ

blocking copy（`wt step copy-ignored`）を伴う依頼では、作成の成功後に同じペインで copy を sentinel 付きで実行する。copy が失敗したら worktree とタブを残して停止し、自動 retry・rollback をしない。

## (b) fork あり

(a) の成功後、同じペイン（worktree に cd 済み）で fork エージェントを起動し、初動の指示まで送る。開始前に session ID と client 種別を SKILL.md §5 の規則で特定する。特定できなければこのフローへ入らない。

1. `herdr agent`（kind 一覧）と対象 client の現行 help を確認し、fork 引数を古い知識で組み立てない
2. `herdr agent start <正規化名> --kind <kind> --pane <root-pane-id> -- <fork 引数>` を実行する。対応は次のとおり

   | client | kind | `--` 以降の fork 引数 |
   |---|---|---|
   | Pi | `pi` | `--fork <session-id>` |
   | Claude Code | `claude` | `--resume <session-id> --fork-session` |
   | Codex | `codex` | `fork <session-id>` |
   | OpenCode | `opencode` | `--session <session-id> --fork` |

   ペインは対話 fish なので、client は safehouse wrapper の fish 関数として解決され、fork されたエージェントは通常どおり sandbox 内で起動する
3. 起動成功後、`herdr agent prompt <名前> "<引き継ぎタスクの要約>"` を送る。fork は会話の文脈を持つので要約は短くする。`--wait` を付けず、初動を見届けない
4. 起動と送信の完了、タブ位置、agent 名を報告して停止する。現在の session はコーディネーターとして元の worktree に残る

`agent start` が起動タイムアウト（既定 30 秒）で失敗したら、`pane read` で出力を確認して報告し、再試行しない。worktree とタブは残す。

## (c) メンテナンス操作

copy-ignored 単体、`wt remove`、cleanup 付き `wt merge`、live `wt step prune`、`wt step promote` など、住み着く場所が要らない一発実行。SKILL.md が承認を要求する操作は、ユーザーの承認を得るまでペインへ送らない。

1. `herdr pane split --current --direction right --cwd <実行ディレクトリ> --no-focus` で一時ペインを作る（縦長のペインでは `down`）
2. 対象コマンドを sentinel 付きで `pane run` し、`wait-output` で待つ
3. `pane read --source recent-unwrapped` で出力を回収して結果を報告する
4. 成功時だけ `pane close` で一時ペインを閉じる。失敗時は診断用に残し、path を報告する

live prune は §7 どおり、Agent 内の dry-run 要約 → ユーザー確認 → live 実行の順を保つ。現在の session の worktree を削除・入替する操作の後は、§7 に従い session を継続しない。

## 承認プロンプトと失敗の分岐

sentinel が来ないまま `wait-output` がタイムアウトしたら、`pane read` で状態を確認して分岐する。

- **wt が対話 approval を求めている**: エージェントは応答しない。`--yes` での迂回もしない。「共通規則」の入力クリア（`ctrl+c`）も未解決の承認プロンプトには適用しない。`herdr tab focus <tab-id>` で該当タブへユーザーを誘導し（一時ペインが現在タブ内にあるときはさらに `herdr pane focus --direction <split時の方向> --current` でペインへ寄せる。`pane focus` は `--direction` が必須で、任意の pane ID を直接指定できない）、承認待ちであることを報告して待つ。ユーザーの応答後に再度 `wait-output` で sentinel を待つ
- **コマンドが失敗した（`__WT_DONE=` が非ゼロ、またはエラー出力）**: 出力の要点を秘密値を伏せて報告し、ペイン・タブ・作成済み worktree を残す。自動 retry・rollback・force 系オプションの追加をしない
- **まだ実行中**: hook の実行など時間のかかる正当な処理なら、タイムアウトを延ばして待ち直す

## 報告

SKILL.md §8 の項目に加え、herdr で実行した操作、作成して残したタブ・ペインの ID とラベル、fork した agent 名を含める。
