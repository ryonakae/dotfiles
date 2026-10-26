# T3 Code 中心への簡素化 Implementation Plan

## Requirements

エージェント作業を T3 Code + Zed + Ghostty に寄せ、不要になった仕組みを dotfiles から削除する。

- **保護**: Agent Safehouse を廃止する。危険操作への対策は T3 の Auto モード（Claude `auto`、Codex `on-request` + `auto_review` + `workspace-write`）に任せる。Pi は Auto を持たないことを了承済み。
- **秘密**: dotenvx を廃止し、Git 管理外の平文 `.env` と値のない `.env.example` の方式に統一する。共有トークンは T3 の provider instance の Environment variables（Sensitive）に、Hermes 用は `~/.hermes/.env` に置く。値は Git に入れず、1Password を控えとする。
- **削除**: Herdr 一式（Zerdr、plugins、外部スキル、エージェント連携を含む）、tmux、mosh、ccstatusline、Worktrunk 一式、Safehouse 一式、エージェント用 fish wrapper（`claude` / `codex` / `pi` / `opencode` / `agy` / `hermes` / `safe` / `__safehouse_args`）、dotenvx 一式、`~/.local/bin/rm`（ゴミ箱 wrapper）と macos-trash、自作の通知 hook と terminal-notifier。
- **残す**: Pi、OpenCode、Antigravity、Hermes。Ghostty、Zed、fish、mise、Brewfile、macOS 設定、Karabiner、Hammerspoon、自作スキル。
- **Hermes**: 独自の gateway 管理（plist 生成、`hermes-gateway.fish`、launchctl adapter、Safehouse wrapper）をやめ、fork 標準の `hermes gateway install|start|stop|status` に任せる。checkout と導入用の mise task は残す。
- **別リポジトリ**: `~/Dev/colorsing/use-figma`（private）の dotenvx 化を戻す。
- **指示の書き換え**: グローバル指示（`config/.agents/AGENTS.md`）から Herdr、`wt`、dotenvx のルールを削り、worktree は T3 Code で扱う旨に書き換える。

対象外:

- 着手前からある未コミット変更（Claude の `opus[1m]` と vercel plugin、Codex 設定、Zed の `trust_all_worktrees`、T3 設定の配置宣言と `config/.t3/`）。触らず、commit もしない。同じファイルを編集する場合（`config/.claude/settings.json`、`mise.default.toml`）は、本計画の hunk だけを stage する。`config/.t3/` は未追跡なので、`defaultRuntimeMode` の追加は編集だけ行い、commit はユーザーの判断に任せる。
- Yazi、zoxide、fzf など、今回話題にしていないシェル周りのツール。
- 各プロジェクトへの `t3.json` の追加（Worktrunk の ignored ファイルのコピーの代わり）。必要になったリポジトリで個別に行う。
- `docs/dig/` と `docs/plans/archived/` の過去記録。

## Implementation Decisions

- **T3 の既定モード**: `config/.t3/userdata/settings.json` に `"defaultRuntimeMode": "auto"` を足す。T3 はスレッドごとにモードを明示して渡すので、Claude の `permissions.defaultMode` は変えない。
- **T3 に渡す秘密**: Environment variables は UI から登録する。T3 は Sensitive の値を `~/.t3/userdata/secrets/` に移し、settings.json には `value: ""` と `valueRedacted: true` だけを書く（`apps/server/src/serverSettings.ts:628-656`）。settings.json は dotfiles への symlink のまま、提供元を書き換える（`packages/shared/src/atomicWrite.ts`）。このため登録後の settings.json の差分に値が無いことを必ず確認する。
- **Hermes の起動**: 標準 installer の `products` 段階が `~/.local/bin/hermes` を作るので、`~/.local/libexec/hermes` の launcher と fish の `hermes` 関数は不要になる。`~/.hermes/.env` は fork が自分で読み込む（`hermes_cli` の `load_hermes_dotenv`）。
- **リンクの解除と実機操作**: 個別に宣言したリンク（`~/.local/bin/rm`、外部スキル `herdr` / `worktrunk`、Hermes の libexec 2件）は、宣言を消す前に `mise dot unapply TARGET` で解除する。`symlink-each` の配下（`~/.config` の herdr、agent-safehouse、ccstatusline、worktrunk、fish 関数、`~/.claude/hooks`、`~/.codex/hooks`、`~/.agents/hooks`、Pi の notification 拡張）は、Git 追跡から外したあとに apply で整理する。unapply、apply、brew uninstall、Herdr 連携の解除、Keychain の削除、Hermes の移行は実機操作なので、対象を示してその都度ユーザーの承認を得る。
- **Herdr 連携の解除順**: `herdr integration uninstall` は Claude の settings.json（dotfiles 側）などを書き換える。そのため、settings.json の手編集より前に実行し、Git 差分を確認する。

