# Brewfile・mise 中心の dotfiles への移行 Implementation Plan

## Requirements

合意の正本は [dig log](../dig/2026-10-14-nix-to-mise.md)。Nix の機能を独自基盤で再実装せず、Brewfile・mise・薄いセットアップ入口に置き換える。この Mac の実機切替と Nix 撤去までを対象とする。別 Mac の実機操作は含めない。

- `default private` のように適用構成をすべて明示する。共通分を自動追加しない。`private` 単独も許容する。
- アプリは構成別 Brewfile を標準 `brew bundle` で導入・更新する。`--no-upgrade` や自動 cleanup は使わない。削除は宣言から外したうえで対象を指定して行う。
- sudo は最初の昇格時に認証し、必要な実行中だけ標準キャッシュを維持する。パスワード保存、sudoers 変更、全体の root 実行はしない。Apple Account・ベンダー認証・TCC の確認は別で、入力1回を保証しない。
- mise は最新版へ更新可能。共通 Node/Python/Ruby/Bun は現在の指定版を維持し、更新は別操作。既存 AWS CLI の管理方式・指定版も移行を理由に変えない。プロジェクト側の mise 設定は変更しない。
- Hermes は mise で `ryonakae/hermes-agent` の `ryonakae` ブランチから導入する。通常 setup は未導入時のみ、本体更新は別の明示操作。追加依存の一致・全機能の動作確認は移行のゲートにしない。Nix 固有の voice 除外を機械的に移植しない。
- Hermes の wrapper・gateway/dashboard・GUI domain 操作補助から Nix 参照を外す。Safehouse の保護、fork 標準の起動・停止、cwd・環境注入・終了コードの契約を維持する。通常 setup にサービスの自動停止・再開・状態保存を追加しない。
- 外部スキルは取得元ブランチを追跡し、setup 時の更新を許容する。必要なスキルだけ明示配置し、新規スキルを自動追加しない。自作は既存の glob・Git 追跡ファイルの直接リンクを継続する。共通／Claude 専用の優先と Antigravity CLI の共通参照を維持する。
- fish の bobthefish/fzf、Yazi の git/smart-enter/full-border は setup 時の最新版への更新を許容する。
- macOS 設定は現行値を再現し、mise 非対応部分だけ標準 CLI の小さなスクリプトで補完する。
- setup の独自入口は全体実行だけ。部分操作・明示更新は Homebrew/mise 等の標準コマンドを文書化する。
- 秘密・認証・DB・memory・session・可変 hooks/cron/plugins・管理外ファイルを保持する。変更対象外の設定・アプリを整理しない。未知の実体を force で置換しない。

計画承認は実装開始の承認とし、実機適用、サービス操作、権限変更、削除は実行直前にも対象を示して確認する。Safehouse 制限を回避せず、実機操作は通常端末で実施する。

## Implementation Decisions

### 1. 構成選択と標準入口

既存 `scripts/dotfiles.sh` → CLT `/usr/bin/python3` → `scripts/dotfiles.py` の起動経路を再利用する。公開入口は `bash scripts/dotfiles.sh setup default private` の形とし、Nix 用 build/switch/update の恒久互換層は残さない。初回に fish・mise・Homebrew を要求しない現在の zsh/CLT 前提は維持する。

- 新規 `brew/Brewfile.default`・`Brewfile.private`・`Brewfile.work` へ現行 Nix の tap/formula/cask/MAS 宣言を移す。work はアプリ追加がなければ空の追加構成でよい。Nix のためだけの nixd は残さず、必要な Bash/fish/mise/usage は Homebrew へ移す。
- 構成引数は実行前に全件検証し、未知名・重複・未指定はエラー。ユーザー指定順に適用し、各構成は追加分だけを持つ。Brewfile の独自パーサーや結合ファイル生成は作らない。
- mise の `-E` は通常の `mise.toml` も必ず読む。共通の適用リソースは `mise.default.toml`、private/work の差分は各 `mise.<name>.toml` に置き、ルート `mise.toml` は選択に依存しない設定だけにする。`private` 単独で default のリンク・runtime・OS設定を適用しないことをテストする。
- 標準の環境選択に指定構成を渡す。継承された `MISE_ENV` や別 cwd によって追加構成が紛れ込まないよう、操作対象 checkout・構成を明示する。別プロジェクトの設定を読んで実行しない。
- 共通 runtime のグローバル設定は現行 `config/.config/mise/config.base.toml` を維持する。setup の対象と独立して普段の shell から使う。private 単独実行時にグローバル tools を暗黙に導入する包括的 bootstrap は使わない。

