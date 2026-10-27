# Pi の素化と T3 Code 委譲スキル Implementation Plan

決定記録: [dig log](../dig/2026-10-27-pi-minimal-t3-delegation.md)

## Requirements

T3 Code で委譲するとき、モデルと思考レベルを根拠を持って選べるようにする。Pi は T3 から使う「システムプロンプトが簡素な実行環境」に寄せ、委譲と Web 調査のための独自の仕組みを外す。

- **`use-t3-code` スキル**: `config/.agents/skills/use-t3-code/` に作る。内容は委譲のガイドで、次を含める。
  - 委譲するかの判断（並列化・速度費用・品質・文脈の独立・明示依頼のどれかに当たるときだけ。迷ったら直接作業）
  - 子への依頼内容（目的・必要な事実・範囲・変更可否・完了条件・報告形式）
  - 親による検証（`completed` を依頼の完了条件と照合し、差分・テスト・出典を確認する）
  - 独立レビューで別系統のモデルを選ぶ観点
  - モデル × 思考レベルの選び方と比較表
  - 適用範囲は内蔵サブエージェント機能（Claude Code の `Agent` など）と `delegate_task` の両方。どちらの経路を使うかは T3 の注入指示に従う
- **比較表**: Codex の Luna / Sol / Astra / Terra と、Claude の Opus 5.5 / Fable 5.1 / Sonnet 5.5 / Haiku 5.5 を effort 別に載せる。出典は Artificial Analysis。未掲載の値は補間せず「未掲載」と書く。Pi は委譲先に含めない。
- **`AGENTS.md` からの参照**: 委譲する前に `use-t3-code` を読む旨の一行を足す。
- **Pi から削除する**: `pi-subagents`、`agent-tool-description.md`、`agents/*.md`、`subagents.json`、`pi-auto-name`（`config/.config/pi-auto-name/config.json` を含む）、`pi-inline-skills`、`"enableSkillCommands": false`。
- **Pi に残す**: `pi-footer`、`pi-tool-call-markers`、`pi-vcc`、`"defaultTools": ["+codemode"]`、`mcp.json`（cua）。
- **`APPEND_SYSTEM.md`**: 「Pi-Specific Behavior > MCP / codemode」の節だけ残す。
- **Pi の拡張の版**: すべて固定せずに書く（`npm:pi-footer` など）。`pi-web-access` は設定なしで追加する。`web-search.json` は作らず、API キーも使わない。cookie 読み取りと第三者のホスト型取得は既定のオフのまま。
- **ketch を削除する**: Brewfile、スキルの配置宣言（共通・Claude）、取得元の repos 宣言、テストの期待値から外す。`AGENTS.md` の該当2行は、ツール名を書かず方針だけにする。
  - 「Web検索・ページ取得は一次情報を優先し、取得件数・文字数を必要な範囲に制限する」
  - 「UI 操作や通常の取得で読めないページの確認には `agent-browser` を使う」
  - `find-docs` と `agent-browser` は残す。

対象外:

- T3 Code 本体への機能要望、Claude の `--append-system-prompt-file`、Codex への専用プロンプトの注入。
- 長時間コマンドの委譲ガイド、公開コード検索の代わりの手段（`gh search code` など）。
- 着手前からある未コミットの `config/.codex/config.toml` の変更。触らず、commit もしない。
- `docs/dig/` と `docs/plans/archived/` の過去の記録。

## Implementation Decisions

- **スキルの構成**: `SKILL.md` 1ファイルにまとめる。判断手順と比較表はどちらもモデル選びのたびに使うので、分けても読み込みは減らない。
  - `target.options` に指定できる値は `orchestrator_capabilities` が正本なので、スキルには列挙しない。スキルに書くのは、どの effort をどう選ぶかと、`delegate_task` の `target` の書き方の例だけにする。
  - 書き方は既存の `use-agent-device` に合わせる（日本語、frontmatter に `name` と `description`）。
- **比較データ**: Pi 版の判断手順と指標の説明（Intelligence / Terminal-Bench / AA-LCR / Omniscience / USD/task / 推定 decode 秒）を土台にする。数値は全8モデルを同じ日に取り直し、確認日を1つだけ書く。日付の違う値を混ぜると比べられなくなるためで、Luna / Sol / Astra も取り直す。
  - Claude 系の effort のうち、Artificial Analysis に掲載されているものだけを行にする。`ultracode` / `ultrathink` など掲載のない段階は行を作らない。
  - 情報の取得は `ketch` を削除する前に行うか、組み込みの WebFetch を使う。
- **`AGENTS.md` の参照行**: 「ツール・環境」節の `use-agent-device` の行の近くに置く。例: 「サブエージェントへ委譲する（内蔵機能・T3 Code の `delegate_task`）ときは、モデルを選ぶ前に `use-t3-code` スキルを読む」。
- **リンクの整理**:
  - `~/.pi` と `~/.config` は `symlink-each` + `manifest = "git"` なので、Git 追跡から外したあとに apply で整理する（前回の簡素化計画と同じ手順）。
  - 個別に宣言している ketch のスキルリンク（`~/.agents/skills/ketch`、`~/.claude/skills/ketch`）は、宣言を消す前に `mise -C ~/dotfiles -E <構成> dot unapply TARGET` で解除する。
  - 新しいスキルは、自作スキルの glob で自動的に配置される。
  - `<構成>` は、この Mac で使っている構成（`default,private` か `default,work`）。
