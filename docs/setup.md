# 手動セットアップと復元

[README](../README.md) の配布後に、使う機能だけ設定する。
秘密の登録とサービスの初期設定は、人間が sandbox 外の fish で行う。

## Nix の初回導入

Nix 移行は準備中。以下は Nix 本体の導入のみで、dotfiles や Homebrew の切替は行わない。
Apple Silicon Mac の通常のユーザーアカウントから、人間が Safehouse 外のターミナルで実行する。

```fish
cd ~/dotfiles
bash scripts/bootstrap-nix.sh --install
```

公式の版固定済み配布物を checksum 検証してから、multi-user インストーラを起動する。Flakes を使うため、従来の channel は追加しない。
APFS volume、mount 設定、build users、daemon、shell 初期化を変更し、必要に応じて sudo と、FileVault 利用時のシステム Keychain 操作を伴う。表示される変更内容を確認して進める。
既存の Nix や残存パスを検出した場合は、自動で上書き・修復しない。

完了後、新しいターミナルで次を確認する。初期状態で PATH にない場合は、インストーラが案内した shell 初期化を反映してから再確認する。

```fish
nix --version
```

この時点では既存のツール・設定は切り替えず、Nix の事前ビルドへ進む。
導入失敗時は出力を確認し、残存 volume やシステム設定を無断で削除して再実行しない。

## Nix の事前ビルド

移行中の構成をビルドする入口。一般 CLI・共通ランタイム、アプリの補完一覧、fish と基本の保護設定まで構成済み。AI ツール・拡張・サービス等の移行が残るため、既存環境の適用・切替には使わない。
Nix と Python 3 が必要（初回は Command Line Tools 付属の Python でも可）。

```fish
mkdir -p ~/.config/dotfiles/host
cp -n config/nix/hosts/host.json.example ~/.config/dotfiles/host/host.json
```

作成した `host.json` の `username` と `homeDirectory` を実機に合わせて編集する。
この2項目は Nix store に入る公開情報として扱い、秘密や認証情報は書かない。ファイルは Git 管理外に置く。

```fish
bash scripts/dotfiles.sh build
```

別の host 入力を使う場合は `build --host DIRECTORY` と指定する。出力された store path はビルド成果物であり、activation は実行されない。
通常の build は lock を更新しない。新しい Nix ファイルは対象を明示して Git に追加してからビルドする。未追跡ファイルを含めるために `path:.` へ切り替えたり、一括 stage したりしない。

本体は nixpkgs の標準パッケージ、設定ファイルの配置は Home Manager で管理する。Nix へ移したプラグインも同じ更新経路を使い、Yazi の対象プラグインを `ya pkg` で重ねて更新しない。通常の設定本文は元の .fish / .toml / .json 等を編集し、Nix 側は導入・連携・配置と Nix 固有の指定に限定する。依存の更新は別操作で行い、lock の差分を確認して再ビルドする。

```fish
bash scripts/dotfiles.sh update nixpkgs
bash scripts/dotfiles.sh update all
```

更新対象は公開 input の名前であり、ツール名ではない。AI ツールも `update nixpkgs` でまとめて更新し、`update ai` や専用 updater は使わない。標準管理が難しい対象だけ、補完方法を相談して決める。更新は適用・起動を行わない。`switch` はサービス・残りの設定の移行が揃うまで未提供。

fish の生成設定は管理済み example を基にした共通設定で、Git 外の実 `config.fish` のコピーではない。切替前に、人間が秘密の移行と必要な非秘密の差分を確認する。既存の Fisher 配置・リンクも退避してから移し、二重読み込みさせない。`fish_variables` と履歴は Nix で管理しない。

## 共通ツール用の秘密

共通 API キーは `config/.config/.env` にまとめ、dotenvx で暗号化し、復号鍵を macOS Keychain に保存する。
プロジェクト・本番環境の秘密や各エージェント自身の認証は混ぜない。

```fish
cd ~/dotfiles
cp -n config/.config/.env.example config/.config/.env
chmod 600 config/.config/.env
```

エディタで実値を入力する。既存ファイルは上書きせず、値をチャットやログに貼らない。
`~/.config/.env` がこのファイルへのリンクであることを確認してから暗号化する。

```fish
ls -l ~/.config/.env
dotenvx encrypt --quiet --no-armor -f "$HOME/.config/.env"
dotenvx native up --quiet -f "$HOME/.config/.env" -fk "$HOME/.config/.env.keys"
```

Keychain への保存を確認し、鍵ファイルが残る場合や保存エラーは解消してからエージェントを起動する。
起動処理は鍵ファイルへ自動で切り替えないため、Keychain から復号できないと停止する。
以前 `config.fish` にキーを export していた場合は、その設定と現在のシェルに残る値を除く。既存の環境変数が dotenvx より優先されるため。