### 2. 全体 setup の順序と失敗境界

独自の依存解決・状態台帳・並列ジョブ管理は追加しない。既存の対象ユーザー／HOME・Safehouse・root 拒否と対話確認を、Nix 非依存の必要な範囲で維持する。

1. 引数、CLT、対象 checkout・ユーザー、適用範囲を確認する。既存の Nix 管理 Homebrew を検出した場合は通常 setup で強制置換せず、一度きりの移行手順へ案内する。
2. 新規 Mac だけ、承認下で Homebrew 公式 installer を使う。mise 等の setup に必須の基盤は選択プロファイルとは別の導入前提とし、不足時だけ導入する。private 単独指定を default アプリ一式の導入に読み替えない。
3. 選択した Brewfile を順に実行し、アプリを導入・更新する。setup 基盤の mise が更新された場合は後続で新しい `/opt/homebrew/bin/mise` を使う。
4. 対象の mise 設定だけを信頼する確認を行い、選択された repos を取得・更新する。外部 source が存在してから dotfiles の dry-run を行う。初回 clone 前の full bootstrap dry-run 成功を必須にしない。
5. 時間制限付きの配置 dry-run と衝突確認後、mise でリンクを配置する。通常設定・自作スキルの既存挙動を保ち、HOME 一括走査に戻さない。
6. default を選択した場合、HOME を基準に指定版 runtime と必要な plugin を導入する。Hermes は対象 tool のインストール状況を mise の機械可読出力で判定し、未導入時だけ入れる。Nix 版の `command -v hermes` を判定に使わない。包括的な `mise upgrade` は呼ばない。
7. Hermes 起動定義は必要な場合だけ安全に配置し、選択した macOS 設定・電源設定を適用する。サービス起動や Dock/端末の自動再起動は行わず、必要な後続操作を表示する。
8. 終了状態と変更済み段階を報告する。途中失敗では後続へ進まず、自動再試行・rollback をしない。再開は成功済み全体を無条件に繰り返さず、標準の個別コマンドを案内する。

sudo キャッシュ維持は既存の最小処理を再利用し、終了・エラー・割込みで維持処理を終了する。更新失敗時は進行中の操作結果を回収して後続を止める。既存の同時 setup を行わない運用を維持する。アプリ更新を伴う全体再実行を冪等な無変更操作とは説明しない。

### 3. スキル・plugin と shell

- `nix/skill-sources/*.nix` の取得元・ブランチを `bootstrap.repos` へ移す。同じ repository は一つの checkout を共有し、`~/.local/share/agent-skill-sources/` 配下で管理する。現行は原則 main、find-docs の context7 と herdr は master。実際の選択パスは `nix/home/skills.nix` と取得元から照合する。
- `~/.agents/skills/` と `~/.claude/skills/` に選択した外部スキルだけ symlink する。既存の自作スキルが所有する宛先は外部宣言から外し、Claude 専用同名版がある場合は共通側だけに外部版を配置する。現在の共通指示 symlink と配布先を増やさない方針を維持する。
- repos の更新は dirty checkout・origin 不一致で停止する標準挙動を使う。宣言削除による checkout の自動削除はしない。リンクの削除・改名は先に標準 unapply。
- fish/Yazi plugin は現行 plugin を保持する。標準の plugin manager または repos+リンクで対応できる最小方式を実装時に選び、二重所有させない。fish のロード規約と Yazi の `main.lua` 等を確認し、単なる checkout 完了を導入成功としない。独自 updater は作らない。
- `config.fish` から HM の `nix-init.fish` 読込みを除去し、Homebrew fish と plugin の初期化へ置換する。mise/zoxide の二重 activation を避け、対話・非対話 PATH とプロジェクト版選択を維持する。
- `/etc/shells` とログインシェルは通常設定配置から分離する。新規 Mac は現在と同じ手動切替、実機移行時は別承認で Homebrew fish へ切り替える。

