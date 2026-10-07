# Nix・Homebrew・mise の責務分離 Implementation Plan

## Requirements

日常のツール更新と設定配置のための Nix build / switch を減らす。macOS の宣言管理は残し、通常設定は HOME から Git 正本へ直接 symlink で接続する。Home Manager の store 経由リンクによる、Claude Code 等からの編集の不便を解消する。

2026-10-07 の会話で合意した分担:

| 対象 | 管理主体 |
|---|---|
| macOS 設定・Nix 本体 | nix-darwin |
| Homebrew 本体 | nix-homebrew |
| 普段使う CLI / GUI / App Store アプリ | Homebrew。導入一覧は引き続き Nix の `homebrew.*` |
| Bash・fish・mise 本体と mise の補完用 usage | Nix |
| 共通 Node / Python / Ruby / Bun | mise |
| 通常設定・自作スクリプト・自作スキル | `config/` を正本にし、mise で直接リンクを配置 |
| Hermes fork・外部スキル・fish / Yazi 外部 plugin | 必要な Nix 管理を残す。理由は後述 |

追加合意:

- `config/.config/fish/config.fish` は Git 管理してよい。example は不要。旧 `config.fish.example` はすでに削除済みなので再作成しない。
- Herdr 本体を Homebrew に移し、Claude hook は Herdr 標準 installer で管理する。Claude settings の Herdr 用登録変更を含めるが、既存変更を保持して差分を確認する。
- `.agents/skills/dotfiles-setup/SKILL.md` と同梱 `references/setup.md`、`README.md`、ルート `AGENTS.md` を更新する。

制約・対象外:

- 自前 Brewfile、mise による brew / cask / App Store 管理、独自 updater、独自 symlink 管理基盤は作らない。mise の track / history watcher / 双方向同期も使わない。
- macOS preferences、Hermes fork の依存調整、停止・再開方式、Safehouse の保護範囲、外部スキルの取得元と版を変更しない。Home Manager 廃止自体を目標にしない。
- 移管と無関係なアプリ更新・再インストール、他プロジェクトの mise 設定変更、全件 cleanup / prune / GC、秘密・認証・DB・session の移行は含めない。
- 宣言の変更・検証と実機適用を分ける。計画承認だけで switch、サービス操作、Keychain 操作、既存ファイルの退避を実行しない。
- 調査開始時からの Claude settings、Zed settings、Pi settings、Pi fast-mode config の既存差分を保持する。Herdr 登録以外を移行の都合で書き換えない。

関連履歴は [Nix 移行の dig log](../dig/2026-10-03-nix-migration.md) と [旧計画](2026-10-03-nix-migration.md)。本計画は旧来の「通常 CLI・共通ランタイムを Nix、通常設定を HM live link に統一」という管理方針を置き換える。過去の実機操作・検証記録を新方式の検証結果には流用しない。旧計画の未完了事項も自動的に完了扱いしない。

## Implementation Decisions

### 1. 本体の移管と版差

`config/nix/home/packages.nix` の通常 CLI を `config/nix/darwin/homebrew.nix` に移す。`programs.zoxide` のような暗黙導入と、wrapper が供給していた実行時コマンドも対象にする。移管先の名称が異なるもの・注意対象は以下。

| 現在の Nix 名 | Homebrew の宣言 |
|---|---|
| `awscli2` | formula `awscli` |
| `gws` / `mole-cleaner` | formula `googleworkspace-cli` / `mole` |
| `antigravity-cli` / `claude-code` / `codex` | 同名 cask。Antigravity IDE ではなく CLI |
| `agent-safehouse` | formula `eugene1g/safehouse/agent-safehouse` |
| `dotenvx` | formula `dotenvx/brew/dotenvx` |
| `keifu` | formula `trasta298/tap/keifu` |
| `herdr` / `pi-coding-agent` | 同名の core formula |
| HM の `programs.zoxide` | formula `zoxide` |

