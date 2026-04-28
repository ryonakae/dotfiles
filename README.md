# dotfiles

Mac を新規購入・OS クリーンインストールした時にやるやつ

## リポジトリを clone

ユーザーのホームディレクトリに clone する

```
$ cd ~/
$ git clone https://github.com/ryonakae/dotfiles.git
$ cd dotfiles
```

## Xcode Command Line Tools と Homebrew のインストール

```
$ sh scripts/install.sh
```

## \*.example ファイルのコピー

`Brewfile.example` `fish.config.example` などを `Brewfile` `fish.config` にリネームしてコピーする

```
$ sh scripts/copy.sh
```

PC によって設定を変えたいものは適宜コメント or コメントアウト解除

## シンボリックリンクの作成

各設定ファイルのシンボリックリンクをホームディレクトリに貼る

```
$ sh scripts/create-symlink.sh
```

## brew bundle の実行

```
$ cd brew
$ brew bundle -v
```

- Brewfile に記述したものがインストールされる
- 管理者パスワード入れる必要がある場合があるのでターミナルをチラ見しておく

### Homebrew でインストールしたやつを優先的に利用する

fish を使うなら `config.fish` 内の `brew shellenv` と `fish_add_path --move` で Homebrew のパスが先頭側に来る。

それでも GUI アプリや他の shell で `/usr/bin` が先に来る警告が出る場合は、`/etc/paths` の順番を入れ替える。

- Apple Silicon: `/opt/homebrew/bin`
- Intel Mac: `/usr/local/bin`

```
/opt/homebrew/bin
/usr/local/bin
/usr/bin
/bin
/usr/sbin
/sbin
```

設定後に `exec fish` またはターミナル再起動で反映される

## fish の設定

### デフォルトの Shell を fish にする