### 4. Hermes の導入と起動経路

mise の Git Python backend で `pypi:git+https://github.com/ryonakae/hermes-agent.git@ryonakae` を利用する。最新 mise の実際の tool ID・インストール状況出力を確認し、成功した導入を日常 setup が再インストール・更新しないようにする。branch の更新操作は標準 mise コマンドで文書化し、独自 updater を追加しない。

- `.local/libexec/hermes` という既存の安定入口を維持し、Nix へのリンクを mise 管理実体へ接続する小さな launcher に置換する。`mise where` はインストール先照会用の標準 read-only 操作で、未導入なら失敗する。対象 tool を明示して解決し、単なる cwd の `hermes` や PATH の別ソフトを選ばない。具体的な branch 解決と `bin/hermes` は実導入時に確認する。
- 起動時の自動インストール／更新は追加せず、未導入・解決失敗なら非0で止める。launcher の解決用 subprocess の cwd と Hermes 自体の cwd を混同しない。更新後も launcher を手動で毎回書き換える方式にしない。
- `safe-hermes-gateway.sh` / `safe-hermes-dashboard.sh` は Git 正本を直接配布し、Nix shebang/実体置換を廃止する。Homebrew Bash が必要な箇所だけ絶対パスを使い、OS 標準 Bash で足りる箇所は既存 shebang を維持する。
- `hermes-gui-launchctl` は現行の GUI domain 固定・失敗時停止の処理を Git 管理スクリプトとして保持する。管理関数、環境注入、Safehouse profile/feature の差分を変えない。
- plist は `ai.hermes.gateway` / `ai.hermes.dashboard` のラベル、cwd、Disabled/RunAtLoad/KeepAlive、ログ、dashboard の host/port を維持し、PATH から Nix を外す。mise の LaunchAgent 管理は自動ロードを伴うため使わない。
- plist はユーザー所有の通常ファイルとして配置する。symlink・未知の実体・手動変更を保護し、同一なら書込みを省く。現行 HM 世代に依存する比較は移行後も使える最小方式へ置換する。別途認可した初回引渡し後は、配置先と現在の生成結果を比較し、未知の差分は自動上書きせず確認する。必要以上の履歴台帳は作らない。
- Hermes の認証・DB・memory・session・cron/hooks や fork 自身の内容には触れない。追加依存や GUI 機能の検証を受入条件に追加しない。

### 5. macOS 設定

`nix/darwin/preferences.nix` と `nix/hosts/{default,private,work}.nix` の値を移す。型・domain・キーを確認し、mise の named keys で意味が変わるものは raw defaults を使う。

- default: 共通 preferences、スクリーンセーバー600秒、即時パスワード要求を含む。
- private: 現行の電源復旧・sleep 設定と追加アプリ。
- work: 現行の電源別 pmset 設定。ハードウェア非対応や失敗を成功扱いしない。
- Dock には CleanArchiver と Chrome Apps 等の手動導入対象が含まれる。mise の named `dock.apps` は全アプリの存在を要求するため、raw defaults 等で現在の宣言の意味を維持し、勝手にアプリ追加・項目削除をしない。persistent-others のフォルダ表示形式も維持する。
- 補完は `scripts/` の小さなスクリプトに限定し、選択構成にない電源設定を適用しない。defaults を root の preferences へ書かない。旧値・型・未設定状態は変更対象だけ記録し、TCC は手動許可のままにする。

### 6. 実機引渡しと撤去の順序

調査で、`/opt/homebrew/bin/brew` と `Library/Homebrew` が Nix store を参照していることを確認した。nix-homebrew は marker と fake repository も作る。Cellar/Caskroom/Taps・アプリ本体・データを保持し、Homebrew 全体の uninstall は行わない。

現行の `darwin-uninstaller` は空構成 activation を呼ぶが、HM の所有リンクや Hermes の `~/Library/LaunchAgents` は解除しない。一方、system サービス・`/etc/static`・shell に作用し、`/etc/**/*.before-nix-darwin` を元の名前へ戻す。Nix daemon が installer 版へ復帰する場合もあり、nix-darwin 撤去と Nix 本体撤去は別工程である。