Bash は nix-darwin の標準導入・初期化を維持し、mise と補完用 `usage` も Nix に残す。それ以外の通常 CLI は、調査した同名 core formula を使う。`uv` は CLI として Homebrew に移す。Pi は現行と同じ `earendil-works/pi` 系列を維持する。Homebrew の `gws` は別製品なので使わない。Pi 等の Nix wrapper から暗黙に得ていた `ripgrep` / `fd` の可用性を確認し、必要な直接利用コマンドは Homebrew 宣言に含める。

Safehouse・dotenvx・keifu の取得元は、それぞれ upstream が案内する既成の公式 tap。既存 `ryonakae/tap` に加えてこの3件を Nix で宣言する。独自 tap / packaging は追加しない。

Homebrew の標準配布版は旧 Nix 版と一致する保証がない。調査時には OpenCode が `1.18.34 → 2.0.20`、Pi が `1.0.2 → 1.0.4`、terminal-notifier が `2.0.0 → 3.1.0` という差があった。これは実機の使用版ではなく、固定 nixpkgs と公開 formula の比較である。切替直前に実際の使用版と導入候補を確認し、移管対象の版差を実機適用の承認範囲へ含める。重大な非互換が見つかったら相談し、旧版用 packaging や無断の Nix 残留で解決しない。

nix-homebrew の `autoMigrate`、既存の GUI / App Store 一覧、`homebrew.onActivation` の `autoUpdate = false` / `upgrade = false` / `cleanup = "none"` は維持する。root と外部スキルの lock は、移管のためにまとめて更新しない。

### 2. 配置の正本と所有権

リポジトリ直下の `mise.toml` を配置宣言の正本とする。通常の本文は `config/` に残し、配置は `mise -C ~/dotfiles dot apply` で明示的に行う。グローバルなツール指定は `config/.config/mise/config.base.toml` に分離し、HOME の `~/.config/mise/config.toml` から直接リンクする。Nix build / switch に mise apply や runtime install を埋め込まない。

- mise 2026.9.18 で確認できた `[dotfiles]`、`symlink`、`symlink-each`、必要な箇所の `manifest = "git"` を使う。新しい dotfile groups を使うためだけに mise / nixpkgs を更新しない。
- パスの個別列挙を避けるというユーザーの指摘を受け、同じ相対位置への通常配置は `config/` → HOME の `symlink-each` 1件にまとめる。対象は Git index と明示した除外に限定し、現行 HM の配置範囲を引き継ぐ。Nix ソース、生成 wrapper、テスト、example、秘密・実行時状態を無差別に展開しない。
- mixed directory はファイルごとの直接リンクで統合し、認証・履歴・キャッシュ・管理外の兄弟を含む親ディレクトリを丸ごと置換しない。各エージェントの共通指示と mise の設定ファイル名など、配置先が異なる例外だけを個別指定する。Pi、自作 Yazi plugin、Hermes の SOUL / Compose も従来の配置先を維持する。
- 自作スキルも共通向け・Claude 向けの2つの glob と `symlink-each` / Git manifest で配置し、名前を列挙しない。ディレクトリ自体でなく追跡済みの各ファイルを正本へ直接リンクする。Claude 専用の同名スキルが必要な場合だけ、その宛先を明示して共通 glob より優先させる。Nix の外部スキル選択は、この配布対象を参照して shadowing を決め、同じ宛先を二重所有しない。Antigravity CLI から共通スキル集合への参照も維持する。
- 本文編集は再配置不要。Git manifest で走査する範囲の増減は apply で反映する。明示エントリの削除・改名は、宣言を消す前に対象を確認し、標準の unapply で該当する管理リンクだけを解除する。宣言削除だけで HOME 側も消えるとは扱わない。
- 通常の自作スキル追加では名前の配置宣言を増やさず、Git 追跡と apply で反映する。スキル単位の削除・無効化は移動前に対象の unapply を行う。glob の一致から消えた宛先が自動解除されるとは仮定しない。外部スキルとの優先関係が変わる場合だけ Nix 側の選択変更・適用も必要になる。
- apply 前に対象の差分と実体・リンク先を確認する。未知の実ファイル・ディレクトリ・別リンクは保持して相談し、`--force`、一括退避、親ディレクトリ削除で解決しない。mise の標準 apply を、未知の symlink を必ず拒否する仕組みとは仮定しない。

