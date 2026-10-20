# トラブル対応

[README](../README.md) / トラブル対応

失敗した段階とエラーを確認してから再開する。

| 症状 | 読む場所 |
|---|---|
| Xcode・App Store の認証で止まる | [Xcode・App Store](#xcodeapp-store) |
| 権限不足・Homebrew・macOS 設定の失敗 | [setup の失敗](#setup-が失敗する) |
| 適用は成功したが、設定が配置されない | [設定配置だけ再開](#設定配置だけ再開する) |
| 設定配置後の `mise install` が失敗する | [ランタイム導入だけ再開](#ランタイム導入だけ再開する) |
| fish が起動しない | [fish](#fish-に切り替わらない) |
| `.env` が見つからない・復号できない | [秘密の読み込み](#秘密の読み込みでエージェントが起動しない) |
| インストールした版が選ばれない | [バージョンの確認](#期待したバージョンが使われない) |
| 削除したファイルを戻したい | [ゴミ箱から復元](#削除したファイルを復元する) |

## Xcode・App Store

- ライセンス未同意：Xcode を開いて同意・初期設定を済ませる。
- Command Line Tools 未導入：`xcode-select --install` で導入する。これだけでは Xcode のライセンス同意は済まない。
- mas が進まない：App Store を開き、サインイン・利用規約・購入確認の画面を確認する。
- 購入パスワードが何度も出る：システム設定の「Apple Account → メディアと購入」で、要求頻度を任意で調整する。

原因を解消し、現在の処理が終了してから再開する。

## setup が失敗する

ログの `Setup stopped at` と `Completed`、終了コードを確認する。原因を解消してから、標準コマンドで必要な部分だけ再開する。

| エラー | 対処 |
|---|---|
| `Could not write domain com.apple.universalaccess` | 実行元アプリの[フルディスクアクセス](setup.md#2-ターミナルにフルディスクアクセスを許可する)を確認し、端末を開き直す |
| `brew bundle` の失敗 | 失敗した formula / cask と理由を確認する。無効化された cask は Brewfile を直し、失敗した構成だけ `brew bundle` を再開する |
| repos の dirty / origin 不一致 | 対象 checkout の変更と取得元を確認する |
| plist の衝突・手動変更 | 実配置と生成結果・所有元を確認する |
| macOS / 電源設定の失敗 | 変更済みの対象キー・構成を確認し、[macOS の部分操作](usage.md#macos-設定を適用する)を使う |
| その他の衝突 | 該当ファイル・リンク・変更済み範囲を確認する |

## 設定配置だけ再開する

選択したアプリ・repos の準備が済み、mise の配置が未完了の場合に使う。外部の配置元がまだなければ、先に[repos の取得・更新](usage.md#外部スキルと-plugin-を更新する)を行う。

衝突や timeout の原因を解消してから通常端末で進める。以下は家用の例。ルートと選択構成の宣言を確認して、それらだけを trust する。同じ内容を trust 済みなら不要。

```fish
/opt/homebrew/bin/mise trust ~/dotfiles/mise.toml
/opt/homebrew/bin/mise trust ~/dotfiles/mise.default.toml
/opt/homebrew/bin/mise trust ~/dotfiles/mise.private.toml
/usr/bin/python3 -c 'import os, subprocess; subprocess.run(["/opt/homebrew/bin/mise", "-C", os.path.expanduser("~/dotfiles"), "-E", "default,private", "dot", "apply", "--dry-run"], timeout=60, check=True)'
```

60秒以内に成功し、配置予定に不明な実体・別リンクがなければ適用する。

```fish
/opt/homebrew/bin/mise -C ~/dotfiles -E default,private dot apply
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

リンク先が `~/dotfiles/config/` の正本なら配置完了。必要なら[ランタイム導入](#ランタイム導入だけ再開する)へ進む。

## ランタイム導入だけ再開する

setup の `Completed` に `link verification` があり、共通 runtime 導入で失敗した場合に使う。ダウンロードやコンパイルのエラーを解消してから、通常端末で必要な runtime を指定する。

```fish
env MISE_ENV= /opt/homebrew/bin/mise -C ~ install node python ruby bun aqua:aws/aws-cli
```

設定済みの版を導入する。setup 時と同じ `MISE_DATA_DIR` を使い、カスタム指定がある場合は保持する。成功しても後続の Hermes・plist・macOS 設定は未実施なので、次の手順へ進む。

### runtime 復旧後の残りを完了する

`Completed` を確認し、未完了の段階だけを順に実行する。各操作が成功してから次へ進む。以下の Hermes 操作は `private` を選択していた場合だけ行う。

1. `default` を選択していた場合は、[Herdr のプラグイン導入](apps.md#プラグインの導入登録)を行う。
2. [Hermes の初回導入 task](apps.md#初回設定と起動)を実行する。ルートと Hermes 用宣言が未 trust なら、内容を確認して先に trust する。

```fish
mise -C ~/dotfiles -E hermes run hermes:install
```

途中状態で止まったら、下の[導入・更新の復旧](#hermes-の導入更新が途中で止まった)へ進む。

3. [Hermes の起動定義配置](apps.md#hermes)を行う。
4. [macOS の部分操作](usage.md#macos-設定を適用する)で、当初選択した構成の defaults と電源設定を完了する。`default` を選択していた場合は、ログインシェルも `mise -C ~/dotfiles -E default bootstrap user apply` で変更する。

残りの段階が完了してから、[初回セットアップの再起動以降](setup.md#6-mac-を再起動する)へ戻る。

## Hermes の導入・更新が途中で止まった

成功した段階と失敗したコマンドをログで確認する。

取得元・branch・HEAD・作業差分を確認する。想定外の origin、別 branch、dirty checkout、symlink があれば、その変更の扱いを決めるまで進めない。

```fish
git -C ~/Dev/personal/hermes-agent remote get-url origin
git -C ~/Dev/personal/hermes-agent branch --show-current
git -C ~/Dev/personal/hermes-agent rev-parse HEAD
git -C ~/Dev/personal/hermes-agent status --short
```

想定する取得元は `https://github.com/ryonakae/hermes-agent.git`、branch は `ryonakae`。

checkout が正常で、依存の導入だけ失敗した例では、原因を解消してから同じ HEAD の installer を次のように呼ぶ。通常端末で実行し、利用中の CLI・サービスは先に停止する。

```fish
bash ~/Dev/personal/hermes-agent/scripts/install.sh --stage python-deps \
  --dir ~/Dev/personal/hermes-agent --hermes-home ~/.hermes --branch ryonakae
```

成功したら未完了の `products` を実行し、launcher と `~/.local/bin/hermes*` を生成する。そこだけが失敗していた場合は、依存の段階を繰り返さずここから再開する。

```fish
env SHELL=/opt/homebrew/bin/fish bash ~/Dev/personal/hermes-agent/scripts/install.sh --stage products \
  --dir ~/Dev/personal/hermes-agent --hermes-home ~/.hermes --branch ryonakae
```

対象の段階がすべて成功してから完了記録を更新し、初回導入 task が完了済みと判定することを確認する。

```fish
bash ~/Dev/personal/hermes-agent/scripts/install.sh --stage complete \
  --dir ~/Dev/personal/hermes-agent --hermes-home ~/.hermes --branch ryonakae
mise -C ~/dotfiles -E hermes run hermes:install
```

初回 setup の続きなら[残りの段階](#runtime-復旧後の残りを完了する)へ戻る。更新だった場合は CLI の起動を確認してから、更新のために止めたサービスだけ再開する。

## fish に切り替わらない

setup のログインシェル変更が失敗した場合は、`/opt/homebrew/bin/fish` の導入と `/etc/shells` の登録を確認し、`mise -C ~/dotfiles -E default bootstrap user apply` を再実行する。

変更後も zsh が開く場合は、端末アプリの起動設定を「デフォルトのログインシェル」にする。独自の起動コマンドが設定されていると `chsh` だけでは変わらない。

## .env が見つからない・既存ファイルがある

`cp` は実ファイルを作るだけで、`~/.config/.env` のリンクは作らない。[リンクの作成](secrets.md#2-リンクを作る)へ進む。

`File exists` の場合は `ls -ld "$HOME/.config/.env"` で種類とリンク先を確認する。期待する実ファイルへのリンクなら作成は不要。通常ファイル・ディレクトリ・別リンクなら、内容を保全して扱いを決める。

## 秘密の読み込みでエージェントが起動しない

[初回設定](secrets.md#初回設定)の実ファイル・リンク・Keychain 登録と、Keychain のロック状態・アクセス許可を確認する。

## 期待したバージョンが使われない

`type -a` と対象の version 表示で、実行先を確認する。

- Homebrew：formula / cask の提供版と実際の解決先を確認する。
- mise：共通設定の exact pin と `mise which` を確認する。
- Hermes：`git -C ~/Dev/personal/hermes-agent rev-parse HEAD` と `~/.local/libexec/hermes` の参照先を確認し、別の `hermes` が PATH で先に選ばれていないか確認する。

## 会社が管理するアプリをスキップする

この Mac の `brew --prefix` 配下の `etc/homebrew/brew.env` に、除外する cask 名を設定する。Zoom の例：

```text
HOMEBREW_BUNDLE_CASK_SKIP=zoom
```

既存ファイルと除外名を保持し、複数名は空白区切りにする。

## 削除したファイルを復元する

Safehouse 内の `rm` は Finder のゴミ箱へ移す。通常端末の `rm` は直接削除なので、この方法では戻せない。通常端末でもゴミ箱を使いたい場合は macOS 標準の `trash` を使う。

1. Finder でゴミ箱を開く。
2. 戻したい項目を右クリックし、「戻す」を選ぶ。元の場所に戻れば完了。

「戻す」が表示されない項目は、元の場所へ手で移す。Safehouse 内の `rm` を並行して実行した場合などに起こる。Safehouse 内からゴミ箱の中身は操作できないので、復元と掃除は Finder か通常端末で行う。

外部ボリューム上のファイルは、Safehouse 内の `rm` ではゴミ箱へ移せず、元のまま残る。