1. **実行前調査・保全**: 対象 Mac の現行 system/HM 世代、公開された管理リンク・plist・Homebrew 本体リンク・marker・shell 登録・Nix 関連 daemon/APFS を対象限定で記録する。既存バックアップの復元先衝突も確認する。秘密を収集しない。関係のないアプリの全件棚卸しはしない。
2. **Nix が動く間に所有解除を準備**: 現行 lock を使った一時移行構成で HM 所有リンクを標準解除する。不要な通常設定・plugin/skills の旧所有と Hermes 生成リンクを対象にし、ユーザーデータは残す。HM の無効化だけでリンクが消えると仮定しない。旧構成・解除前世代は撤去前まで参照可能に保つ。
3. **代替準備と配置事前確認**: Nix を残したまま必要な取得・導入を進め、HM 所有解除前に実 HOME の配置 dry-run を時間制限付きで完了させる。既知の旧 HM 衝突以外、未知の実体、timeout では所有解除を開始しない。
4. **所有権を引き渡す**: 必要なサービス操作は現在の管理関数で別承認のもとに実行する。停止中だったサービスを起動しない。HM 標準解除後、新しい配置を適用する。Hermes の通常 plist は旧管理結果との一致を確認して別に引き渡す。引渡し失敗時に旧構成を無条件再適用しない。
5. **Homebrew 本体を標準構成へ戻す**: 公式 installer の対象 revision/処理を確認し、既知の Nix 管理本体リンク・marker/fake repo だけを対象限定で保全・解除して、既存 prefix に標準本体を導入する。未知の通常ファイルは上書きしない。Cellar/Caskroom/Taps は保持する。作業順を HM 移行 activation と調整し、この後旧 homebrew-enabled activation を実行しない。公式手順で保全した移行が成立しない場合は実操作前に相談する。
6. **非 Nix 経路の受入**: 新しい fish を登録・選択し、新規端末で起動を確認する。稼働サービスがある場合は承認下で明示的に切り替え、登録済み Program/PATH と実プロセスが旧 store を使っていないことを確認する。CLI の PATH だけで完了扱いしない。
7. **nix-darwin 撤去**: 最後に使用する uninstaller/空構成 activation の内容と復元候補を再確認する。標準処理の `/etc` 復元が新設定を上書きする場合は事前に解決し、黙って実行しない。別承認後に実行し、終了コードだけでなく shell・サービス・Homebrew・設定が保持されていることを確認する。
8. **Nix 本体撤去**: installer 種別と実機の volume/daemon/build users/profile を照合し、上流 macOS 手順で対象を示して別承認を得る。APFS volume は実際の識別子を確認して削除する。既存 shell 設定を古いバックアップで一括上書きしない。旧 Nix を使うプロセスが残る場合は削除を止める。空の `/nix` mountpoint が再起動まで残ること自体は失敗ではない。

この一度きりの移行・撤去を日常 setup に組み込まない。移行中だけ必要な Nix 宣言・コードは最後に撤去し、恒久的な dual mode は残さない。

## Tasks

実装開始時の review base は `d89bcdc2ee1582128d851223fec7722c45f1ca1e`。`master` と `origin/master` は一致し、既存 staged 変更はない。既存 unstaged 変更の扱いはユーザー承認済み: `config/.config/fish/config.fish` の cua installer による `.local/bin` PATH 追加は保持して周囲を移行し、`flake.lock` の Hermes fork revision 更新（`fc0ce243cf515f7e65513eb068c44c33c7d41980`）は移行中に利用して Nix 撤去時にファイルごと削除する。Claude/Ghostty 設定と `.DS_Store` は対象外として保持する。実装・隔離テストは下記まで進行。実機適用と push は未実施。Tasks 1–5 の候補は local commit と独立レビューを実施済み。

### 実装・検証の進捗