### 3. fish・ランタイム・起動経路

`config.fish` は現在の公開済み `shell-init.fish` / `interactive-init.fish` と必要な初期化から構成する。Git 管理外の旧実ファイルをそのまま stage せず、保全が必要な場合は人間が先に扱う。旧計画では追加で引き継ぐ非秘密差分はないと確認済みであり、旧本文や秘密を読み出して移植しない。`.gitignore` の `config.fish` 除外を外し、秘密・実行時状態の除外は残す。

Home Manager の fish 標準生成処理は、Nix profile・外部 plugin 等のために必要な補助ファイルへ配置先を分離し、Git 正本の `config.fish` から読み込む。HOME の `config.fish` 自体を HM が生成しない。bobthefish / fzf plugin の取得・標準ロード処理は Nix に残し、Fisher や独自 plugin manager は導入しない。mise / zoxide の初期化と通常の環境設定は Git 側へ置き、二重 activation を防ぐ。

共通ランタイムは Node 22、Python 3.11、Ruby 3.3 と現在の Bun 系列を維持し、最初の宣言は実機の使用版を確認して決める。Ruby の `compile = true` は勝手に変更せず、ビルドに必要な依存を確認する。Brew CLI が内部で利用する Node / Python / Ruby と、Hermes の Nix 内部ランタイムはこの共通環境とは別の依存として扱う。

対話 shell は mise activation、非対話の agent / launchd 子プロセスは明示 PATH に含めた mise shims で共通ランタイムを利用できるようにする。ただし Hermes 自身や各 package が固定する内部依存は shim で置換しない。プロジェクト内ではそのプロジェクトの版選択を維持する。agent の cwd を配置用リポジトリへ変更せず、Hermes service の cwd は `~/.hermes` のままにする。既存の `.local/bin` や universal PATH による shadowing は関連項目だけ確認し、全消去しない。

通常 CLI の Nix 絶対パス置換は解除する。ただし安全上固定していた実行先を無検証の PATH 任せにはしない。Safehouse / dotenvx は Apple Silicon Homebrew の既知の実行先で解決し、Hermes は引き続き Nix fork を参照する。Hermes の実行先だけを Nix 補助定義または安定した Nix 管理パスから供給し、通常の fish 関数まで store 生成に戻さない。

Nix 操作入口 `scripts/dotfiles.sh` は、mise の導入・配置・プロジェクトごとの Python に依存せず実行できるよう、前提の Command Line Tools 付属 `/usr/bin/python3` を使う。`build` / `switch` / `update` の引数、Git snapshot、lock 不変、確認と権限境界は変更しない。

Codex は Homebrew の標準配布をそのまま使う。Nix パッケージ固有の daemon 自動起動無効化はユーザーの要件ではなく、移行先で再現しない。これを目的とする `/etc/codex/config.toml` の追加や CLI override は行わず、既存のユーザー明示設定を保持する。Pi の `PI_TELEMETRY=0` は起動経路で引き継ぐ。Nix 専用の自己更新案内は Homebrew 運用へ修正し、別の installer / self-update を重ねない。

### 4. 残す Nix 管理と Herdr の引継ぎ

Hermes の fork package、`voice` group 除外、launchd plist、service wrapper、停止確認は Nix に残す。生成物は Hermes 本体の Nix 実行先を固定する一方、Safehouse / dotenvx と外部コマンドは新しい管理先へ接続する。環境注入は sandbox の前、復号失敗・必須 profile 欠落は fail closed、HOME 許可・profile 順・引数・終了コード・TMPDIR 補正を維持する。service の feature を対話用の集合に広げない。

Hermes の操作は既存の `hermes-gateway` / `hermes-dashboard` から fork 標準処理を使う。switch は停止確認と plist 所有・改変検査だけを行い、自動停止・再開・状態保存・installer による plist 再生成を追加しない。

外部スキルは現在の Source registry、専用 lock、選択、標準 HM 配布を維持する。自作の優先判定と配置所有権だけを新方式に合わせる。外部 fish / Yazi plugin も固定取得を残し、Brew Yazi との互換性を受入時に確認する。plugin 更新を本体移管へ混ぜない。

