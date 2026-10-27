# dig log: Pi の素化と T3 Code 委譲スキル

## 目的・前提・制約
- T3 Code の `delegate_task` で別 provider・モデルを子タスクとして使うとき、モデルと思考レベルを根拠を持って選べるようにしたい。
  - きっかけは Hermes の advanced-delegation（名前付きルートで provider・model・effort を固定し、エージェントは名前だけ選ぶ）。T3 Code にはルート機能がない。
- Pi は T3 Code 導入後、単体で使う必要が薄れた。Pi を使う意味は「Codex よりシステムプロンプトが簡素で、モデルのネイティブな挙動を使える」こと。T3 から Pi を使うなら委譲は T3 の `delegate_task` で足りる。
- 確認済みの事実:
  - `orchestrator_capabilities` が返すのはモデル ID・options・既定値のみ。性能・費用の情報はない。2026-10-27 時点の委譲可能 provider は codex（gpt-6-astra / gpt-6.1-sol / gpt-6.1-terra / gpt-6-luna、options: reasoningEffort, serviceTier）、claudeAgent（Opus 5.5 / Fable 5.1 / Sonnet 5.5 / Haiku 5.5、options: effort, fastMode）、pi（openai-codex/gpt-6-astra / gpt-6.1-sol / gpt-6-luna、options: thinking）。
  - T3 Code の Claude provider は Launch arguments の `--append-system-prompt-file` を読んでシステムプロンプトに追記する（相対パスはスレッド cwd 基準、`~` 非展開）。Codex は T3 がターンごとに `developer_instructions` を送るため、ユーザー側の追加指示が残る保証がない。T3 専用のシステムプロンプト欄はない。
  - T3 Code は Pi を `pi --mode rpc` で起動し、独自拡張 `pi-t3-mcp-extension.ts` を注入して `t3-code` MCP ツールを `pi.registerTool` で直接登録する（`orchestrator_capabilities` / `delegate_task` / `task_status` は direct、他は `tool_search` 経由の deferred）。codemode に依存しない。`mcp.json` に `t3-code` を書くと T3 の登録より優先されるため書かない。
  - Pi 1.3.0 では `mcp.json` のサーバーは既定で codemode exposure になり、接続時に codemode が自動有効化される。`"defaultTools": ["+codemode"]` は MCP サーバーがなくても codemode を有効にする設定。
  - Pi の `enableSkillCommands` の既定は `true`（`/skill:name` を登録）。現在 `false`。
  - `pi-web-access`（npm、v0.45.0、nicobailon/pi-web-access）は Web 検索・URL 取得・GitHub・PDF 等に対応し、複数の検索バックエンドを持つ。リポジトリに `chrome-cookies.ts` がある。
  - ketch の参照箇所: `mise.default.toml:43,59,81`（スキル配置と取得元）、`config/.agents/AGENTS.md:43`、`brew/Brewfile.default:22`、`scripts/tests/test_dotfiles_links.py:110`。
  - `pi-web-access` の README（main、v0.45）: API キーなしで動く（Exa MCP。Pi が `openai-codex` の ChatGPT サブスクリプションでログイン済みなら OpenAI 検索を優先）。キー・詳細設定は `~/.pi/agent/web-search.json`。ブラウザ cookie 利用は `allowBrowserCookies: true` か `PI_ALLOW_BROWSER_COOKIES=1` での opt-in（既定 false）。第三者のホスト型取得サービスも `fetchRouting.allowRemoteHostedProviders` の opt-in が必要。Claude Code・Codex 向けの MCP サーバーとしても動く。
  - 過去の導入履歴: `70c349e`（2026-06-17）で `npm:pi-web-access` を追加し、後に `npm:pi-web-access@0.35.0` と版固定。`933080a`（2026-10-09）で「Replace pi-web-access with the Ketch CLI and shared research guidance」として削除。Git 履歴に `web-search.json` はなく、現在の `~/.pi/agent/web-search.json` も存在しない（設定なしで使っていた）。
  - 既存の Pi 委譲ガイドは `config/.pi/agent/agent-tool-description.md`（判断手順と Artificial Analysis の比較表。Luna / Sol / Astra のみ）。
- 制約: リポジトリ CLAUDE.md の規則（配置の削除は宣言を消す前に unapply、setup に cleanup を追加しない、自作スキルは `config/.agents/skills/`、など）に従う。

## 決定事項
- 委譲のモデル選択ガイドはスキル `use-t3-code` に置き、`config/.agents/AGENTS.md` から参照して読まれる確率を上げる方向で進める。
  - 理由: Claude・Codex の両方から読める。`--append-system-prompt-file` は Claude 専用。
  - 出典: dig 開始前のユーザー提案
- `use-t3-code` の範囲は委譲（いつ委譲するか、モデル × 思考レベルの選び方、比較表、`target.options` の指定例）。T3 のツールの使い方は T3 が注入する指示に任せ、重複させない。`AGENTS.md` の worktree 規則は移さない。T3 注入指示にない委譲関連の項目があれば追加する。
  - 内訳として含める: 委譲の判断基準（並列化・速度費用・品質・文脈の独立・明示依頼、迷ったら直接作業）、子への依頼内容（目的・事実・範囲・変更可否・完了条件・報告形式）、親による結果の検証（完了状態を依頼の完了条件と照合）、独立レビューで異なるモデル系統を選ぶ観点。
  - 出典: Q1