- Tasks 1–5 の候補を `8200bf604ff9de7a5923002aa901c84b4b8256ce` に local commit。構成宣言・setup・起動経路・文書が同じ新契約に依存するため、一つの成果物にまとめた。
- 構成: `brew/Brewfile.{default,private,work}` と `mise.{default,private,work}.toml` を作成。外部14 checkout・16選択スキル、fish/Yazi plugin を repos とリンクへ移管。ルートは適用リソースなし。配置11件、repos/plugin 4件のテスト成功。親の検査で不存在 launcher 宣言を発見し、実在する2ファイルの配置へ修正済み。
- setup: `scripts/dotfiles.py` を新契約へ変更。構成選択・環境隔離・確認後変更・sudo lifecycle・失敗時停止・Hermes 初回導入を含む23件成功。実 Git backend の導入後 `ls` 出力は未確認。
- shell/Hermes: Nix 初期化を外し、Homebrew vendor snippet との二重 activation を防止。launcher・GUI adapter・確認付き通常 plist 配置を追加。起動契約25件、plist10件、TMPDIR 1件成功。実サービスは操作していない。
- macOS: `scripts/macos-settings.sh` と型・Dock・current-host を含む10件成功。51項目を現行 Nix 生成値と照合。mise 2026.9.18 の defaults dry-run は終了0、49項目が現在値と一致し Dock 2項目のみ再適用予定。実設定は変更していない。
- 文書: README、setup/usage/migration/troubleshooting/apps、AGENTS、dotfiles-setup を更新。ローカル参照118件・アンカー63件に欠落なし。shell/fish/TOML/Brewfile の構文・標準解釈と `git diff --check` が成功。
- 一時 HM 引渡し: `nix/release-home-manager.nix` と flake package を追加。build と `nix flake check --no-update-lock-file` が成功。成果物 `/nix/store/9pj2p7ib2gzk94rihyxw9y5241bldmcd-home-manager-generation` の home-files は空、activation に launchctl・copyApps はない。適用はしていない。移行中の旧構成評価のため `nix/home/skills.nix` は新しい default 宣言を読む。
- mise 提供版: Safehouse 内の検証用 `brew fetch` は Homebrew lock への書込み拒否で停止。その後、ユーザー承認下の通常端末で Homebrew 提供最新2026.10.8の取得に成功。一時領域のバイナリで配置11件・repos/plugin 4件と default,private / private / work の defaults dry-run が成功。ホストへの install/link、実 HOME apply、OS設定変更はしていない。上流2026.10.9の通知があり、提供版とは区別する（上流版自体は未検証）。ログは `/tmp/dotfiles-latest-mise-verification.log`。
- 統合テスト: Safehouse 内では96件中94件成功、skip 0、失敗2。未変更の `test_bootstrap_nix.py` の download-failure と daemon-mode が失敗し、後者は `/bin/rm: Operation not permitted`。ユーザー承認下で同じコマンド `uv run --no-project python -m unittest discover -s scripts/tests -p 'test_*.py'` を通常端末で再実行し、96件すべて成功（終了0、skipなし）。ログは `/tmp/dotfiles-migration-tests-outside.log`。テストや受入条件の緩和はしていない。
- commit 対象: fish の既存 Cua PATH 追加を未コミットのまま保持し、今回の移行差分だけを分離して stage する扱いをユーザー承認済み。他者の Claude/Ghostty/flake.lock 差分と `.DS_Store` は引き続き対象外。実機引渡し・撤去と最終ゲートは未完了。
- 独立レビュー: base `d89bcdc2ee1582128d851223fec7722c45f1ca1e` → head `8200bf604ff9de7a5923002aa901c84b4b8256ce` の36ファイルを read-only の別コンテキストで確認。blocking/high と decision required はなし。以下の medium 2件は親でも確認し、ユーザー承認後に修正した。修正差分の再レビューは下記の進捗に記録する。
  1. `scripts/dotfiles.py:147` が `MISE_DATA_DIR` も除去するため、カスタムデータディレクトリ使用時、setup と普段の shell/Hermes の導入・参照先が分離する。構成選択の隔離とデータディレクトリの継承を分ける修正が推奨される。
  2. `docs/troubleshooting.md:77` は runtime 復旧後に fish 切替・版確認だけを案内しており、その後に残る Hermes 導入・plist・選択 macOS 設定への復旧導線が不足する。全体 setup の再実行ではなく、未実施段階の個別操作へ接続する修正が推奨される。