Herdr の Claude hook は HM 配置を外し、Homebrew で導入した本体の `herdr integration install claude` に一本化する。本体に埋め込まれた同版 hook を使い、別版の Nix ソースから取り出さない。installer は settings の symlink を追って Git 正本を更新し得るため、Herdr 登録以外の既存差分を保持する。実際の設定への適用前に、非秘密の検証用 settings で登録の変更範囲を確認する。Herdr の plugin、session、log の再インストールや整理はしない。

## Tasks

タスク1〜4は安全に組み合わせられる候補構成を作り、実機の所有権移行はタスク6でまとめて行う。実装は既存テストの適切な境界を使って TDD で進める。

実装開始時の review base は `837aa5a64b136af0861753265b1ab919e1012712`。`master` と `origin/master` は一致し、既存 staged 変更はない。Claude / Zed / Pi の既存4差分は commit 対象から除外する。実機で確認した初回ランタイム候補は Node `22.23.3`、Python `3.11.17`、Ruby `3.3.10`、Bun `1.4.2`。導入はまだ実行していない。

- [x] **1. 本体の導入宣言**: `config/nix/home/packages.nix`、`config/nix/darwin/homebrew.nix`、`config/nix/home/fish.nix` を変更し、通常 CLI と共通ランタイムを Nix のユーザー向け導入集合から外す。
  - 暗黙導入、Nix wrapper に隠れていた依存も確認する。Hermes 等の内部 closure を、ユーザー向け重複導入と誤認して削らない。
  - `flake.nix` の不要になった unfree 許可等は利用がなくなったものだけ整理する。fish / mise の導入と Nix formatter は保持する。
  - **ユーザーによる追加判断**: mise と補完依存 `usage` を Nix に残す。Home Manager の mise モジュールを維持し、`usage` の Homebrew 宣言は除去する。設定・activation は引き続き Git 側で管理する。
  - **候補実装**: 通常 CLI を Homebrew 宣言へ移し、共通 runtime と不要な unfree 許可を Nix から除去した。Pi の暗黙依存だった ripgrep と zoxide も直接宣言した。Nix 構文・nixfmt と実 flake check / system build が成功。生成 Home Manager profile は fish / mise / usage / Hermes のみ。system profile の Bash はユーザー承認により標準の Nix 管理を維持し、Brew 宣言から除去した。
- [x] **2. 直接リンクと所有権の分離**: `mise.toml` を追加し、`home/files.nix`、`pi.nix`、`skills.nix`、`protection.nix`、`hermes.nix`、`default.nix` から通常配置だけを移す。
  - `scripts/tests/test_dotfiles_links.py` を追加し、実 mise と使い捨て HOME / Git fixture で配置契約を検証する。独自の配置処理や状態台帳は作らない。
  - 自作スキルの glob 配置・Claude 専用例外と外部選択を同じ管理集合に合わせる。共通指示の正本・既存 symlink は実ファイルへ複製しない。
  - **候補実装**: `mise.toml` をディレクトリ単位の Git manifest と例外指定へ整理した。実 mise の隔離 HOME 検証で、直接編集・冪等性、追跡ファイル増減、衝突保持、unapply、共通指示、スキル共有、除外、Claude 専用例外を確認した（既存5件＋追加2件成功）。実 HOME は未変更。
  - 空になった module や不要な `dotfilesLink` 等の引数・imports は同じ変更で除去する。
  - HM 側の通常配置を除去し、外部 Yazi plugin・外部 skills・Hermes 生成物・fish 補助を残した。`pi.nix` / `protection.nix` と不要な引数を除去。自作 skill の shadowing は mise の glob source と明示例外を参照する。実 build の HM リンク42件と mise 配置先299件を照合し、同一パス・親子パスの所有重複なし。通常設定・自作スキル・Herdr hook の HM 所有解除を生成物で確認した。