- **実機操作は都度承認を取る**: 次の操作は、対象を示してその都度ユーザーの承認を得る。編集と計画の承認だけでは実行しない。
  - unapply / apply
  - `brew uninstall ketch`
  - repos 宣言から外した `~/.local/share/agent-skill-sources/ketch` の checkout の削除（宣言を消しても checkout は残るため）
  - 外したパッケージの後始末（`pi update --extensions` で整理されるかを `pi list` で確かめ、残っていれば `pi remove`）
  - `pi remove` などは symlink 先の `settings.json` を書き換えるおそれがある。実行後に Git の差分を確認する。
  - `~/Library/Caches/ketch` は削除しない。

## Tasks

review base: `71374d5`

- [ ] **`use-t3-code` スキルの作成**: `config/.agents/skills/use-t3-code/SKILL.md` を作る。
  - Requirements の内訳を書き、Pi 版から引き継ぐ内容は T3 向けに書き換える。
    - `run_in_background` / `get_subagent_result` → `mode: "async"` / `task_status`
    - モデル ID → `providerInstanceId` + `model`
    - `thinking` → `target.options`
  - Pi 固有の節（長時間コマンド、`SubagentWorkflow`、`max_turns`）は移さない。
  - description には、サブエージェントへの委譲・`delegate_task`・モデル選択で使う旨を書く。
- [ ] **共通指示の更新**: `config/.agents/AGENTS.md` に `use-t3-code` の参照行を足し、ketch の2行を Requirements の文言に書き換える。
- [x] **Pi の素化**: 実施済み。`settings.json` は JSON 構文 OK、削除対象への参照は dig・plans 以外に残りなし。
  - 削除する: `config/.pi/agent/agent-tool-description.md`、`config/.pi/agent/agents/`、`config/.pi/agent/subagents.json`、`config/.config/pi-auto-name/`。
  - `config/.pi/agent/settings.json` を変更する。
    - `packages` を `npm:pi-footer`、`npm:@pi-kaush/pi-tool-call-markers`、`npm:@sting8k/pi-vcc`、`npm:pi-web-access` にする。
    - `enableSkillCommands` を削除する。
    - その他のキーはそのまま残す。
  - `config/.pi/agent/APPEND_SYSTEM.md` を MCP / codemode の節だけにする。見出しの構成は残る節に合わせて整える。
  - `docs/apps.md` の Pi 節を直す。
    - 「拡張の版指定は `settings.json` で管理する」を、版を固定せず `pi update --extensions` で更新する旨に書き換える。
    - Web 検索は `pi-web-access` で、設定なしで使う旨を足す。
- [ ] **ketch の削除**:
  - unapply（承認後）のあと、次から ketch を外す: `mise.default.toml` の3行（`~/.agents/skills/ketch`、`~/.claude/skills/ketch`、repos の `~/.local/share/agent-skill-sources/ketch`）、`brew/Brewfile.default` の `brew "ketch"`、`scripts/tests/test_dotfiles_links.py` の期待集合の `'ketch'`。
- [ ] **実機への反映（要承認）**:
  - apply の dry-run を確認してから apply する。対象は、削除した Pi・pi-auto-name のリンクの整理と、`use-t3-code` のリンクの作成。
  - そのあと、`brew uninstall ketch`、ketch の checkout の削除、Pi のパッケージの後始末を、それぞれ承認を得て行う。

## Final Validation

- [ ] **設定ファイルの構文**: `python3 -m json.tool config/.pi/agent/settings.json` と `python3 -c 'import tomllib; tomllib.load(open("mise.default.toml","rb"))'` → どちらもエラーなし
- [ ] **配置宣言とテスト**: `uv run --no-project python scripts/tests/test_dotfiles_links.py` と `uv run --no-project python scripts/tests/test_dotfiles_sources.py` → すべて成功し、skip なし
- [ ] **Brewfile**: `brew bundle list --file brew/Brewfile.default` → エラーがなく、`ketch` を含まない
- [ ] **配置予定**: `mise -C ~/dotfiles -E <構成> dot apply --dry-run` → ketch のリンクを作らない。`use-t3-code` のリンクを作り、Pi の削除対象のリンクを整理する。それ以外に不明な実体や衝突がない
- [ ] **参照の残り**: `rg -n 'ketch|agent-tool-description|pi-subagents|subagents\.json|inline-skills|pi-auto-name' --glob '!docs/dig/**' --glob '!docs/plans/**'` → 該当なし。あわせて `git diff --check` も問題なし
- [ ] **スキルの内容**:
  - 比較表に8モデル分の行があり、各値の出典リンクと確認日がある。
  - `use-t3-code` が `orchestrator_capabilities` と矛盾しない。provider ID、モデル ID、options のキー名を、実行時の出力と照らし合わせる。
- [ ] **実機（apply 後）**:
  - `~/.agents/skills/use-t3-code` と `~/.claude/skills/use-t3-code` が正本を指している。
  - T3 で Pi のスレッドを新しく開き、`web_search` と `mcp__t3-code__delegate_task` が使え、Agent / subagent 系のツールがないことを確かめる。
  - `pi list` に削除した拡張が出ない。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
