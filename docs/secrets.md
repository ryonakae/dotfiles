# 共通 API キーを管理する

[README](../README.md) / [日常操作](usage.md) / 共通 API キー

共通ツール用の API キーは dotenvx で暗号化し、復号鍵は macOS Keychain に保存する。

- 初めて準備する：[初回設定](#初回設定)
- キーを追加・変更する：[値の追加・更新](#値を追加更新する)
- 別の Mac へ移す：[バックアップと復元](#バックアップと復元)

秘密の操作はユーザーが通常端末で行う。値や鍵をチャット・ログ・Git に貼らない。プロジェクト・本番環境の秘密、各エージェントの OAuth 認証は、このファイルとは別に管理する。

以下のコマンドは zsh・fish 共通。

## 値を追加・更新する

初回設定が済んでいる場合は、この操作だけでよい。`NEW_API_KEY` を追加・更新する環境変数名に置き換える。

```sh
dotenvx set NEW_API_KEY --no-armor --no-create -f "$HOME/dotfiles/config/.config/.env"
```

表示された非表示入力のプロンプトに値を貼り付ける。値をコマンドの引数に書くとシェル履歴に残るので、変数名だけを指定する。

新しい名前なら追加、既存の名前なら更新される。値は暗号化して保存される。`--plain` は付けない。`_PLAIN` で終わる名前も暗号化対象外なので、秘密には使わない。

既存の公開鍵を使う通常の追加・更新では、Keychain への鍵登録はやり直さない。保存が成功したら、[使うプロセスを再起動](#変更を反映する)する。mise apply は不要。

## 初回設定

実ファイルは `~/dotfiles/config/.config/.env`、ツールが読むリンクは `~/.config/.env`。どちらも setup / mise では自動作成されない。

以下は新規作成用。既存の `.env` がある場合はコピーせず使い、暗号化済みファイルを引き継ぐ場合は[復元手順](#バックアップと復元)へ進む。既存のディレクトリや別リンクを上書きしない。

### 1. ファイルを作る

```sh
cd ~/dotfiles
cp -n config/.config/.env.example config/.config/.env
chmod 600 config/.config/.env
```

新規ファイルをエディタで開き、必要な値を入力する。`cp -n` は既存ファイルを上書きしない。コピーの失敗表示が出た場合は、ファイルの有無を確認し、上書きし直さない。

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

`~/.config/.env` → `~/dotfiles/config/.config/.env` のリンクなら次へ進む。別の実体や `File exists` があれば、削除・強制置換せず[トラブル対応](troubleshooting.md#env-が見つからない既存ファイルがある)を確認する。

### 3. 暗号化して鍵を登録する

まずファイルを暗号化する。

```sh
dotenvx encrypt --quiet --no-armor -f "$HOME/.config/.env"
```

成功したら復号鍵を Keychain に保存する。

```sh
dotenvx native up --quiet -f "$HOME/.config/.env" -fk "$HOME/.config/.env.keys"
```

保存結果を確認する。鍵ファイルが残る場合や保存エラーがある場合は、解消してから進む。起動処理は `.env.keys` へ自動で切り替わらない。

値を表示せず、実際の起動処理で読み込めることを確認する。

```sh
"$HOME/.config/agent-safehouse/run-with-agent-env.sh" /usr/bin/true
```

エラーなく終了すれば、[エージェントを起動](setup.md#7-共通-api-キーを準備してエージェントを起動する)できる。

## 変更を反映する

環境変数は起動時に読み込む。既に動いているプロセスには自動反映されない。

- コーディングエージェントと Hermes CLI：作業を保存して終了し、新しい端末から起動し直す。
- Hermes gateway / dashboard：稼働中で変更を反映したいサービスだけ、次の管理関数で再起動する。

```fish
hermes-gateway restart
hermes-dashboard restart
```

失敗した場合は再試行を重ねず状態を確認する。常駐サービスでの Keychain 利用は、ロック状態・アクセス許可も実機で確認する。

`config.fish` や端末で同名の変数を export している場合は、それが `.env` より優先される。不要な旧定義を取り除いてから新しい端末を開く。

## バックアップと復元

暗号化した `.env` と login Keychain の両方を、暗号化されたバックアップに含める。暗号化ファイルだけでは復号できない。

別の Mac では実ファイルと対応する鍵を復元し、[リンクの作成](#2-リンクを作る)と[読み込みの確認](#3-暗号化して鍵を登録する)を行う。既に暗号化済みなら、ひな形のコピーや再暗号化は不要。鍵の復元は Keychain の正規手順で行う。

起動できない場合も、暗号化 `.env` や Keychain 項目を削除しない。[トラブル対応](troubleshooting.md#秘密の読み込みでエージェントが起動しない)を確認する。
