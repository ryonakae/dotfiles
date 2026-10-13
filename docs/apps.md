# アプリ別の設定

[README](../README.md) / アプリ別の設定

必要なアプリの項目だけを使う。認証・権限設定・サービス起動は、ユーザーが通常端末で行う。

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

Herdr の Claude hook を使う場合は、Homebrew 版 Herdr の標準 installer で登録する。旧 Home Manager の hook がある場合は、先に[移行](migration.md)する。

```fish
herdr integration install claude
```

この操作は Claude の settings を変更する。実行前後の Git 差分を確認し、既存の設定を保持する。本体更新後も hook の版を確認する。

statusline の初回取得には npm registry への接続が必要。

## Pi

OpenAI の認証は Pi 内で `/login openai` を実行し、`Sign in with ChatGPT` を選ぶ。

MCP の個人設定は `~/.pi/agent/mcp.json`。OAuth が必要なサーバーは `pi mcp login SERVER` を使う。`SERVER` は設定したサーバー名に置き換える。

本体は Homebrew で更新する。拡張の版指定は `config/.pi/agent/settings.json` で管理し、取得先は Pi の管理ディレクトリを使う。設定・footer の変更は Git 正本への書き込みとなるため、Git 差分を確認する。

## oMLX

[公式 Releases](https://github.com/jundot/omlx/releases) の DMG から手動導入し、アプリ内の更新機能で更新する。メニューバーアプリからサーバーの起動・停止を行い、モデルは管理画面 `http://127.0.0.1:8000/admin` でダウンロード・ロードする。Homebrew の Formula 版は併用しない。

サーバーは `127.0.0.1:8000` で待ち受け、API キー認証を使う。発行したキーは[共通 API キーの手順](secrets.md#値を追加更新する)で `OMLX_API_KEY` として登録する。

OpenCode での利用を想定し、`config/.config/opencode/opencode.json` に oMLX の provider を設定済み。

oMLX の設定は `~/.omlx/settings.json`、モデルの標準保存先は `~/.omlx/models/`。内部設定・モデル・キャッシュ・履歴は dotfiles では管理しない。

## Hermes

CLI・gateway・dashboard は[共通 API キー](secrets.md)を起動時に読み込む。Hermes 固有の認証・設定と共通キーは分けて管理する。

gateway / dashboard はホストの launchd で動かす。同じ `~/.hermes` を使う Docker dashboard を同時起動しない。

### 初回設定と起動

共通 API キー、Hermes の認証・設定を準備する。`openai-codex` を使う場合は `~/.codex` の認証も復元する。

起動定義は Nix が配置する。`hermes gateway install` や旧 installer で plist を再生成しない。Hermes の setup でサービス導入・即時起動を聞かれたら No を選ぶ。

起動・停止・再起動は、対象ユーザーの `gui/<UID>` ドメインで行う。macOS にそのユーザーがログイン済みで、操作する端末から対象ドメインへアクセスできる必要がある。Herdr・tmux・SSH などで操作元が `Background` でも、それだけでは拒否しない。

管理関数は対象ドメインを明示して確認・操作する。ドメインが存在しない、権限不足などで確認や操作に失敗した場合は中止し、別ドメインや直接起動へ切り替えない。sandbox による拒否がある場合は、制限を変更せず通常端末から操作する。

必要なバックアップと認証設定を済ませ、使うサービスだけ開始する。

```fish
hermes-gateway start
hermes-dashboard start
hermes-gateway status
hermes-dashboard status
```

start したサービスは以後のログイン時も起動対象になる。stop すると次の start まで無効化される。Gateway は KeepAlive により、`/restart-gateway` による終了や異常終了後に自動再起動する。`hermes-gateway stop` はサービスをアンロードするため、自動再起動されない。Dashboard は自動再起動しない。

常駐サービスの Keychain 利用は、実機のロック状態・アクセス許可を確認する。CLI で使えることだけでは、ログイン時の自動起動成功を保証しない。

ローカル音声認識・マイク入力用の `voice` グループは同梱しない。利用したい場合は依存構成の変更が必要。

### status の表示を確認する

`hermes-gateway status` は launchd の稼働状態と起動設定を表示する。

```text
Gateway: running (PID 10250)
Program: /nix/store/…-safe-hermes-gateway.sh
Start at login: enabled
Restart on crash (plist): enabled
```

`Gateway: running` と PID が表示されれば、プロセスは稼働している。メッセージング連携などの正常動作までは保証しない。`Program` は launchd に登録された実行先、`Start at login` は plist と launchd の有効・無効設定から判定した値。`Restart on crash (plist)` は配置済み plist の設定であり、稼働中プロセスへの反映確認ではない。

停止中・未登録・状態や設定の取得失敗時は非ゼロで終了する。`unavailable` の場合は、併記された launchctl のエラーで未登録か取得失敗かを確認する。

### Hermes を停止・更新する

Hermes が稼働中でも、[Nix の更新・適用](usage.md#nix-を更新適用する)を実行できる。更新対象は `hermes-agent`。`hermes update` / `hermes-gateway update` は使わない。Nix の適用は Safehouse 外の通常端末から行い、`Aqua` セッションは必須ではない。

適用は起動定義の配置のみで、稼働中のサービスは自動再起動しない。本体・wrapper・起動定義の変更を反映するには、適用成功後に対象ユーザーの GUI ドメインを操作できる端末から、使っているサービスだけ再起動する。

```fish
hermes-gateway restart
hermes-dashboard restart
```

停止だけしたい場合は `hermes-gateway stop` / `hermes-dashboard stop` を使う。停止や再起動が失敗した場合は先へ進まず、状態を確認する。管理関数を迂回して直接 `launchctl` を操作しない。停止処理はタイムアウト時に強制終了する場合があり、DB の整合したバックアップは別途必要。

### リモートアクセス

Hermes dashboard の認証を設定し、信頼できる LAN / VPN 内で使う。`--insecure` では認証を迂回できない。

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

dotfiles の setup は Herdr の設定・キーバインド・プラグイン設定を配置するが、プラグイン本体のインストールと登録は行わない。初回導入や別 Mac への復元では、以下も実施する。設定だけでは、Worktrunk・Zerdr のキーバインドや Agent Context の表示は動かない。

### プラグインの導入・登録

Safehouse 外の通常の fish 端末で、各コマンドが成功してから次へ進む。再インストールは既存 checkout の交換と有効化を伴うので、導入済みの場合は稼働中の利用状態を確認する。

```fish
herdr plugin install ryonakae/herdr-agent-context --ref 10b8ead9d86b2cbb7b13d87ef50dec4b87ee21cd --yes
herdr plugin install devashish2203/herdr-worktrunk --ref a3107ca566bafcd463bc138007a0c01051970784 --yes
```

`--ref` は省略しない。更新時はこの一覧の commit も変更する。Agent Context の導入には release binary と checksum を取得するネットワーク接続が必要。Worktrunk プラグインには `wt >= 0.60.0`、`fzf`、`jq` が必要。

Zerdr は Homebrew 版を使う。初回導入・復元時や登録先を切り替える場合は、次を実行する。`brew --prefix` が未インストールのエラーになった場合は止めて、本体の導入状態を確認する。

```fish
set -l zerdr_bin (brew --prefix ryonakae/tap/zerdr)/bin/zerdr
$zerdr_bin setup install
```

Herdr の登録と Zed tasks が変更される。両方の実行先が Homebrew 版を指すことを確認する。古い絶対パス入りの manifest はコピーしない。

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
- `herdr-agent-context listen` のプロセスがある。登録一覧の有効表示や `reload-config` の成功だけでは、このプロセスの稼働確認にはならない。

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

再起動後、対象セッション内でプロセスと表示を再確認する。別セッションの listener もプロセス一覧に出るため、プロセスの存在だけで表示の更新まで確認済みとしない。まだ動かない場合は、再インストールを繰り返さずログを確認する。

```fish
herdr plugin log list --plugin ryonakae.agent-context --limit 20
```

## CuaDriver

本体は Homebrew 管理。公式 installer を重ねず、初回のアクセシビリティ・画面収録の許可と daemon 起動は[公式 Quickstart](https://cua.ai/docs/cua-driver/quickstart)に従う。

以前の `~/.local/bin/cua-driver` がある場合は、`type -a cua-driver` と `cua-driver --version` で Homebrew 版が選ばれるか確認する。古いリンクは確認せず削除しない。

## Cua Spaces

`cua` は Cua Spaces アプリ同梱の CLI を使う。`command -v cua` と `cua --version` で利用可能か確認する。アプリ本体の導入・認証は別途行い、`cua agents setup` によるスキル・MCP の自動配置は使わない。

Pi・Claude Code・Codex・OpenCode・Antigravity CLI の MCP 定義は dotfiles 管理。新規ファイルは[設定ファイルの配置](usage.md#設定ファイルを変更する)、公式 `cua-spaces` スキルは[Nix のビルド・適用](usage.md#ビルドと適用を分ける)で反映する。既存の `cua-driver` スキルはこの Mac の GUI 操作用として残す。

Claude Code は fish の `claude` 関数が `~/.claude/mcp.json` を追加指定する。関数を経由せず起動するときは `claude --mcp-config ~/.claude/mcp.json` を使う。`--strict-mcp-config` は付けず、プロジェクトの MCP 設定も読み込む。他のクライアントは標準のユーザー設定を使う。プロジェクトの信頼・承認は各クライアントで行い、グローバル設定の追加を自動承認とみなさない。同名の MCP・スキルの優先順位はクライアントごとに異なるため、プロジェクト専用のものは `cua` / `cua-spaces` と別名にする。

Hermes の `~/.hermes/config.yaml` は管理外。既存の設定に次を追加・統合する。既に同じキーがある場合は重複させない。

```yaml
mcp_servers:
  cua:
    command: cua
    args: [daemon, mcp, --permissions, "spaces:all"]
skills:
  external_dirs:
    - ~/.agents/skills
```

MCP は Spaces の作成・削除・コマンド実行を含む `spaces:all` を許可し、必要に応じて共通の Cua daemon を起動する。Space の作成や認証情報・アプリセッションの転送は別途確認してから行う。Hermes は対話セッションの `/reload-mcp` で反映でき、起動中の gateway は設定変更を自動反映する場合がある。Hermes のプロジェクトスキルには信頼設定が必要で、プロジェクトの `.mcp.json` の自動読込は前提にしない。

反映後は各エージェントの MCP 一覧に `cua`、スキル一覧に `cua-spaces` があることを確認する。プロジェクト内でも既存の MCP・スキルが残っていることを確認する。MCP 一覧の取得自体が接続・daemon 起動を伴うクライアントもある。

## Unity CLI

本体は `brew upgrade --cask unity-cli` で更新する。公式 installer や `unity self-update` は併用しない。Editor と追加モジュールはプロジェクトに必要な版を CLI / Hub で管理する。

旧 installer からの移行では `~/.unity/bin/unity` と `~/.config/fish/conf.d/unity-cli.fish` の PATH 設定を確認・保全し、新しい shell の `type -a unity` で Homebrew 版が選ばれることを確認する。既存の Editor・Hub データは削除しない。

`brew uninstall --zap unity-cli` は使わない。Hub のデータも削除対象になる。[公式の導入方法](https://docs.unity.com/en-us/unity-cli/use-unity-cli#install-with-a-package-manager)と[cask の削除対象](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/u/unity-cli.rb)を参照する。

## Karabiner

設定は `config/.config/karabiner/karabiner.json` を編集する。アプリ側の変更も Git 差分になる。

既存設定がある Mac は、配置前に必要な JSON を保全する。既存の実ディレクトリや旧ファイル単位リンクを上書きせず、[移行手順](migration.md)で解除・退避してから配置する。

ディレクトリの配置場所が変わった後は、[公式手順](https://karabiner-elements.pqrs.org/docs/manual/misc/configuration-file-path/)に従って `Karabiner-Console-User-Server` を一度再起動する。再起動までは新しい場所の変更が自動検知されない。アプリの初期設定と macOS の権限許可も別途行う。

## macOS とその他のアプリ

Nix 管理の設定を GUI で変えても、次の switch で宣言値へ戻る。継続して変える設定は `nix/darwin/preferences.nix` を編集する。適用時には Dock が再起動する。

次の項目は自動復元されないため、必要なものだけ手動で準備する。

- Apple Account・iCloud・Touch ID、アクセシビリティ・画面収録・自動化などの許可
- Xcode の SDK / Simulator、署名証明書・provisioning profile、VPN 認証
- Docker の初期設定、volume
- 入力ソース、標準・アプリ別ショートカット、Karabiner 管理外のデバイス設定、電源設定
- Dock に登録した Chrome 製アプリなどの実体
- `Dropbox/App` に保存した、Git 管理外のアプリ設定

Vim は外部プラグインなしの最小構成。旧 `~/.vim/bundle` は設定変更だけでは消えないため、不要なら中身を確認して別途整理する。
