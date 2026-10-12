# 新しい Mac に導入する

[README](../README.md) / 初回セットアップ

Apple Silicon Mac の標準「ターミナル」と zsh で始める。エージェントは不要。各コマンドが成功してから次へ進む。

導入済みの Mac は[日常操作](usage.md)、古い Home Manager 構成からの切替は[既存環境の移行](migration.md)を使う。

## 1. App Store と Xcode を準備する

1. App Store に Apple Account でサインインし、規約・購入の確認を済ませる。
2. App Store から Xcode をインストールする。
3. Xcode を起動し、ライセンス同意と初期設定を終える。
4. ターミナルで開発ツールを確認する。

```sh
xcode-select -p
xcrun --find clang
git --version
/usr/bin/python3 --version
```

すべて応答すれば次へ進む。CLT 未導入やライセンスのエラーは[トラブル対応](troubleshooting.md#xcodeapp-store)を参照する。

## 2. ターミナルにフルディスクアクセスを許可する

システム設定の「プライバシーとセキュリティ → フルディスクアクセス」で「ターミナル」を許可し、ターミナルを完全終了して開き直す。

この権限は保護されたデータへの広いアクセスを許す。今回の macOS 設定の書き込みに必要で、sudo では代用できない。別の端末アプリを使う場合は、そのアプリを許可する。

以降の導入操作も、Safehouse やエージェント内ではなく、この通常端末で行う。

## 3. dotfiles を取得する

```sh
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

取得済みなら clone せず `cd ~/dotfiles` だけを実行する。

家用 Mac は `private`、共通設定だけなら `default` を使う。以降の例は家用。共通構成では `--configuration private` を省く。

```sh
id -un
printf '%s\n' "$HOME"
```

出力と[ホスト定義](../nix/hosts/default.nix)のユーザー名・ホームパスが一致することを確認する。異なる場合は、適用前にホスト定義を直す。`private` も同じホスト定義を使う。

## 4. Nix を導入する

Nix が未導入の場合だけ実行する。Nix の volume・daemon・shell 初期化が変更される。

```sh
bash scripts/bootstrap-nix.sh --install
```

完了後、新しいターミナルを開く。

```sh
nix --version
cd ~/dotfiles
```

版が表示されれば次へ進む。Homebrew は次の手順で入るため、別途インストールしない。既存 Nix や残存パスのエラーでは、削除・再インストールせず[トラブル対応](troubleshooting.md#nix-の導入で止まる)を確認する。

## 5. アプリと設定を導入する

```sh
bash scripts/dotfiles.sh setup --configuration private
```

ビルド、システム適用、設定配置を順に行う。全体を sudo で起動せず、表示された確認に応答する。

| 表示された確認 | 進めてよい条件 | 入力 |
|---|---|---|
| システムの適用 | 対象ユーザー・成果物・適用先が正しい | `switch` |
| shell ファイルの退避（必要な場合） | 表示された既存設定を退避してよい | `backup` |
| mise 設定の信頼 | 表示された `~/dotfiles/mise.toml` の内容を確認した | `trust` |
| リンクの配置 | 配置予定に不明なファイルや衝突がない | `apply` |

分からない内容があれば承認せず止める。既存ファイルを `--force` で上書きしない。Karabiner に既存設定がある場合は、配置前に[Karabiner の移行](apps.md#karabiner)を確認する。

sudo のパスワードは端末のプロンプトへ入力する。適用中は認証キャッシュを維持するが、会社のポリシーによっては再入力が必要。App Store の認証は別なので、アプリ導入中は App Store の確認画面も見る。

終了まで別の setup / switch を起動せず、設定配置が終わるまで今の zsh を閉じない。終了直後に確認する。

```zsh
echo $?
ls -ld /run/current-system /nix/var/nix/profiles/system
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

終了コードが `0` で、ログに失敗がなく、設定リンクが `~/dotfiles/config/` を指していれば次へ進む。途中で止まった場合は[トラブル対応](troubleshooting.md)。適用成功後に配置だけ失敗した場合は、[配置だけ再開](troubleshooting.md#設定配置だけ再開する)する。

## 6. fish に切り替える

現在の zsh から fish を起動する。

```sh
/run/current-system/sw/bin/fish
```

設定の読み込みにエラーがなければ、ログインシェルとして登録されていることを確認する。

```fish
grep -Fx /run/current-system/sw/bin/fish /etc/shells
```

パスが表示されたら、ログインシェルを変更する。

```fish
chsh -s /run/current-system/sw/bin/fish
```

今の端末を残して新しいターミナルを開き、fish が起動することを確認する。

```fish
status is-login
echo $status
```

`0` なら完了。この切替は一度だけでよい。失敗した場合は[fish の切替](troubleshooting.md#fish-に切り替わらない)を確認する。

## 7. ランタイムを導入する

新しい fish の端末で実行する。

```fish
cd ~
mise install
node --version
python --version
ruby --version
bun --version
```

[共通ランタイム設定](../config/.config/mise/config.base.toml)の指定版が使えれば完了。

## 8. 共通 API キーを準備してエージェントを起動する

[共通 API キーの初回設定](secrets.md#初回設定)を済ませる。別の Mac から引き継ぐ場合は、同ページの[バックアップと復元](secrets.md#バックアップと復元)を使う。

準備後、使うエージェントを起動する。Pi の例：

```fish
cd ~/dotfiles
type pi
pi
```

`type pi` が fish 関数を示し、Safehouse 経由で画面が開けば導入完了。各エージェントへのログインは別途行う。[アプリ別の設定](apps.md)を参照する。

導入後の設定変更や更新は[日常操作](usage.md)から行う。