暗号化した `.env` と login Keychain の両方を、暗号化されたバックアップに含める。
OS 移行時は Keychain も復元する。暗号化ファイルだけでは復号できない。
初期設定後は新しい端末で CLI を起動し、常駐中の Hermes は管理関数から再起動する。

起動できなくなったら再起動を繰り返さず、sandbox 外で変更した管理ファイルを以前の版へ戻す。
暗号化 `.env`、Keychain 項目、ごみ箱データは削除しない。

## 削除したファイルの復元

rm 転送用のごみ箱は通常 `~/.local/share/Trash`。`XDG_DATA_HOME` 指定時はその配下の `Trash` を使う。
Finder のごみ箱とは別で、復元は gomi から行う。

```fish
gomi --config "$HOME/.config/gomi/config.yaml" --restore
```

エージェントの削除操作が終わってから、sandbox 外で実行する。
一覧から対象を選び、Enter で復元する。元の場所に別のデータがある場合は、先に退避して復元先を確認する。
復元・掃除中は別の rm / gomi を並行実行しない。
容量を空けるための永久削除は、人間が復元・バックアップを確認してから行う。自動掃除は設定しない。

rm 転送を外す場合は `~/.local/bin/rm`、fish の `rm.fish`、`conf.d/gomi.fish` のリンクだけを確認して退避する。
ごみ箱の実体は残す。

## 外部スキル

`npx skills` はホームで実行する。`-g` と `update` は使わず、追加・更新の配布先を `-a claude-code` に絞る。
自作スキルは dotfiles 側で管理し、外部スキルの実体は `~/.agents/skills/` に置く。
Nix への切替後は自作スキルを Home Manager で個別配置し、旧 `create-skills-symlink.sh` を併用しない。初回は既知の自作リンクだけを確認・退避し、外部スキルや Claude の他のディレクトリは保持する。外部スキルの固定復元は移行中であり、以下の取得手順とは区別する。

新規マシンで lock の登録内容を取得する場合:

```fish
cd ~
npx skills experimental_install -a claude-code
```

これは固定版の再現ではなく、取得元の最新版を取り直す操作で、lock のハッシュも変わる。通常の更新には使わない。
個別の追加・更新は、取得元とスキル名を指定して `add` を再実行する。例:

```fish
cd ~
npx skills add callstack/agent-device -s agent-device -a claude-code -y
```

取得後は次を確認する。

1. 単一エージェントへの配布で `~/.claude/skills/` に実体コピーができた場合は、取得した最新版を `~/.agents/skills/` へ移し、Claude 側を symlink に戻す。既存実体は退避し、古い内容で最新版を上書きしない。
2. Antigravity CLI は `~/.agents/skills/` へのディレクトリリンクで参照する。Hermes や Pi 専用ディレクトリなど、配布対象外に余分なリンクを残さない。
3. `config/skills-lock.json` の差分を確認する。削除時も、配布ファイルと lock の両方から登録が消えたことを確認する。

## Pi

Nix への切替後も `settings.json`、footer、fast-mode の設定は書き込み可能な実ファイルとして使う。Home Manager の標準 merger は再適用時にリポジトリの定義値を優先し、未定義キーを保持する。アプリ内で変更した定義済みの値を永続化する場合は、正本にも反映する。正本からキーを削除しても実ファイルの同じキーは削除されない。

適用前には Pi を停止する。初回は既存の設定リンクを対象ごとに確認・退避し、正本へのリンクではなくローカルの実ファイルへ移す。リンク先へ書き戻す事故を避けるため、設定ファイルや親ディレクトリが別の実体へリンクしていると適用は中止する。認証・session を移行用の設定や store へ含めない。

拡張の本体版は `config/.pi/agent/settings.json` の npm version / Git commit で固定する。これは npm の推移依存全体の lock ではなく、新規取得時の全機能の復元検証は移行中の残作業。拡張のインストール先は通常の Pi 管理ディレクトリに保ち、Nix の build / activation では取得・更新しない。Nix 管理の Pi 本体には自己更新コマンドを使わない。

OpenAI は Pi 内の `/login openai` から `Sign in with ChatGPT` を選んで認証する。
MCP の個人設定は `~/.pi/agent/mcp.json` に置く。OAuth が必要なサーバーには `pi mcp login <server>` を使う。

## Hermes Agent

gateway / dashboard はホストの launchd、Hindsight は Docker で動かす。
同じ `~/.hermes` を使う Docker dashboard をホスト版と同時起動しない。
共通ツール用の秘密を設定し、Docker を起動してから進める。

### 初回設定