参考：[ログインシェルを fish にしてみる \- Qiita](https://qiita.com/bleru/items/047a4e8ea2afb654d9e1)

```
# /etc/shells の末尾にfishを追記
$ sudo sh -c 'echo $(which fish) >> /etc/shells'

# ユーザのデフォルトシェルを変更
$ which fish
$ chsh -s <which fishで表示されたパス>
```

Shell を再起動で fish がデフォルトになる

### fishfile に書かれたパッケージをインストール

```
$ fisher update
```

### HOMEBREW_GITHUB_API_TOKEN の設定

- https://github.com/settings/tokens にアクセスして、Homebrew 用のトークンを作成 (既にあれば Regenerate)
- トークンを config.fish の HOMEBREW_GITHUB_API_TOKEN の箇所にコピペ

## Vim の設定

### NeoBundle と VimProc のインストール

```
$ mkdir -p ~/.vim/bundle
$ git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
$ git clone https://github.com/Shougo/vimproc ~/.vim/bundle/vimproc
$ cd ~/.vim/bundle/vimproc
$ make -f make_mac.mak
```

### Vim プラグインのインストール

```
$ vim hoge
:NeoBundleInstall
!q
```

## Ruby、Node、Python とか設定する

[mise](https://mise.jdx.dev/) を使う

### PHP を mise で管理する

- [mise を使って複数の PHP バージョンをインストールする \#PHP \- Qiita](https://qiita.com/yuki777/items/8c71f4535e696a2434b3)
- [asdf\+Homebrew で怠惰に PHP の環境を整える](https://zenn.dev/meihei/articles/85f9c235c666f6)

### ディレクトリごとに環境変数を切り替える

[asdf, direnv をやめて mise に移行する](https://blog.sh1ma.dev/articles/20240108_from_asdf_to_mise)

---

## 日々のメンテナンス

[【Homebrew】コマンド一覧 \#homebrew \- Qiita](https://qiita.com/P-man_Brown/items/82b7e2f1e108a72d89f4)

```
# Homebrew 自体を更新
$ brew update

# 更新可能な formula & cask を表示
$ brew outdated

# 他の formula の依存関係としてのみインストールされ不要となったものをアンインストール
$ brew autoremove

# formula や cask のキャッシュを削除
$ brew cleanup

# システムに問題がないかチェック
$ brew doctor
```

---

## Hermes Agent

gateway はホスト（launchd + agent-safehouse）で動かし、hindsight / dashboard / open-webui は `~/.hermes/services/docker-compose.yml` で一括管理する。

### 構成

| コンポーネント | 動作場所 | port | 役割 |
|---|---|---|---|
| gateway | ホスト (launchd + safehouse) | 8642 | Slack / cron / API server |
| hindsight | Docker | 8888 | memory provider (vector DB) |
| dashboard | Docker | 9119 | gateway モニタリング |
| open-webui | Docker | 8787 | ブラウザチャット UI |

open-webui は `/v1/chat/completions` 経由でホスト gateway を叩くので、agent 実行は safehouse 配下に収まる。[hermes-webui](https://github.com/nesquena/hermes-webui) を使わないのは、コンテナ内で agent を独自起動して safehouse の deny ルールを迂回してしまうため。UI として採用しているのは [Open WebUI](https://github.com/open-webui/open-webui)。

### dotfiles で管理するファイル

`config/.hermes/` 以下を `create-symlink.sh` で `~/.hermes/` に配置する。

- `SOUL.md` — エージェント人格定義
- `services/docker-compose.yml` — Docker サービス構成
- `services/.env.example` — docker compose 用 env テンプレート（`API_SERVER_KEY` 等）
- `services/hindsight/config.json` — hindsight クライアント設定
- `services/hindsight/.env.example` — hindsight LLM 設定テンプレート

`.env` 実体は `copy.sh` で `.env.example` から生成し、`.gitignore` 対象。編集は dotfiles 側で行う。

### セットアップ

```sh
# 1. hermes インストール（初回のみ）
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. plist を生成（fish の hermes 関数は safehouse ラッパーなので command で迂回）
command hermes gateway install

# 3. plist の ProgramArguments を safehouse ラッパーに「完全置換」
#    python 起動引数（-m hermes_cli.main gateway run --replace）を全部削除し、
#    wrapper 1 要素だけの array にする:
#      <array>
#        <string>/Users/ryo.nakae/.config/agent-safehouse/safe-hermes-gateway.sh</string>
#      </array>
vim ~/Library/LaunchAgents/ai.hermes.gateway.plist

# 4. API server 有効化（port 8642 で listen するために必須）
echo 'API_SERVER_ENABLED=true' >> ~/.hermes/.env

# 5. dotfiles から .env と symlink を展開
sh scripts/copy.sh
sh scripts/create-symlink.sh

# 6. Docker サービス一括起動
cd ~/.hermes/services && docker compose up -d

# 7. memory provider を hindsight に設定（プロンプトは全て Enter でデフォルト採用）
hermes memory setup

# 8. launchd サービスをロード
hermes-gateway start

# 9. 稼働確認
sleep 30
curl -sf http://localhost:8642/health && echo "gateway OK"
curl -sf http://localhost:8888/health && echo "hindsight OK"
curl -sf http://localhost:8787/ > /dev/null && echo "open-webui OK"
open http://localhost:9119  # dashboard
open http://localhost:8787  # open-webui（初回は admin アカウント作成）
hermes memory status        # Provider: hindsight / Status: available
```

ラッパースクリプトの実体は `config/.config/agent-safehouse/safe-hermes-gateway.sh`。hermes-gateway が git push などで SSH 秘密鍵を使うため、safehouse ポリシーを通じて SSH_AUTH_SOCK 環境変数を引き継いでいる。

### アップデート

`hermes update` は内部で git ssh を使うため agent-safehouse にブロックされる。safehouse を迂回する `command` 経由で実行する。

```sh
command hermes update
hermes-gateway restart
```

### 再実行時の注意

- `hermes gateway install --force` / `hermes gateway start` は plist を再生成するので、実行後はステップ 3 をやり直す
- `hermes gateway setup` の "Install as launchd service?" / "Start it now?" は **No**（plist 再生成される）

### 停止・再起動

`hermes-gateway` 関数（`config/.config/fish/functions/hermes-gateway.fish`）で gateway を、`docker compose` で Docker サービスを操作する。

```sh
hermes-gateway {start|stop|restart|status}      # gateway

cd ~/.hermes/services && docker compose restart # Docker サービスまとめて再起動

# 全部停止
hermes-gateway stop
cd ~/.hermes/services && docker compose down
```

**重要**: `hermes-gateway stop` / `restart` は、launchd の `bootout` を実行する前に `hermes gateway stop` で正規シャットダウンを通します。これは hindsight の vector DB 破損を防ぐためのものです（launchd の SIGTERM/SIGKILL だけではクリーンアップが不完全になる可能性があるため）。

### Open WebUI の初期設定

初回 `http://localhost:8787` にアクセスすると admin アカウント作成を求められる（1 人目のユーザーが admin になる）。ログイン後、モデルドロップダウンに **hermes-agent** が出れば疎通 OK。

接続先は起動時の環境変数 `OPENAI_API_BASE_URL=http://host.docker.internal:8642/v1` で自動設定されるため、Admin Settings での手動設定は不要。変更したい場合は Admin UI か、volume 削除（`docker volume rm services_open-webui`）で初期化する。

### Tailscale serve で外部公開

| サービス | ローカル port |
|---|---|
| open-webui | 8787 |
| dashboard | 9119 |
| hindsight dashboard | 9999 |

```sh
tailscale serve --bg --https=8787 http://127.0.0.1:8787
tailscale serve --bg --https=9119 http://127.0.0.1:9119
tailscale serve --bg --https=9999 http://127.0.0.1:9999
tailscale serve status
```

### Bearer 認証キー（任意）

gateway API を `127.0.0.1` bind だけで使うなら不要。tailscale serve 越しのアクセスに対する多層防御として Bearer key を設定できる。

```sh
# 1. キー生成
openssl rand -hex 32

# 2. 両方の .env に同じ値を書く
#    ~/.hermes/.env               → API_SERVER_KEY=<値>（hermes 側で受理）
#    ~/.hermes/services/.env      → 同じ値（open-webui から送る）

# 3. 反映
hermes-gateway restart
cd ~/.hermes/services && docker compose up -d --force-recreate open-webui
```

### Google Workspace CLI (`gws`) 連携

Hermes Agent に Google Workspace 操作を許すときは、人間用 (`~/.config/gws`) とは別の credential store (`~/.hermes/gws`) を発行する。自律エージェントに人間と同等の権限を渡さないための分離。

`GOOGLE_WORKSPACE_CLI_CONFIG_DIR` / `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND` / `SSL_CERT_FILE` は `hermes.fish` と `safe-hermes-gateway.sh` で sandbox 内側に渡しているので、マシン側の作業は初回ログインだけ。

セットアップ（マシンごとに 1 回）:

1. 初回ログインは sandbox 外の素のターミナルで人間が実行する。

   ```sh
   env GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.hermes/gws" \
       GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
       gws auth login
   ```

2. `hermes-gateway restart` で反映。

以降の token refresh は Hermes 内で完結する。人間が `gws` を直接叩く場合は env を付けずに実行すれば `~/.config/gws/` のフルスコープ credential を使う。

---

## その他

### 各 App の設定

- 各 App の設定は自分でやる
- `Dropbox/App` にアプリの設定を保存したりしているので、適宜インポートなど

### Dock の表示/非表示を早くする

```
$ defaults write com.apple.dock autohide-time-modifier -float 0.15;killall Dock
$ defaults write com.apple.dock autohide-delay -float 0;killall Dock
```

### SSH 鍵を新しい PC に丸ごと移行する

[SSH 鍵を新しい PC に移動させる方法（mac） \#SSH \- Qiita](https://qiita.com/yamaking/items/65da45bd69e616f8f88d)

### Homebrew で使われていないものを検索

[Homebrew で使われていない formula を削除する :: by and for engineers](https://yulii.github.io/brew-cleanup-installed-formulae-20200509.html)

```
$ brew list --formula | xargs -I{} sh -c 'brew uses --installed {} | wc -l | xargs printf "%20s is used by %2d formulae.\n" {}' | grep '0 formula'
```

### PHP を Homebrew でインストール・切り替えする

[Mac で複数のバージョンの PHP を同時に使う \#PHP \- Qiita](https://qiita.com/koriym/items/17662cd9c44c43081bf9)

### SourceTree で push できないとき

[SourceTree で GitHub の Personal access tokens を利用する方法](https://zenn.dev/koushikagawa/articles/3c35e503c8553a)