- [x] **3. fish と共通ランタイム**: `.gitignore`、`config/.config/fish/config.fish`、公開済み init ファイル、`config/.config/mise/config.base.toml`、`home/fish.nix` を変更する。
  - Nix 補助設定と Git 側初期化を分離し、plugin / 補完 / `zoxide --cmd cd` の従来機能と、対話・非対話のランタイム選択を保つ。
  - `scripts/dotfiles.sh` の Python を安定化し、`test_dotfiles_cli.py` に入口の循環依存と cwd に関する必要な回帰ケースを加える。bootstrap 本体の仕様は変更しない。
  - **入口の独立成果物 `4c18231`**: shell 入口を `/usr/bin/python3` に固定した。壊れた PATH 上の Python と別プロジェクト cwd を扱う回帰テストは変更前に終了127で失敗し、変更後に成功。`uv run --no-project python scripts/tests/test_dotfiles_cli.py` は16件成功・skipなし。Bash 構文・対象差分も確認済み。
  - **操作ミスと維持の承認**: 旧 `config/.config/fish/config.fish` は Git 管理外の通常ファイル（3032 bytes）だった。必要な保全の扱いを確認する前に、公開済み init ファイルを source する11行の公開版へ上書きしてしまった。旧本文は読み出しておらず、この作業でバックアップも作成していない。報告後、ユーザーから現在の公開版を維持する承認を得た。現在の本文が作成した公開内容と完全一致し、APIキーを含まないことを確認した。Git 管理の init ファイルと Nix fish module でも、資格情報の設定・既知のキー形式は検出されなかった。承認後の build に向け、公開版と `mise.toml` の2件だけを明示 stage した。
  - `.gitignore` の除外解除、HM 生成設定の `nix-init.fish` 分離、対話 mise / zoxide activation、非対話 shims、確認済み4 runtime の exact pin を実装した。fish 構文と、隔離 HOME の対話/非対話 × 既定/明示 `MISE_DATA_DIR` の4条件の初期化・PATH・cwd 検証は成功。生成された HM 補助の配置先・構文・二重 activation の不在も確認した。実 runtime の導入と、切替後の実 plugin 動作は未検証。
- [x] **4. 起動・保護・連携**: `config/.config/fish/functions/` の対象関数、`run-with-agent-env.sh`、`home/protection.nix`、`home/hermes.nix` を新しい実行先へ接続する。
  - `test_agent_runtime.py` と `test_hermes_tmpdir.py` で関連する PATH / cwd / 失敗経路を補強する。`check_dotenvx_runtime.py` の HM 固定の実行先を新方式に直す。
  - Pi の telemetry 抑止を起動経路へ移す。Codex は既存のユーザー設定を保持して Homebrew 標準版へ移す。必要な設定変更が既存のユーザー変更と競合した場合は止めて確認する。
  - **要件の誤認を訂正**: ユーザーの指摘により、Codex の daemon 自動起動を既定で無効にする条件と、それを理由にした停止を撤回した。Nix パッケージ側の補正をユーザー要件と誤認していたもので、system defaults の追加承認は不要。Codex 用の実設定・コードは変更していない。
  - Herdr hook の旧 HM 宣言を除去し、標準 installer の検証用 fixture と実機の引継ぎ手順を用意する。実機の installer 実行はタスク6へ残す。
  - **候補実装**: Safehouse / dotenvx の Brew 固定参照、Hermes の安定参照、非対話 shims、Pi telemetry を実装した。`test_agent_runtime.py` 9件、`test_hermes_tmpdir.py` 1件（21 subtests）が成功し、worker の差分を親が確認した。fish / shell / Python / Nix 構文も成功。生成 wrapper は Nix shebang / Hermes 絶対パス以外が正本と一致し、Bash 構文も成功。plist の実行先、cwd、shims、Disabled / RunAtLoad / KeepAlive を生成物で確認した。
  - 隔離 HOME の Herdr installer 検証は、既存 Brew `0.9.0` と現行 Nix `0.9.3` で成功。settings symlink、無関係な設定・hook、実行属性、冪等性を確認した。実設定は変更せず、候補版の Brew 導入検証や実機 hook 更新を済ませたとは扱わない。
