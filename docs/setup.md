# 新しい Mac に導入する

[README](../README.md) / 初回セットアップ

Apple Silicon Mac の標準「ターミナル」と zsh で始める。各コマンドが成功してから次へ進む。

導入済みの Mac は[日常操作](usage.md)を使う。

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

CLT が未導入なら `xcode-select --install` で導入する。認証やライセンスのエラーは[トラブル対応](troubleshooting.md#xcodeapp-store)を参照する。

### Git のコミット情報を設定する

コミットする前に、名前とメールアドレスをこの Mac で設定する。setup では設定されない。通常端末で以下の例を自分の情報に置き換える。GitHub に紐づける場合は、登録済みメールアドレスか GitHub のメール設定に表示される `noreply` アドレスを使う。

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 2. ターミナルにフルディスクアクセスを許可する

システム設定の「プライバシーとセキュリティ → フルディスクアクセス」で「ターミナル」を許可し、完全終了して開き直す。

別の端末アプリを使う場合は、そのアプリを許可する。

## 3. dotfiles を取得する

```sh
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

適用する構成は毎回すべて明示する。家用は `default private`、仕事用は `default work`、共通設定だけなら `default`。

## 4. 導入対象を確認する

[共通 Brewfile](../brew/Brewfile.default)と、[家用](../brew/Brewfile.private)または[仕事用](../brew/Brewfile.work)の追加分を確認する。setup は不足分の導入に加えて、選択したアプリを更新する。

macOS 設定は [mise.default.toml](../mise.default.toml)などの構成別宣言と[電源設定の補完](../scripts/macos-settings.sh)を確認する。

`work` の電源設定は Mac ノート向け。「バッテリー使用時のビデオストリーミングを最適化」は自動設定に含めていないため、システム設定の「バッテリー」でオンにする。

新規 Mac では setup が確認のうえで Homebrew と必要な基盤を導入する。

## 5. アプリと設定を導入する

家用の例：

```sh
bash scripts/dotfiles.sh setup default private
```

選択した Brewfile、外部リポジトリ、設定リンク、共通 runtime、Herdr のプラグイン、未導入の Hermes、macOS 設定、ログインシェルを順に適用する。共通 runtime・Herdr のプラグイン・fish へのログインシェル変更は `default`、Hermes の導入は `private` を選択した場合だけ。

表示された対象と確認に応答する。

| 表示された確認 | 進めてよい条件 | 入力 |
|---|---|---|
| 全体 setup | 対象ユーザー・checkout・構成・更新範囲、Homebrew の導入（未導入時）、信頼する mise 宣言の全文、電源設定・ログインシェル・Herdr・Hermes の対象が正しい | `setup` |
| リンクの配置 | dry-run の配置予定に不明なファイルや衝突がない | `apply` |

ほかに止まるのは、パスワードの入力と、導入済みの Hermes で起動定義（plist）に差分がある場合の `y` だけ。Karabiner に既存設定がある場合は、配置前に[Karabiner の手順](apps.md#karabiner)を確認する。

sudo のパスワードは端末のプロンプトへ入力する。アプリの導入中や会社のポリシーによっては再入力が必要。`sudo cache refresh failed` と表示されても setup は続くので、求められたらパスワードを入力する。ログインシェルの変更（`chsh`）も別にパスワードを求める場合がある。

終了直後に確認する。

```zsh
echo $?
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

終了コードが `0` で、`Setup complete:` が表示され、設定リンクが `~/dotfiles/config/` を指していれば次へ進む。途中で止まった場合は[トラブル対応](troubleshooting.md)で成功済み段階を確認し、必要な部分だけ再開する。

## 6. Mac を再起動する

作業を保存して Mac を再起動する。Dock の並びなどの macOS 設定と、新しいログインシェルは再起動後に反映される。

再起動後にターミナルを開き、fish が起動して Dock が[宣言](../mise.default.toml)どおりに並んでいれば完了。fish にならない場合は[fish の切替](troubleshooting.md#fish-に切り替わらない)を確認する。

## 7. 環境変数を準備してエージェントを起動する

[環境変数の初回設定](secrets.md#初回設定)を済ませる。別の Mac から引き継ぐ場合は、同ページの[バックアップと復元](secrets.md#バックアップと復元)を使う。

準備後、使うエージェントを起動する。Pi の例：

```fish
cd ~/dotfiles
type pi
pi
```

`type pi` が fish 関数を示し、Safehouse 経由で画面が開けば導入完了。各エージェントへのログイン、Apple Account、権限は別操作。[アプリ別の設定](apps.md)を参照する。