## Tasks

review base: dotfiles `5e9667d`、use-figma `22f60fa`

- [x] **Herdr 連携とリンクの解除（実機、要承認）**
  - `herdr integration uninstall claude|pi|codex|opencode` を実行する。`~/.claude/hooks/herdr-agent-state.sh`、`~/.codex/hooks.json`、`~/.codex/herdr-agent-state.sh`、`~/.pi/agent/extensions/herdr-agent-state.ts`、`~/.config/opencode/plugins/herdr-agent-state.js` と Git 正本の変化を確認する。
  - 上記の個別リンクを `mise -C ~/dotfiles -E default,private dot unapply TARGET` で解除する（private はこの Mac に Hermes がない場合、宣言の確認だけ）。
- [x] **Herdr、tmux、mosh、ccstatusline の削除**
  - `config/.config/herdr/`、`hdr.fish`、`mise.default.toml` の `herdr:plugins` task と外部スキル `herdr` の宣言（共通・Claude・repos）、`.disabled/herdr-agent-team`、`scripts/allow-mosh-firewall.sh`、`config/.config/ccstatusline/` と `.editorconfig` の該当節を削除する。
  - `config/.claude/settings.json` の Herdr の SessionStart hook（解除後も残っていれば）と `statusLine` を削除する。
  - `config/.config/pi-auto-name/config.json` の Herdr / tmux 用キーを削除する（スキーマ上、必須なら false のまま残す）。
    - pi-auto-name 自身の機能を無効にする設定なので、false のまま残した。
  - `config/.config/fish/conf.d/ssh-agent.fish` の mosh 用 PATH 補完を削除し、SSH_AUTH_SOCK の補完は ssh 用として残す。
  - `scripts/dotfiles.py` の Herdr plugins 段階と案内文、対応する `test_dotfiles_cli.py` の期待を更新する。
- [x] **Worktrunk の削除**: `config/.config/worktrunk/`、`wt.fish`、`completions/wt.fish`、`config/.agents/skills/use-worktrunk/`、外部スキル `worktrunk` の宣言（共通・Claude・repos）を削除する。
- [x] **Safehouse とエージェント wrapper の削除**
  - `config/.config/agent-safehouse/` 全体、fish 関数（`safe`、`__safehouse_args`、`claude`、`codex`、`pi`、`opencode`、`agy`、`hermes`）、`config/.agents/skills/use-agent-safehouse/`、`scripts/tests/check_safehouse_runtime.py`、`test_agent_runtime.py` を削除する。
  - `APP_SANDBOX_CONTAINER_ID` による拒否（`scripts/dotfiles.py`、`scripts/macos-settings.sh`、`scripts/hermes-install.py`）と対応テストの Safehouse ケースを削除する。root・非対話の拒否は残す。
  - `config/.agents/skills/ask-codex/SKILL.md` の「Agent Safehouse 内での実行」節と判定手順を削除する。
  - `pi.fish` が設定していた `PI_TELEMETRY=0` と `GIT_OPTIONAL_LOCKS=0` は、T3 の Pi instance の Environment variables へ移すよう docs に記す（`PI_CLIPBOARD_OSC52` は Herdr のペイン内で mosh 越しにクリップボードへ書き込むための設定なので移さない）。
  - `claude.fish` の `--mcp-config ~/.claude/mcp.json` が T3 経由で失われる点は、`mcp.json` の中身を見て、T3 の Claude instance の `launchArgs` へ移すか `~/.claude.json` 側へ寄せるかを実装時に決め、docs に反映する。
    - `mcp.json` は `cua` だけを定義している。T3 Code の Claude の Launch arguments に `--mcp-config <絶対パス>` を指定する手順を `docs/apps.md` に記した（設定はユーザーが画面で行う）。
- [x] **ゴミ箱 wrapper の削除**: `config/.local/bin/rm`、`mise.default.toml` の該当リンク、`scripts/tests/test_rm_trash.py`、Brewfile の `macos-trash` を削除する。
- [x] **通知 hook の削除**
  - `config/.agents/hooks/`、`config/.claude/hooks/`、`config/.codex/hooks/`、`config/.pi/agent/extensions/notification/`、Claude settings.json の Notification hook、Brewfile の `terminal-notifier` を削除する。
  - Codex の `notify`（Computer Use）と `[features] hooks` は自作通知とは別物なので変えない。
