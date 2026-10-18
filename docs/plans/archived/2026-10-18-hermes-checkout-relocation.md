# Hermes checkout 移設 Implementation Plan

## Requirements

- 稼働用の `ryonakae/hermes-agent` checkout を `~/.hermes/hermes-agent` から `~/Dev/private/hermes-agent` へ移す。`HERMES_HOME` は `~/.hermes` のまま変えない。
- 目的: hermes-agent のテストガード（`tests/home_io_guard.py`）が、checkout の親 `~/.hermes/manifest.json` への読み取り（`pm/environments.py` の `_payload_manifest`）を本物の Hermes ホームへの I/O として拒否し、`tests/hermes_state` だけで約700件が環境要因で失敗している状態を解消する。
- `scripts/hermes-install.py` とテストを現行 fork の installer に合わせる（ユーザー合意済み）。現行 `scripts/install.sh --manifest` の stage は `prerequisites, repository, venv, python-deps, config, products, setup, gateway, complete`。`node-deps` は存在せず、`venv/bin/hermes` は作られない。起動用の launcher `<checkout>/.hermes/bin/hermes` と `~/.local/bin/hermes*` は `products` stage が生成する。
- `config/.local/libexec/hermes` と `scripts/tests/test_agent_runtime.py` の既存の未コミット変更（`venv/bin/hermes` → `.hermes/bin/hermes`）は破棄せず、新パスへ置き換える。`config/.pi/agent/settings.json` の未コミット変更は対象外で、触らない。
- launchd plist、Safehouse wrapper、fish の管理関数は変更しない。いずれも `~/.local/libexec/hermes` 経由で起動しており、Safehouse は `--add-dirs="$HOME"` で新しい配置先も許可済み。
- 対象外: checkout 内の旧 `venv/` の削除。旧 install state（`~/.hermes/installs/01f3a163eab293b7`）は手動では消さない。ただし、`inputs/.project-root` に記録された checkout が data root（`~/.hermes`）配下で消えた状態は、PM の startup pruner（`pm/install_states.py` の `_provably_deleted`）が自動削除の対象にする。そのため、移設後の初回起動で消える前提で扱う。

## Implementation Decisions

- **移設方法は `mv`**: fresh clone は使わない。ignored のファイルや作業ブランチの状態をそのまま保てる。切り戻しも `mv` で戻すだけで済む。
- **新パスでの依存とランチャーは installer の標準 stage で作り直す**: PM の install state は `sha256(resolve(checkout))` をキーにしている（`pm/environments.py:20`）。`.hermes/bin/hermes` と `~/.local/bin/hermes*` には checkout の絶対パスが埋め込まれている。どちらも新パスで `python-deps` → `products` → `complete` を実行して再生成する。
- **移行作業は `hermes:update` ではなく troubleshooting の手動 stage 手順で行う**: `hermes-install.py` は、完了 marker の `pinnedCommit` が HEAD と一致することを前提にしている。現在の marker は `36273931cc` で、HEAD は `8631ce1889`。この不一致で update は停止する。marker の扱いは既存の安全設計のため変更しない。
- **`hermes-install.py` の stage 構成**: install は `venv, python-deps, products, complete`、update は `python-deps, products, complete` にする。
  - `--skip-browser --skip-computer-use` は廃止し、install でも update でも渡さない（ユーザー合意済み）。agent-browser と cua-driver は、Hermes が固定しているバージョンを PM に管理させる。理由は次のとおり。
    - `config.yaml` で `browser` と `computer_use` がどちらも有効になっている。
    - cua-driver は、PM の binary か `HERMES_CUA_DRIVER_CMD` しか使わず、PATH にはフォールバックしない（`tools/computer_use/cua_backend_driver.py:75`）。除外すると computer use が使えなくなる。
    - agent-browser は、PM の版がなければ PATH の Homebrew 版（0.39.1。PM の固定版は 0.26.0）に切り替わる（`tools/browser_tool_install.py:60`）。
    - 現在のインストールにも `declined-packages.json` はなく、PM が両方を管理している。
  - 完了判定と管理対象のパスは `venv/bin/hermes` から `.hermes/bin/hermes` に変える。
  - HERMES_HOME 側の管理パス（`~/.hermes` と、現行 installer が uv などを置く `~/.hermes/tools`）は、`target.parent` ではなく `~/.hermes` を明示して指す（移設後は `target.parent` が `~/Dev/private` になるため）。
  - `venv` stage は現行の installer では Python を準備するだけで、venv ディレクトリを作らない。そのため、既存 venv の再作成を防ぐガードは不要になる。