- 修正 cycle 1: `MISE_DATA_DIR` を継承しつつ構成選択変数の隔離を維持。カスタムデータディレクトリで Hermes 未導入／導入済みの両方を対象に Red → Green を確認し、setup テスト24件が成功。runtime 復旧後の Hermes 照会・初回限定 install・plist・選択 macOS 設定への導線を追加。Python 構文・参照先・`git diff --check` は成功。変更が及ばない統合テスト・mise・Nix の既存成功結果は再利用し、修正差分の独立再レビュー待ち。
- コミット済み fish の構文を再確認し、既存 Cua PATH 追加だけが unstaged に残ることを確認。Claude/Ghostty/flake.lock と `.DS_Store` はコミットに含めていない。

- [ ] **1. 構成宣言と標準ツールへの移管**: `brew/`、ルート `mise*.toml`、必要な `config/` を整備する。現行アプリ一覧・ホスト差分・取得元・選択スキルを移し、default の明示選択と自作優先を保つ。plugin の標準導入方式を決め、Nix 所有との初回引渡し対象を列挙する。
- [ ] **2. セットアップ入口**: `scripts/dotfiles.sh` / `scripts/dotfiles.py` を新契約へ置換する。既存テストの境界で TDD を行い、構成選択・実行順・sudo lifecycle・失敗時中止・Hermes の初回限定導入を保証する。runtime の版指定は維持する。
- [ ] **3. shell と Hermes の起動・配置**: fish 初期化、管理関数、`.local/libexec` の launcher、Safehouse wrapper、plist 配置を非 Nix 経路へ変更する。`scripts/tests/test_agent_runtime.py` 等の既存境界を更新し、サービスを動かさず契約を検証する。
- [ ] **4. macOS 設定**: mise の宣言と必要最小限の補完処理へ現行値を移す。型、Dock、スクリーンロック、電源別設定を保持し、選択した構成だけ適用することを検証する。
- [ ] **5. 文書・指示と実機移行準備**: `README.md`、`docs/setup.md` / `usage.md` / `migration.md` / `troubleshooting.md` / `apps.md`、`AGENTS.md`、dotfiles-setup スキルを新運用に合わせる。標準コマンドによる個別操作、Hermes の明示更新、新規 Mac の導入前提を記す。一時移行構成と対象限定の引渡し・復旧手順を準備する。
- [ ] **6. 承認下でこの Mac を切り替える**: 上記の実機引渡し順序に従って Homebrew/HM/shell/Hermes を移管し、Nix 非依存を確認する。各段階の適用結果と未完了範囲をこの計画へ記録する。
- [ ] **7. 撤去と最終整理**: 別承認で nix-darwin・Nix 本体を撤去する。`flake.nix` / `flake.lock` / `nix/`、`scripts/bootstrap-nix.sh`、廃止契約専用のテスト・現行文書を整理する。過去の dig/archived plan は履歴として保持し、現行手順として参照しない。
  - `flake.lock` には開始前から他者の変更がある。削除前にその差分の保全・扱いをユーザーへ確認する。fish/config や Claude/settings の既存変更も上書き・混入させない。`.DS_Store` は作業範囲外。

## Final Validation

計画作成中はテスト・インストール・実機適用を実行しない。実装では既存の TDD スキルと検証規約に従う。以下は実装後の確認項目で、通過済み結果は後続変更が無効化しない限り再利用する。