- [x] **5. 運用文書と指示**: `dotfiles-setup` の `SKILL.md` / `references/setup.md`、`README.md`、`AGENTS.md` を新分担へ更新する。
  - 運用の正本は同梱 `setup.md` に保つ。README は分担と入口、AGENTS は編集・所有権・検証上の制約に絞り、パッケージ一覧や設定値を重複掲載しない。
  - config 本文編集・配置増減、CLI の導入 / 更新 / 削除、runtime、Nix 基盤、外部スキルで手順を分ける。通常のツール更新を一律 `update nixpkgs` へ誘導しない。
  - Homebrew の日常更新は `brew update && brew upgrade`、本体更新は Nix。自己更新を抑止する CLI は、使用する Homebrew 版での `auto_updates` / `:latest` の扱いを確認し、必要な場合だけ対象を限定して `--greedy` 等を案内する。全 cask の更新へ無条件に広げない。削除は Nix 宣言から除外したうえで対象の `brew uninstall`。`cleanup = "none"` では宣言削除だけでアンインストールされないことを明記する。
  - mise の配置と runtime の install / upgrade を区別し、初回の版維持と更新時の指定方法を説明する。自作スキルの追加・無効化、明示リンクの unapply、外部との優先関係変更も扱う。
  - 初回導入と既存機の切替・復旧を区別する。Herdr integration の旧併用禁止を新運用へ置換し、更新時に本体と hook の整合を確認する。Hermes の installer 禁止は維持する。
  - fish の生成 config 前提、Pi / Vim / 通常 CLI の Nix 更新案内など、変更で古くなる記述を対象を絞って除去する。旧計画の現行再開指示には本計画への参照を加え、過去の記録は保持する。
  - **候補実装**: 指定の文書5件を更新し、親が差分を確認した。作業者によるリンク47件の検査と対象 diff check は成功。`setup.md` は300行超で、依頼外の全体再構成は行っていない。
- [ ] **6. 承認下での切替と受入**: 下記手順で実機を切り替え、配置・解決先・起動経路を確認する。実施範囲と未検証の実サービス・別 Mac の範囲を記録する。

## 現在の判断待ちと検証状況

- **Bash の管理先は承認済み**: nix-darwin の標準 `programs.bash.enable = true` による導入・初期化を維持し、Bash も Nix 基盤に残すことをユーザーが承認した。Homebrew の `bash` 宣言だけを除去し、Bash の初期化や PATH の追加変更はしていない。
- Task 3 の上書きについては、ユーザーが公開版の維持を承認し、APIキーを含まないことを確認済み。
- Safehouse 内の評価拒否は、ユーザーが Herdr の通常ペインで評価・build のみを承認したことで検証を進められた。`bash scripts/dotfiles.sh build` の flake check / system build は終了0。Bash / usage を Nix に残す候補は `/nix/store/5axbnzlq4dp2qrg8x6xpvdj0a6nmvbsa-darwin-system-26.11.4cff07d`。生成 Brewfile は40 formula で、Bash / usage を含まない。HM generation は `/nix/store/zimzvifcg7gn2j5l8k3sd2cdx04jrfl8-home-manager-generation`。root / registry lock は変更なし。ログは `/tmp/dotfiles-hybrid-build.GRTGTZ/build-bash.log`。
- 新しい通常ペインでは既存 mise `2026.6.14` が root `mise.toml` の未信頼警告を出した。build は独立して成功しており、trust の変更はしていない。実配置時には Nix mise の解決先と、確認済み設定に限定した trust を扱う。
- Task 1〜5 は検証済み候補として、入口独立化 `4c18231` と責務分離の2単位で local commit にまとめる。責務分離の設定・配置・起動経路は相互依存するため、ファイル種別で分割しない。独立レビューはこの候補全体を対象とし、Task 6 の実機操作とは区別する。
- install / update / switch、実 HOME の mise apply、実設定への Herdr integration、サービス・Keychain 操作は未実施。実機受入と独立レビューのゲートが残るため、archive / push は行わない。既存4件の他者差分は未読・未編集のまま保持し、commit に含めない。

## 切替・復旧手順