- **`products` stage の副作用**: `products` は `~/.local/bin` の PATH 追加（`wire_shell_path`）も行う。この処理は `$SHELL` を見て追記先を選ぶ。fish なら、`config/.config/fish/config.fish:12` に `fish_add_path ... "$HOME/.local/bin"` があるので、追記は起きない。新しい Mac の setup では、login shell を fish に変える `bootstrap user apply` が hermes:install より後に実行される。そのため、hermes:install の時点の `$SHELL` は元の zsh のままである。そのため `~/.zshrc` と `~/.zprofile` に追記されてしまう。これを防ぐため、`hermes-install.py` は `products` stage を `SHELL=/opt/homebrew/bin/fish`（`mise.default.toml` の `login_shell` と同じ値）で実行する。installer に PATH 追加を止めるオプションはない。Desktop のビルドは `apps/desktop/release/<platform>` があるときだけ行われ、現状このディレクトリはないので実行されない。setup.md の「PATH・設定・gateway・Desktop 段階は呼ばない」は、`products`（command の生成を含む）を使う形に改める。
- **`products` の副作用の明示**（レビュー後にユーザーが決定）: `products` は launcher と `~/.local/bin/hermes*` の生成に加えて、tui/web のビルド、bundled skills と profile の同期、`~/.hermes/config.yaml` の移行（非対話で自動適用）、PM の既定ツールの導入も行う。docs、setup.md、`hermes-install.py` の実行前の告知にこれを書き、「設定は任せない」という記述は「`config` stage（初期設定の生成）は呼ばない」に絞る。
- **fish の PATH 行を前提条件にする**（レビュー後にユーザーが決定）: `hermes-install.py` は、stage を実行する前（完了済みの install で何もしない場合を除く）に、`~/.config/fish/config.fish` に installer の判定（`^[[:space:]]*fish_add_path.*\.local/bin`）に一致する行があることを確認する。一致する行がなければ、何も書き込まずに停止し、先に `default` を適用するよう案内する。`private` 単独の setup で `products` が `config.fish` を普通のファイルとして作ってしまうのを防ぐためである。
- **切り替え中のサービス停止**: `~/.local/libexec/hermes` は dotfiles の作業ツリーへのシンボリックリンクなので、編集した瞬間に稼働中の起動先が変わる。gateway は `KeepAlive` が有効なため、停止しないまま異常終了すると新パスが未完成の状態で再起動してしまう。そこで、dotfiles の編集はサービスを止めてから行う。

## Tasks

review base: `adb75dd`

- [x] **dotfiles のパス・installer 追従**（`test_hermes_install.py` 26件、`test_agent_runtime.py` 24件成功）: 次のファイルを変更する。
  - `mise.hermes.toml`: `[bootstrap.repos]` のキーを `"~/Dev/private/hermes-agent"` にする。
  - `config/.local/libexec/hermes`: exec 先を `$HOME/Dev/private/hermes-agent/.hermes/bin/hermes` にする。
  - `scripts/hermes-install.py`: `target` を新パスにし、Implementation Decisions のとおり stage 構成・完了判定・管理パスを現行 installer に合わせる。
  - `scripts/tests/test_hermes_install.py`: fixture installer を現行の stage（`products` が `.hermes/bin/hermes` を作る）に合わせ、期待する stage 列・パスを更新する。旧 `node-deps` 固有のケース（`FIXTURE_DIRTY_NODE` など）は、対応する現行 stage の失敗・再開ケースに置き換える。`--skip-*` をどの stage にも渡さないこと、`products` が `SHELL=/opt/homebrew/bin/fish` で実行されることを確認するケースを入れる。`test_real_default_repos_update_does_not_advance_hermes_checkout` の `assertNotIn('~/.hermes/hermes-agent', ...)` は、新パスに対する assertion に置き換える（削除しない）。
  - `scripts/tests/test_agent_runtime.py`: `hermes_launcher` の install ルートを新パスにする。旧パスの legacy launcher が選ばれないことの確認は、新旧の配置で意味が通る形に保つ。
  - 注意: `config/.pi/agent/settings.json` は stage しない。`config/.local/libexec/hermes` だけは、移行手順の手順4で編集する。
