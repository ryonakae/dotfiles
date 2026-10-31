# アプリ別の設定

[README](../README.md) / アプリ別の設定

必要なアプリの項目だけを使う。

- [T3 Code](#t3-code)
- [Claude Code](#claude-code)
- [Pi](#pi)
- [OpenCode](#opencode)
- [oMLX](#omlx)
- [Hermes](#hermes)
- [CuaDriver](#cuadriver)
- [Cua Spaces](#cua-spaces)
- [Unity CLI](#unity-cli)
- [Karabiner](#karabiner)
- [Hammerspoon](#hammerspoon)
- [macOS とその他のアプリ](#macos-とその他のアプリ)

## T3 Code

エージェントは T3 Code から起動する。worktree・ターミナル・通知も T3 Code の機能を使う。

設定は `~/.t3/userdata/settings.json` を dotfiles で管理する。画面での変更も Git 正本への書き込みになるので、Git 差分を確認する。キーバインドは既定のまま使い、管理しない。

新しいスレッドの権限モードは Auto を既定にしている（**Settings → General → New threads → Permissions**）。Claude は自動承認の分類器、Codex は workspace-write の sandbox と自動レビューで危険な操作を止める。Pi は Auto に対応しないため、Supervised か Full access を選ぶ。

エージェントに渡す API キーは[環境変数の管理](secrets.md#t3-code-のエージェントに渡す)で登録する。

iOS Simulator の Device パネルとエージェントからの操作は全プロジェクトで有効にしている。一覧には一度起動したシミュレーターだけが出るので、新しく作った・入れ直した機種は先に DeviceHub（`open -a DeviceHub`。Xcode 27 に Simulator.app はない）か `xcrun simctl boot <UDID>` で起動する。

Zed は `zed` コマンドが PATH にあれば、T3 Code の「エディタで開く」に表示される。

## Claude Code

dotfiles 管理の MCP 定義 `~/.claude/mcp.json` を読ませるため、T3 Code の **Settings → Providers → Claude** の **Launch arguments** に `--mcp-config` と絶対パスを指定する。`~` は展開されない。

```text
--mcp-config /Users/USER/.claude/mcp.json
```

`USER` はユーザー名に置き換える。ターミナルから起動する場合も `claude --mcp-config ~/.claude/mcp.json` を使う。

## Pi

OpenAI の認証は Pi 内で `/login openai-codex` を実行し、ChatGPT のサブスクリプションでサインインする。

MCP の個人設定は `~/.pi/agent/mcp.json`。OAuth が必要なサーバーは `pi mcp login SERVER` を使う。`SERVER` は設定したサーバー名に置き換える。

Web 検索・ページ取得は `pi-web-access` 拡張が担う。API キーなしで動き、`openai-codex` でサインイン済みなら OpenAI の検索を使う。

本体は Homebrew で更新する。拡張は `config/.pi/agent/settings.json` に版を固定せず列挙し、`pi update --extensions` で更新する。設定・footer の変更は Git 正本への書き込みとなるため、Git 差分を確認する。

## OpenCode

本体は Homebrew、グローバル設定は [config/.config/opencode/opencode.json](../config/.config/opencode/opencode.json) で管理する。`default` 構成で `~/.config/opencode/opencode.json` に配置する。既存リンクの本文変更は再配置不要。

LLM は [oMLX](#omlx) のローカルモデルだけを使う。API キーは環境変数 `OMLX_API_KEY` から読む。

OpenCode は oMLX のモデルを自動検出しない。oMLX でモデルをダウンロードしたら、設定の `providers.omlx.models` にモデル ID・ツール対応・コンテキスト長を追記し、必要なら `model` に既定値を指定する。oMLX のサーバーを起動してから、任意の作業ディレクトリで OpenCode を起動する。

```fish
opencode models
opencode
```

サーバー停止中もモデルは一覧に表示されるが、推論はできない。モデルの取得・起動・停止は OpenCode では行わない。

[プロバイダーポリシー](https://opencode.ai/v2/docs/policies/)で他のプロバイダーを禁止する。MCP などの外部通信はこの制限の対象外。プロジェクト設定で許可済みプロバイダーの接続先やモデル定義を書き換えることまでは防がない。

## oMLX

[公式 Releases](https://github.com/jundot/omlx/releases) の DMG から手動導入し、アプリ内の更新機能で更新する。メニューバーアプリからサーバーの起動・停止を行い、モデルは管理画面 `http://127.0.0.1:8000/admin` でダウンロード・ロードする。Homebrew の Formula 版は併用しない。

サーバーは `127.0.0.1:8000` で待ち受ける。

oMLX の設定は `~/.omlx/settings.json`、モデルの標準保存先は `~/.omlx/models/`。

## Hermes

CLI・gateway は `~/.hermes/.env` の[環境変数](secrets.md#hermes-に渡す)を起動時に読み込む。gateway は Hermes 標準の launchd サービスで動かす。

### 初回設定と起動

環境変数、Hermes の認証・設定を準備する。`openai-codex` を使う場合は `~/.codex` の認証も復元する。

取得元は `ryonakae/hermes-agent` の `ryonakae` ブランチ、配置先は `~/Dev/personal/hermes-agent`。`private` を選択した setup は未導入時だけ導入する。

本体だけを初回導入する場合は、通常端末でルートと Hermes 用の宣言を確認してから実行する。

```fish
mise -C ~/dotfiles -E hermes trust ~/dotfiles/mise.toml
mise -C ~/dotfiles -E hermes trust ~/dotfiles/mise.hermes.toml
mise -C ~/dotfiles -E hermes run hermes:install
```

表示された取得元・revision・導入段階を確認して進める。途中状態や未知の実体で止まった場合は、[Hermes の復旧](troubleshooting.md#hermes-の導入更新が途中で止まった)へ進む。導入処理は gateway を登録しない。

gateway を launchd に登録して起動する。

```fish
hermes gateway install
hermes gateway status
```

以後の起動・停止・再起動は `hermes gateway start|stop|restart` を使う。

### Hermes を停止・更新する

本体更新は全体 setup と分けて行う。利用中の CLI を終了し、gateway が稼働中なら `hermes gateway stop` で先に止める。

```fish
mise -C ~/dotfiles -E hermes run hermes:update
```

対象と表示された revision・段階を確認して進める。

成功後に `git -C ~/Dev/personal/hermes-agent rev-parse HEAD` と CLI の起動を確認する。依存の fallback が表示された場合は警告を確認する。更新のために止めた gateway は `hermes gateway start` で再開する。

### Google Workspace

ユーザー用 `~/.config/gws` とは認証を分け、Hermes 用に必要な権限だけを付与する。

```fish
env GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.hermes/gws" \
    GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
    gws auth login
```

ログインが成功したら、稼働中の gateway を `hermes gateway restart` で再起動する。

## CuaDriver

本体は Homebrew 管理。初回のアクセシビリティ・画面収録の許可と daemon 起動は[公式 Quickstart](https://cua.ai/docs/cua-driver/quickstart)に従う。

## Cua Spaces

`cua` は Cua Spaces アプリ同梱の CLI を使う。アプリの「Install the Cua CLI」でシンボリックリンクとして導入し、アプリの更新に追従させる。`command -v cua` と `cua --version` で利用可能か確認する。アプリ本体の導入・認証は別途行い、`cua agents setup` によるスキル・MCP の自動配置は使わない。

Linux の Space は `cua spaces create ghcr.io/trycua/linux:24.04-slim --kind microvm` で作る。作成後に日本語フォント（`fonts-noto-cjk`）、`ja_JP.UTF-8` ロケール、`Asia/Tokyo` タイムゾーンを設定する。デスクトップはイメージの `LANG` と `TZ` を引き継ぐため、`~/.config/xfce4/xinitrc` で上書きしてから `/etc/xdg/xfce4/xinitrc` を実行する。

`private` 構成では、Space の自動起動と relay への再登録を LaunchAgent で行う。[スクリプト](../config/.local/bin/cua-relay-keepalive.example)と [plist](../config/Library/LaunchAgents/com.ryonakae.cua-relay-keepalive.plist.example) の example を元に、Space ID、`cua spaces relay-register` が返す relay ID、ホームのパスを埋めた実ファイルを `~/.local/bin/`（実行権限付き）と `~/Library/LaunchAgents/` に置き、読み込む。

```fish
launchctl bootstrap gui/(id -u) ~/Library/LaunchAgents/com.ryonakae.cua-relay-keepalive.plist
```

Pi・Claude Code・Codex・OpenCode・Antigravity CLI の MCP 定義は dotfiles 管理。新規ファイルは[設定ファイルの配置](usage.md#設定ファイルを変更する)、公式 `cua-spaces` スキルは[外部 repos の更新と配置](usage.md#外部スキルと-plugin-を更新する)で反映する。

Claude Code は [Launch arguments の `--mcp-config`](#claude-code) で `~/.claude/mcp.json` を読み込む。

Hermes の `~/.hermes/config.yaml` は管理外。既存の設定に次を追加・統合する。

```yaml
mcp_servers:
  cua:
    command: cua
    args: [daemon, mcp, --permissions, "spaces:all"]
skills:
  external_dirs:
    - ~/.agents/skills
```

Hermes は対話セッションの `/reload-mcp` で反映する。

反映後は各エージェントの MCP 一覧に `cua`、スキル一覧に `cua-spaces` があることを確認する。プロジェクト内でも既存の MCP・スキルが残っていることを確認する。

## Unity CLI

本体は `brew upgrade --cask unity-cli` で更新する。公式 installer や `unity self-update` は併用しない。Editor と追加モジュールはプロジェクトに必要な版を CLI / Hub で管理する。

`brew uninstall --zap unity-cli` は使わない。Hub のデータも削除対象になる。[公式の導入方法](https://docs.unity.com/en-us/unity-cli/use-unity-cli#install-with-a-package-manager)と[cask の削除対象](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/u/unity-cli.rb)を参照する。

## Karabiner

設定は `config/.config/karabiner/karabiner.json` を編集する。アプリ側の変更も Git 差分になる。

既存設定がある Mac は、配置前に必要な JSON を保全する。

ディレクトリの配置場所が変わった後は、[公式手順](https://karabiner-elements.pqrs.org/docs/manual/misc/configuration-file-path/)に従って `Karabiner-Console-User-Server` を一度再起動する。再起動までは新しい場所の変更が自動検知されない。

## Hammerspoon

設定は `config/.hammerspoon/init.lua` を編集する。トラックパッドの4本指クリックを `Cmd+W`、3本指クリックをミドルクリック、3本指の左スワイプを `Ctrl+Tab`、右スワイプを `Ctrl+Shift+Tab` に変える。その他のスワイプは macOS の defaults で設定し、[macOS の部分操作](usage.md#macos-設定を適用する)で反映する。

初回起動時に、システム設定の「プライバシーとセキュリティ > アクセシビリティ」で Hammerspoon を許可する。ログイン時の起動は Hammerspoon の Preferences で有効にする。

## macOS とその他のアプリ

mise 管理の設定を GUI で変えても、次の defaults apply で宣言値へ戻る。継続して変える設定は構成別 `mise.<name>.toml` と `scripts/macos-settings.sh` を編集し、[macOS の部分操作](usage.md#macos-設定を適用する)で反映する。

次の項目は自動復元されないため、必要なものだけ手動で準備する。

- Apple Account・iCloud・Touch ID、アクセシビリティ・画面収録・自動化などの許可
- Xcode の SDK / Simulator、署名証明書・provisioning profile、VPN 認証
- Docker の初期設定、volume
- 入力ソース、宣言外の標準ショートカット、アプリ別ショートカット、Karabiner 管理外のデバイス設定、宣言外の電源設定
- Dock に登録した Chrome 製アプリなどの実体
- `Dropbox/App` に保存した、Git 管理外のアプリ設定
