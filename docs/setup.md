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

本体は原則 nixpkgs の標準パッケージ、設定ファイルの配置は Home Manager で管理する。Hermes は `ryonakae/hermes-agent` fork 同梱の Flake のパッケージを採用し、その依存も root lock で固定する。サービスモジュールは取り込まない。fork のビルド状況は移行計画を参照し、サービスの実機検証と切替は別に行う。下記の Nix 移行後の手順は、切替を承認するまで実行しない。Nix へ移したプラグインも同じ更新経路を使い、Yazi の対象プラグインを `ya pkg` で重ねて更新しない。通常の設定本文は元の .fish / .toml / .json 等を編集し、Nix 側は導入・連携・配置と Nix 固有の指定に限定する。依存の更新は別操作で行い、lock の差分を確認して再ビルドする。

```fish
bash scripts/dotfiles.sh update nixpkgs
bash scripts/dotfiles.sh update hermes-agent
bash scripts/dotfiles.sh update all
```

更新対象は公開 input の名前であり、ツール名ではない。nixpkgs の AI ツールは `update nixpkgs`、Hermes は `update hermes-agent` で更新する。`update ai` や専用 updater は使わない。標準管理が難しい対象だけ、補完方法を相談して決める。更新は適用・起動を行わない。`switch` はサービス・残りの設定の移行が揃うまで未提供。

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
Nix への切替後は、自作スキルと `config/nix/home/external-skills.nix` で固定した外部スキルを Home Manager で個別配置する。旧 `create-skills-symlink.sh` や、以下の `experimental_install` による上書きを併用しない。外部スキルの更新は revision / hash を明示して変更し、build 後に適用する。

初回は既知の自作リンクと、Nix 管理対象となる外部スキルの実ディレクトリを個別に確認・退避する。未管理スキルや Claude の `synced` は保持し、親ディレクトリ全体を置き換えない。Python キャッシュ等の実行時生成物は復元対象に含めない。旧 `skills-lock.json` だけに残る未配置スキルの判断は移行中の残作業。以下は切替前の旧配布手順であり、Nix 管理対象の復元には使わない。

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

## Claude Code

Nix への切替後、Herdr の Claude hook は Home Manager が Herdr 本体と同じソースから配置する。Herdr の UI / CLI から Claude integration を再インストール・更新すると管理対象の hook と settings を書き換えようとするため、併用しない。

statusline は設定内の npm version を固定し、通常の `npx` で利用する。Nix build / activation にはインストールを含めず、初回取得には npm registry への接続が必要。

## Pi

Nix への切替後も `settings.json`、footer、fast-mode の設定は書き込み可能な実ファイルとして使う。Home Manager の標準 merger は再適用時にリポジトリの定義値を優先し、未定義キーを保持する。アプリ内で変更した定義済みの値を永続化する場合は、正本にも反映する。正本からキーを削除しても実ファイルの同じキーは削除されない。

適用前には Pi を停止する。初回は既存の設定リンクを対象ごとに確認・退避し、正本へのリンクではなくローカルの実ファイルへ移す。リンク先へ書き戻す事故を避けるため、設定ファイルや親ディレクトリが別の実体へリンクしていると適用は中止する。認証・session を移行用の設定や store へ含めない。

拡張の本体版は `config/.pi/agent/settings.json` の npm version / Git commit で固定する。これは npm の推移依存全体の lock ではなく、新規取得時の全機能の復元検証は移行中の残作業。拡張のインストール先は通常の Pi 管理ディレクトリに保ち、Nix の build / activation では取得・更新しない。Nix 管理の Pi 本体には自己更新コマンドを使わない。

OpenAI は Pi 内の `/login openai` から `Sign in with ChatGPT` を選んで認証する。
MCP の個人設定は `~/.pi/agent/mcp.json` に置く。OAuth が必要なサーバーには `pi mcp login <server>` を使う。

## Hermes Agent