1. **候補の事前検証**: 構文・関連テスト・Nix build を完了し、新 HM の配置集合から mise 所有先が外れていることを確認する。旧 system generation、対象リンクの種類と宛先、実際の CLI / runtime 版を記録する。設定内容や環境変数を全量取得しない。
2. **切替範囲の確認**: 追加 formula / cask / tap、移管対象の版差、リンク引継ぎ、Herdr 登録の変更範囲を提示して実機適用を承認してもらう。衝突対象だけを個別に保全する。稼働する Hermes は既存管理関数で別途停止し、リンク切替と競合するアプリだけ必要に応じて停止する。
3. **利用可能性の準備**: 既存 Mac では、承認した Homebrew の移管対象と mise runtime を、旧実行環境を失う前に準備して確認する。Nix 宣言を正本にした対象限定の標準 install を使い、全体 upgrade はしない。runtime の候補設定を明示して準備し、旧実行先からの切替前に不足を検出する。mise の trust は確認した当該設定だけを対象とし、信頼検査を全体で無効化しない。
4. **Nix の所有解除**: Safehouse 外の通常の対話端末から既存 `bash scripts/dotfiles.sh switch` を実行する。switch 自身が取得した snapshot に対して check / build / apply する契約を維持する。mise に先に同じ宛先を書かせて HM と競合させない。
5. **mise の配置**: HM の終了コードと実際の解除済み範囲を確認し、残った旧リンクがあれば由来を確認して扱う。`mise -C ~/dotfiles dot apply` で直接リンクを配置する。新規 Mac では Nix による fish / mise / Homebrew 導入後にこの配置と runtime install を行う。利用可能な作業用 shell を、設定・runtime の確認が終わるまで残す。
6. **Herdr integration**: 旧 HM hook が解除されたことを確認し、Homebrew 本体から標準 installer を実行する。Git 正本への settings 差分が承認範囲内で、hook が現行本体に対応することを確認する。別の integration / plugin installer をついでに実行しない。
7. **受入**: 新しい shell の本体・runtime の解決先、直接リンク、主要 CLI と設定編集を確認する。Hermes を使わない Mac で検証のためにサービスを起動しない。必要なサービス再開は受入後に別途承認し、既存管理関数から行う。

途中失敗時は進行を止め、Nix profile・HM・mise・Homebrew・Herdr のどこまで変更されたかを確認する。switch や apply を最初から自動再試行しない。旧 Nix 世代へ戻す場合も、mise が所有する該当リンクを確認して標準 unapply 等で引き渡してから適用し、未知の実体を force しない。本文の復旧は後続変更を確認して Git で別に扱う。Nix の世代切替で Brew 本体以外のパッケージ版、mise の導入済み runtime、settings 本文、preferences、DB が戻るとは保証しない。旧世代・退避物の削除や GC はこの移行に含めない。

## Final Validation

### 継続して守る契約の自動検証

- [x] **直接リンク配置**: `uv run --no-project python scripts/tests/test_dotfiles_links.py`。実 mise、隔離した HOME / mise 状態ディレクトリ、Git fixture を使用する。リポジトリ外 cwd と空白を含むパスでも正本へ直接リンクし、編集が正本へ届くこと、再適用が冪等なこと、走査対象の追加・削除と明示 unapply が管理外の兄弟・実ファイルを壊さないことを確認する。秘密・実行時状態の非配布と、スキルの同名優先・二重所有の不在も該当する配置境界で確認する。実 HOME や実秘密を fixture に使わない。
- [x] **Nix 入口**: `uv run --no-project python scripts/tests/test_dotfiles_cli.py`。mise Python が未導入または project cwd で利用不能でも入口が動き、snapshot / lock / 構成名 / 確認 / Hermes 停止確認の既存契約を維持する。実 Nix がなく integration が skip された場合は未検証として残す。
- [x] **保護された起動**: `uv run --no-project python scripts/tests/test_agent_runtime.py` と `uv run --no-project python scripts/tests/test_hermes_tmpdir.py`。sandbox 前の注入、引数・空引数・終了コード、最小の非対話 PATH、cwd、profile 順・欠落、対話 / service の feature 差、TMPDIR を確認する。既存の保証は重複して作り直さない。
- [x] **構文と候補構成**: 変更した fish は `fish --no-execute`、shell は shebang の shell の `-n`、TOML は parser で検査する。新規の非秘密ファイルだけをパス指定で Git source に含め、`bash scripts/dotfiles.sh build` を実行する。生成された fish 補助・Hermes wrapper / plist と HM 配置を確認し、原本だけのテストで Nix 生成結果まで保証したことにしない。root / registry lock の不要な変更がないことも確認する。