- Pi の `agent-tool-description.md` にあった「長時間コマンドの実行」（軽量モデルへのバックグラウンド委譲）は移さない。
  - 理由: Claude Code・Codex は自前でバックグラウンド実行でき、T3 子タスクの方が重い。Pi 固有の回避策で、素化後は必要性が薄い。必要になれば追加する。
  - 出典: Q2
- 比較表には Codex 4モデル（Luna / Sol / Astra / Terra）と Claude 4モデル（Opus 5.5 / Fable 5.1 / Sonnet 5.5 / Haiku 5.5）を載せ、Terra と Claude 系の effort 別データを Artificial Analysis で追加調査する。未掲載値は補間せず「未掲載」と書く。Pi は委譲先の選択肢から外す（表にも載せない）。
  - 理由: 委譲元が Claude でも Codex でも、両系統を同じ基準で比べられるようにする。
  - 出典: Q3
- `use-t3-code` のモデル選択基準は、内蔵サブエージェント機能（Claude Code の `Agent` ツール等）と `delegate_task` の両方に適用する。どちらの経路を使うかは T3 の注入指示に従う。スキル名は `use-t3-code` のまま。
  - 理由: 経路は T3 の規則で決まり、モデル選択の判断は同じ。同一 provider 委譲だけ根拠なしで選ぶ状態を残さない。
  - 出典: Q4
- Pi の `pi-subagents`、`agent-tool-description.md`、`agents/*.md`、`subagents.json` を削除する。
  - 出典: dig 開始前のユーザー回答
- `APPEND_SYSTEM.md` は「Pi-Specific Behavior > MCP / codemode」の節だけ残し、Progress Updates・Task Execution・Communication・Subagents・Skills の節は削除する。
  - 理由: codemode はオンのままなので使い方の指示は必要。その他は共通 `AGENTS.md` と重なるか、削除する拡張が前提。
  - 出典: dig 開始前のユーザー回答、Q5
- `pi-auto-name`、`pi-inline-skills` を削除する。`pi-footer`、`pi-tool-call-markers`（TUI をたまに使うため）、`pi-vcc` は残す。
  - 出典: dig 開始前のユーザー回答
- codemode は Pi 本体の機能なのでオンのまま（`defaultTools` の `+codemode` を維持）。`mcp.json`（cua）は残す。
  - 出典: dig 開始前のユーザー回答
- ketch を削除する。`find-docs`、`agent-browser` は残す（Claude・Codex に相当する組み込みツールがないため）。
  - 出典: dig 開始前のユーザー回答
- ketch 削除に伴い `config/.agents/AGENTS.md` の該当2行を、ツール名を書かず方針だけにする: 「Web検索・ページ取得は一次情報を優先し、取得件数・文字数を必要な範囲に制限する」「UI 操作や通常の取得で読めないページの確認には `agent-browser` を使う」。公開コード検索の指定はなくす（`gh search code` 等も追加しない）。
  - 理由: 組み込みツールは各エージェントが把握している。方針はツール非依存で有効。新手段の追加は必要になってから。
  - 出典: Q6
- Pi に `pi-web-access` を設定なしで追加する。`web-search.json` は作らず、ブラウザ cookie 利用・第三者ホスト型取得は既定のオフのまま。API キーは使わない。
  - 理由: 過去も同じ形で使えていた。ChatGPT サブスクリプション認証で OpenAI 検索が使える。素化の方針に合う。
  - 出典: Q7
- Pi の拡張はすべて版固定なしで記述する（`npm:pi-footer` 等。`pi-web-access` も同様）。更新は `pi update --extensions`。`docs/apps.md` の「拡張の版指定は `settings.json` で管理する」も合わせて直す。
  - 理由: ユーザーの意向（固定不要）と記法の統一。素化後は利用頻度が下がり、手動で版を上げる価値が小さい。
  - 補足: Pi 1.3.0 `docs/packages.md` によれば版付き npm 指定は固定され、`pi update --extensions` で版なし指定のパッケージが更新される。
  - 出典: Q8
- `settings.json` の `"enableSkillCommands": false` を削除し、既定の `true`（`/skill:name` 登録）に戻す。
  - 理由: `pi-inline-skills` 削除後も TUI でスキルを明示的に呼べるようにする。素の挙動に戻す方針に合う。
  - 出典: Q9

## 未決・保留
- 以下は計画で詰める実装詳細（設計判断は不要）:
  - 削除する Pi 配置（`~/.pi` は `symlink-each` + `manifest = "git"`）と ketch のスキル配置・取得元の、宣言削除前の unapply 手順。インストール済み Pi パッケージの後始末（`pi remove` 等）と `brew uninstall ketch` はユーザー操作として案内するか。
  - `use-t3-code` のファイル構成（SKILL.md と比較表の分割）、`AGENTS.md` に足す参照行の文言、比較表の調査日付。既存の Luna / Sol / Astra の値も調査時に再確認するか。
  - `scripts/tests/test_dotfiles_links.py:110` の ketch 削除、`docs/apps.md` の Pi 節の更新。

## 対象外
- T3 Code 本体への機能要望（名前付きルート等）。
- 長時間コマンドの委譲ガイド（Q2）。
- 公開コード検索の代替手段の追加（Q6）。
- Codex への T3 専用システムプロンプト注入、Claude の `--append-system-prompt-file` の利用。
- Pi を委譲先として扱うこと（Q3）。
- 作業開始時点で未コミットの `config/.codex/config.toml` の変更。

## 撤回・置換済み
- codemode の節・`+codemode` の削除案は撤回。codemode はオンのまま。
  - 出典: dig 開始前のユーザー回答
