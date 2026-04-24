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

hermes gateway（ホスト・launchd）と Docker サービス 3 つ（hindsight / dashboard / open-webui）で構成する。gateway は agent-safehouse 経由でサンドボックス化、Docker サービスは `~/.hermes/services/docker-compose.yml` で一括管理。

### 構成

| コンポーネント | 動作場所 | port | 役割 |
|---|---|---|---|
| gateway | ホスト (launchd + safehouse) | 8642 | Slack / cron / API server |
| hindsight | Docker | 8888 | memory provider (vector DB) |
| dashboard | Docker | 9119 | gateway モニタリング |
| open-webui | Docker | 8787 | ブラウザチャット UI（`/v1/chat/completions` 経由でホスト gateway を叩く。agent 実行は safehouse 内で行われる） |

ブラウザチャット UI に [hermes-webui](https://github.com/nesquena/hermes-webui) を使わない理由は、hermes-webui がコンテナ内で独自に hermes-agent を起動する構造で safehouse の deny ルール（`.env` / 認証系ファイル等）が効かないため。[Open WebUI](https://github.com/open-webui/open-webui) は純粋な UI でホスト gateway の API server を叩くので、agent 実行が safehouse 配下に収まる。

### dotfiles で管理するファイル

`config/.hermes/` 以下にシンボリックリンクで管理（`create-symlink.sh` で配置）:

- `SOUL.md` — エージェント人格定義
- `services/docker-compose.yml` — Docker サービス構成
- `services/.env.example` — docker compose 用の env テンプレート（`API_SERVER_KEY` 等）
- `services/hindsight/config.json` — hindsight クライアント設定
- `services/hindsight/.env.example` — hindsight LLM 設定テンプレート

`.env` 実体は `.gitignore` で除外し、`copy.sh` で `.env.example` から生成する。`create-symlink.sh` が `~/.hermes/services/` に symlink を張るので、編集は dotfiles 側（または symlink 越し）で行う。

**管理しない**（hermes が自動更新 or 機密）: `config.yaml`（クレデンシャル）、`hooks/`, `cron/`, `automations/`, `skills/hermes-custom/`（自己改善で書き換わる）、`memories/`, `sessions/`, `state.db`, `logs/`, `hermes-agent/`, `services/hindsight/data/`, `services/hindsight/codex-auth/`（Docker volume）、認証系全般。

### 前提

- `~/.hermes/` が存在する（hermes 初回インストール済み）
- Docker Desktop が起動している

### セットアップ

```sh
# 1. hermes インストール（初回のみ）
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. plist を生成（fish の hermes 関数は safehouse ラッパーなので command で迂回）
command hermes gateway install

# 3. plist の ProgramArguments を safehouse ラッパーに「完全置換」
#    python 起動引数（-m hermes_cli.main gateway run --replace）は全部削除し、
#    wrapper 1 要素だけの array にする。
#
#      <array>
#        <string>/Users/ryo.nakae/.config/agent-safehouse/safe-hermes-gateway.sh</string>
#      </array>
vim ~/Library/LaunchAgents/ai.hermes.gateway.plist

# 4. .env に API server 有効化を追記（port 8642 で listen するために必須）
echo 'API_SERVER_ENABLED=true' >> ~/.hermes/.env

# 5. dotfiles 側から .env などを展開してシンボリックリンクを配置
#    （.env.example → .env の展開と、SOUL.md / docker-compose.yml / hindsight/* の symlink）
sh scripts/copy.sh
sh scripts/create-symlink.sh

# 6. Docker サービス一括起動（hindsight / dashboard / open-webui）
cd ~/.hermes/services
docker compose up -d

# 7. OpenAI Codex にログイン（provider 認証。期限切れで 300s タイムアウトの原因になる）
codex login

# 8. memory provider を hindsight に設定（プロンプトは全て Enter でデフォルト採用）
hermes memory setup

# 9. launchd サービスをロード
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist

# 10. 稼働確認
sleep 30
curl -sf http://localhost:8642/health && echo "gateway OK"
curl -sf http://localhost:8888/health && echo "hindsight OK"
curl -sf http://localhost:8787/ > /dev/null && echo "open-webui OK"
open http://localhost:9119  # dashboard
open http://localhost:8787  # open-webui（初回は admin アカウント作成）
hermes memory status        # Provider: hindsight / Status: available ✓
```

ラッパースクリプトは `config/.config/agent-safehouse/safe-hermes-gateway.sh`。

### Open WebUI の初期設定

初回 `http://localhost:8787` アクセス時に admin アカウント作成を求められる（1 人目のユーザーが admin になる）。ログイン後、モデルドロップダウンに **hermes-agent** が出てくれば疎通 OK。

接続先はコンテナ起動時の環境変数（`OPENAI_API_BASE_URL=http://host.docker.internal:8642/v1`）で自動設定されるので、Admin Settings からの手動設定は不要。環境変数は**初回起動時のみ**有効なので、後から変えたい場合は Admin UI からか、volume 削除（`docker volume rm services_open-webui`）で初期化。

tailnet 公開している場合、最低限 **Admin Settings → 一般 → 新規登録を有効にする: OFF** を確認すること（他の tailnet ユーザーがサインアップできてしまうのを防ぐ）。

### Bearer 認証キー（任意・defense-in-depth）

gateway API が `127.0.0.1` bind のみなら認証不要だが、tailscale serve 越しのアクセスに対する多層防御として Bearer key を設定できる。

```sh
# 生成
openssl rand -hex 32

# ~/.hermes/.env に追加（hermes 側で受理するキー）
echo "API_SERVER_KEY=<生成した値>" >> ~/.hermes/.env

# ~/.hermes/services/.env に同じ値を設定（open-webui から送るキー）
# 実体は gitignore 対象だが dotfiles 配下にある（symlink 越しに編集可）。
# docker-compose.yml は ${API_SERVER_KEY:-not-needed} で参照する。
# vim ~/.hermes/services/.env

# 反映
launchctl bootout gui/$(id -u)/ai.hermes.gateway
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist
cd ~/.hermes/services && docker compose up -d --force-recreate open-webui
```

未設定 (default `not-needed`) でも 127.0.0.1 bind なら動作するので、導入は任意。

### 再実行時の注意

- `hermes gateway install --force` / `hermes gateway start` は plist を再生成するので、実行後はステップ 3 をやり直す
- `hermes gateway setup` のプロンプトで "Install as launchd service?" や "Start it now?" が出たら **No** を選ぶ（plist 再生成される）
- `codex login` の OAuth セッションは期限付き。gateway が 300 秒タイムアウトで起動しない症状が出たら再ログインする

### 停止・再起動

fish 関数 `hermes-gateway` に `{start|stop|restart|status}` を渡して操作する（`config/.config/fish/functions/hermes-gateway.fish`）。

```sh
hermes-gateway start      # bootstrap
hermes-gateway stop       # bootout
hermes-gateway restart    # bootout → bootstrap
hermes-gateway status     # launchctl print

# Docker サービスまとめて再起動
cd ~/.hermes/services && docker compose restart

# 全部停止
hermes-gateway stop
cd ~/.hermes/services && docker compose down
```

### トラブルシュート

| 症状 | 原因 | 対処 |
|---|---|---|
| `curl http://localhost:8642/health` が fail | `API_SERVER_ENABLED` 未設定 | `.env` に `API_SERVER_ENABLED=true` を追加して再起動 |
| `gateway.log` が「Starting...」バナーで止まる | hindsight コンテナ未起動 | `cd ~/.hermes/services && docker compose up -d` |
| 300 秒タイムアウト（`No response from provider for 300s`） | codex 認証切れ or モデル名が古い | `codex login` / `hermes model` でデフォルトモデル更新 |
| `hermes memory status` が `not available` | hindsight コンテナ未起動 or `hermes memory setup` 未実行 | 上 2 つを実施 |
| `bootstrap failed: 5: Input/output error` | 既にロード済み | 先に `launchctl bootout gui/$(id -u)/ai.hermes.gateway` |
| dashboard コンテナが Restarting ループ | `/opt/data` が `:ro` で mkdir 失敗 | `docker-compose.yml` の dashboard volume を `$HOME/.hermes:/opt/data`（`:ro` なし）に |
| Open WebUI のモデル一覧に `hermes-agent` が出ない | gateway の API server が落ちている or URL 誤り | `curl http://localhost:8642/v1/models` で `hermes-agent` が返るか確認。Admin UI 側は URL が `/v1` まで含まれているか確認 |

### Tailscale serve で外部公開する場合

スマホ・別 PC から tailnet 経由で使えるよう serve する。gateway API は露出させず、UI レイヤーのみ公開する方針。

| サービス | ローカル port | 露出可否 |
|---|---|---|
| open-webui | 8787 | 公開（スマホ等のチャット入口） |
| dashboard | 9119 | 公開（モニタリング） |
| hindsight 管理 UI | 9999 | 任意 |
| gateway API | 8642 | **公開しない**（open-webui が代理） |
| hindsight health | 8888 | 公開しない（内部用）|

```sh
tailscale serve --bg --https=8787 http://127.0.0.1:8787
tailscale serve --bg --https=9119 http://127.0.0.1:9119
tailscale serve --bg --https=9999 http://127.0.0.1:9999

# 確認
tailscale serve status
```

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
