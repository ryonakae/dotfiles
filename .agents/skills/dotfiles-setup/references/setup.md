# 手動セットアップと復元

[README](../../../../README.md) の導入後に、使う機能だけ設定する。checkout は `~/dotfiles` に置く。
秘密の登録、認証、サービスの初期設定は、人間が sandbox 外の fish で行う。日常の dotfiles 操作は [dotfiles-setup](../SKILL.md) を入口にする。

## 目次

- [Nix の初回導入](#nix-の初回導入)
- [Nix の事前ビルド](#nix-の事前ビルド)・[適用と復旧準備](#nix-の適用と復旧準備)
- [共通ツール用の秘密](#共通ツール用の秘密)・[削除したファイルの復元](#削除したファイルの復元)
- [外部スキル](#外部スキル)
- [Claude Code](#claude-code)・[Pi](#pi)・[Hermes Agent](#hermes-agent)・[Herdr](#herdr)
- [Homebrew の補完対象](#homebrew-の補完対象)・[ランタイム](#ランタイム)・[Unity CLI](#unity-cli)・[Vim](#vim)
- [macOS と手動復元](#macos-と手動復元)・[アプリ設定](#アプリ設定)

## Nix の初回導入

新規 Mac 向けの Nix 本体の導入。この操作だけでは dotfiles や Homebrew の切替は行わない。
Apple Silicon Mac の通常のユーザーアカウントから、人間が Safehouse 外のターミナルで実行する。

```fish
cd ~/dotfiles
bash scripts/bootstrap-nix.sh --install
```

版固定済みの公式配布物を checksum 検証してから、multi-user インストーラを起動する。Flakes を使うため、従来の channel は追加しない。
APFS volume、mount 設定、build users、daemon、shell 初期化を変更し、必要に応じて sudo と、FileVault 利用時のシステム Keychain 操作を伴う。表示される変更内容を確認して進める。
既存の Nix や残存パスを検出した場合は、自動で上書き・修復しない。

完了後、新しいターミナルで次を確認する。PATH にない場合は、インストーラが案内した shell 初期化を反映してから再確認する。

```fish
nix --version
```

導入失敗時は出力を確認し、残存 volume やシステム設定を無断で削除して再実行しない。

## Nix の事前ビルド

Nix と Python 3 が必要（初回は Command Line Tools 付属の Python でも可）。まず Git 管理外の host 入力を準備する。

```fish
cd ~/dotfiles
mkdir -p ~/.config/dotfiles/host
cp -n config/nix/hosts/host.json.example ~/.config/dotfiles/host/host.json
```

`host.json` の `username` と `homeDirectory` を実機に合わせて編集する。この2項目は Nix store に入る公開情報として扱い、秘密や認証情報は書かない。

```fish
bash scripts/dotfiles.sh build
```

別の host 入力を使う場合は `build --host DIRECTORY` と指定する。ビルドは構成を適用せず、出力された store path に対する activation も実行しない。
通常の build は lock を更新しない。新しい Nix ファイルは対象を明示して Git に追加してからビルドする。未追跡ファイルを含めるために `path:.` へ切り替えたり、一括 stage したりしない。

追跡済みの通常設定・自作スキル・静的スクリプトは `~/dotfiles/config/` への live link で配布する。本文の編集やアプリからリンク先への書き込みは Git 差分になり、Nix 再適用は不要。Nix はリンクの配置を管理し、本文の復元は Git で行う。本体・外部 plugin・外部スキルは固定 store 管理。Nix executable パスや shebang の置換が必要な wrapper / fish 関数、macOS 宣言、生成 fish config は store 生成に残す。

依存を更新するときは、公開 input 名を指定する。

```fish
bash scripts/dotfiles.sh update nixpkgs
bash scripts/dotfiles.sh update hermes-agent
bash scripts/dotfiles.sh update nix-homebrew
bash scripts/dotfiles.sh update agent-skills
bash scripts/dotfiles.sh update all
```

nixpkgs の AI ツールは `update nixpkgs`、Hermes は `update hermes-agent`、スキル管理ライブラリは `update agent-skills` で更新する。`update all` は全公開 input を更新するが、Source registry の外部スキルは含まない。外部スキルは[専用の標準コマンド](#追加更新復元)で更新する。`update ai` や独自 updater は使わない。標準管理が難しい対象だけ、補完方法を相談して決める。

更新は update → lock 差分確認 → build → 承認した範囲で switch の順に行う。update は適用・起動を行わず、通常の build / switch は lock を更新しない。復元時は更新を混ぜず、既存の lock でビルドする。Nix 管理の Yazi プラグインを `ya pkg` で重ねて更新しない。

fish の `config.fish` は Home Manager で生成し、Git 外の実ファイルや旧 example をコピーしない。既存設定と衝突する場合は、人間が秘密と必要な非秘密差分を確認し、該当する Fisher 配置・リンクも保全して二重読み込みを避ける。日常のプラグイン更新に Fisher は使わない。`fish_variables` と履歴は Nix で管理しない。

### Homebrew 本体とアプリの管理

Homebrew 本体は `nix-homebrew` で導入・版固定する。新規 Mac で Homebrew の公式インストーラを別途実行する必要はなく、承認後の Nix 適用で導入する。Nix 本体の初回導入は引き続き必要。

既存 Mac は `autoMigrate` で Homebrew を引き継ぐ。適用時に Homebrew 本体の Git 追跡ファイル・`.git`・残存 vendor ディレクトリを削除して Nix 管理へ置き換える。既存の Cellar / Caskroom・ユーザー追加 tap 等は保持する設計だが、本体へのローカル修正は引き継がれない。ビルドだけでは移行しない。既存 Homebrew を移行する場合は、管理部分の保全・復旧範囲を確認して承認する。Nix 世代の rollback だけで移行前の管理方式へ戻るとは扱わない。

formula・cask・App Store アプリの一覧は nix-darwin で管理する。適用時の自動 update・upgrade・未宣言パッケージの削除は無効。tap は Homebrew 管理を維持し、Intel 用 Homebrew は追加しない。本体の更新は `update nix-homebrew` 後に build・適用する。Homebrew 配下のアプリの版まで `flake.lock` で固定されるわけではなく、アプリの更新は Homebrew やアプリ自身の更新機能で行う。

### 組織管理アプリをこの Mac だけスキップする

Zoom など、管理者が導入・更新するアプリは dotfiles の cask 宣言に残し、その Mac の Homebrew 標準設定で Bundle から除外できる。`brew --prefix` の下の `etc/homebrew/brew.env` に、例えば次を設定する。

```text
HOMEBREW_BUNDLE_CASK_SKIP=zoom
```

既存の `brew.env` があればファイルを上書きせず、既存の除外名も保って編集する。複数名は空白区切り。実ファイルはマシン固有のローカル設定として Git / Nix store に入れない。Homebrew 自身が読み込むため、sudo をまたいだ環境変数の継承を追加する必要はない。ユーザー別 `brew.env` に同じキーがあれば上書きされるので、適用時の skip 表示を確認する。

これは `brew bundle` のインストール対象から外す設定であり、既存アプリをアンインストールしたり、組織の管理を解除したりするものではない。PC 別の Nix 構成や全 PC 共通の除外は追加しない。

## Nix の適用と復旧準備

**適用範囲を確認・承認した後にだけ使う。** 秘密・サービス・OS 設定の変更を無断で含めない。対象ユーザーの通常の対話端末から、Safehouse 外で実行する。スクリプト全体を `sudo` で起動しない。

```fish
cd ~/dotfiles
bash scripts/dotfiles.sh switch
```

`--host DIRECTORY` も指定できる。候補 system と前の system profile を確認し、`switch` と入力して進める。入口は build と同じ snapshot を使い、対象ユーザーと HOME、Hermes の停止状態を確認してから、候補の `darwin-rebuild` の標準 `switch` 部分を sudo で実行する。非対話・root・Safehouse 内からは実行できない。

全アプリ停止・未宣言ツールの全件棚卸し・全設定の一括バックアップを常時の適用条件にしない。実際に衝突や書き込み競合がある場合は、その対象の種別・リンク先・必要な内容を確認し、個別に保全と操作範囲を承認する。退避時に競合する書き込み元だけを停止し、認証・session・DB・管理外の兄弟や共有正本を一括移動しない。既存バックアップへ上書きしない。

通常設定の衝突は Home Manager / nix-darwin の標準 activation 内の検査に任せ、force や自動退避オプションで通さない。アプリが管理リンクを実ファイル等へ置き換えた場合も衝突として保持する。外部スキルの[標準 link 配布](#外部スキル)では管理対象リンクの置換を受け入れるため、通常設定と区別する。

Hermes の配置変更に必要な停止は[管理関数](#更新停止既存環境の移行)で行う。入口は稼働状態を保存せず、自動停止・再開・独自バックアップ・自動 rollback を行わない。Nix daemon 等の変更も適用範囲として確認・承認する。

**全変更前の検査や原子的な適用を保証しない。** system profile は activation より前に更新される。後段で衝突・エラーになると、それ以前の設定変更が残り得る。標準 `check` / `--dry-run` activation を安全な事前検査として実行しない。失敗時は出力と変更済み対象を確認して再開か復旧を決め、bootstrap・switch・退避操作を最初から機械的に繰り返さない。

以前の nix-darwin 世代がある場合は標準の `--list-generations` / `--switch-generation` による復旧を検討できるが、実行は別途承認する。世代の切替は管理リンクを戻す操作であり、live link 先の本文は戻らない。本文は後続変更を確認して Git で別に戻す。Homebrew アプリ・preferences・DB・Docker volume・認証も世代の切替だけで戻るとは扱わない。

初回移行当時の退避・system 復旧の検討経緯が必要な場合だけ、[検討履歴](../../../../docs/plans/archived/2026-10-03-initial-migration-procedures.md)を参照する。現行の必須手順や、その資料だけでの実行許可ではない。

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

通常の `rm` は直接削除する。ごみ箱へ移す場合は `gomi ファイル` を明示する。
gomi のごみ箱は通常 `~/.local/share/Trash`。`XDG_DATA_HOME` 指定時はその配下の `Trash` を使う。
Finder のごみ箱とは別で、復元は gomi から行う。

```fish
gomi --config "$HOME/.config/gomi/config.yaml" --restore
```

エージェントの削除操作が終わってから、sandbox 外で実行する。
一覧から対象を選び、Enter で復元する。元の場所に別のデータがある場合は、先に退避して復元先を確認する。
復元・掃除中は別の rm / gomi を並行実行しない。
容量を空けるための永久削除は、人間が復元・バックアップを確認してから行う。自動掃除は設定しない。

旧 rm 転送から切り替える環境では、`~/.local/bin/rm`、fish の `rm.fish`、`conf.d/gomi.fish` の旧管理リンクを個別に確認・保全して除去する。起動済み fish には関数が残るため、新しい shell の `type -a rm` で通常の `rm` を参照することを確認する。日常の更新でこの退避を繰り返さず、gomi 本体・設定・ごみ箱の実体は残す。

## 外部スキル

外部スキルは agent-skills-nix の Source registry と標準 Home Manager モジュールで取得・選択・配布する。取得元と探索範囲は `config/nix/skill-sources/`、revision / hash は `config/nix/skill-sources.lock.json` で管理する。同じ repository の取得元は共有する。root の `flake.lock` は管理ライブラリ `agent-skills` などの固定に使い、スキルの取得元は root input に追加しない。

外部スキルは標準の `structure = "link"` で store へのリンクとして配置する。自作スキルは追跡済み正本への個別 live link を維持する。同名の自作スキルを外部スキルより優先し、Claude 側では Claude 専用の同名スキルを優先する。ドット始まりのディレクトリは配布しない。選択・配布先の正本は `config/nix/home/skills.nix` とする。

共通の配置先は `~/.agents/skills/`、Claude は `~/.claude/skills/`。Antigravity CLI は `~/.gemini/antigravity-cli/skills` から共通集合を参照する。Hermes / Pi 専用や Antigravity IDE 用へ配布を広げない。対象外の兄弟スキルと Claude の `synced` は保持する。

### 追加・更新・復元

追加時は `config/nix/skill-sources/` に取得元と必要な探索範囲を宣言し、スキルの選択を更新する。同じ repository を使うなら既存の取得元を共有する。新しいスキルを無条件に導入する広い `enableAll` は避け、同名の自作・Claude 専用の優先順位を維持する。取得元を追加するために `flake.nix` を編集する必要はない。

リポジトリのルートから、外部取得元を一括更新する。

```fish
cd ~/dotfiles
nix run .#skills-sources-lock
```

標準の npins ベースの更新処理で、全取得元の解決後に専用 lock を置き換える。宣言を変更した場合も実行する。既存の取得元も更新されるため、lock 全体の revision と選択結果を確認する。標準コマンドに取得元名を渡す単体更新機能はない。独自 updater や子 Flake は併用しない。

管理ライブラリだけなら `bash scripts/dotfiles.sh update agent-skills`、システムの全公開 input なら `update all` を使う。どちらも専用 lock の更新とは別操作。外部取得元の更新は、同じ repository から選択したスキルすべてに影響する。新規ファイルを Git ソースに含めてから、宣言・lock・選択の差分を確認してビルドする。

```fish
bash scripts/dotfiles.sh build
```

生成物を確認し、[適用条件](#nix-の適用と復旧準備)を満たした後に Safehouse 外の対話端末で実行する。

```fish
bash scripts/dotfiles.sh switch
```

新規 Mac の復元ではどちらの更新コマンドも実行せず、既存の `flake.lock` と `config/nix/skill-sources.lock.json` で build / switch する。`npx skills` による取得・コピーや旧 lock による復元は併用しない。自作本文の編集は live link に即時反映されるが、配置対象の追加・無効化には再適用が必要。

既存の実ディレクトリなどが新たに管理対象になる場合は、その対象だけを確認・保全して退避する。親ディレクトリ全体や `synced` は動かさず、実行時キャッシュを固定版として復元しない。日常の更新では標準モジュールの管理対象リンク置換を受け入れ、初回の未知の実体の保全を恒久的な上書き禁止へ拡張しない。

## Claude Code

Herdr の Claude hook は Home Manager が Herdr 本体と同じソースから配置する。Herdr の UI / CLI から Claude integration を再インストール・更新すると管理対象の hook と settings を書き換えようとするため、併用しない。

statusline は設定内の npm version を固定し、通常の `npx` で利用する。Nix build / activation にはインストールを含めず、初回取得には npm registry への接続が必要。

## Pi

`settings.json`、footer、fast-mode の設定3件は追跡済み正本への通常の live link。Pi からリンク先への書き込みは Git 差分になり、merger やローカル通常ファイルへの複製は使わない。日常の内容編集で Pi の停止を一律に求めない。アプリがリンク自体を置換した場合は衝突として保持し、force overwrite しない。認証・session を移行用設定や store へ含めない。

拡張の本体版は `config/.pi/agent/settings.json` の npm version / Git commit で固定する。これは npm の推移依存全体の lock ではなく、新規取得時の全機能の復元を保証しない。拡張のインストール先は通常の Pi 管理ディレクトリに保ち、Nix build / activation では取得・更新しない。Nix 管理の Pi 本体には自己更新コマンドを使わない。

OpenAI は Pi 内の `/login openai` から `Sign in with ChatGPT` を選んで認証する。
MCP の個人設定は `~/.pi/agent/mcp.json` に置く。OAuth が必要なサーバーには `pi mcp login <server>` を使う。

## Hermes Agent

gateway / dashboard はホストの launchd、Hindsight は Docker で動かす。同じ `~/.hermes` を使う Docker dashboard をホスト版と同時起動しない。

### 初回設定

本体は `ryonakae/hermes-agent` の `ryonakae` ブランチを lock で固定し、fork 同梱の Flake で導入する。起動定義は Home Manager が管理する。サービスモジュールは取り込まない。`hermes gateway install` 等による plist 再生成、旧 installer、Hermes 専用 mise / venv の復元は併用しない。`setup` のサービス導入・即時起動の質問には No を選ぶ。

ローカル音声認識・マイク入力用の `voice` グループは同梱しない。Apple Silicon では CTranslate2 の検証用依存を通じて PyTorch のソースビルドが必要になり得るため、fork 標準の `override` でこのグループだけ除外している。Hindsight、メッセージング、TTS 用の追加グループは残す。ローカル音声機能が必要になった場合は、この選択を見直して依存の dry-run を確認する。

利用を開始する Mac で、人間が sandbox 外から共通ツール用の秘密、Hermes の認証・設定、Docker を準備する。認証・DB・memory・session・cache は store に入れない。Hindsight の秘密は Git 管理外の `~/.hermes/hindsight/.env` に置き、`openai-codex` 用の `~/.codex` 認証も人間が復元する。

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

本体の更新は `bash scripts/dotfiles.sh update hermes-agent` と事前ビルドで準備する。`hermes-gateway update` / `hermes update` では更新しない。停止・必要なバックアップ・適用・再開は人間が別々に行う。dotfiles の適用入口は利用状態を保存せず、自動停止・再開もしない。

Home Manager は配置前に launchd の Hermes 登録、判別可能な Hermes プロセス、plist の所有関係を確認する。未停止・読み取り失敗・未知の形式なら配置を中止し、停止操作は行わない。確認はユーザーの GUI セッションを前提とし、全プロセスの所属や子プロセスの終了を追跡する仕組みではない。未知の既存 plist は強制上書きせず、確認済みの退避・復旧手順を用意する。旧定義や管理外プロセスの移行は、その環境で確認して行う。旧 `~/.hermes/mise.toml` や venv の整理も、その切替時に明示して行う。

Hindsight の停止・データ移行は別に承認する。必要な停止時は `~/.hermes/services` で `docker compose down` を実行し、データ volume を削除しない。

### リモートアクセス

dashboard は `0.0.0.0:9120` を使うが、採用済み Hermes では認証 provider が必要。`--insecure` は認証を迂回しない。人間が認証を設定してから起動し、信頼できる LAN / VPN 内で使う。

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

Agent Context の installer は release binary と同じ release の checksum を取得するため、ネットワークが必要。source commit の固定は binary の Nix 固定出力管理とは異なる。Shepherd 本体と plugin は復元対象から外す。既存導入物・稼働中 daemon・保存データの停止や削除は、宣言の変更と分けて行う。

Zerdr は Homebrew 版を使う。導入対象は nix-darwin で宣言するが、本体は Homebrew が管理し、`flake.lock` による版固定・ロールバックの対象にはならない。

Zerdr のローカルプラグインは本体が `~/Library/Application Support/dev.ryonakae.zerdr/` に配置する。切替時は、開発版を拾わないよう Homebrew 版のパスを明示して生成・登録する。古い絶対パスを含む manifest をコピーしない。

```fish
set -l zerdr_bin (brew --prefix ryonakae/tap/zerdr)/bin/zerdr
$zerdr_bin setup install
```

この操作は Herdr の登録と Zed tasks を更新するため、切替時に実行する。実行後に両方が Homebrew 版の実行先を参照することを確認する。Zed tasks は Nix 管理に追加していない。
worktrunk プラグインには `wt >= 0.60.0`、`fzf`、`jq` が必要。
導入後は `herdr plugin list` で確認する。

worktree の作成・削除には Worktrunk を使う。Herdr 本体の作成機能では Worktrunk の配置・hooks・ignored ファイルのコピーを引き継げない。
`herdr worktree open` は既存 checkout の登録に限って使う。
設定変更後は `herdr config check` で検査し、`herdr server reload-config` で反映する。

## Homebrew の補完対象

1Password CLI と Google Cloud CLI は Homebrew cask で管理する。依存ライブラリは依存元のパッケージ管理に任せ、直接の導入一覧へ重ねて追加しない。以前の暫定保持対象だった `icu4c@76` / `libpq` / `oniguruma` / `pcre2` / `postgresql@17` は直接管理せず、必要なら移行時に手動導入する。PostgreSQL のデータ・サービスは別扱いとし、宣言からの除外を理由に削除・停止しない。Homebrew の自動 cleanup は無効のまま維持する。

## ランタイム

Nix / Homebrew で管理するのは合意済みの共通環境だけ。他プロジェクトのツール・ランタイムは、そのプロジェクトの設定と mise 等に任せる。npm / uv のグローバル配置やインストール済みという事実だけで dotfiles 管理へ追加しない。未宣言の導入物の全件分類を切替条件にせず、既存実体や他プロジェクトの設定を一括削除・変更しない。

`~/.local/bin` に Node / npm のリンクを置く場合は、Hermes 専用の実体ではなく mise の shim を参照させる。
Node の問題を直すためにこのディレクトリの PATH 優先順位を変更する場合は、他のユーザー配置 CLI への影響も確認する。

## Unity CLI

Homebrew の `unity-cli` cask で本体を管理する。更新は `brew upgrade --cask unity-cli` を使い、公式 installer や `unity self-update` を併用しない。導入対象は Nix で宣言するが、本体の版は `flake.lock` に固定されない。Editor・追加モジュールはプロジェクトに必要な版を CLI / Hub で管理し、認証・プロジェクト登録等の状態は Git / store に入れない。

旧 installer から切り替える場合は、`~/.unity/bin/unity` と `~/.config/fish/conf.d/unity-cli.fish`、そこから参照する PATH 設定を確認・保全し、承認後に個別に整理する。新しい shell で `type -a unity` を確認し、Homebrew 版が選ばれることを確かめる。旧本体を残したまま Homebrew 側だけ更新しても、PATH によっては旧本体が使われ続ける。既存の Editor・Hub データは削除しない。

`brew uninstall --zap unity-cli` は使わない。cask の `zap` 対象に `~/Library/Application Support/UnityHub` が含まれ、CLI 本体以外の状態まで削除するため。

導入・更新方法は [Unity 公式手順](https://docs.unity.com/en-us/unity-cli/use-unity-cli#install-with-a-package-manager)、削除対象は [cask 定義](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/u/unity-cli.rb)を参照する。

## Vim

Vim は外部プラグインを使わない補助的な編集用の最小構成。NeoBundle の導入・更新は不要で、本体は nixpkgs と一緒に更新する。
旧 `~/.vim/bundle` の実体は設定変更だけでは削除しない。不要物の整理は対象を確認して行う。

## macOS と手動復元

Nix 管理する preferences は `config/nix/darwin/preferences.nix` を正本にする。標準オプションで現在の動作を表現できる範囲だけを管理し、独自の適用スクリプトで補完しない。明示されていないキーへ推測で値を設定しない。管理対象を GUI で変更しても、次回 switch で宣言値へ戻る。適用時は標準 nix-darwin モジュールが Dock を再起動するため、作業中の UI への影響を確認してから切り替える。キーボードのリピート値・Dock サイズは整数型、トラックパッドのタップ設定は真偽値で書き込まれる。

preferences は宣言や Nix 世代を戻すだけでは元に戻らない場合がある。適用直前に変更対象の旧値・型・未設定状態を記録し、戻す場合は対象キーだけを復旧する。未設定だったキーは、値を書き込むのでなくそのキーの削除が必要。再起動やログアウトが必要なら、その都度確認する。

次の作業はパッケージや設定ファイルの復元とは分け、人間が行う。

- App Store / Apple ID へのサインイン、iCloud、Touch ID、TCC（アクセシビリティ・画面収録・自動化等）の許可。許可や認証を preferences 全量コピーで移さない。
- Xcode の初回起動・ライセンス確認、必要な SDK / Simulator platform の取得。署名証明書・provisioning profile・VPN 認証・秘密・Keychain は各製品の正規手順で復元する。
- Docker runtime の初期設定と必要な volume の移行。Hindsight のデータや認証は Nix 世代に含まれず、アプリ導入だけでは復元されない。
- 入力ソース、macOS 標準ショートカット、アプリ別ショートカット、デバイス別キー割り当て、バッテリー／AC 別の電源設定、未宣言のアプリ独自設定は必要なものだけ個別に復元する。
- Dock の固定項目・並びは Nix 管理するが、項目を宣言してもアプリ本体は導入されない。Chrome 製アプリなど、別途復元が必要なものは先に用意する。未導入のアプリは Dock 項目だけあっても起動できない。

## アプリ設定

Git 管理していないアプリ設定は `Dropbox/App` にも保存している。新しい Mac では必要なものを個別にインポートする。
