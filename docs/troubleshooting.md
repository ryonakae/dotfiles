# トラブル対応

[README](../README.md) / トラブル対応

失敗した段階とエラーを確認してから再開する。setup / switch は途中まで変更して止まる場合があり、自動では元に戻らない。別の適用を同時に起動しない。

| 症状 | 読む場所 |
|---|---|
| Xcode・App Store の認証で止まる | [Xcode・App Store](#xcodeapp-store) |
| Nix の導入で止まる | [Nix](#nix-の導入で止まる) |
| `/etc` の衝突・権限不足・Homebrew の失敗 | [システム適用](#システム適用が失敗する) |
| 適用は成功したが、設定が配置されない | [設定配置だけ再開](#設定配置だけ再開する) |
| 設定配置後の `mise install` が失敗する | [ランタイム導入だけ再開](#ランタイム導入だけ再開する) |
| fish が起動しない | [fish](#fish-に切り替わらない) |
| `.env` が見つからない・復号できない | [秘密の読み込み](#秘密の読み込みでエージェントが起動しない) |
| インストールした版が選ばれない | [バージョンの確認](#期待したバージョンが使われない) |
| 削除したファイルを戻したい | [ごみ箱から復元](#削除したファイルを復元する) |

## Xcode・App Store

- ライセンス未同意：Xcode を開いて同意・初期設定を済ませる。
- Command Line Tools 未導入：`xcode-select --install` で導入する。これだけでは Xcode のライセンス同意は済まない。
- mas が進まない：App Store を開き、サインイン・利用規約・購入確認の画面を確認する。
- 購入パスワードが何度も出る：システム設定の「Apple Account → メディアと購入」で、要求頻度を任意で調整する。無料ダウンロードは別設定の場合がある。選択肢は macOS・アカウント・Touch ID の設定によって異なる。

原因を解消し、現在の処理が終了してから再開する。アプリ導入の途中で別の switch を重ねない。

## Nix の導入で止まる

`nix` が見つからない場合は、新しいターミナルを開き、インストーラの shell 初期化案内を確認する。

既存 Nix や残存パスが検出された場合は、その状態を確認する。bootstrap の再実行や、既存パスの削除・再インストールで押し通さない。

## システム適用が失敗する

| エラー | 対処 |
|---|---|
| `Backup already exists` / `Shell backup stopped` | `/etc/bashrc`・`/etc/zshrc` と対応する `.before-nix-darwin` を確認する。一部だけ退避済みの場合もある。既存退避を上書き・削除しない |
| `Unexpected files in /etc` | エラーの対象と残したい内容を確認する。自動退避は bashrc / zshrc の確認付き処理だけ。他のファイルは個別に扱う |
| `Could not write domain com.apple.universalaccess` | 実行元アプリの[フルディスクアクセス](setup.md#2-ターミナルにフルディスクアクセスを許可する)を確認し、端末を開き直す |
| `brew bundle` の失敗 | 失敗した formula / cask と理由を確認する。無効化された cask は同じ成果物を再適用しても直らない。宣言を直した場合は再ビルドする |
| Hermes が未停止 | [管理関数で停止](apps.md#hermes-を停止更新する)し、停止できたことを確認する |
| その他の衝突 | 該当ファイル・リンク・変更済み範囲を確認する。force や一括退避を使わない |

ログの `Completed` と `System profile` / `current-system` を確認する。profile 登録だけでは適用成功ではない。原因と途中状態を確認できたら、[確認済み成果物の switch](usage.md#ビルドと適用を分ける)から再開する。宣言を変更した場合は新しく build する。

sudo の認証更新で止まった場合も、適用結果を確認してから再認証する。パスワードをスクリプトへ保存しない。

## 設定配置だけ再開する

システム適用が成功し、mise の設定配置だけが未完了の場合に使う。適用自体の失敗をこの手順で飛ばさない。

衝突やタイムアウトの原因を解消してから、通常端末で進める。以下は zsh・fish 共通。

```sh
"/etc/profiles/per-user/$USER/bin/mise" --version
```

`~/dotfiles/mise.toml` の内容を確認して、そのファイルだけを trust する。同じ内容を trust 済みなら最初のコマンドは不要。

```sh
"/etc/profiles/per-user/$USER/bin/mise" trust ~/dotfiles/mise.toml
/usr/bin/python3 -c 'import os, pwd, subprocess; mise = "/etc/profiles/per-user/" + pwd.getpwuid(os.getuid()).pw_name + "/bin/mise"; subprocess.run([mise, "-C", os.path.expanduser("~/dotfiles"), "dot", "apply", "--dry-run"], timeout=60, check=True)'
```

60秒以内に成功し、配置予定に不明な実体・別リンクがなければ適用する。未知のリンクが自動で拒否されるとは限らないため、表示を確認する。失敗・時間超過では先へ進まない。

```sh
"/etc/profiles/per-user/$USER/bin/mise" -C ~/dotfiles dot apply
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

リンク先が `~/dotfiles/config/` の正本なら配置完了。setup の残りを進める場合は、次の[ランタイム導入](#ランタイム導入だけ再開する)へ進む。成功済みの build / switch や shell 退避は繰り返さない。

## ランタイム導入だけ再開する

setup の `Completed` に `link verification` があり、`mise install` で失敗した場合に使う。ダウンロードやコンパイルのエラーを解消してから、通常端末で実行する。zsh・fish 共通。

```sh
"/etc/profiles/per-user/$USER/bin/mise" -C "$HOME" install
```

設定済みの版を導入する。既に導入済みの runtime を強制再インストールする必要はない。成功したら[初回セットアップの fish 切替](setup.md#6-fish-に切り替える)から続ける。切替済みなら[版の確認](setup.md#7-ランタイムを確認する)だけでよい。setup や設定配置はやり直さない。

## fish に切り替わらない

`chsh` が失敗した場合は `/etc/shells` に `/run/current-system/sw/bin/fish` があるか、switch が成功しているかを確認する。`/etc/shells` を手で上書きしない。

変更後も zsh が開く場合は、端末アプリの起動設定を「デフォルトのログインシェル」にする。独自の起動コマンドが設定されていると `chsh` だけでは変わらない。

## .env が見つからない・既存ファイルがある

`cp` は実ファイルを作るだけで、`~/.config/.env` のリンクは作らない。[リンクの作成](secrets.md#2-リンクを作る)へ進む。

`File exists` の場合は `ls -ld "$HOME/.config/.env"` で種類とリンク先を確認する。期待する実ファイルへのリンクなら作成は不要。通常ファイル・ディレクトリ・別リンクなら、内容を保全して扱いを決める。`ln -f` で置き換えない。

## 秘密の読み込みでエージェントが起動しない

[初回設定](secrets.md#初回設定)の実ファイル・リンク・Keychain 登録を確認する。dotenvx の strict モードで読み込むため、ファイルや鍵が欠けていれば起動前に止まる。平文や別の鍵ファイルへの自動切替はない。

値を出力する `env` / `printenv` / `dotenvx get` を診断ログへ貼らない。暗号化ファイルや鍵は削除せず、Keychain のロック状態・アクセス許可を確認する。

## 期待したバージョンが使われない

`type -a` と対象の version 表示で、実行先を確認する。

- Homebrew：formula / cask の提供版を確認する。アプリの版は `flake.lock` では固定されない。
- mise：共通設定の pin と `mise which` を確認する。個別プロジェクトの設定が優先される場合がある。
- Nix：`flake.lock` の固定コミットを確認する。`unstable` でも build のたびに最新版へ更新されるわけではない。

[Nix の依存更新](usage.md#依存を更新する)は同じ input の他の依存も変える。更新先に希望版が含まれるか確認してからビルドする。復元のためだけに更新しない。

## 会社が管理するアプリをスキップする

この Mac の `brew --prefix` 配下の `etc/homebrew/brew.env` に、除外する cask 名を設定する。Zoom の例：

```text
HOMEBREW_BUNDLE_CASK_SKIP=zoom
```

既存ファイルと除外名を保持し、複数名は空白区切りにする。ユーザー別 `brew.env` の同名設定が優先される場合があるため、適用時の skip 表示を確認する。

これは Bundle の導入対象から外す設定で、アプリの削除や組織管理の解除は行わない。マシン固有のファイルを Git / Nix store に入れない。

## 削除したファイルを復元する

Safehouse 内の `rm` は gtrash のごみ箱へ移す。通常端末の `rm` は直接削除なので、この方法では戻せない。通常端末でもごみ箱を使いたい場合は `gtrash put` を使う。

削除操作が終わったら、Safehouse 外の通常端末で実行する。

```sh
gtrash restore
```

TUI の `?` で操作方法を確認する。復元先にデータがある場合は `--restore-to` で別の場所へ戻す。復元・掃除と削除を並行実行しない。

保存先は Finder のごみ箱とは別。HOME volume では既定で `~/.local/share/Trash`、`XDG_DATA_HOME` 指定時はその配下。別 volume ではその volume のごみ箱を使い、利用できなければ失敗する。

以前の gomi データは次で復元する。

```sh
gomi --config "$HOME/.config/gomi/config.yaml" --restore
```

永久削除は復元・バックアップを確認してから行う。

## システムを以前の状態へ戻したい

Nix の旧世代に戻しても、Git 正本の本文・mise のリンク・アプリ・DB・認証・Docker volume がすべて戻るわけではない。Home Manager と mise の所有先が重なる場合は、先にリンクの引渡しも必要になる。

旧世代と現在の変更範囲を確認し、[既存環境の移行・復旧](migration.md)として個別に進める。自動 rollback や一括削除は行わない。