- [x] **dotenvx の削除と秘密の移行**
  - `config/.config/.env.example`、`scripts/tests/check_dotenvx_runtime.py`、Brewfile の dotenvx と tap を削除する。`.gitignore` の `.env` は残す。
  - `docs/secrets.md` を「T3 の provider instance の Environment variables（Sensitive）／`~/.hermes/.env`／プロジェクトの `.env` と `.env.example`、値の控えは 1Password」の手順に書き直す。
    - どの変数をどの instance に入れるかを書く。`CONTEXT7_API_KEY` は Claude / Codex / Pi / OpenCode、`OMLX_API_KEY` は OpenCode / Pi。`HOMEBREW_GITHUB_API_TOKEN` と `TYPESAFE_API_KEY` は廃止する（合意済み）。`~/.config/.env` も廃止し、シェル用の読み込み処理は作らない。
    - エージェントの `env` 出力が T3 の `statev2.sqlite` に平文で残る既知の issue（pingdotgg/t3code#24790）を注意として残す。
  - 移す値は `dotenvx get` で `~/.config/.env` から、または 1Password から取り出す。登録は `brew uninstall dotenvx` より前に終える。
  - 実機操作（要承認）: `~/.config/.env` のリンクと実ファイルの扱い、Keychain の dotenvx 鍵の削除は、値を移し終えてからユーザーが行う。
  - `config/.config/fish/config.fish` の `AGENT_BROWSER_ARGS` にある `--no-sandbox` 系は、Safehouse 内で Chrome の sandbox が失敗するのを避けるためのものだった。ほかに必要な理由が無ければ削除する。
- [x] **Hermes の標準化**
  - 削除するもの: `scripts/hermes_plists.py`、`test_hermes_activation.py`、`test_hermes_tmpdir.py`、`hermes-gateway.fish`、`__hermes_bootstrap.fish`、`config/.local/libexec/hermes`、`config/.local/libexec/hermes-gui-launchctl/`、`mise.private.toml` の libexec リンク2件。
  - `scripts/dotfiles.py` の Hermes plist 配置段階と案内文、`test_dotfiles_cli.py`、`test_dotfiles_links.py` の Hermes launcher の期待を更新する。
  - `config/.hermes/SOUL.md` の Safehouse 前提の行を、標準 gateway の前提に直す。
  - `docs/apps.md#hermes` を書き直す。秘密は `~/.hermes/.env`、gateway は `hermes gateway install|start|stop|status` を使う。既存 Mac の移行手順として、旧 `hermes-gateway stop`、`~/Library/LaunchAgents/ai.hermes.gateway.plist` の退避、標準 install を記す。
  - `hermes-install.py` は従来どおり installer の gateway 段階を呼ばない。`hermes gateway install` は導入後にユーザーが行う別手順として docs に記す。
  - この Mac には Hermes がないので、移行の実施は private の Mac でユーザーが行う。
- [x] **T3 設定**: `config/.t3/userdata/settings.json` に `defaultRuntimeMode: "auto"` を追加する。
  - 着手時点でユーザーが設定済みだったため、編集は不要だった。
- [x] **Brewfile**: `herdr`、`ryonakae/tap/zerdr` と `tap "ryonakae/tap"`（ほかに使っていなければ）、`agent-safehouse` と tap、`dotenvx` と tap、`tmux`、`mosh`、`worktrunk`、`macos-trash`、`terminal-notifier` を宣言から外す。
  - 宣言を外してもアンインストールにはならないので、`brew uninstall` は最後に対象を示し、承認を得て実行する。
  - 未実施（要承認）: `brew uninstall`、checkout の削除、古いリンクを掃除する `mise dot apply`。
  - repos の宣言を外しても checkout は消えない。`~/.local/share/agent-skill-sources/{herdr,worktrunk}` の削除も同じタイミングで承認を得て行う。
- [x] **指示とスキルの更新**
  - `config/.agents/AGENTS.md`: `HERDR_ENV` の行と dotenvx の行を削除する。`wt` の行を「worktree は T3 Code（スレッド起動時の worktree 指定や `t3_*` ツール）で作成・削除し、`git worktree` を直接使わない」に書き換える。秘密は「Git 管理外の `.env` に置き、値のない `.env.example` だけを管理する」に統一する。
  - リポジトリの `AGENTS.md`: Herdr、Safehouse、Hermes の旧運用ルールを、今回の構成に合わせて書き換えるか削除する。
  - `.agents/skills/dotfiles-setup/`（SKILL.md、`references/setup.md`）: Hermes の管理元表、Safehouse、Herdr、Zerdr の項を更新する。
- [x] **ユーザー向け docs**
  - `README.md`: Safehouse の説明を、T3 Code の Auto モードを前提とした説明に置き換える。
  - `docs/setup.md`: Herdr と Hermes の段階、`type pi` による完了確認を、T3 Code での provider 確認と秘密の登録に置き換える。
  - `docs/usage.md`: mosh、Safehouse の記述を削除する。
  - `docs/troubleshooting.md`: `.env` の復号、Herdr、Safehouse 内 `rm` の節を削除する。
  - `docs/apps.md`: Herdr 節と各エージェントの Herdr 連携行、statusline の行を削除し、T3 Code 節（既定モード、Environment variables、Zed 連携）を追加する。