- [x] **dotfiles 文書**: `docs/apps.md`（配置先、`venv/bin/hermes` の記述、「ブラウザ本体・cua-driver は追加導入しない」の記述）、`docs/troubleshooting.md`（Hermes 復旧手順を新パスと現行 stage `python-deps → products → complete` に更新し、`node-deps` の手順は削除）、`.agents/skills/dotfiles-setup/references/setup.md`（配置先、launcher の参照先、installer の stage の記述、「browser/cua-driver の追加導入を省き」の記述）を、現行の配置と stage、および agent-browser・cua-driver の固定版を PM に管理させる方針に合わせる。
- [x] **稼働環境の移行**: Safehouse 外で、`$SHELL` が fish の端末から実行する（herdr のペインは条件を満たす）。dotfiles の作業ツリーはシンボリックリンク経由で即座に稼働環境へ効くので、手順は次の順序を守る。
  1. 事前確認: `git -C ~/.hermes/hermes-agent status --short` が空であること。HEAD が `origin/ryonakae` に push 済みであること。上記2タスク（`config/.local/libexec/hermes` を除く）の編集と、その検証が済んでいること。
  2. `hermes-gateway stop`、`hermes-dashboard stop`。
  3. `mv ~/.hermes/hermes-agent ~/Dev/private/hermes-agent`。旧パスを cwd にしているシェルやセッションは、以後すべて絶対パスで操作する。
  4. `config/.local/libexec/hermes` を新パスに編集する。
  5. 新パスで installer の stage を順に実行する。
     - `bash ~/Dev/private/hermes-agent/scripts/install.sh --stage python-deps --dir ~/Dev/private/hermes-agent --hermes-home ~/.hermes --branch ryonakae`
     - 続けて同じ引数で `--stage products`、`--stage complete` を実行する。
     - `products` 後も `~/.local/bin/hermes`・`hermes-acp`・`hermes-agent` が旧パスを指している場合は、この3ファイルを削除して `products` を再実行する。`expose_cli` は別の root を指す既存の wrapper を上書きしない（`hermes_cli/_launchers.py` の `_owns_launcher`）。（実施時に判明し、ユーザーの承認を得て追加）
  6. `hermes-gateway start`、`hermes-dashboard start`。
- [x] **ローカルスクリプトの固定パス**: `~/.hermes/scripts/tests/test_restart_gateway_from_slash.py:18` の `HERMES_SOURCE` を新パスにする（git 管理外のファイル）。

## 切り戻し

移行手順 5 または 6 で失敗し、その場で直せない場合:

1. `hermes-gateway stop`、`hermes-dashboard stop`
2. dotfiles の今回の変更を元に戻す（未コミットなら該当ファイルを、コミット済みなら `git revert` で）。`libexec/hermes` は `.hermes/bin/hermes` 方式のまま旧パスを指す状態に戻す。
3. `mv ~/Dev/private/hermes-agent ~/.hermes/hermes-agent`
4. 新パスを指す `~/.local/bin/hermes`・`hermes-acp`・`hermes-agent` を削除し、旧パスで `python-deps` → `products` stage を実行して、install state と `.hermes/bin/hermes`、`~/.local/bin/hermes*` を旧パスに戻す。旧 install state が pruner に消されていなければ、`python-deps` は既存の環境を検証するだけで終わる。
5. `hermes-gateway start`、`hermes-dashboard start`

