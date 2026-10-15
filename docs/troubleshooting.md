# トラブル対応

[README](../README.md) / トラブル対応

失敗した段階とエラーを確認してから再開する。setup は途中まで変更して止まる場合があり、自動では元に戻らない。別の適用を同時に起動しない。

| 症状 | 読む場所 |
|---|---|
| Xcode・App Store の認証で止まる | [Xcode・App Store](#xcodeapp-store) |
| Nix 管理 Homebrew を検出して止まる | [既存 Nix 環境](#既存-nix-環境で止まる) |
| 権限不足・Homebrew・macOS 設定の失敗 | [setup の失敗](#setup-が失敗する) |
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

原因を解消し、現在の処理が終了してから再開する。アプリ導入の途中で別の setup を重ねない。

## 既存 Nix 環境で止まる

Nix 管理 Homebrew や旧 Home Manager 所有リンクがある場合は、[移行手順](migration.md)で対象を確認して引き渡す。通常 setup の再実行や force で押し通さない。Homebrew 全体を uninstall しない。

## setup が失敗する

ログの `Setup stopped at` と `Completed`、終了コードを確認する。失敗段階にも一部変更が残る場合がある。原因と途中状態を確認してから、標準コマンドで必要な部分だけ再開する。

| エラー | 対処 |
|---|---|
| `Could not write domain com.apple.universalaccess` | 実行元アプリの[フルディスクアクセス](setup.md#2-ターミナルにフルディスクアクセスを許可する)を確認し、端末を開き直す |
| `brew bundle` の失敗 | 失敗した formula / cask と理由を確認する。無効化された cask は Brewfile を直し、失敗した構成だけ `brew bundle` を再開する |
| repos の dirty / origin 不一致 | 対象 checkout の変更と取得元を確認する。変更を捨てず、独自 updater や別 checkout を重ねない |
| plist の衝突・手動変更 | 実配置と生成結果・所有元を確認する。旧 HM 由来なら移行として引き渡す。自動上書きしない |
| macOS / 電源設定の失敗 | 変更済みの対象キー・構成を確認し、[macOS の部分操作](usage.md#macos-設定を適用する)を使う。ハードウェア非対応を成功扱いしない |
| その他の衝突 | 該当ファイル・リンク・変更済み範囲を確認する。force や一括退避を使わない |

sudo の認証更新で止まった場合も、進行中の操作結果を確認してから再認証する。パスワードをスクリプトへ保存しない。成功済みの全体 setup を無条件に繰り返さない。

## 設定配置だけ再開する

選択したアプリ・repos の準備が済み、mise の配置が未完了の場合に使う。外部の配置元がまだなければ、先に[repos の取得・更新](usage.md#外部スキルと-plugin-を更新する)を行う。

衝突や timeout の原因を解消してから通常端末で進める。以下は家用の例。ルートと選択構成の宣言を確認して、それらだけを trust する。同じ内容を trust 済みなら不要。

```fish
/opt/homebrew/bin/mise trust ~/dotfiles/mise.toml
/opt/homebrew/bin/mise trust ~/dotfiles/mise.default.toml
/opt/homebrew/bin/mise trust ~/dotfiles/mise.private.toml
/usr/bin/python3 -c 'import os, subprocess; subprocess.run(["/opt/homebrew/bin/mise", "-C", os.path.expanduser("~/dotfiles"), "-E", "default,private", "dot", "apply", "--dry-run"], timeout=60, check=True)'
```

60秒以内に成功し、配置予定に不明な実体・別リンクがなければ適用する。未知のリンクが自動拒否されるとは限らないため表示を確認する。失敗・時間超過では先へ進まない。

```fish
/opt/homebrew/bin/mise -C ~/dotfiles -E default,private dot apply
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

リンク先が `~/dotfiles/config/` の正本なら配置完了。必要なら[ランタイム導入](#ランタイム導入だけ再開する)へ進む。成功済みのアプリ更新・repos 更新を繰り返す必要はない。

## ランタイム導入だけ再開する

setup の `Completed` に `link verification` があり、共通 runtime 導入で失敗した場合に使う。ダウンロードやコンパイルのエラーを解消してから、通常端末で必要な runtime を指定する。

```fish
env MISE_ENV= /opt/homebrew/bin/mise -C ~ install node python ruby bun aqua:aws/aws-cli
```

設定済みの版を導入する。既に導入済みの runtime を強制再インストールする必要はない。成功したら[初回セットアップの fish 切替](setup.md#6-fish-に切り替える)から続ける。切替済みなら[版の確認](setup.md#7-ランタイムを確認する)だけでよい。setup や設定配置はやり直さない。

## fish に切り替わらない

`chsh` が失敗した場合は `/opt/homebrew/bin/fish` の導入と `/etc/shells` の登録を確認する。[初回の登録手順](setup.md#6-fish-に切り替える)を使い、`/etc/shells` を一括上書きしない。

変更後も zsh が開く場合は、端末アプリの起動設定を「デフォルトのログインシェル」にする。独自の起動コマンドが設定されていると `chsh` だけでは変わらない。

## .env が見つからない・既存ファイルがある

`cp` は実ファイルを作るだけで、`~/.config/.env` のリンクは作らない。[リンクの作成](secrets.md#2-リンクを作る)へ進む。

`File exists` の場合は `ls -ld "$HOME/.config/.env"` で種類とリンク先を確認する。期待する実ファイルへのリンクなら作成は不要。通常ファイル・ディレクトリ・別リンクなら、内容を保全して扱いを決める。`ln -f` で置き換えない。

## 秘密の読み込みでエージェントが起動しない

[初回設定](secrets.md#初回設定)の実ファイル・リンク・Keychain 登録を確認する。dotenvx の strict モードで読み込むため、ファイルや鍵が欠けていれば起動前に止まる。平文や別の鍵ファイルへの自動切替はない。

値を出力する `env` / `printenv` / `dotenvx get` を診断ログへ貼らない。暗号化ファイルや鍵は削除せず、Keychain のロック状態・アクセス許可を確認する。

## 期待したバージョンが使われない

`type -a` と対象の version 表示で、実行先を確認する。

- Homebrew：formula / cask の提供版と実際の解決先を確認する。Brewfile は全依存の版固定ではない。
- mise：共通設定の exact pin と `mise which` を確認する。個別プロジェクトの設定が優先される場合がある。
- Hermes：指定 Git tool のインストール先を `mise where` で確認する。別の `hermes` が PATH で先に選ばれていないか確認する。
- 移行中：旧 Nix の PATH・リンク・稼働プロセスが残っていないか、対象限定で確認する。

上流最新版、管理元の提供版、導入済み版を区別する。復元のためだけに包括的な更新を実行しない。

## 会社が管理するアプリをスキップする

この Mac の `brew --prefix` 配下の `etc/homebrew/brew.env` に、除外する cask 名を設定する。Zoom の例：

```text
HOMEBREW_BUNDLE_CASK_SKIP=zoom
```

既存ファイルと除外名を保持し、複数名は空白区切りにする。ユーザー別 `brew.env` の同名設定が優先される場合があるため、適用時の skip 表示を確認する。

これは Bundle の導入対象から外す設定で、アプリの削除や組織管理の解除は行わない。マシン固有のファイルを Git に入れない。

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