- [x] **use-figma の dotenvx 撤去**（`~/Dev/colorsing/use-figma`、private のため日本語で commit）
  - 実機操作（要承認）: `.env` を `dotenvx decrypt` で平文に戻し、`DOTENV_PUBLIC_KEY` 行を削除する。値は表示しない。
  - `git rm --cached .env` で追跡を外し、`.gitignore` に `.env` を足し、`.env.example`（`FIGMA_ACCESS_TOKEN=`）を追加する。
  - `package.json` の `mcp:figma-console` を `set -a && . ./.env && set +a && npx -y figma-console-mcp@latest` にする。npm scripts は sh で、パッケージルートを cwd にして実行される。
  - `AGENTS.md` の「秘密情報」節と `.agents/skills/figma-console/SKILL.md` の前提を、平文 `.env` の方式に書き換える。
  - 過去の commit には暗号化された `.env` が残るが、履歴は書き換えない。dotenvx の鍵（Keychain）の削除は、MCP の起動を確認してからユーザーが行う。

## Final Validation

- [x] **構文**: 変更・残存した fish ファイルに `fish --no-execute`、shell script に shebang に合わせた `-n` を実行する → エラーなし。
- [x] **setup 入口と配置のテスト**: `uv run --no-project python -m unittest discover -s scripts/tests -p 'test_*.py'` → すべて成功。削除したテスト以外に skip が無い。
- [x] **TOML と Brewfile**: `mise -C ~/dotfiles -E default,private dot apply --dry-run` → 削除したリンクの解除と残りの配置だけが表示され、未知の実体への上書きが無い。`brew bundle list --file=brew/Brewfile.default` → 外した formula が出ない。
- [x] **参照の残り**: `rg -n -i 'herdr|zerdr|safehouse|dotenvx|worktrunk|\bwt\b|tmux|mosh|ccstatusline|hermes-gateway|hermes_plists|notification\.sh'` を `docs/dig/`、`docs/plans/archived/`、本計画を除いて実行する → 意図して残した記述だけ。
- [x] **文書**: 変更した Markdown のリンクとアンカーを確認し、`git diff --check` → 問題なし。
- [ ] **T3 の動作（手動）**: T3 を再起動して新しいスレッドを作り、Claude と Codex で次を確かめる。
  - 既定モードが Auto になっている。
  - 登録した環境変数がエージェントの環境に存在する（値は表示せず、有無だけを見る）。
  - `git diff config/.t3/userdata/settings.json` に秘密の値が無い。
- [x] **use-figma（手動）**: `git status` で `.env` が追跡外かつ無視されていることを確かめる。Claude から `figma-console` MCP が起動することを確かめる。
  - `.env` は追跡外で無視されている。MCP は `npm run --silent mcp:figma-console` で起動し、`MCP server started successfully on stdio transport` を確認した。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。

## Gate Summary

- レビュー対象: dotfiles `5e9667d..99ff2e4`（`3833870`、`37cae19`、`5d39697`、`97b2db1`、`27254e8`、`98958c6`、`af21cac`、`1aace96`、`99ff2e4`）、use-figma `22f60fa..66349a8`。
- 独立レビュー: blocking/high なし。decision required 3 件（秘密の確認手順、ターミナル起動時の秘密、Hermes 旧リンクの解除順序）と medium 2 件（スキルに残った Safehouse 確認、移行手順の抜け）を、計画の範囲内の文書修正として採用した（`1aace96`）。再レビューで解消を確認した。
- 再レビューで出た low のうち、計画外の 1Password 鍵削除の記述を取り消した（`99ff2e4`）。
- 採用しなかったもの: use-figma の `--strict` 相当の空値チェック、`.env.keys` の ignore 削除（low）。OpenCode 節のターミナル起動手順への注記（low）。
- 最終検証: 全テスト 120 件成功（作業ツリーから着手前の T3 リンク宣言を除いた複製で実行）、fish 構文、Brewfile、`mise dot apply --dry-run`、文書リンク、`git diff --check`。
- 実機操作（承認済み・実施済み）: Herdr 連携の解除、個別リンクと自作スキルの unapply、`mise dot apply`、brew uninstall（`terminal-notifier` は fastlane の依存のため残した）、tap 2 件の削除、外部スキル checkout 2 件の削除、use-figma の `.env` 復号。
- 未実施: T3 Code での手動確認、T3 の Environment variables と Claude の Launch arguments の登録、この Mac の `~/.config/.env` の値の移行と dotenvx の削除。いずれもユーザーが行う。
- 未解決の blocking/high: なし。