以下は **Nix 移行後**の運用。現時点では switch と実機検証が未完了なので、既存環境へ配布・適用しない。
gateway / dashboard はホストの launchd、Hindsight は Docker で動かす。同じ `~/.hermes` を使う Docker dashboard をホスト版と同時起動しない。

### 初回設定

本体は `ryonakae/hermes-agent` の `ryonakae` ブランチを lock で固定し、fork 同梱の Flake で導入する。起動定義は Home Manager が管理する。`hermes gateway install` 等による plist 再生成、旧 installer、Hermes 専用 mise / venv の復元は併用しない。`setup` のサービス導入・即時起動の質問には No を選ぶ。

この Mac では Hermes を起動しない。利用を開始する Mac で、人間が sandbox 外から共通ツール用の秘密、Hermes の認証・設定、Docker を準備する。認証・DB・memory・session・cache は store に入れない。Hindsight の秘密は Git 管理外の `~/.hermes/hindsight/.env` に置き、`openai-codex` 用の `~/.codex` 認証も人間が復元する。

Hindsight のデータと認証を準備し、コンテナ起動を承認した後に実行する。

```fish
cd ~/.hermes/services
docker compose up -d hindsight
hermes memory setup
```

memory provider に Hindsight を選ぶ。Compose は tag と digest を固定するが、Docker の volume・認証は Nix 世代へ巻き戻らない。

plist の生成・配置だけではサービスを開始しない。初期設定と必要な状態バックアップを済ませ、起動を承認したサービスだけ管理関数から開始する。

```fish
hermes-gateway start
hermes-dashboard start
hermes-gateway status
hermes-dashboard status
```

新定義は既定で disabled。明示的な start で有効化し、以後のログイン時も起動対象になる。stop が成功したサービスは無効化され、次の start まで停止状態を維持する。KeepAlive による自動再生成は行わないため、異常終了時も原因を確認して管理関数から再起動する。

### 更新・停止・既存環境の移行

gateway は `hermes-gateway`、dashboard は `hermes-dashboard` で操作する。管理関数は fork 標準の停止コマンドを呼ぶ。タイムアウト時の強制終了も fork の仕様に従い、強制終了しないことは保証しない。独自の停止 controller や子プロセス管理は追加しない。

停止コマンドや launchd 操作がエラーなら後続の再起動を中止する。直接の `launchctl` で管理関数を飛ばしたり、管理操作と設定適用を並行して行ったりしない。成功表示だけで DB バックアップの整合性を保証した扱いにはせず、既存データの保全は別に確認する。

```fish
hermes-dashboard stop
hermes-gateway stop
```

本体の更新は `bash scripts/dotfiles.sh update hermes-agent` と事前ビルドで準備する。`hermes-gateway update` / `hermes update` では更新しない。停止・バックアップ・適用・再開は人間が別々に行う。dotfiles の適用入口は利用状態を保存せず、自動停止・再開もしない。

Home Manager は配置前に launchd の Hermes 登録、判別可能な Hermes プロセス、plist の所有関係を確認する。未停止・読み取り失敗・未知の形式なら配置を中止し、停止操作は行わない。確認はユーザーの GUI セッションを前提とし、全プロセスの所属や子プロセスの終了を追跡する仕組みではない。未知の既存 plist は強制上書きせず、確認済みの退避・復旧手順を用意する。別 Mac の旧定義や管理外プロセスの移行は、その環境で確認して行う。旧 `~/.hermes/mise.toml` や venv の整理も、その切替時に明示して行う。

Hindsight の停止・データ移行は別に承認する。必要な停止時は `~/.hermes/services` で `docker compose down` を実行し、データ volume を削除しない。

### リモートアクセス

dashboard は既存どおり `0.0.0.0:9120` を使うが、採用済み Hermes では認証 provider が必要。`--insecure` は認証を迂回しない。人間が認証を設定してから起動し、信頼できる LAN / VPN 内で使う。

