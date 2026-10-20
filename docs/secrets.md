# 環境変数の管理

[README](../README.md) / [日常操作](usage.md) / 環境変数の管理

API キーなどの環境変数は `~/.config/.env` に置き、dotenvx で暗号化する。復号鍵は macOS Keychain に保存し、1Password にバックアップする。

- 初めて準備する：[初回設定](#初回設定)
- 環境変数を追加・変更する：[値の追加・更新](#値を追加更新する)
- 別の Mac へ移す：[バックアップと復元](#バックアップと復元)

プロジェクト・本番環境の秘密、各エージェントの OAuth 認証は、このファイルとは別に管理する。

以下のコマンドは zsh・fish 共通。

## 初回設定

実ファイルは `~/dotfiles/config/.config/.env`、ツールが読むリンクは `~/.config/.env`。どちらも setup / mise では自動作成されない。

以下は新規作成用。暗号化済みファイルを引き継ぐ場合は[復元手順](#バックアップと復元)へ進む。

### 1. ファイルを作る

```sh
cd ~/dotfiles
cp -n config/.config/.env.example config/.config/.env
chmod 600 config/.config/.env
```

新規ファイルをエディタで開き、必要な値を入力する。

### 2. リンクを作る

`~/.config/.env` が未配置の場合だけ実行する。既に配置済みなら作成を飛ばし、下のリンク確認へ進む。

```sh
mkdir -p "$HOME/.config"
ln -s "$HOME/dotfiles/config/.config/.env" "$HOME/.config/.env"
```

作成後に確認する。

```sh
ls -ld "$HOME/.config/.env"
```

`~/.config/.env` → `~/dotfiles/config/.config/.env` のリンクなら次へ進む。別の実体や `File exists` があれば[トラブル対応](troubleshooting.md#env-が見つからない既存ファイルがある)を確認する。

### 3. 暗号化して鍵を登録する

まずファイルを暗号化する。

```sh
dotenvx encrypt --quiet --no-armor -f "$HOME/.config/.env"
```

復号鍵の保存先を聞かれたら、`Local` → `macOS Keychain` を選ぶ。`Password Managers` は選ばない。

成功したら、鍵を Keychain へ移す。

```sh
dotenvx native up --quiet -f "$HOME/.config/.env" -fk "$HOME/.config/.env.keys"
```

値を表示せず、実際の起動処理で読み込めることを確認する。

```sh
"$HOME/.config/agent-safehouse/run-with-agent-env.sh" /usr/bin/true
```

### 4. 鍵を 1Password に控える

別の Mac で復元するために必要。鍵を作り直した場合もやり直す。

1. 1Password に新しいパスワード項目を作る。名前は `dotenvx ~/.config/.env` など、どのファイルの鍵か分かるものにする。
2. 公開鍵を表示し、項目のテキスト欄に貼る。公開鍵は秘密ではない。

   ```sh
   dotenvx keypair DOTENV_PUBLIC_KEY --no-armor -f "$HOME/.config/.env"
   ```

3. Keychain の復号鍵をクリップボードへコピーし、項目のパスワード欄に貼って保存する。

   ```sh
   dotenvx keypair DOTENV_PRIVATE_KEY --no-armor -f "$HOME/.config/.env" | pbcopy
   ```

4. クリップボードを空にする。

   ```sh
   pbcopy < /dev/null
   ```

1Password への保存は `dotenvx 1password` を使わない。

ここまで済めば、[エージェントを起動](setup.md#7-環境変数を準備してエージェントを起動する)できる。

## 値を追加・更新する

`NEW_API_KEY` を追加・更新する環境変数名に置き換える。

```sh
dotenvx set NEW_API_KEY --no-armor --no-create -f "$HOME/dotfiles/config/.config/.env"
```

表示された非表示入力のプロンプトに値を貼り付ける。

`_PLAIN` で終わる名前は暗号化対象外なので、秘密には使わない。

保存が成功したら、[使うプロセスを再起動](#変更を反映する)する。

## 変更を反映する

環境変数は起動時に読み込む。既に動いているプロセスには自動反映されない。

- コーディングエージェントと Hermes CLI：作業を保存して終了し、新しい端末から起動し直す。
- Hermes gateway：稼働中で変更を反映したい場合は、次の管理関数で再起動する。

```fish
hermes-gateway restart
```

`config.fish` や端末で同名の変数を export している場合は、それが `.env` より優先される。不要な旧定義を取り除いてから新しい端末を開く。

## バックアップと復元

暗号化した `.env` は暗号化されたバックアップに含める。復号鍵は[初回設定](#4-鍵を-1password-に控える)で 1Password に控えたものを使う。

### 別の Mac で復元する

1. 暗号化した `.env` を `~/dotfiles/config/.config/.env` に戻し、[リンクを作る](#2-リンクを作る)。既に暗号化済みなので、ひな形のコピーや再暗号化は不要。
2. 1Password の項目から復号鍵をコピーし、Keychain に登録する。表示されたプロンプトに貼り付ける。

   ```sh
   security add-generic-password -U -s dotenvx -a "$(dotenvx keypair DOTENV_PUBLIC_KEY --no-armor -f "$HOME/.config/.env")" -l dotenvx -w
   ```

3. `pbcopy < /dev/null` でクリップボードを空にし、実際の起動処理で読み込めることを確認する。エラーなく終了すれば復元できている。

   ```sh
   "$HOME/.config/agent-safehouse/run-with-agent-env.sh" /usr/bin/true
   ```

起動できない場合は[トラブル対応](troubleshooting.md#秘密の読み込みでエージェントが起動しない)を確認する。
