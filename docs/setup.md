# 新しい Mac に導入する

[README](../README.md) / 初回セットアップ

Apple Silicon Mac の標準「ターミナル」と zsh で始める。エージェントは不要。各コマンドが成功してから次へ進む。

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

CLT が未導入なら `xcode-select --install` で導入する。CLT だけでは Xcode の初期設定は済まない。認証やライセンスのエラーは[トラブル対応](troubleshooting.md#xcodeapp-store)を参照する。

### Git のコミット情報を設定する

コミットする前に、名前とメールアドレスをこの Mac で設定する。setup では設定されない。通常端末で以下の例を自分の情報に置き換える。GitHub に紐づける場合は、登録済みメールアドレスか GitHub のメール設定に表示される `noreply` アドレスを使う。

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

設定はホーム側に保存し、dotfiles の管理対象には加えない。作業リポジトリ内で実際に使われる情報を確認する。

```sh
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

リポジトリ固有の設定や環境変数で上書きされる場合がある。変更は今後のコミットに使われ、既存履歴は変わらない。

## 2. ターミナルにフルディスクアクセスを許可する

システム設定の「プライバシーとセキュリティ → フルディスクアクセス」で「ターミナル」を許可し、完全終了して開き直す。

この権限は保護されたデータへの広いアクセスを許す。今回の macOS 設定の書き込みに必要で、sudo では代用できない。別の端末アプリを使う場合は、そのアプリを許可する。

以降の導入操作も、Safehouse やエージェント内ではなく、この通常端末で行う。

## 3. dotfiles を取得する

```sh
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

取得済みなら clone せず `cd ~/dotfiles` だけを実行する。

適用する構成は毎回すべて明示する。家用は `default private`、仕事用は `default work`、共通設定だけなら `default`。`private` / `work` 単独も指定できるが、共通アプリ・リンク・runtime・macOS 設定は自動追加されない。

```sh
id -un
printf '%s\n' "$HOME"
```

setup が表示する対象ユーザー・HOME と一致することを確認する。異なる場合は、適用前に [setup 入口](../scripts/dotfiles.py)の対象定義を変更する。秘密や認証は定義に加えない。

## 4. 導入対象を確認する

[共通 Brewfile](../brew/Brewfile.default)と、[家用](../brew/Brewfile.private)または[仕事用](../brew/Brewfile.work)の追加分を確認する。setup は不足分の導入に加えて、選択したアプリを更新する。自動削除はしない。

macOS 設定は [mise.default.toml](../mise.default.toml)などの構成別宣言と[電源設定の補完](../scripts/macos-settings.sh)を確認し、変更対象だけ現在の値・型・未設定状態を控える。宣言を戻すだけでは、以前の設定に戻らない。

`work` の電源設定は Mac ノート向け。「バッテリー使用時のビデオストリーミングを最適化」は自動設定に含めていないため、システム設定の「バッテリー」でオンにする。

新規 Mac では setup が確認のうえで Homebrew と必要な基盤を導入する。Homebrew の初回導入後、既に開いている端末では `brew` が見つからない。setup 中に別の端末で使う場合は、新しいウインドウを開くか `/opt/homebrew/bin/brew` を使う。

## 5. アプリと設定を導入する

家用の例：

```sh
bash scripts/dotfiles.sh setup default private
```

選択した Brewfile、外部リポジトリ、設定リンク、共通 runtime、Herdr のプラグイン、未導入の Hermes、macOS 設定、ログインシェルを順に適用する。共通 runtime・Herdr のプラグイン・fish へのログインシェル変更は `default`、Hermes の導入は `private` を選択した場合だけ。Hermes の導入は `default` が配置する fish 設定を前提にするため、`default` を一度も適用していない環境で `private` 単独の setup を実行すると Hermes の段階で止まる。導入済みの Hermes 本体と Herdr のプラグインは更新しない。

全体を sudo で起動せず、表示された対象と確認に応答する。確認語の入力は2回。

| 表示された確認 | 進めてよい条件 | 入力 |
|---|---|---|
| 全体 setup | 対象ユーザー・checkout・構成・更新範囲、Homebrew の導入（未導入時）、信頼する mise 宣言の全文、電源設定・ログインシェル・Herdr・Hermes の対象が正しい | `setup` |
| リンクの配置 | dry-run の配置予定に不明なファイルや衝突がない | `apply` |

ほかに止まるのは、パスワードの入力と、導入済みの Hermes で起動定義（plist）に差分がある場合の `y` だけ。分からない内容があれば承認せず止める。既存ファイルを `--force` で上書きしない。Karabiner に既存設定がある場合は、配置前に[Karabiner の手順](apps.md#karabiner)を確認する。

sudo のパスワードは端末のプロンプトへ入力する。必要な処理中だけ認証キャッシュを維持するが、アプリの導入中にキャッシュが失効したり、会社のポリシーによっては再入力が必要。`sudo cache refresh failed` と表示されても setup は続くので、求められたらパスワードを入力する。ログインシェルの変更（`chsh`）も別にパスワードを求める場合がある。App Store やベンダーの認証は別操作で、入力1回を保証しない。

終了まで別の setup を起動せず、設定配置が終わるまで今の zsh を閉じない。終了直後に確認する。

```zsh
echo $?
ls -l ~/.config/fish/config.fish ~/.config/mise/config.toml
```

終了コードが `0` で、`Setup complete:` が表示され、設定リンクが `~/dotfiles/config/` を指していれば次へ進む。setup はサービスや Dock、端末を自動再起動しない。途中で止まった場合は[トラブル対応](troubleshooting.md)で成功済み段階を確認し、必要な部分だけ再開する。

## 6. Mac を再起動する

作業を保存して Mac を再起動する。Dock の並びなどの macOS 設定と、新しいログインシェルは再起動後に反映される。

再起動後にターミナルを開き、fish が起動して Dock が[宣言](../mise.default.toml)どおりに並んでいれば完了。fish にならない場合は[fish の切替](troubleshooting.md#fish-に切り替わらない)を確認する。

## 7. 共通 API キーを準備してエージェントを起動する

[共通 API キーの初回設定](secrets.md#初回設定)を済ませる。別の Mac から引き継ぐ場合は、同ページの[バックアップと復元](secrets.md#バックアップと復元)を使う。

準備後、使うエージェントを起動する。Pi の例：

```fish
cd ~/dotfiles
type pi
pi
```

`type pi` が fish 関数を示し、Safehouse 経由で画面が開けば導入完了。各エージェントへのログイン、Apple Account、権限、秘密の復元は別操作。[アプリ別の設定](apps.md)を参照する。

導入後の設定変更や更新は[日常操作](usage.md)から行う。
