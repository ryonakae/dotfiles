# setup の確認集約と初回後手順の自動化 Implementation Plan

決定の経緯: [dig log](../dig/2026-10-17-setup-fewer-prompts.md)

## Requirements

- setup の確認語は、最初の `setup` と dry-run 後の `apply` の2回だけにする。
  - 最初の確認で、対象ユーザー・checkout・構成に加えて次を表示し、まとめて承認を取る: Homebrew 未導入なら公式 installer の URL と prefix、trust する mise 宣言の全文、電源設定の補完、ログインシェルを `/opt/homebrew/bin/fish` に変える、Herdr プラグイン導入と `zerdr setup install`（`default` 選択時）、Hermes 宣言の全文と初回導入（`private` 選択時）。
  - 廃止する確認: Homebrew の `install`、mise の `trust`、Hermes の `trust`、`hermes-install.py` の確認語2回、電源設定の `apply`。
  - Homebrew 公式 installer は `NONINTERACTIVE=1` で実行する。
  - Hermes plist の `y` は、置換する差分が出た場合だけ残す（`hermes_plists.py` の現行動作のまま）。
  - 単独実行したときの `macos-settings.sh` と `hermes-install.py` の確認は残す。
- ログインシェル: `mise.default.toml` に `[bootstrap.user] login_shell = "/opt/homebrew/bin/fish"` を宣言し、`default` 選択時に setup の sudo 段階で `mise bootstrap user apply --yes` を実行する。
- Herdr: `default` 選択時、`ryonakae.agent-context` と `worktrunk` プラグインを未導入の場合だけ commit 固定で導入し、`zerdr setup install` を実行する。
- 完了時に「Dock の並びなどの macOS 設定は Mac の再起動後に反映される」と再起動を案内する。setup は Dock・Finder・SystemUIServer を再起動しない。
- docs/setup.md の手順 6（fish 切替）・7（runtime 版確認）・8（Herdr）を削除・整理する。Herdr 内での検証・反映・稼働確認は初回手順から外す。
- 対象外: Dock の自動再起動、サービスの停止・再開、runtime 版確認の追加、Herdr セッション内の設定検証、Hermes installer 本体の挙動変更。

## Implementation Decisions

- 確認の省略は、各スクリプトに `--yes` を追加して setup から渡す。単独実行時の既定は今のまま確認する。
  - `macos-settings.sh <name> [--yes]`。
  - `hermes-install.py install --yes`。setup からは `mise run hermes:install -- --yes` で渡す（`mise run TASK [ARGS]` の引数が raw 文字列 task の末尾に付くかは実装時に実 mise で確認し、付かなければ task 定義側で `{{arg}}` 等の標準手段を使う）。`--yes` でも非対話端末の拒否・managed path 検査・HEAD 変化の検知は維持する。
- Herdr は `mise.default.toml` に task `herdr:plugins` を置く。固定 commit はここが正本で、docs/apps.md はこの task へのリンクにする。
  - 未導入判定は `herdr plugin list --json` の plugin id（`ryonakae.agent-context` / `worktrunk`）で行う。Brewfile 導入済みの `jq` を使ってよい。
  - 実装前に、Herdr サーバー未起動時に `herdr plugin list --json` と `herdr plugin install` が動くかを確認する。動かない場合は止めてユーザーへ確認する（setup がサーバーを起動する変更は合意外）。
  - `zerdr setup install` は `$(brew --prefix ryonakae/tap/zerdr)/bin/zerdr` を使う。
  - setup では mise apply・link verification の後、runtime install の前後どちらかで実行する（Herdr 設定の配置後であること）。
- ログインシェル変更は macOS 設定と同じ sudo 段階で実行する。`chsh` が別途パスワードを求める場合がある旨を最初の確認と docs に書く。
- 宣言の全文表示は現在の `trust` 確認の表示を最初の確認へ移す。snapshot は確認前に取得済みで、確認後の変更検知は現行どおり。

## Tasks

