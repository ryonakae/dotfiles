# アプリ別の設定

[README](../README.md) / アプリ別の設定

必要なアプリの項目だけを使う。

- [Claude Code](#claude-code)
- [Pi](#pi)
- [oMLX](#omlx)
- [Hermes](#hermes)
- [Herdr](#herdr)
- [CuaDriver](#cuadriver)
- [Cua Spaces](#cua-spaces)
- [Unity CLI](#unity-cli)
- [Karabiner](#karabiner)
- [macOS とその他のアプリ](#macos-とその他のアプリ)

## Claude Code

Herdr の Claude hook を使う場合は、Homebrew 版 Herdr の標準 installer で登録する。

```fish
herdr integration install claude
```

この操作は Claude の settings を変更する。実行前後の Git 差分を確認し、既存の設定を保持する。

statusline の初回取得には npm registry への接続が必要。

## Pi

OpenAI の認証は Pi 内で `/login openai` を実行し、`Sign in with ChatGPT` を選ぶ。

MCP の個人設定は `~/.pi/agent/mcp.json`。OAuth が必要なサーバーは `pi mcp login SERVER` を使う。`SERVER` は設定したサーバー名に置き換える。

本体は Homebrew で更新する。拡張の版指定は `config/.pi/agent/settings.json` で管理する。設定・footer の変更は Git 正本への書き込みとなるため、Git 差分を確認する。

### ローカルモデル用の作業場所

`~/Dev/local` とその配下では、mise が `PI_CODING_AGENT_DIR` を `~/Dev/local/.pi` に切り替える。通常の `pi` コマンドを使い、LFM2.5 または Qwen3.6 を oMLX 経由で選択する。

`~/Dev/local/mise.toml` と `.pi/` はマシン上の実ファイルで、dotfiles では管理・復元しない。既存設定を変更した場合は、通常の fish で mise 設定を trust する。

```fish
mise trust ~/Dev/local/mise.toml
cd ~/Dev/local
```

次のプロンプトが表示されたら、設定元を確認して起動する。

```fish
printf '%s\n' $PI_CODING_AGENT_DIR
pi
```

設定元が `~/Dev/local/.pi` の絶対パスになっていればよい。

mise のプロンプトフックが動かない非対話起動では、対象ディレクトリで `mise exec -- fish -c 'pi'` を使い、通常の Safehouse 起動関数を通す。

## oMLX

[公式 Releases](https://github.com/jundot/omlx/releases) の DMG から手動導入し、アプリ内の更新機能で更新する。メニューバーアプリからサーバーの起動・停止を行い、モデルは管理画面 `http://127.0.0.1:8000/admin` でダウンロード・ロードする。Homebrew の Formula 版は併用しない。

サーバーは `127.0.0.1:8000` で待ち受け、API キー認証を使う。発行したキーは[環境変数の追加手順](secrets.md#値を追加更新する)で `OMLX_API_KEY` として登録する。

Pi の[ローカルモデル用の作業場所](#ローカルモデル用の作業場所)で使用する。モデル定義は `~/Dev/local/.pi/models.json`。

oMLX の設定は `~/.omlx/settings.json`、モデルの標準保存先は `~/.omlx/models/`。

## Hermes

CLI・gateway・dashboard は[環境変数](secrets.md)を起動時に読み込む。

gateway / dashboard はホストの launchd で動かす。同じ `~/.hermes` を使う Docker dashboard を同時起動しない。

### 初回設定と起動

環境変数、Hermes の認証・設定を準備する。`openai-codex` を使う場合は `~/.codex` の認証も復元する。

取得元は `ryonakae/hermes-agent` の `ryonakae` ブランチ、配置先は `~/Dev/private/hermes-agent`。`private` を選択した setup は未導入時だけ導入する。

本体だけを初回導入する場合は、通常端末でルートと Hermes 用の宣言を確認してから実行する。

```fish
mise -C ~/dotfiles -E hermes trust ~/dotfiles/mise.toml
mise -C ~/dotfiles -E hermes trust ~/dotfiles/mise.hermes.toml
mise -C ~/dotfiles -E hermes run hermes:install
```

表示された取得元・revision・導入段階を確認して進める。途中状態や未知の実体で止まった場合は、[Hermes の復旧](troubleshooting.md#hermes-の導入更新が途中で止まった)へ進む。

Hermes の setup でサービス導入・即時起動を聞かれたら No を選ぶ。

起動定義だけを再配置する場合は、通常端末から引数なしで実行する。

```fish
/usr/bin/python3 ~/dotfiles/scripts/hermes_plists.py
```

同一なら無変更。初回作成・差分置換は表示を確認して `y` を入力する。

起動・停止・再起動は、対象ユーザーの `gui/<UID>` ドメインで行う。macOS にそのユーザーがログイン済みで、操作する端末から対象ドメインへアクセスできる必要がある。

使うサービスだけ開始する。

```fish
hermes-gateway start
hermes-dashboard start
hermes-gateway status
hermes-dashboard status
```

start したサービスは以後のログイン時も起動対象になる。stop すると次の start まで無効化される。Gateway は KeepAlive により、`/restart-gateway` による終了や異常終了後に自動再起動する。Dashboard は自動再起動しない。

### status の表示を確認する

`hermes-gateway status` は launchd の稼働状態と起動設定を表示する。

```text
Gateway: running (PID 10250)
Program: /Users/ryo.nakae/.config/agent-safehouse/safe-hermes-gateway.sh
Start at login: enabled
Restart on crash (plist): enabled
```

`Gateway: running` と PID が表示されれば、プロセスは稼働している。`Program` は launchd に登録された実行先、`Start at login` は plist と launchd の有効・無効設定から判定した値。`Restart on crash (plist)` は配置済み plist の設定。

停止中・未登録・状態や設定の取得失敗時は非ゼロで終了する。`unavailable` の場合は、併記された launchctl のエラーで未登録か取得失敗かを確認する。

### Hermes を停止・更新する

本体更新は全体 setup と分けて行う。利用中の CLI を終了し、稼働中のサービスだけ `hermes-gateway stop` / `hermes-dashboard stop` で先に止める。

```fish
mise -C ~/dotfiles -E hermes run hermes:update
```

対象と表示された revision・段階を確認して進める。

成功後に `git -C ~/Dev/private/hermes-agent rev-parse HEAD` と CLI の起動を確認する。依存の fallback が表示された場合は警告を確認する。

更新のために止めたサービスだけ、対象ユーザーの GUI ドメインを操作できる端末から `hermes-gateway start` / `hermes-dashboard start` で再開する。

停止だけしたい場合は `hermes-gateway stop` / `hermes-dashboard stop` を使う。停止処理はタイムアウト時に強制終了する場合があり、DB の整合したバックアップは別途必要。

### リモートアクセス

Hermes dashboard の認証を設定し、信頼できる LAN / VPN 内で使う。

iPhone から Tailscale 経由で利用する場合は、必要なポートだけ公開する。

```fish
tailscale serve --bg --https=9119 http://127.0.0.1:9120
tailscale serve status
```

表示されたホスト名の `:9119` が Hermes の dashboard。ローカルでは `hermes-dashboard open` で開く。

### Google Workspace

ユーザー用 `~/.config/gws` とは認証を分け、Hermes 用に必要な権限だけを付与する。

```fish
env GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.hermes/gws" \
    GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
    gws auth login
```

ログインが成功したら、稼働中の gateway を `hermes-gateway restart` で再起動する。

## Herdr

`default` を選択した setup は、Herdr の設定・キーバインド・プラグイン設定を配置し、未導入のプラグインを導入して Zerdr を登録する。初回導入や別 Mac への復元で追加の操作は不要。

### プラグインの導入・登録

導入するプラグインと固定 commit は [mise.default.toml](../mise.default.toml) の `herdr:plugins` task が正本。setup を使わずに導入する場合は、Safehouse 外の通常の fish 端末で実行する。

```fish
mise -C ~/dotfiles -E default run herdr:plugins
```

プラグインを更新する場合は task の commit を変更し、`herdr plugin install <repo> --ref <commit> --yes` で入れ直す。Agent Context の導入には release binary と checksum を取得するネットワーク接続が必要。Worktrunk プラグインには `wt >= 0.60.0`、`fzf`、`jq` が必要。

worktree の作成・削除は Worktrunk を使う。Herdr の `worktree open` は既存 checkout の登録だけに使う。

### 設定の反映と稼働確認

Herdr を起動し、そのセッション内の通常端末で設定を検証する。設定変更後も同じ手順を使う。

```fish
herdr config check
```

成功したら反映する。

```fish
herdr server reload-config
```

登録と常駐プロセスを確認する。

```fish
herdr plugin list
herdr plugin action list
pgrep -fl herdr-agent-context
```

- プラグイン一覧で Agent Context・Worktrunk・Zerdr が有効になっている。
- アクション一覧に `worktrunk.open`・`worktrunk.open-current`・`worktrunk.remove`・`zerdr.open-zed`・`zerdr.detach-thread` がある。
- `herdr-agent-context listen` のプロセスがある。

`prefix + Shift + g` で Worktrunk の選択画面が開くことを確認し、操作せずキャンセルする。Pi などの対応エージェントを起動・再開し、Agent Context によるタブ名とサイドバーの最終メッセージが更新されることも確認する。

### Agent Context が起動しない場合

Agent Context は Herdr 起動時に常駐プロセスを開始する。稼働中のセッションへ後から導入した場合、設定の再読み込みだけでは起動しないことがある。上のプロセス確認で何も表示されなければ、セッションを再起動する。

**停止すると、そのセッション内のペインとエージェントを含む実行中プロセスが終了する。** 作業を保存し、必要な会話の再開方法を確認してから、Herdr 外の通常端末で実行する。画面の開き直しだけではサーバーの再起動にならない。

```fish
herdr session list
```

対象を確認する。以下は `default` セッションの場合。停止が成功してから起動する。

```fish
herdr session stop default
herdr
```

名前付きセッションの場合は `default` を対象名に置き換え、起動には `herdr session attach セッション名` を使う。

再起動後、対象セッション内でプロセスと表示を再確認する。まだ動かない場合はログを確認する。

```fish
herdr plugin log list --plugin ryonakae.agent-context --limit 20
```

## CuaDriver

本体は Homebrew 管理。初回のアクセシビリティ・画面収録の許可と daemon 起動は[公式 Quickstart](https://cua.ai/docs/cua-driver/quickstart)に従う。

## Cua Spaces

`cua` は Cua Spaces アプリ同梱の CLI を使う。`command -v cua` と `cua --version` で利用可能か確認する。アプリ本体の導入・認証は別途行い、`cua agents setup` によるスキル・MCP の自動配置は使わない。

Pi・Claude Code・Codex・OpenCode・Antigravity CLI の MCP 定義は dotfiles 管理。新規ファイルは[設定ファイルの配置](usage.md#設定ファイルを変更する)、公式 `cua-spaces` スキルは[外部 repos の更新と配置](usage.md#外部スキルと-plugin-を更新する)で反映する。

Claude Code は fish の `claude` 関数が `~/.claude/mcp.json` を追加指定する。関数を経由せず起動するときは `claude --mcp-config ~/.claude/mcp.json` を使う。

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

## macOS とその他のアプリ

mise 管理の設定を GUI で変えても、次の defaults apply で宣言値へ戻る。継続して変える設定は構成別 `mise.<name>.toml` と `scripts/macos-settings.sh` を編集し、[macOS の部分操作](usage.md#macos-設定を適用する)で反映する。

次の項目は自動復元されないため、必要なものだけ手動で準備する。

- Apple Account・iCloud・Touch ID、アクセシビリティ・画面収録・自動化などの許可
- Xcode の SDK / Simulator、署名証明書・provisioning profile、VPN 認証
- Docker の初期設定、volume
- 入力ソース、宣言外の標準ショートカット、アプリ別ショートカット、Karabiner 管理外のデバイス設定、宣言外の電源設定
- Dock に登録した Chrome 製アプリなどの実体
- `Dropbox/App` に保存した、Git 管理外のアプリ設定