iPhone からのアクセス用に Tailscale Serve を設定する。これは Nix の適用とは別の、人間によるネットワーク設定操作。

```fish
tailscale serve --bg --https=9119 http://127.0.0.1:9120
tailscale serve --bg --https=9999 http://127.0.0.1:9999
tailscale serve status
```

表示されたホスト名の `:9119` が Hermes、`:9999` が Hindsight の dashboard。`hermes-dashboard open` はローカルの URL を開く。

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

Git plugin は標準 CLI で以下の commit を個別に復元する。registry / checkout / state は Herdr の可変データとして残し、Nix build / activation からインストールしない。再インストールは checkout を交換し、有効化も行うため、稼働中の利用状態を確認してから人間が実行する。

```fish
herdr plugin install ryonakae/herdr-agent-context --ref 10b8ead9d86b2cbb7b13d87ef50dec4b87ee21cd --yes
herdr plugin install devashish2203/herdr-worktrunk --ref a3107ca566bafcd463bc138007a0c01051970784 --yes
```

更新時も採用する commit をこの一覧へ反映し、`--ref` を省略しない。省略して再インストールすると、保存済み ref を引き継がず remote HEAD へ移る。

Agent Context の installer は release binary と同じ release の checksum を取得するため、ネットワークが必要。source commit の固定は binary の Nix 固定出力管理とは異なる。Shepherd 本体と plugin は復元対象から外す。既存の実機導入物・稼働中 daemon・保存データの停止や削除は、移行宣言の変更と分けて行う。

Zerdr は Homebrew 版を使う。導入対象は nix-darwin の Homebrew 設定で宣言するが、本体は Homebrew が管理し、`flake.lock` による版固定・ロールバックの対象にはならない。

Zerdr のローカルプラグインは本体が `~/Library/Application Support/dev.ryonakae.zerdr/` に配置する。切替時は、開発版を拾わないよう Homebrew 版のパスを明示して生成・登録する。古い絶対パスを含む manifest をコピーしない。

```fish
set -l zerdr_bin (brew --prefix ryonakae/tap/zerdr)/bin/zerdr
$zerdr_bin setup install
```

この操作は Herdr の登録と Zed tasks を更新するため、切替時に実行する。現在の開発版への登録はまだ変更していない。Zed tasks は Nix 管理に追加していない。
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

## macOS と手動復元

Nix 管理する preferences は `config/nix/darwin/preferences.nix` を正本にする。明示されていないキーへ推測で値を設定しない。適用時は標準 nix-darwin モジュールが Dock を再起動するため、作業中の UI への影響を確認してから切り替える。キーボードのリピート値・Dock サイズは標準オプションの整数型、トラックパッドのタップ設定は真偽値で書き込まれる。

preferences は宣言や Nix 世代を戻すだけでは元に戻らない場合がある。適用直前に変更対象の旧値・型・未設定状態を記録し、戻す場合は対象キーだけを復旧する。未設定だったキーは、値を書き込むのでなくそのキーの削除が必要。再起動やログアウトが必要なら、その都度確認する。

次の作業はパッケージや設定ファイルの復元とは分け、人間が行う。

- App Store / Apple ID へのサインイン、iCloud、Touch ID、TCC（アクセシビリティ・画面収録・自動化等）の許可。許可や認証を preferences 全量コピーで移さない。
- Xcode の初回起動・ライセンス確認、必要な SDK / Simulator platform の取得。署名証明書・provisioning profile・VPN 認証・秘密・Keychain は各製品の正規手順で復元する。
- Docker runtime の初期設定と必要な volume の移行。Hindsight のデータや認証は Nix 世代に含まれず、アプリ導入だけでは復元されない。
- 宣言していない入力ソース・ショートカット・Dock の並び・アプリ独自設定は、必要なものだけ個別に復元する。

## アプリ設定

Git 管理していないアプリ設定は `Dropbox/App` にも保存している。新しい Mac では必要なものを個別にインポートする。