## Final Validation

- [x] **dotfiles の installer と launcher の契約**: `cd ~/dotfiles; uv run --no-project python scripts/tests/test_hermes_install.py` と `uv run --no-project python scripts/tests/test_agent_runtime.py` → それぞれ全件成功。統合テストの skip は成功扱いにしない。
- [x] **dotfiles の構文と文書**: `sh -n config/.local/libexec/hermes`、`mise.hermes.toml` の TOML 構文確認、`git diff --check` → エラーなし。文書中の掲載コマンドが、現行の `install.sh --manifest` の stage 名と一致すること。
- [x] **旧パス参照の残り**: `rg -n '\.hermes/hermes-agent|node-deps|venv/bin/hermes' ~/dotfiles --glob '!docs/plans/**' --glob '!docs/dig/**'` → ヒットは `scripts/tests/test_agent_runtime.py` の意図的な legacy fixture（旧 `venv/bin/hermes` が選ばれないことの確認用）だけ。
- [x] **稼働の確認**: `hermes-gateway status` が稼働中であること。`head -3 ~/.local/bin/hermes` と `~/Dev/private/hermes-agent/.hermes/bin/hermes` が新パスを指すこと。Slack からメッセージを送ると応答があり、`~/.hermes/logs/gateway.error.log` に新しい `Transcript read failed` が出ないこと。
- [x] **テストガードの解消**（今回の目的）: 新パスで `scripts/run_tests.sh tests/hermes_state tests/agent/test_compression_rotation_state.py tests/agent/test_compression_refusal_restores_transcript.py tests/agent/test_salvage_grown_transcript.py tests/agent/test_transcript_decoration_idempotence.py` を herdr ペインなど Safehouse 外で実行する → `TEST BUG: file I/O against the REAL hermes home: /Users/ryo.nakae/.hermes/manifest.json` が0件。
  - 移設前の同じ範囲の基準値: 1054 passed / 698 failed、ガードによる失敗 720件（2026-10-18、`8631ce1889`）。
  - 新しい install key で初めて実行するときは、test-environment が作り直されるので時間がかかる。
  - これ以外の失敗が残る場合は一覧にして、ユーザーに報告する。
  - 結果（`8631ce1889`、新パス）: 1752 passed / 65 failed。`manifest.json` のガードは0件。65件はすべて移設前から失敗していたテストで（新しい失敗はない）、state.db の holder 判定・修復・保守系に集中している。残る136件のガード表示（多くはログ行の重複）は `~/.hermes/logs/gateway.log` で、稼働中のゲートウェイが開いているファイルを holder 判定（`hermes_state_holders.py:558`）が走査したもの。checkout の位置とは関係しない。

## Gate Summary

- レビュー対象: `d6b286a`、`bc03f7c`、`cd84551`（base `adb75dd`）。read-only の独立レビューを3回行い、`blocking/high` はいずれもなし。
- `decision required` 2件はユーザーが決定（`products` の副作用の明示、fish の PATH 行を前提条件にする）。`bc03f7c` で実装し、scoped re-review で解消を確認した。
- 移行中に判明した、旧パスを指す `~/.local/bin/hermes*` の扱いは、ユーザーの承認を得て手順に追加・実施した。
- 未修正で残した medium/low: 失敗時に表示する復旧コマンドに `SHELL` の固定がない。update の経路で `--skip-*` を渡さないことのテストがない。禁止 stage の一覧に、現行にない `'path'` が残っている。`config.fish` が UTF-8 以外のときは案内文ではなくデコードエラーが表示される。手動の復旧手順には fish の前提条件の判定がない。計画の決定文（PM の既定ツールの導入、tui/web のビルド）が、docs と告知の記載より広い。
- 未解決の blocker はなし。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