- [x] 宣言の追加: `mise.default.toml` に `[bootstrap.user]` と task `herdr:plugins` を追加する。
- [x] スクリプトの `--yes`: `scripts/macos-settings.sh`、`scripts/hermes-install.py`（必要なら `mise.hermes.toml` の task 定義）に確認省略の引数を追加し、`scripts/tests/test_macos_settings.py`・`scripts/tests/test_hermes_install.py` に「`--yes` で確認なし・既定では確認あり」を追加する。
- [x] setup の再構成: `scripts/dotfiles.py` の確認を最初の `setup` と dry-run 後の `apply` に集約し、`NONINTERACTIVE=1`、`--yes` の受け渡し、`mise bootstrap user apply --yes`、`mise run herdr:plugins`、完了時の再起動案内を追加する。`scripts/tests/test_dotfiles_cli.py` の期待コマンド列・確認回数・表示内容を更新する。
  - 最初の確認を拒否したら、どのコマンドも実行しないこと（既存テストの境界）を維持する。
- [x] 文書とルール: `CLAUDE.md`（「setup に … chsh を追加しない」から chsh を外す）、`.agents/skills/dotfiles-setup/references/setup.md`（30・79 行目付近の chsh 分離、確認の扱い）、`docs/setup.md`（確認の表、手順 6〜8 の削除・統合、再起動の案内）、`docs/apps.md`（Herdr の導入手順を task へのリンクに、初回の稼働確認を外す）、`docs/troubleshooting.md`（chsh・Hermes 再開手順の記述）を更新する。

## Final Validation

- [x] setup・各スクリプトの確認と実行順: `uv run --no-project python scripts/tests/test_dotfiles_cli.py`、`scripts/tests/test_macos_settings.py`、`scripts/tests/test_hermes_install.py` → すべて成功、skip 0。
- [x] 構文: `bash -n scripts/macos-settings.sh scripts/dotfiles.sh`、`mise -C ~/dotfiles -E default tasks ls` で `herdr:plugins` が表示される、`mise -C ~/dotfiles -E default bootstrap user apply --dry-run` が fish 済みの環境で変更なしを示す。
- [ ] Herdr task の動作（未実行: 承認なし。検出部分のみ `herdr plugin list --json` で確認）: `zerdr setup install` が実 Herdr 登録と Zed tasks を書き換えるため、実行前にユーザーの承認を取る。承認後、導入済みのこの Mac で `mise -C ~/dotfiles -E default run herdr:plugins` を実行 → プラグインの再導入が起きず、`herdr plugin list` が変わらない。承認がなければ未実行として報告する。
- [x] 文書: リンク・参照パスと掲載コマンドが現行コードと一致、`git diff --check` が成功。
- [ ] 実機（実装後、ユーザーが新規 Mac で実施）: setup の確認語が2回だけ、ログインシェルが fish、Herdr プラグイン3件が有効、再起動後に Dock の並びが宣言どおり。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。

## Gate Summary

- base `2f02268`。commit: `b510fb4`（宣言）、`3e3946f`（`--yes`）、`b38b22d`（setup）、`8716c71`（文書）、test 修正（`af7608d` 由来の既存失敗、ユーザー承認済み）。
- 実装メモ: `mise run hermes:install --yes` で引数が task へ渡ることを確認。Herdr はサーバー未起動でも `plugin list --json` が動作（空なら `plugins: []`）。
- 検証: `scripts/tests/test_*.py` 全件成功・skip なし。`mise -E default tasks ls` に `herdr:plugins`、`bootstrap user apply --dry-run` は already set。リンク・アンカー確認と `git diff --check` 成功。
- 独立レビュー: blocking/high なし。decision required 2件（Hermes revision 未表示での installer 実行、Agent Context 常駐確認の削除）は dig Q3・Q6 の決定どおりとして不採用。medium/low（zerdr 再登録の冪等性、`brew --version` 確認の削除）は残す。
- 未実施: 新規 Mac での実機確認（確認2回・fish・Herdr 3件・再起動後の Dock）。