[Hermes の公式手順](https://github.com/NousResearch/hermes-agent)で本体を導入し、ランタイムと plist を準備する。

```fish
mise -C ~/.hermes install
command hermes gateway install
```

`~/Library/LaunchAgents/ai.hermes.gateway.plist` の `ProgramArguments` を、`~/.config/agent-safehouse/safe-hermes-gateway.sh` の**絶対パス1要素**へ完全置換する。
元の Python 起動引数は残さない。plist 内では `~` や `$HOME` を展開しない。
`~/.hermes/.env` に `API_SERVER_ENABLED=true` を設定する。

dashboard の plist は Git 管理外の `~/Library/LaunchAgents/ai.hermes.dashboard.plist` に作成する。

| 項目 | 値 |
|---|---|
| `Label` | `ai.hermes.dashboard` |
| `ProgramArguments` | `~/.config/agent-safehouse/safe-hermes-dashboard.sh` の絶対パス1要素 |
| `WorkingDirectory` | `~/.hermes/hermes-agent` の絶対パス |
| `EnvironmentVariables` | gateway と同じ `PATH` / `VIRTUAL_ENV` / `HERMES_HOME` |

Hindsight の `.env` は dotfiles 側で編集し、認証を準備する。
`openai-codex` provider を使う場合は、ホストの `~/.codex` の認証も必要。

```fish
cd ~/.hermes/services
docker compose up -d hindsight
hermes memory setup
```

memory provider に Hindsight を選ぶ。plist の構文を確認してからサービスを起動する。

```fish
plutil -lint ~/Library/LaunchAgents/ai.hermes.gateway.plist
plutil -lint ~/Library/LaunchAgents/ai.hermes.dashboard.plist
hermes-gateway start
hermes-dashboard start
```

起動後に状態を確認する。

```fish
hermes-gateway status
hermes-dashboard status
hermes memory status
```

Python のバージョンを変更した場合は、Hermes 本体の `venv` も再作成する。
`hermes gateway install --force` / `start` / `setup` で plist を再生成した場合は、wrapper への差し替えをやり直す。
`setup` のサービス導入・即時起動の質問には No を選び、起動は管理関数で行う。

### 更新・停止

gateway は `hermes-gateway`、dashboard は `hermes-dashboard` で操作する。
停止時の処理を飛ばさないよう、`launchctl` を直接使わない。

```fish
hermes-gateway update
```

停止する場合:

```fish
hermes-dashboard stop
hermes-gateway stop
cd ~/.hermes/services
docker compose down
```

### リモートアクセス

dashboard は `0.0.0.0:9120 --insecure` で待ち受けるため、信頼できる LAN 内でのみ動かす。
iPhone からのアクセス用に Tailscale Serve を設定する。

```fish
tailscale serve --bg --https=9119 http://127.0.0.1:9120
tailscale serve --bg --https=9999 http://127.0.0.1:9999
tailscale serve status
```

表示されたホスト名の `:9119` が Hermes、`:9999` が Hindsight の dashboard。

### Google Workspace

人間用の `~/.config/gws` と認証を共有せず、Hermes 用に必要な権限だけを付与する。
初回ログインは sandbox 外で行う。

```fish
env GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.hermes/gws" \
    GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
    gws auth login
hermes-gateway restart
```

## Herdr

プラグインには復元用 lock がないため、新規マシンでは個別に導入する。

```fish
herdr plugin install ryonakae/herdr-agent-context --yes
herdr plugin install ryonakae/shepherd/packages/shepherd-herdr-plugin --yes
herdr plugin install devashish2203/herdr-worktrunk --yes
```

`zerdr` は Zerdr 本体が `~/Library/Application Support/dev.ryonakae.zerdr/` に配置するローカルプラグインを使う。
worktrunk プラグインには `wt >= 0.60.0`、`fzf`、`jq` が必要。
導入後は `herdr plugin list` で確認する。

worktree の作成・削除には Worktrunk を使う。Herdr 本体の作成機能では Worktrunk の配置・hooks・ignored ファイルのコピーを引き継げない。
`herdr worktree open` は既存 checkout の登録に限って使う。
設定変更後は `herdr config check` で検査し、`herdr server reload-config` で反映する。

## ランタイム

`~/.local/bin` に Node / npm のリンクを置く場合は、Hermes 専用の実体ではなく mise の shim を参照させる。
Node の問題を直すためにこのディレクトリの PATH 優先順位を下げない。rm 転送にも影響するため。

## Vim

Vim は補助的な編集用に、外部プラグインを使わない最小構成とする。NeoBundle の導入・更新は不要。
Nix への切替後は標準の Vim と `config/.vimrc` を配布し、本体は nixpkgs と一緒に更新する。
旧 `~/.vim/bundle` の実体は設定変更だけでは削除しない。不要物の整理は切替後に対象を確認して行う。

## アプリ設定

Git 管理していないアプリ設定は `Dropbox/App` にも保存している。新しい Mac では必要なものを個別にインポートする。