- [ ] **入口・失敗経路**: `uv run --no-project python scripts/tests/test_dotfiles_cli.py` → 明示構成順、private 単独で default 非適用、未知/重複/未指定の事前拒否、root/Safehouse 拒否、sudo refresh の終了・失敗、後続中止、Hermes 導入済みで更新しない、指定版 runtime 維持。コマンド境界を stub 化し、実 sudo・brew・サービス操作をしない。
- [ ] **配置**: `uv run --no-project python scripts/tests/test_dotfiles_links.py` → 実 mise と隔離 HOME/Git fixture で直接リンク、追跡ファイル増減、衝突保持、unapply、共通/Claude 優先、外部の選択配置、管理外データ保持を確認。fixture repos で remote branch 更新と dirty 保護も必要な境界に追加する。HOME 一括走査への回帰を防ぐ。
- [ ] **起動契約**: `uv run --no-project python scripts/tests/test_agent_runtime.py` と `uv run --no-project python scripts/tests/test_hermes_tmpdir.py` → 非対話 PATH/cwd、環境注入と失敗時停止、TMPDIR、指定 Hermes の解決、引数・終了コードが維持される。`test_hermes_activation.py` は恒久的に必要な plist 所有・同一時無変更・手動変更保護・サービス非操作のテストへ置換し、同じコマンドで実行する。
- [ ] **macOS 宣言と補完**: TOML 解析と fake defaults/pmset 等の境界で型・構成別適用・エラー中止を確認する。構成別の設定移管漏れは旧宣言との一度きりの照合で確認し、旧 Nix 宣言を恒久 fixture として残さない。
- [ ] **構文・標準解釈**: 変更した fish は `fish --no-execute`、shell は shebang の shell の `-n`。Brewfile は標準 `brew bundle list --file=...` で解釈できること、TOML は最新 mise の標準表示・dry-run で構成選択が正しいことを確認する。実 HOME の適用やサービス再起動を構文検査の代わりにしない。
- [ ] **一時 Nix 移行構成**: 使用する場合は dotfiles-setup の build 手順で実 flake check/build を行う。秘密や Git 外の設定を store に取り込まない。必要な新規 Nix ファイルだけ明示的に追跡対象とする。失敗・skip を移行準備成功としない。
- [ ] **実機適用前後**: 承認下で実 HOME dry-run、新配置、Homebrew 本体の非 store 化、標準 brew 動作、fish 新規 login、指定 runtime、選択 plugin/スキルの読み込みを確認する。Hermes は launcher/CLI とサービスの実行経路だけを受入対象とし、追加依存・全機能をゲートにしない。サービスを起動していない Mac では勝手に起動せず、plist と実行先確認の範囲を明記する。
- [ ] **撤去後**: Nix daemon・build users・profile・実 volume の撤去結果と、必要な shell登録・Homebrew・mise・Hermes 起動経路の存続を確認する。対象の有効設定・管理リンク・プロセスに Nix 依存が残らないことを確認する。無関係な HOME 全量や秘密を走査しない。
- [ ] **文書・範囲**: 掲載コマンド、リンク・参照パス、現行の Nix 参照と廃止入口を対象限定で確認する。`git diff --check`、差分レビュー、既存変更の保持を確認する。削除済みコードの不在だけを証明する恒久テストは追加しない。

## 参照資料と調査限界

- [mise environments](https://mise.jdx.dev/configuration/environments.html): base config の自動読込みと複数環境の優先順。
- [mise repos](https://mise.jdx.dev/bootstrap/repos.html): ref、更新、dirty 保護、削除の挙動。
- [mise Python backend](https://mise.jdx.dev/dev-tools/backends/pypi.html) / [where](https://mise.jdx.dev/cli/where.html): Git branch の導入、Git ソースの lock 制限、インストール先の read-only 照会。
- [mise macOS defaults](https://mise.jdx.dev/bootstrap/macos-defaults.html) / [LaunchAgents](https://mise.jdx.dev/bootstrap/launchd.html): defaults と自動ロードの境界。
- [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile) / [Installation](https://docs.brew.sh/Installation): 標準導入・更新と既存 prefix の保持。
- [nix-homebrew](https://github.com/zhaofengli/nix-homebrew) / [module](https://github.com/zhaofengli/nix-homebrew/blob/main/modules/default.nix): store 本体、marker/fake repo と prefix の分離。
- [nix-darwin uninstall](https://github.com/nix-darwin/nix-darwin#uninstalling) / [Nix macOS uninstall](https://nix.dev/manual/nix/latest/installation/uninstall.html): 別工程の撤去。
- ローカルは mise 2026.9.18 と現行生成 uninstaller を読み取り確認。最新資料の全機能が同版で動くとは扱わない。最新 mise の実導入、Homebrew 逆移行、実 HOME の衝突、各種 installer の動作は未実施。実装時の具体化と承認付き実機工程で確認する。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
