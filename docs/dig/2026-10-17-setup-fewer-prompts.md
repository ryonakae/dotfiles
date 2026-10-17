# dig log: setup の確認削減と初回後手順の自動化

## 目的・前提・制約
- 別 Mac での初回 setup で、入力のために止まる回数が多すぎる。確認を減らしたい。
- docs/setup.md の 6（fish 切替）・7（runtime 版確認）・8（Herdr プラグイン導入）も setup で自動化したい。
- 現状の確認（default work）: `setup`、`install`（Homebrew 未導入時）、mise `trust`、リンク配置 `apply`、電源設定 `apply`、sudo パスワード。private 選択時は Hermes の `trust`・初回導入の確認語・plist の `y` が加わる。
- 既存の制約: CLAUDE.md に「setup に cleanup・サービス再起動・chsh を追加しない」とある。今回の chsh 自動化はこの規則の変更を伴う。
- 既存の判断（docs/dig/2026-10-12-human-first-setup.md）: chsh と runtime install は setup に含めない、とユーザーが手動手順を選んでいた。runtime install はその後 setup に追加済み。
- Herdr の設定反映・稼働確認（config check / reload-config / plugin list）は Herdr セッション内でしか行えない。
- Hermes installer 自身の確認は fork 側の処理で、dotfiles 側では変えない。
- Dock の並び（`persistent-apps` / `persistent-others`）と各種設定は `mise.default.toml` の `[bootstrap.macos.defaults."com.apple.dock"]` で宣言済みで、setup で書き込まれている。
- mise は Dock / Finder / SystemUIServer を再起動しない（公式 docs: macos-defaults の Restart affected apps）。Dock は起動時に設定を読むため、再起動しないと宣言が画面に出ず、稼働中の Dock が状態を書き戻すと宣言が上書きされうる。Nix 時代は activation で再起動されていた。
- mise には `[bootstrap.macos.dock] apps`（並びを path で宣言、既存 tile の metadata を維持、全 app の存在が前提）と、`[bootstrap.hooks] post-defaults` がある。
- mise の `[bootstrap.user] login_shell` が `/etc/shells` への追記（必要なら sudo）と `chsh` を行う。

## 決定事項
- 方針の検討は dig → plan の順で進める。
  - 出典: dig 開始前のユーザーの承認
- mise 宣言の trust は、最初の `setup` 確認で宣言全文と trust 対象を表示してまとめて承認する。別の `trust` 確認は廃止する。
  - 理由: 承認内容は同じで時点が前に移るだけ。snapshot で確認後の変更を検知するため安全性は変わらない。
  - 出典: Q1
- setup は Dock / Finder / SystemUIServer を再起動しない。完了時に「macOS 設定（Dock の並びなど）は Mac の再起動後に反映される」と再起動を案内する。
  - 理由: ユーザーの選択。作業中のアプリを setup が巻き込まない。
  - 出典: Q2
  - 確認事項: 実装後、新規 Mac で再起動後に Dock の並びが宣言どおりになるかを実機で確認する。
- 電源設定の `apply` は最初の `setup` 確認に含め、setup から呼ぶときは省く。`private` 選択時に限り、Hermes 宣言の trust と `hermes-install.py` の確認語も最初の確認に含めて省く。単独実行時の各スクリプトの確認は残す。
- Hermes plist の確認は、置換する差分が出た場合だけ残す（新規 Mac では出ない）。
  - 理由: 実行前に内容を表示できないものを承認なしで置換しない。
  - 出典: Q3
- ログインシェルは `mise.default.toml` の `[bootstrap.user] login_shell = "/opt/homebrew/bin/fish"` で宣言し、setup の sudo 段階で `mise bootstrap user apply --yes` を実行する。最初の確認に「ログインシェルを fish に変更する」と表示する。CLAUDE.md の「setup に chsh を追加しない」と docs の手動手順を更新する。
  - 理由: fish 本体・設定と同じ構成。`/etc/shells` の確認・追記と chsh を mise 標準機能に任せ、自前実装しない。
  - 出典: Q4
  - 注意: `chsh` は sudo の認証キャッシュと別に、パスワードを求める場合がある。
- docs/setup.md の手順 7（runtime 版確認）は削除し、setup にも版確認を追加しない。
  - 理由: setup の `mise install` 成功で指定版の導入は確定する。PATH の問題は fish 切替後の新規端末で分かる。
  - 出典: Q5
- `default` 選択時、Herdr の `agent-context` と `worktrunk` プラグインを未導入の場合だけ commit 固定で `herdr plugin install --ref ... --yes` し、`zerdr setup install` も実行する。最初の確認で対象を表示する。固定 commit は宣言側へ移し、docs/apps.md はリンクにする。
  - 理由: 新規 Mac で必要な操作が setup で完結する。未導入時だけなので既存 checkout を置換しない。zerdr setup install は Homebrew 版への再登録で冪等。
  - 出典: Q6
  - plan で実機確認: 未導入判定の手段（`herdr plugin list` / `plugins.json`）、Herdr サーバー未起動時に install が動くか。
- Homebrew 未導入時の公式 installer による導入（URL・prefix）は最初の確認に含め、`install` の確認は廃止する。
  - 出典: Q7
- 公式 installer は `NONINTERACTIVE=1` で実行し、installer 自身の Enter 確認を省く。sudo は直前の `sudo -v` で認証済み。
  - 出典: Q8
- setup の確認語は最初の `setup` と dry-run 後の `apply` の2回にする。dry-run 後の確認は既存ファイルとの衝突を見る唯一の機会なので残す。
  - 出典: Q1〜Q7 の集約
- 初回 setup の手順から Herdr 内での検証・反映・稼働確認を外す。docs/apps.md の設定変更時の確認手順は残す。
  - 理由: ユーザー判断で不要。
  - 出典: Q6 への補足

## 未決・保留
- plan での実機確認: Herdr の未導入判定の手段、Herdr サーバー未起動時の `herdr plugin install` の動作。
- 実装後の実機確認: 再起動後に Dock の並びが宣言どおりになるか。