### 移管に固有の確認

- [ ] **実機の所有権と使い勝手**: `readlink` で通常設定・Git 管理 config.fish が `/nix/store` を挟まず正本へ向くことを確認する。非秘密の検証用リンクを Claude Code 等から編集し、正本へ反映できることを確認する。認証・session・管理外の兄弟・既存ユーザー差分が保持されていることも対象を絞って確認する。
- [ ] **解決先と互換性**: 新規の対話 shell と非対話環境で `type -a`、`command -s`、`mise which`、対象の version / help を確認する。通常 CLI は Brew、Bash / fish / mise / usage / Hermes は Nix、共通 runtime は mise の意図した版になる。二重 activation・旧 PATH の shadowing がなく、既存のプロジェクト選択を壊さない。Yazi plugin、fish の prompt / 補完、Herdr の Claude hook を確認する。
- [ ] **実ツールでの保護**: Safehouse / dotenvx の配布変更に対応する `check_safehouse_runtime.py` / `check_dotenvx_runtime.py` を、承認した通常端末から `uv run --no-project python` で実行する。前者は使い捨て HOME、後者は dummy Keychain item / launchd job を使う既存検証で、実秘密を読まない。Keychain / launchd 操作には別途承認が必要。未承認ならこの項目を未完了とし、単体テストで代替済みとしない。
- [ ] **Herdr と既存変更**: fixture で無関係な settings が保たれることを確認したうえで、実機の変更を Herdr 用登録と hook に限定する。現在使用する本体と hook の同版性を確認し、既存の Claude / Pi / Zed 差分を紛れ込ませない。
- [x] **文書と廃止経路**: 参照リンク、標準コマンド、管理主体、実機の手順を照合し、`git diff --check` を行う。古い Nix 導入参照・実行先置換・config.fish example / ignore・HM 通常配置の残存は、対象を絞った検索と差分で確認する。削除完了だけを証明する恒久テストは作らない。

## 調査根拠と未検証範囲

調査はリポジトリ・固定ソース・公開パッケージ定義の読み取りまで。Homebrew の導入成功、mise の実配置、ランタイムの実ビルド、Herdr installer の実設定への適用、Hermes の実サービス動作はこの計画作成では検証していない。

- [mise 2026.9.18 の dotfiles 仕様](https://github.com/jdx/mise/blob/v2026.9.18/docs/dotfiles.md): 配置と tracking の区別、source の基準、Git manifest、競合。
- [nix-homebrew](https://github.com/zhaofengli/nix-homebrew): Homebrew 本体と package 管理の分離。
- [Homebrew googleworkspace-cli](https://formulae.brew.sh/api/formula/googleworkspace-cli.json)、[Pi](https://formulae.brew.sh/api/formula/pi-coding-agent.json)、[OpenCode](https://formulae.brew.sh/api/formula/opencode.json): 製品と提供版の確認。
- [Safehouse 公式導入](https://github.com/eugene1g/agent-safehouse#install)、[dotenvx 公式導入](https://dotenvx.com/docs/ops/install)、[keifu 公式導入](https://github.com/trasta298/keifu#with-homebrew): 追加する upstream tap。
- [Herdr v0.9.3 integration installer](https://github.com/herdrdev/herdr/blob/v0.9.3/src/integration/targets.rs)、[settings の編集](https://github.com/herdrdev/herdr/blob/v0.9.3/src/integration/claude_settings.rs)、[symlink 先への書き込み](https://github.com/herdrdev/herdr/blob/v0.9.3/src/integration/config_file.rs): 同版 hook の配置と settings 変更の境界。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
