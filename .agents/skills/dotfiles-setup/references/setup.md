# セットアップと運用

新しい Apple Silicon Mac では、[初回セットアップ](#新しい-mac-のセットアップ)を上から順に進める。
エージェントは不要。標準の「ターミナル」アプリと zsh から始め、ツール・設定・ランタイムを導入してエージェントを起動できるところまでを扱う。

| 目的 | 読む場所 |
|---|---|
| 新しい Mac に導入する | [新しい Mac のセットアップ](#新しい-mac-のセットアップ) |
| 導入中に止まった | [初回導入で止まったとき](#初回導入で止まったとき) |
| 設定やツールを更新する | [日常の変更と更新](#日常の変更と更新) |
| 管理元や配置方法を確認する | [管理の分担と通常配置](#管理の分担と通常配置) |
| 既存の Home Manager 配置から移行する | [既存 Mac の切替](#既存-mac-の切替) |
| 適用の影響や復旧条件を確認する | [Nix の適用と復旧準備](#nix-の適用と復旧準備) |
| 任意の機能を設定する | [機能別リファレンス](#機能別リファレンス) |

## 新しい Mac のセットアップ

各手順は、直前の操作が成功してから次へ進む。一括で貼り付けて実行しない。
すでに Nix や dotfiles を導入している Mac では、bootstrap や退避を繰り返さず、未完了の工程から再開する。

### 1. App Store と Xcode を準備する

1. **App Store を開き、Apple Account にサインインする。** 購入や利用規約などの確認画面があれば済ませる。後のアプリ導入でも App Store を開いておく。
2. **App Store から Xcode をインストールする。** ダウンロード完了後に Xcode を起動し、ライセンスに同意して初期設定を終える。Xcode は dotfiles の導入一覧にもあるが、初回は switch より先に準備する。
3. 「ターミナル」を開いて、開発ツールが使えることを確認する。

```sh
xcode-select -p
xcrun --find clang
git --version
/usr/bin/python3 --version
```

ライセンス未同意のエラーが出たら、Xcode に戻って同意する。Command Line Tools が未導入と表示された場合は `xcode-select --install` で導入を終え、上の確認をやり直す。CLT の導入だけで Xcode のライセンス同意が済むわけではない。

アプリごとのパスワード入力を減らしたい場合は、システム設定の「Apple Account → メディアと購入」で要求頻度を確認する。「購入とアプリ内購入」を「15分後に要求」など、希望する設定へ変更する。無料ダウンロードの要求設定があれば別に確認する。選択肢や表示名は macOS・アカウント・Touch ID の設定によって異なる。認証を省く設定は任意で、dotfiles から自動変更しない。

**次へ進む条件:** Xcode の初期設定が終わり、上のコマンドがエラーなく応答する。

### 2. ターミナルの権限を準備する

システム設定の「プライバシーとセキュリティ → フルディスクアクセス」で、switch に使う「ターミナル」を許可する。その後、ターミナルを完全終了して開き直す。別の端末アプリを使う場合は、そのアプリの許可が必要。

この権限はアプリに保護されたデータへの広いアクセスを許す。今回の構成ではアクセシビリティ設定の書き込みに必要となり、未許可だと `Could not write domain com.apple.universalaccess` で止まることがある。`sudo` だけでは代わりにならない。

以後、手順6までは標準の zsh で実行する。Safehouse やエージェント内から実行しない。

### 3. dotfiles を取得して構成を選ぶ

```sh
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

すでに取得済みなら clone は不要。`cd ~/dotfiles` でその checkout を使う。

| Mac | 使う構成 |
|---|---|
| 家用 | `private` |
| 共通設定だけ | `default` |

以降の例は家用の `private`。共通設定だけなら、switch の `--configuration private` を省く。

```sh
id -un
printf '%s\n' "$HOME"
```

出力と [ホスト定義](../../../../nix/hosts/default.nix) の `system.primaryUser`・ホームパスが一致することを確認する。`private` もこの共通ホスト定義を使う。異なる場合は適用前にホスト定義を実機に合わせる。ユーザー名とホームは Git 管理し、秘密や認証情報は書かない。

### 4. Nix を導入する

```sh
cd ~/dotfiles
bash scripts/bootstrap-nix.sh --install
```

sudo や macOS の許可ダイアログには、表示内容を確認して応答する。この操作は Nix の volume、daemon、shell 初期化などを変更する。Homebrew を別のインストーラで導入する必要はない。

完了後、新しいターミナルを開く。

```sh
nix --version
cd ~/dotfiles
```

版が表示されれば次へ進む。コマンドが見つからない場合はインストーラの shell 初期化案内を確認する。既存の Nix や残存パスを理由に停止した場合は、削除や再インストールをせず状態を確認する。

### 5. ビルドと適用を実行する

```sh
cd ~/dotfiles
bash scripts/dotfiles.sh switch --configuration private
```

**この1コマンドで check → build → 確認 → 適用まで進む。別途 build は不要。**
表示された対象ユーザー・適用先を確認し、適用してよければ `switch` と入力する。スクリプト全体を sudo で起動しない。

初回は、既存の `/etc/bashrc`・`/etc/zshrc` の内容と `.before-nix-darwin` という退避先を表示する。**独自設定の引継ぎが不要で、退避してよければ `backup` と入力する。** 分からない内容や残したい設定があれば、別の文字列を入力して中止する。内容表示では制御文字をエスケープしている。

sudo のパスワードを求められたら入力する。スクリプトが元ファイルを退避して、そのまま適用する。手動の `mv` は不要。退避先がすでにある場合や、未知のリンク・ディレクトリ、確認後の変更を検出した場合は停止する。管理済みのリンクと退避済みで元ファイルがない対象は、そのまま進む。

**設定配置が終わるまで、今の zsh のターミナルを閉じない。** switch は fish を導入するが、既存ユーザーのログインシェルは変更しない。切替は[手順7](#7-fish-をログインシェルにする)で行う。

macOS 設定、Homebrew 本体、アプリ、Home Manager の設定を適用する。アプリの導入には時間がかかるため、App Store の確認画面も見る。終了するまで別の switch を起動しない。

コマンドが終了した直後に確認する。

```sh
echo $?
ls -ld /run/current-system /nix/var/nix/profiles/system
```

**終了コード0で、Homebrew などの失敗がログに残っていないことを確認してから次へ進む。**
profile のリンクがあるだけでは成功とは判断できない。途中で止まったら、[該当する対処](#初回導入で止まったとき)を読む。

### 6. 設定を配置する

まだ zsh のまま実行する。導入した Nix 版 mise と Homebrew を、この端末の PATH に加える。

```sh
export PATH="/etc/profiles/per-user/$(id -un)/bin:/run/current-system/sw/bin:/opt/homebrew/bin:$PATH"
command -v mise
mise --version
```

`mise` が `/etc/profiles/per-user/<ユーザー名>/bin/mise` を指すことを確認する。
配置する設定は [mise.toml](../../../../mise.toml)。内容を確認して、このファイルだけを trust する。

```sh
mise trust ~/dotfiles/mise.toml
```

まず60秒の制限付きで配置予定を確認する。

```sh
/usr/bin/python3 -c 'import os, subprocess; subprocess.run(["mise", "-C", os.path.expanduser("~/dotfiles"), "dot", "apply", "--dry-run"], timeout=60, check=True)'
```

エラーやタイムアウトなら apply へ進まない。初回の走査は既存の状態ディレクトリにも及ぶため、長時間止まる場合は対象を確認する。
配置先に既存ファイル・ディレクトリ・別リンクがある場合は、実体と内容を確認する。`--force` で上書きせず、必要なものだけ保全して衝突を解消する。Karabiner の既存設定がある場合は[アプリ設定](#アプリ設定)も確認する。

dry-run が完了し、配置先に問題がなければ適用する。

```sh
mise -C ~/dotfiles dot apply
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

エラーなく完了し、リンク先が `~/dotfiles/config/` 配下の正本であることを確認する。

### 7. fish をログインシェルにする

設定配置後、現在の zsh から fish を起動し、設定の読み込みでエラーが出ないことを確認する。ここからのコマンドは fish 用。

```sh
/run/current-system/sw/bin/fish
```

Nix 版 fish が利用可能なログインシェルとして登録されていることを確認する。

```fish
grep -Fx /run/current-system/sw/bin/fish /etc/shells
```

パスが表示されたら、現在のユーザーのログインシェルを変更する。

```fish
chsh -s /run/current-system/sw/bin/fish
```

アカウントのパスワードを求められたら入力する。パスが見つからない場合や `chsh` が失敗した場合は、`/etc/shells` を手で上書きせず、switch の終了状態とエラーを確認する。

今の端末を残したまま新しいターミナルを開き、fish が起動することを確認する。

```fish
status is-login
echo $status
```

標準 Terminal のログインシェルとして起動していれば `0` になる。zsh などが開く場合は、端末アプリの起動設定が「デフォルトのログインシェル」になっているかを確認する。端末が独自の起動コマンドを指定している場合、`chsh` だけでは変わらない。

ログインシェルの変更はこの一度だけでよく、通常の switch のたびに実行する必要はない。

### 8. ランタイムを導入してエージェントを起動する

新しい fish の端末で、個別プロジェクトの設定を混ぜないよう HOME から指定版をインストールする。

```fish
cd ~
mise install
node --version
python --version
ruby --version
bun --version
```

インストールの成功と、[共通ランタイム設定](../../../../config/.config/mise/config.base.toml)の指定版を確認する。エラーがあれば、その runtime の導入を解決してから進む。

エージェントの起動には、ユーザー側で秘密環境の準備を済ませておく必要がある。起動 wrapper は `~/.config/.env` を strict モードで読み込むため、ファイルや必要な復号鍵が未準備だと起動前に停止する。秘密の登録・復元や各サービスへのログイン方法は、この初回手順では扱わない。

使うエージェントを1つ起動する。例えば Pi の場合：

```fish
cd ~/dotfiles
type pi
pi
```

`type pi` が fish の関数を示し、Safehouse 経由で Pi の画面が開けば初回セットアップは完了。ログインなどはユーザーが別途行う。エラーが出た場合は保護設定を外さず、表示された不足ファイル・コマンド・秘密環境を確認する。

## 初回導入で止まったとき

失敗した操作とエラー出力を確認してから再開する。bootstrap、退避、switch を最初から機械的に繰り返さない。適用途中の変更は自動では戻らない。

| 症状 | 確認・対処 | 再開地点 |
|---|---|---|
| shell 退避の確認で止まった | 表示された内容を確認し、引継ぎが不要なら `backup` と入力する | 実行中の確認から続行 |
| `Backup already exists`、未知の shell リンク、`Shell backup stopped` | 元ファイルと `.before-nix-darwin` の両方を確認する。一部の退避だけが完了している場合もある。既存退避を上書き・削除せず、衝突を解消する | 問題を解消した後、同じ構成の switch |
| `Unexpected files in /etc` | エラーが示す対象を確認する。自動対応は bashrc / zshrc の確認付き退避だけ。他のファイルは出所・必要な内容・退避先を個別に確認する | 原因が分かるまで停止 |
| `Could not write domain com.apple.universalaccess` | [手順2](#2-ターミナルの権限を準備する)の実行元アプリのフルディスクアクセスを確認し、端末を開き直す。許可済みでも失敗する場合は、別の原因を調べる | 権限の問題を解消した後、同じ構成の switch |
| mas の処理が進まない | App Store を開いてサインイン・規約・購入確認の画面を見る。開くことで進んだ事例あり | 実行中ならその処理を確認し、別の switch を重ねない |
| アプリごとに購入パスワードを求められる | [手順1](#1-app-store-と-xcode-を準備する)の要求頻度を任意で調整する | 実行中の確認画面へ応答する |
| Homebrew が Xcode ライセンス未同意で失敗 | 現在の switch の終了を待ち、Xcode を起動して同意・初期設定を完了する | 開発ツールの動作確認後、同じ構成の switch |
| mise の dry-run が失敗・時間超過 | 配置先の実体、衝突、走査対象を確認する。`--force` を使わない | 問題を解消して dry-run から |
| その他の衝突・失敗 | 対象だけの内容・リンク先・変更済み範囲を確認する | 原因が分かるまで停止 |

## 日常の変更と更新

| 変更したいもの | 操作 |
|---|---|
| 通常設定・自作スキルの本文 | `config/` の正本を編集。直接リンクなので再適用不要 |
| 配置するファイルの追加・削除 | [配置ルール](#管理の分担と通常配置)を確認して mise apply。削除・改名は先に unapply |
| CLI / GUI アプリ | [Homebrew](#homebrew-本体とアプリの管理)で更新 |
| 共通ランタイム | [ランタイム](#ランタイム)の版指定と install / upgrade |
| Nix 基盤・macOS 設定 | 宣言・差分を確認して switch。適用せず検証する場合だけ build |
| 外部スキル | [外部スキル](#外部スキル)の専用更新手順 |

家用 Mac の適用：

```fish
cd ~/dotfiles
bash scripts/dotfiles.sh switch --configuration private
```

共通構成なら `--configuration private` を省く。Nix の依存更新は下の update 手順、実適用の条件は[Nix の適用と復旧準備](#nix-の適用と復旧準備)を参照する。稼働中の Hermes がある場合は、その節の停止手順を先に確認する。

### Nix の事前ビルド

**適用せずに検証したい場合だけ使う。通常の適用は `switch` 一回でよく、先に `build` を実行する必要はない。**

Nix と Command Line Tools 付属の `/usr/bin/python3` が必要。`scripts/dotfiles.sh` はこの Python を使い、mise の導入・配置やプロジェクトの Python に依存しない。ホスト定義は `nix/hosts/` の Nix module を正本とし、`flake.nix` の `darwinConfigurations` から読み込む。既定の `default` は共通設定、`private` は共通設定に家用アプリを加えた構成。適用前に `system.primaryUser` と `users.users.<name>.home` が実機に合うことを確認する。

別の構成を追加するときは、その差分用 module を作り、`darwinConfigurations` に対応する構成を定義する。構成名は英字または `_` で始め、以降は英数字・`_`・`-` を使う。ユーザー名・ホームなどの非秘密の定義は Git 管理し、秘密や認証情報は書かない。

```fish
cd ~/dotfiles
bash scripts/dotfiles.sh build
```

別の定義済み構成を使う場合は `build --configuration NAME` と指定する。構成が見つからなければエラーになり、既定の `default` へ切り替わることはない。ビルドは構成を適用せず、出力された store path に対する activation も実行しない。
通常の build は lock を更新しない。新しい Nix ファイルは対象を明示して Git に追加してからビルドする。未追跡ファイルを含めるために `path:.` へ切り替えたり、一括 stage したりしない。

通常設定と自作スキルの配置は[mise の直接リンク](#管理の分担と通常配置)で行い、Nix は同じ宛先を所有しない。Nix に残す Hermes 本体・生成 wrapper / plist・停止検査、外部スキル・外部 plugin は store 管理とする。通常の fish 関数や起動スクリプトは Git 正本を使い、Safehouse / dotenvx の実行先は `/opt/homebrew/bin` に固定する。Hermes は Nix 管理の安定パス `~/.local/libexec/hermes` を参照する。

依存を更新するときは、公開 input 名を指定する。

```fish
bash scripts/dotfiles.sh update nixpkgs
bash scripts/dotfiles.sh update hermes-agent
bash scripts/dotfiles.sh update nix-homebrew
bash scripts/dotfiles.sh update agent-skills
bash scripts/dotfiles.sh update all
```

Bash は nix-darwin の標準導入と初期化を維持する。mise の補完用 `usage` も Home Manager の mise モジュールで Nix 導入し、どちらも Homebrew へ重複宣言しない。

Bash / fish / mise 本体や Nix に残した依存は `update nixpkgs`、Hermes は `update hermes-agent`、Homebrew 本体は `update nix-homebrew`、スキル管理ライブラリは `update agent-skills` で更新する。通常 CLI / GUI は[Homebrew](#homebrew-本体とアプリの管理)、共通ランタイムは[mise](#ランタイム)で更新する。`update all` は全公開 input を更新するが、Source registry の外部スキルは含まない。外部スキルは[専用の標準コマンド](#追加更新復元)で更新する。独自 updater は使わない。

更新は update → lock 差分確認 → 承認した範囲で switch の順に行う。エージェントに検証を任せる場合や適用前に生成物を確認したい場合は、switch の前に build を使う。update は適用・起動を行わず、通常の build / switch は lock を更新しない。復元時は更新を混ぜず、既存の lock でビルドする。Nix 管理の Yazi プラグインを `ya pkg` で重ねて更新しない。

fish の `config.fish` は Git 正本を mise で直接リンクする。Home Manager の標準生成設定は `~/.config/fish/nix-init.fish` に分離し、Git 側から source する。外部 plugin と標準 `conf.d` は Nix に残し、Fisher を併用しない。非対話の `shell-init.fish` は mise shims を PATH に含め、対話時の mise / zoxide activation は Git 側で行う。二重 activation を避け、`fish_variables` と履歴は管理対象にしない。

### ツールのバージョン差を確認する

まず `type -a` や対象の version 表示で解決先・使用版を確認する。Homebrew は提供 formula / cask の版、mise は Git 正本の pin と `mise which` による選択、Nix は lock の収録版を照合する。Brew アプリの版を `flake.lock` が固定するわけではなく、Hermes 内部依存と共通 runtime も別管理。

以下は Nix に残した対象だけの手順。`flake.nix` が取得元とブランチを選び、`flake.lock` が特定のコミットを固定する。`unstable` を指定していても、build のたびに最新版へ更新されるわけではない。

Nix 管理の対象が上流より古い場合は、まず通常の更新を検討する。

```fish
bash scripts/dotfiles.sh update nixpkgs
```

これは対象ツール単体ではなく、共通の nixpkgs の固定コミットを更新する操作。他のツールや依存関係も変わり得るため、その範囲を確認して実行する。更新だけでは使用中の環境は切り替わらない。

更新後は `git diff -- flake.lock` で変更された input を確認し、更新先コミットの対象パッケージ定義で取得元とバージョンを確認する。同名の別ソフトに注意し、検索結果や上流の最新リリースだけで収録版を判断しない。ローカルで評価できない場合は、更新先コミットの公開定義を確認できるが、ビルド・動作検証の代わりにはならない。

更新しても希望版に届かなければ、利用ブランチの nixpkgs 側が未対応であることを伝え、収録を待つか、個別対応するかを相談する。希望版が収録されていれば、lock 差分確認後に承認した範囲で switch へ進む。適用前の検証だけを行う場合は build を使う。固定版からの復元では、この更新を行わない。

### Homebrew 本体とアプリの管理

Homebrew 本体は `nix-homebrew` で導入・版固定する。新規 Mac で Homebrew の公式インストーラを別途実行する必要はなく、承認後の Nix 適用で導入する。Nix 本体の初回導入は引き続き必要。

既存 Mac は `autoMigrate` で Homebrew を引き継ぐ。適用時に Homebrew 本体の Git 追跡ファイル・`.git`・残存 vendor ディレクトリを削除して Nix 管理へ置き換える。既存の Cellar / Caskroom・ユーザー追加 tap 等は保持する設計だが、本体へのローカル修正は引き継がれない。ビルドだけでは移行しない。既存 Homebrew を移行する場合は、管理部分の保全・復旧範囲を確認して承認する。Nix 世代の rollback だけで移行前の管理方式へ戻るとは扱わない。

formula・cask・App Store アプリの一覧は `nix/darwin/homebrew.nix` で管理する。適用時は `autoUpdate = false` / `upgrade = false` / `cleanup = "none"` を維持する。tap は Homebrew 管理を維持し、Intel 用 Homebrew は追加しない。本体の更新は `update nix-homebrew` 後に build・switch する。パッケージの版は `flake.lock` で固定されない。

通常 CLI の日常更新は Homebrew で行う。

```fish
brew update && brew upgrade
```

これは tap / パッケージの更新であり、nix-homebrew 所有の Homebrew 本体を Nix 管理外へ戻す操作ではない。対象限定なら `brew upgrade FORMULA` や `brew upgrade --cask CASK` を使う。App Store アプリの更新・認証は App Store / `mas` の標準手順で別に扱う。通常アプリの更新・削除のための Nix build / switch は必須でない。

追加・削除は先に Nix 一覧を整合させ、対象限定の `brew install` / `brew uninstall` を使える。GUI は `--cask` を指定する。`cleanup = "none"` なので宣言削除だけではアンインストールされず、未宣言の兄弟も自動削除しない。`--zap`、全件 cleanup、DB / サービスの削除を通常手順に混ぜない。

brew 管理の CLI に別 installer / self-update を重ねない。GUI の自己更新を使うか抑止するかは製品ごとに判断する。利用する brew 版の `brew help upgrade` と `brew info --cask CASK` で `auto_updates` / `version :latest` の扱いを確認する。通常 upgrade の対象外で、自己更新も抑止した対象だけ必要に応じて `brew upgrade --cask --greedy CASK` 等を使う。全 GUI を無条件に greedy 更新しない。

### 組織管理アプリをこの Mac だけスキップする

Zoom など、管理者が導入・更新するアプリは dotfiles の cask 宣言に残し、その Mac の Homebrew 標準設定で Bundle から除外できる。`brew --prefix` の下の `etc/homebrew/brew.env` に、例えば次を設定する。

```text
HOMEBREW_BUNDLE_CASK_SKIP=zoom
```

既存の `brew.env` があればファイルを上書きせず、既存の除外名も保って編集する。複数名は空白区切り。実ファイルはマシン固有のローカル設定として Git / Nix store に入れない。Homebrew 自身が読み込むため、sudo をまたいだ環境変数の継承を追加する必要はない。ユーザー別 `brew.env` に同じキーがあれば上書きされるので、適用時の skip 表示を確認する。

これは `brew bundle` のインストール対象から外す設定であり、既存アプリをアンインストールしたり、組織の管理を解除したりするものではない。PC 別の Nix 構成や全 PC 共通の除外は追加しない。

## 管理の分担と通常配置

| 対象 | 正本・管理主体 |
|---|---|
| macOS・Nix・Homebrew 本体・Bash / fish / mise と補完依存 | Nix / nix-darwin / nix-homebrew |
| 普段使う CLI / GUI / App Store アプリ | Homebrew。導入一覧は `nix/darwin/homebrew.nix` |
| 共通ランタイム | mise。版指定は `config/.config/mise/config.base.toml` |
| 通常設定・自作スクリプト・自作スキル | `config/` の Git 正本。配置はルート `mise.toml` |
| Hermes fork・生成 wrapper / plist・停止検査、外部スキル・fish / Yazi 外部 plugin | Nix / Home Manager |

通常配置は HOME から `config/` の正本へ直接リンクする。アプリ・設定ディレクトリ単位に mise の `symlink-each` と `manifest = "git"` で追跡ファイルごとに配置し、HOME 全体を配置先にしない。親ディレクトリ自体は置換しない。初回は各配置先内の状態ディレクトリも走査され得るため、実 HOME の dry-run 完了を確認する。`exclude` は初回走査を止める指定ではなく、追跡済みの配布不要物と別宣言の対象だけに使う。Nix ソース・生成 wrapper・example・秘密・実行時状態は配布しない。

`symlink-each` は、管理記録がない初回には配置先全体を走査する。[mise PR #11549](https://github.com/jdx/mise/pull/11549) の所有記録を使う改善後も、記録欠落・不正時の走査は残る。この制約を前提に配置先を狭く保ち、mise の内部状態を手動生成して回避しない。

本文の編集やアプリからリンク先への書き込みは Git 差分になり、再配置不要。配置対象の変更は次のように区別する。

- 既存の Git manifest 内の追跡ファイル増減は、対象を確認して apply で反映する。
- 個別リンクや新しい管理ディレクトリの追加は、ルート `mise.toml` の宣言を更新して apply する。
- 個別リンクや管理ディレクトリの削除・改名は、宣言を消す前に該当宛先を標準 unapply で解除する。宣言削除だけで HOME 側も消えるとは扱わない。
- 自作スキルは共通・Claude 向けの2 glob を維持する。通常追加では名前を列挙せず、スキル単位の削除・無効化は[外部スキル節](#外部スキル)に従う。

```fish
mise -C ~/dotfiles dot apply
```

apply 前に対象の実体・リンク先と変更範囲を確認する。未知の実ファイル・ディレクトリ・別リンクを `--force` や一括退避で置換しない。mise が未知の symlink を必ず拒否するとは仮定しない。解除には対象を確認して `mise -C ~/dotfiles dot unapply TARGET` を使う。初回の所有権移行には[事前確認と切替手順](#既存-mac-の切替)も必要。

自前 Brewfile やコピー運用を追加しない。Nix build / switch に mise apply や runtime install を組み込まない。Nix の適用方法は[日常の変更と更新](#日常の変更と更新)を参照する。

## 既存 Mac の切替

この節は、既存の Home Manager 管理から mise へ設定の所有権を移す場合だけ読む。新規 Mac は[初回セットアップ](#新しい-mac-のセットアップ)を使う。

既存 Mac で HM から mise へ所有権を移す初回だけは、次の順を守る。計画承認だけで実機操作を実行しない。

1. 宣言・構文・関連テスト・Nix build を確認し、旧世代、対象リンクの種類・宛先、使用版と導入候補の版差を確認する。設定・環境変数を全量取得しない。
2. 対象の install、リンク引継ぎ、Herdr 登録、必要な停止・保全の範囲を提示し、実機操作を承認する。既存の Claude / Zed / Pi の差分と管理外の状態を保持する。
3. 旧環境が使える間に対象限定の Homebrew install と mise runtime の準備を行う。候補の版指定を明示して不足を確認し、全体 upgrade はしない。mise の trust は確認した当該設定だけに限定する。
4. **Nix の所有解除前に**、実 HOME に対する mise の配置 dry-run を時間制限付きで実行し、完了と結果を確認する。使用する mise 版の標準構文を確認し、実行前に制限時間を決める。既知の旧 HM リンクによる衝突以外の問題、未知の実体、タイムアウトがあれば switch しない。dry-run の成功だけで後続の switch / apply の成功を保証したとは扱わない。
5. アプリを新規起動しない短い切替時間を確保し、失敗時に引き渡す対象リンクと復旧先の旧 Nix 世代、操作の承認範囲を事前に確認する。稼働する Hermes は管理関数で別途停止し、通常端末の `bash scripts/dotfiles.sh switch` で HM の所有を解除する。先に mise を同じ宛先へ適用しない。
6. 終了コードと解除済み範囲を確認し、残った旧リンクは由来を確認する。`mise -C ~/dotfiles dot apply` で直接リンクを配置する。切替中に新しい実体が作られた場合も保持して相談し、force で通さない。
7. 旧 HM hook の解除後、Homebrew 本体から[Herdr integration](#claude-code)を導入し、settings の差分を確認する。plugin / session / log の移行はしない。
8. 新しい shell の本体・runtime の解決先、直接リンク、主要 CLI・fish plugin・Herdr hook を確認する。必要なサービス再開は別途承認し、既存管理関数を使う。検証だけのためにサービスを起動しない。

途中失敗時は進行を止め、Nix profile / HM / mise / Homebrew / Herdr の現状と変更済み範囲を確認する。switch や apply を最初から自動再試行しない。所有リンクの引渡しや旧 Nix 世代への復旧は承認範囲を確認して行い、[本文・アプリ・状態の復旧](#nix-の適用と復旧準備)とは分ける。force、自動 rollback、独自配置ツールは使わず、旧世代や退避物の削除・GC を混ぜない。

## Nix の適用と復旧準備

**適用範囲を確認・承認した後にだけ使う。** 秘密・サービス・OS 設定の変更を無断で含めない。対象ユーザーの通常の対話端末から、Safehouse 外で実行する。スクリプト全体を `sudo` で起動しない。

```fish
cd ~/dotfiles
bash scripts/dotfiles.sh switch
```

家用 Mac は `switch --configuration private` を使う。別途 build した場合は、そのときと同じ構成名を指定する。switch は呼び出しごとに Git snapshot を取得し、その snapshot に対して check / build を行う。過去の build 出力を受け渡す方式ではない。候補 system と前の system profile を確認し、`switch` と入力して進める。対象ユーザーと HOME、Hermes の停止状態を確認してから、候補の `darwin-rebuild` の標準 `switch` 部分を sudo で実行する。非対話・root・Safehouse 内からは実行できない。

全アプリ停止・未宣言ツールの全件棚卸し・全設定の一括バックアップを常時の適用条件にしない。実際に衝突や書き込み競合がある場合は、その対象の種別・リンク先・必要な内容を確認し、個別に保全と操作範囲を承認する。退避時に競合する書き込み元だけを停止し、認証・session・DB・管理外の兄弟や共有正本を一括移動しない。既存バックアップへ上書きしない。

`/etc/bashrc`・`/etc/zshrc` は switch 内の内容表示と別途承認を経て退避する。それ以外の Nix 管理先の衝突は Home Manager / nix-darwin の標準 activation 内の検査で止め、force や一括退避で通さない。mise 管理先は apply 前に別途確認する。アプリが管理リンクを実ファイル等へ置き換えた場合も保持して相談する。外部スキルの[標準 link 配布](#外部スキル)では管理対象リンクの置換を受け入れるため、通常設定と区別する。

Hermes の配置変更に必要な停止は[管理関数](#更新停止既存環境の移行)で行う。入口は稼働状態を保存せず、自動停止・再開・サービスのバックアップ・自動 rollback を行わない。Nix daemon 等の変更も適用範囲として確認・承認する。

**全変更前の検査や原子的な適用を保証しない。** system profile は activation より前に更新される。後段で衝突・エラーになると、それ以前の設定変更が残り得る。標準 `check` / `--dry-run` activation を安全な事前検査として実行しない。失敗時は出力と変更済み対象を確認して再開か復旧を決め、bootstrap・switch・退避操作を最初から機械的に繰り返さない。

以前の nix-darwin 世代がある場合は標準の `--list-generations` / `--switch-generation` による復旧を検討できるが、実行は別途承認する。mise に移した宛先を旧 HM が再び所有する場合は、該当リンクを確認して標準 unapply 等で引き渡してから世代を切り替える。Nix 世代だけでは mise 所有リンクも正本の本文も戻らない。本文は後続変更を確認して Git で別に戻す。Homebrew アプリ・mise runtime・preferences・DB・Docker volume・認証も世代の切替だけで戻るとは扱わない。

初回移行当時の退避・system 復旧の検討経緯が必要な場合だけ、[検討履歴](../../../../docs/plans/archived/2026-10-03-initial-migration-procedures.md)を参照する。現行の必須手順や、その資料だけでの実行許可ではない。

## 機能別リファレンス

ここからは必要な機能だけ参照する。認証・秘密・サービスの手順は初回セットアップの対象外で、ユーザーが別途行う。

## 共通ツール用の秘密

共通 API キーは `config/.config/.env` にまとめ、dotenvx で暗号化し、復号鍵を macOS Keychain に保存する。
プロジェクト・本番環境の秘密や各エージェント自身の認証は混ぜない。秘密のファイルは mise の自動配置対象外。既存の `~/.config/.env` リンクは保持し、未配置なら既存実体との衝突がないことを確認して、ユーザーがこの正本へのローカルリンクを準備する。秘密や鍵を Git / store に追加しない。

```fish
cd ~/dotfiles
cp -n config/.config/.env.example config/.config/.env
chmod 600 config/.config/.env
```

エディタで実値を入力する。既存ファイルは上書きせず、値をチャットやログに貼らない。
`~/.config/.env` がこのファイルへのリンクであることを確認してから暗号化する。

```fish
ls -l ~/.config/.env
dotenvx encrypt --quiet --no-armor -f "$HOME/.config/.env"
dotenvx native up --quiet -f "$HOME/.config/.env" -fk "$HOME/.config/.env.keys"
```

Keychain への保存を確認し、鍵ファイルが残る場合や保存エラーは解消してからエージェントを起動する。
起動処理は鍵ファイルへ自動で切り替えないため、Keychain から復号できないと停止する。
API キーを `config.fish` に保存しない。以前キーを export していた場合は、その設定と現在のシェルに残る値を除く。既存の環境変数が dotenvx より優先されるため。秘密は dotenvx の暗号化ファイルと Keychain で管理する。

暗号化した `.env` と login Keychain の両方を、暗号化されたバックアップに含める。
OS 移行時は Keychain も復元する。暗号化ファイルだけでは復号できない。
初期設定後は新しい端末で CLI を起動し、常駐中の Hermes は管理関数から再起動する。

起動できなくなったら再起動を繰り返さず、sandbox 外で変更した管理ファイルを以前の版へ戻す。
暗号化 `.env`、Keychain 項目は削除しない。

## 外部スキル

外部スキルは agent-skills-nix の Source registry と標準 Home Manager モジュールで取得・選択・配布する。取得元と探索範囲は `nix/skill-sources/`、revision / hash は `nix/skill-sources.lock.json` で管理する。同じ repository の取得元は共有する。root の `flake.lock` は管理ライブラリ `agent-skills` などの固定に使い、スキルの取得元は root input に追加しない。

外部スキルは標準の `structure = "link"` で store へのリンクとして配置する。外部の選択・配布先は `nix/home/skills.nix`、自作の配置はルート `mise.toml` を正本にし、Nix 側は mise の対象を参照して同じ宛先を二重所有しない。同名の自作を外部より優先し、Claude 側では Claude 専用の同名スキルを優先する。ドット始まりのディレクトリは配布しない。

自作スキルは共通・Claude 向け glob の `symlink-each` / Git manifest で、追跡ファイルごとに正本へ直接リンクする。通常の追加は Git 追跡と mise apply だけでよく、TOML に名前を列挙しない。Claude 専用の同名スキルが必要な場合だけ、該当宛先の明示エントリに専用 source と `mode = "symlink-each"` / `manifest = "git"` を宣言し、共通 glob を override する。

スキル単位の削除・改名・`.disabled/` への移動は、glob から消える前に該当 target を unapply する。共通・Claude の両方へ配布していれば、それぞれ確認して解除する。外部スキルとの優先関係が変わる場合だけ Nix 側の選択・適用も行い、所有の引渡し順を確認する。

共通の配置先は `~/.agents/skills/`、Claude は `~/.claude/skills/`。Antigravity CLI は `~/.gemini/antigravity-cli/skills` から共通集合を参照する。Hermes / Pi 専用や Antigravity IDE 用へ配布を広げない。対象外の兄弟スキルと Claude の `synced` は保持する。

### 追加・更新・復元

追加時は `nix/skill-sources/` に取得元と必要な探索範囲を宣言し、スキルの選択を更新する。同じ repository を使うなら既存の取得元を共有する。新しいスキルを無条件に導入する広い `enableAll` は避け、同名の自作・Claude 専用の優先順位を維持する。取得元を追加するために `flake.nix` を編集する必要はない。

リポジトリのルートから、外部取得元を一括更新する。

```fish
cd ~/dotfiles
nix run .#skills-sources-lock
```

標準の npins ベースの更新処理で、全取得元の解決後に専用 lock を置き換える。宣言を変更した場合も実行する。既存の取得元も更新されるため、lock 全体の revision と選択結果を確認する。標準コマンドに取得元名を渡す単体更新機能はない。独自 updater や子 Flake は併用しない。

管理ライブラリだけなら `bash scripts/dotfiles.sh update agent-skills`、システムの全公開 input なら `update all` を使う。どちらも専用 lock の更新とは別操作。外部取得元の更新は、同じ repository から選択したスキルすべてに影響する。新規ファイルを Git ソースに含めてから、宣言・lock・選択の差分を確認してビルドする。

```fish
bash scripts/dotfiles.sh build
```

生成物を確認し、[適用条件](#nix-の適用と復旧準備)を満たした後に Safehouse 外の対話端末で実行する。

```fish
bash scripts/dotfiles.sh switch
```

新規 Mac の復元ではどちらの更新コマンドも実行せず、既存の `flake.lock` と `nix/skill-sources.lock.json` で build / switch する。`npx skills` による取得・コピーや旧 lock による復元は併用しない。自作スキルは別途 mise で配置し、本文の編集は即時反映する。

既存の実ディレクトリなどが新たに管理対象になる場合は、その対象だけを確認・保全して退避する。親ディレクトリ全体や `synced` は動かさず、実行時キャッシュを固定版として復元しない。日常の更新では標準モジュールの管理対象リンク置換を受け入れ、初回の未知の実体の保全を恒久的な上書き禁止へ拡張しない。

## Claude Code

Herdr の Claude hook は Homebrew 本体に埋め込まれた同版の hook を、標準 integration installer で導入する。旧 HM 配置と併用せず、所有解除後に実設定への変更範囲を承認して実行する。

```fish
herdr integration install claude
```

installer は settings の symlink を追って Git 正本を書き換え得る。Herdr 用登録以外の既存差分を保持し、実行後に hook と settings の差分・参照先を確認する。本体更新時も hook が同版かを確認し、必要な integration 更新だけ承認して行う。別版の Nix ソースから hook を取り出したり、plugin installer をついでに実行したりしない。

statusline は設定内の npm version を固定し、通常の `npx` で利用する。Nix build / activation にはインストールを含めず、初回取得には npm registry への接続が必要。

## Pi

`settings.json` と footer の設定は追跡済み正本への通常の live link。Pi からリンク先への書き込みは Git 差分になり、merger やローカル通常ファイルへの複製は使わない。日常の内容編集で Pi の停止を一律に求めない。アプリがリンク自体を置換した場合は衝突として保持し、force overwrite しない。認証・session を移行用設定や store へ含めない。

拡張の本体版は `config/.pi/agent/settings.json` の npm version / Git commit で固定する。これは npm の推移依存全体の lock ではなく、新規取得時の全機能の復元を保証しない。拡張のインストール先は通常の Pi 管理ディレクトリに保ち、Nix build / activation では取得・更新しない。Pi 本体は Homebrew で更新し、別 installer / 自己更新コマンドを併用しない。

OpenAI は Pi 内の `/login openai` から `Sign in with ChatGPT` を選んで認証する。
MCP の個人設定は `~/.pi/agent/mcp.json` に置く。OAuth が必要なサーバーには `pi mcp login <server>` を使う。

## CuaDriver

CuaDriver 本体は共通の Homebrew 一覧で管理する。[通常の Brew 運用](#homebrew-本体とアプリの管理)に従い、公式 installer を重ねない。外部 `cua-driver` スキルの配置と本体の導入は別である。

初回利用時のアクセシビリティ・画面収録等の TCC 許可と daemon 起動は、変更範囲を確認してユーザーが [公式 Quickstart](https://cua.ai/docs/cua-driver/quickstart) に従う。アプリ導入だけで権限が復元されるとは扱わない。

以前の手動導入で `~/.local/bin/cua-driver` がある Mac では、`type -a cua-driver` と `cua-driver --version` で解決先・版を確認する。既存リンクを無断で削除せず、Homebrew 版を使うために必要な PATH 整理は対象を確認して行う。

## Hermes Agent

gateway / dashboard はホストの launchd、Hindsight は Docker で動かす。同じ `~/.hermes` を使う Docker dashboard をホスト版と同時起動しない。

### 初回設定

本体は `ryonakae/hermes-agent` の `ryonakae` ブランチを lock で固定し、fork 同梱の Flake で導入する。起動定義・生成 wrapper / plist・停止検査は Home Manager が管理する。SOUL と Compose の通常設定だけを mise の直接リンクで配置する。サービスモジュールは取り込まない。`hermes gateway install` 等による plist 再生成、旧 installer、Hermes 専用 mise / venv の復元は併用しない。`setup` のサービス導入・即時起動の質問には No を選ぶ。

ローカル音声認識・マイク入力用の `voice` グループは同梱しない。Apple Silicon では CTranslate2 の検証用依存を通じて PyTorch のソースビルドが必要になり得るため、fork 標準の `override` でこのグループだけ除外している。Hindsight、メッセージング、TTS 用の追加グループは残す。ローカル音声機能が必要になった場合は、この選択を見直して依存の dry-run を確認する。

利用を開始する Mac で、ユーザーが sandbox 外から共通ツール用の秘密、Hermes の認証・設定、Docker を準備する。認証・DB・memory・session・cache は store に入れない。Hindsight の秘密は Git 管理外の `~/.hermes/hindsight/.env` に置き、`openai-codex` 用の `~/.codex` 認証もユーザーが復元する。

Hindsight のデータと認証を準備し、コンテナ起動を承認した後に実行する。

```fish
cd ~/.hermes/services
docker compose up -d hindsight
hermes memory setup
```

memory provider に Hindsight を選ぶ。Compose は tag と digest を固定するが、Docker の volume・認証は Nix 世代へ巻き戻らない。

plist の生成・配置だけではサービスを開始しない。初期設定と必要な状態バックアップを済ませ、起動を承認したサービスだけ管理関数から開始する。

```fish
hermes-gateway start
hermes-dashboard start
hermes-gateway status
hermes-dashboard status
```

新定義は既定で disabled。明示的な start で有効化し、以後のログイン時も起動対象になる。stop が成功したサービスは無効化され、次の start まで停止状態を維持する。KeepAlive による自動再生成は行わないため、異常終了時も原因を確認して管理関数から再起動する。

### 更新・停止・既存環境の移行

gateway は `hermes-gateway`、dashboard は `hermes-dashboard` で操作する。管理関数は fork 標準の停止コマンドを呼ぶ。タイムアウト時の強制終了も fork の仕様に従い、強制終了しないことは保証しない。独自の停止 controller や子プロセス管理は追加しない。

停止コマンドや launchd 操作がエラーなら後続の再起動を中止する。直接の `launchctl` で管理関数を飛ばしたり、管理操作と設定適用を並行して行ったりしない。成功表示だけで DB バックアップの整合性を保証した扱いにはせず、既存データの保全は別に確認する。

```fish
hermes-dashboard stop
hermes-gateway stop
```

本体の更新は `bash scripts/dotfiles.sh update hermes-agent` と事前ビルドで準備する。`hermes-gateway update` / `hermes update` では更新しない。停止・必要なバックアップ・適用・再開はユーザーが別々に行う。dotfiles の適用入口は利用状態を保存せず、自動停止・再開もしない。

Home Manager は配置前に launchd の Hermes 登録、判別可能な Hermes プロセス、plist の所有関係を確認する。未停止・読み取り失敗・未知の形式なら配置を中止し、停止操作は行わない。確認はユーザーの GUI セッションを前提とし、全プロセスの所属や子プロセスの終了を追跡する仕組みではない。未知の既存 plist は強制上書きせず、確認済みの退避・復旧手順を用意する。旧定義や管理外プロセスの移行は、その環境で確認して行う。旧 `~/.hermes/mise.toml` や venv の整理も、その切替時に明示して行う。

Hindsight の停止・データ移行は別に承認する。必要な停止時は `~/.hermes/services` で `docker compose down` を実行し、データ volume を削除しない。

### リモートアクセス

dashboard は `0.0.0.0:9120` を使うが、採用済み Hermes では認証 provider が必要。`--insecure` は認証を迂回しない。ユーザーが認証を設定してから起動し、信頼できる LAN / VPN 内で使う。

iPhone からのアクセス用に Tailscale Serve を設定する。これは Nix の適用とは別の、ユーザーによるネットワーク設定操作。

```fish
tailscale serve --bg --https=9119 http://127.0.0.1:9120
tailscale serve --bg --https=9999 http://127.0.0.1:9999
tailscale serve status
```

表示されたホスト名の `:9119` が Hermes、`:9999` が Hindsight の dashboard。`hermes-dashboard open` はローカルの URL を開く。

### Google Workspace

ユーザー用の `~/.config/gws` と認証を共有せず、Hermes 用に必要な権限だけを付与する。
初回ログインは sandbox 外で行う。

```fish
env GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.hermes/gws" \
    GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
    gws auth login
hermes-gateway restart
```

## Herdr

Git plugin は標準 CLI で以下の commit を個別に復元する。registry / checkout / state は Herdr の可変データとして残し、Nix build / activation からインストールしない。再インストールは checkout を交換し、有効化も行うため、稼働中の利用状態を確認してからユーザーが実行する。

```fish
herdr plugin install ryonakae/herdr-agent-context --ref 10b8ead9d86b2cbb7b13d87ef50dec4b87ee21cd --yes
herdr plugin install devashish2203/herdr-worktrunk --ref a3107ca566bafcd463bc138007a0c01051970784 --yes
```

更新時も採用する commit をこの一覧へ反映し、`--ref` を省略しない。省略して再インストールすると、保存済み ref を引き継がず remote HEAD へ移る。

Agent Context の installer は release binary と同じ release の checksum を取得するため、ネットワークが必要。source commit の固定は binary の Nix 固定出力管理とは異なる。既存導入物・稼働中 daemon・保存データの停止や削除は、宣言の変更と分けて行う。

Zerdr は Homebrew 版を使う。導入対象は nix-darwin で宣言するが、本体は Homebrew が管理し、`flake.lock` による版固定・ロールバックの対象にはならない。

Zerdr のローカルプラグインは本体が `~/Library/Application Support/dev.ryonakae.zerdr/` に配置する。切替時は、開発版を拾わないよう Homebrew 版のパスを明示して生成・登録する。古い絶対パスを含む manifest をコピーしない。

```fish
set -l zerdr_bin (brew --prefix ryonakae/tap/zerdr)/bin/zerdr
$zerdr_bin setup install
```

この操作は Herdr の登録と Zed tasks を更新するため、切替時に実行する。実行後に両方が Homebrew 版の実行先を参照することを確認する。Zed tasks は Nix 管理に追加していない。
worktrunk プラグインには `wt >= 0.60.0`、`fzf`、`jq` が必要。
導入後は `herdr plugin list` で確認する。

worktree の作成・削除には Worktrunk を使う。Herdr 本体の作成機能では Worktrunk の配置・hooks・ignored ファイルのコピーを引き継げない。
`herdr worktree open` は既存 checkout の登録に限って使う。
設定変更後は `herdr config check` で検査し、`herdr server reload-config` で反映する。

## Homebrew の依存と状態

1Password CLI と Google Cloud CLI は Homebrew cask で管理する。依存ライブラリは依存元のパッケージ管理に任せ、直接の導入一覧へ重ねて追加しない。PostgreSQL のデータ・サービスは別扱いとし、宣言からの除外を理由に削除・停止しない。Homebrew の自動 cleanup は無効のまま維持する。

## ランタイム

AWS CLI v2 も `config/.config/mise/config.base.toml` で mise の `aqua:aws/aws-cli` として管理する。Homebrew 版 Python と macOS 標準ライブラリの不整合を避けるため、AWS 公式配布の同梱 Python を使う。`symlink_bins = true` を維持し、同梱 Python を開発用の PATH に出さない。更新後は `aws --version` と `mise which python` で実行先を確認する。Homebrew の導入一覧には重複登録せず、移行時も `~/.aws` の設定・認証キャッシュは削除しない。

共通の Node / Python / Ruby / Bun は `config/.config/mise/config.base.toml` の exact pin を初期指定とする。値の一覧はこの設定を参照する。HOME の `~/.config/mise/config.toml` はこの正本への直接リンク。Ruby の `compile = true` を維持し、ビルドに必要な依存を準備する。

リンク配置後、個別プロジェクトの設定が混ざらない HOME から宣言版を導入する。

```fish
cd ~
mise install
```

`mise install` は指定版の導入で、pin を新しい版へ変更しない。exact pin の更新は Git 正本の版指定を編集したうえで install し、`mise which` と version 表示を確認する。`mise upgrade` は指定範囲から新しい版を選ぶときの操作で、exact pin が勝手に進むとは扱わない。配置の `dot apply` と runtime の install / upgrade は別操作。復元では指定を更新せず、宣言版を install する。

対話 shell は mise activation、非対話の agent / launchd 子プロセスは明示 PATH の mise shims を使う。個別プロジェクトではそのプロジェクトの版選択を維持し、cwd を配置用リポジトリへ変えない。Brew CLI や Hermes が固定する内部依存を共通 runtime で置換しない。

npm / uv のグローバル配置や導入済みという事実だけで dotfiles 管理へ追加しない。未宣言の導入物の全件分類を切替条件にせず、他プロジェクトの設定や `~/.local/bin` / universal PATH を一括削除・変更しない。既存 Node / npm のリンクが Hermes 専用実体等を指す場合は、関連項目だけ確認・保全し、必要なら mise shim へ引き継ぐ。PATH 優先順位を変更する際は他のユーザー配置 CLI への影響も確認する。

## Unity CLI

Homebrew の `unity-cli` cask で本体を管理する。更新は `brew upgrade --cask unity-cli` を使い、公式 installer や `unity self-update` を併用しない。導入対象は Nix で宣言するが、本体の版は `flake.lock` に固定されない。Editor・追加モジュールはプロジェクトに必要な版を CLI / Hub で管理し、認証・プロジェクト登録等の状態は Git / store に入れない。

旧 installer から切り替える場合は、`~/.unity/bin/unity` と `~/.config/fish/conf.d/unity-cli.fish`、そこから参照する PATH 設定を確認・保全し、承認後に個別に整理する。新しい shell で `type -a unity` を確認し、Homebrew 版が選ばれることを確かめる。旧本体を残したまま Homebrew 側だけ更新しても、PATH によっては旧本体が使われ続ける。既存の Editor・Hub データは削除しない。

`brew uninstall --zap unity-cli` は使わない。cask の `zap` 対象に `~/Library/Application Support/UnityHub` が含まれ、CLI 本体以外の状態まで削除するため。

導入・更新方法は [Unity 公式手順](https://docs.unity.com/en-us/unity-cli/use-unity-cli#install-with-a-package-manager)、削除対象は [cask 定義](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/u/unity-cli.rb)を参照する。

## Vim

Vim は外部プラグインを使わない補助的な編集用の最小構成。本体は Homebrew で更新する。
旧 `~/.vim/bundle` の実体は設定変更だけでは削除しない。不要物の整理は対象を確認して行う。

## macOS と手動復元

Nix 管理する preferences は `nix/darwin/preferences.nix` を正本にする。macOS の既定値と異なる設定だけを管理する。固定版 nix-darwin の説明などで既定値との一致を確認できた宣言は省き、OS・地域・機器依存や既定値が不明な設定は保持する。オプションの `default = null` は未設定を意味し、macOS の既定値の根拠にはしない。標準オプションで現在の動作を表現できる範囲だけを管理し、独自の適用スクリプトで補完しない。明示されていないキーへ推測で値を設定しない。管理対象を GUI で変更しても、次回 switch で宣言値へ戻る。適用時は標準 nix-darwin モジュールが Dock を再起動するため、作業中の UI への影響を確認してから切り替える。キーボードのリピート値は整数型で書き込まれる。

preferences は宣言や Nix 世代を戻すだけでは元に戻らない場合がある。適用直前に変更対象の旧値・型・未設定状態を記録し、戻す場合は対象キーだけを復旧する。未設定だったキーは、値を書き込むのでなくそのキーの削除が必要。再起動やログアウトが必要なら、その都度確認する。

次の作業はパッケージや設定ファイルの復元とは分け、ユーザーが行う。

- App Store / Apple ID へのサインイン、iCloud、Touch ID、TCC（アクセシビリティ・画面収録・自動化等）の許可。許可や認証を preferences 全量コピーで移さない。
- Xcode の初回起動・ライセンス確認、必要な SDK / Simulator platform の取得。署名証明書・provisioning profile・VPN 認証・秘密・Keychain は各製品の正規手順で復元する。
- Docker runtime の初期設定と必要な volume の移行。Hindsight のデータや認証は Nix 世代に含まれず、アプリ導入だけでは復元されない。
- 入力ソース、macOS 標準ショートカット、アプリ別ショートカット、Karabiner 管理外のデバイス別キー割り当て、バッテリー／AC 別の電源設定、未宣言のアプリ独自設定は必要なものだけ個別に復元する。
- Dock の固定項目・並びは Nix 管理するが、項目を宣言してもアプリ本体は導入されない。Chrome 製アプリなど、別途復元が必要なものは先に用意する。未導入のアプリは Dock 項目だけあっても起動できない。

## アプリ設定

Karabiner は `config/.config/karabiner/karabiner.json` のルール・デバイス別設定を共通管理する。通常のファイル単位の Git manifest 配置とは異なり、mise の `symlink` で `~/.config/karabiner` ディレクトリ全体を `config/.config/karabiner` へ直接リンクする。[公式手順](https://karabiner-elements.pqrs.org/docs/manual/misc/configuration-file-path/)のとおり、JSON 単体のリンクでは変更検知・自動再読込が働かないため。

初回は既存ディレクトリ・JSON の実体とリンク先、アプリによる書き込みを確認する。既存のファイル単位の管理リンクがあれば旧宣言を維持した状態で標準 unapply による解除を、実ディレクトリや管理外の内容があれば必要な保全・退避を、対象限定で別途承認してから配置する。未知の内容を force や一括削除で置換しない。実行時状態・履歴・バックアップは Git 管理しない。Karabiner 本体の初期設定と必要な macOS 権限の許可は別に行う。

配置によって JSON の実際の場所が変わった後は、新しい場所の監視を開始するため、公式手順に従って `Karabiner-Console-User-Server` を一度再起動する。再起動までは変更が自動検知されない。この実機操作は配置と分けて承認し、ユーザーが sandbox 外の通常端末で行う。検証や mise apply に自動再起動を組み込まない。

Git 管理していないアプリ設定は `Dropbox/App` にも保存している。新しい Mac では必要なものを個別にインポートする。
