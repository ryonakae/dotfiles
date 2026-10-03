# Nix を中心とした Mac 環境への移行 Implementation Plan

参照: [dig log](../dig/2026-10-03-nix-migration.md)。Q16 への「a」で要件整理を終了し、計画作成を承認された。dig log の最終確認待ちの記載はこの回答で解決済み。計画保存後の「ok」で実装を承認され、その後の「ok」「進めて」で既存 Pi 設定の変更を現在値のまま今回の移行へ含めることも承認された。

追加確認: ユーザーの「hermes動いてないから気にしなくて良い」により、現在の Hermes は停止済みを前提とする。今回の移行で Hermes の停止・待機・中断調整は不要とし、自動起動もしない。将来、稼働中の Hermes を更新する場合の既存の安全要件とは区別する。

追加変更: ユーザーの「回帰テストとかもいらない」「管理が楽な方にして」により、本移行ではテストの追加・再実行を行わず、構文・差分・Nix の評価とビルドで進める。gomi / dotenvx / Agent Safehouse は現行版維持と独立更新を要件から外し、共通 nixpkgs の標準定義を使う。以下の既存テスト結果は過去の実行記録であり、再実行の承認待ちではない。

## Requirements

- 現在と今後の Apple Silicon Mac を、ツール・アプリ・ユーザー設定・macOS 設定を含めて再構築できるようにする。実機で意図的に導入されたものを基準とし、Brewfile.example だけを移す構成にしない。依存ライブラリと直接利用するツール、名称変更・別系列を区別する。
- upstream Nix の multi-user daemon、Flakes、nix-darwin、統合した Home Manager を構成の中心にする。ツールは原則 Nix、macOS 対応・保守負担に問題があるものは Homebrew / App Store 等で補完し、導入一覧の正本を Nix に集約する。
- 共通 Nixpkgs は rolling 系列を使い、通常の適用は固定済み依存から行う。Claude Code・Codex・Pi・OpenCode・Hermes 等と Herdr・agent-device は個別・グループ更新可能にする。外部拡張・プラグイン・スキルも取得元と版を固定する。一般 GUI アプリの自動更新は許容し、flake.lock による同一版復元とは区別する。
- 設定はリポジトリを編集して適用する方式を基本にする。元の形式の設定・スクリプトも利用でき、全内容を Nix 記法へ翻訳する必要はない。既存の即時反映方式を残すためだけの out-of-store link は使わない。
- Node / Python / Ruby / Bun の共通環境は Nix に移す。mise は既存プロジェクトが必要とする用途に限る。別プロジェクトの設定を無断で変更しない。
- dotenvx + Keychain + Safehouse を維持する。機密ファイルの直接アクセスを拒否し、共通ツール用の値は sandbox 外で復号して起動時に注入する。注入済み環境変数の利用は許容し、完全隔離を追加要件にしない。プロジェクト用秘密を共通ファイルへ混ぜない。
- 通常 rm の gomi 転送、失敗時に実 rm へ戻さないこと、Hermes の正規停止と DB 保全を維持する。互換性優先の Safehouse 設計と既存の意図的な例外を狭めず、対話 CLI に承認モード・内蔵 sandbox の強制引数を追加しない。
- 準備・ビルド・復旧準備の後、現在の Mac をなるべくまとめて完全切替する。長期二重管理を完成形としない。停止・再起動・ログアウト・OS 再起動は必要性を示して実行直前に確認する。
- 秘密、認証、memory、session、DB、cache、アプリ生成データは設定世代の復元対象と分離する。実秘密の移行・Keychain 登録・バックアップは人間が sandbox 外で行う。設定の復元とデータの巻き戻しを混同しない。
- Intel / Linux / WSL、macOS 自体の再インストール、Mac 全体の完全復元、無関係な開発プロジェクトの Nix 化は対象外。

## Implementation Decisions

### 1. 構成と管理境界

- ルートに `flake.nix` / `flake.lock` を置き、設定の正本は `config/nix/` と既存 `config/` の明示したファイルにする。`config/nix/darwin/` は OS・Homebrew、`config/nix/home/` はユーザー環境、`config/nix/packages/` は独立版定義を担当する。汎用フレームワークや全パッケージの独自再実装は作らない。
- 基本入力は `nixpkgs-unstable`、nix-darwin `master`、Home Manager `master`。後二者の nixpkgs は共通入力へ follows する。上流 Flake の独自依存は、互換性を確認せず一律 follows しない。初回に解決した revision を lock し、適用時に更新しない。
- 通常 build / switch は、公開 input の lock 追加・再解決が必要なら中止する。`--no-write-lock-file` 単独を固定の保証にしない。まず host override なしの `nix flake metadata --no-update-lock-file --json` で基準 lock の整合を確認する。次に非 Flake の host 入力だけを明示 override した解決済み metadata の lock graph を基準と照合し、host leaf 以外の node / edge / revision / hash に差があれば中止する。検査したソースとホストの store snapshot を build / switch で共用し、再評価による別入力への切替を避ける。公開依存の変更は明示的 update に限定する。
- `nixpkgs.hostPlatform = "aarch64-darwin"`、`home-manager.useGlobalPkgs` / `useUserPackages` を利用する。system / home の stateVersion は初回採用時の互換性基準として固定し、更新のたびに最新値へ変えない。unfree は必要なパッケージへ限定する。
- ユーザー名・HOME 等の非秘密のマシン固有値は共通設定から分離する。既存規約どおり実値は Git 外、値を含まない `*.example` は `config/nix/hosts/` に置く。専用のローカル path input と明示的な override で渡し、build / switch が同じホスト入力を使うようにする。秘密や私的データをこの入力へ混ぜない。ホスト入力は store に入る非秘密の構成情報であり、依存 lock に実機の絶対パスを保存しない。
- Git 管理の flake ソースと、必要なファイルだけの参照を使う。`config/` 全体や HOME を path source として取り込まない。Git 外の実 `.env` 等を含み得る `path:.` の安易な利用を避ける。初回の新規 Nix ファイルが Git ソースに含まれることを確認し、秘密を含む一括 stage で解決しない。

### 2. パッケージと更新

- 初期の移行表を本計画のタスク内へ記録し、各直接導入対象について「現在の導入元・移行先・固定単位・例外理由」を確定してから切替する。別の恒久的な手書きパッケージ一覧は増やさず、導入後の正本は Nix 定義とする。
- 一般 CLI は nixpkgs の既存定義を優先する。独立更新対象は既存の上流 Flake、公式配布物、既存 nixpkgs のパッケージ関数・patch を利用し、版とソースだけでなく依存 hash / 補助配布物も固定する。各ツール用に nixpkgs 全体の入力を複製しない。
- Hermes / Herdr は Darwin 対応の上流 Flake を第一候補にする。gomi / dotenvx / Agent Safehouse は保守の容易さを優先し、共通 nixpkgs の標準定義に揃える。実機の現行版と一致させる override は作らない。
- agent-device は npm 配布物と依存を固定し、Apple helper・署名・XCUITest の実動作を確認する。CLI に同梱された配布物を壊さない方法を優先し、未確認のまま store 内へ runtime install / codesign を行わせない。Nix 化が困難なら補完方式を提示し、個別版固定を失う変更は確認する。
- GUI / App Store アプリと Xcode / SDK は macOS の配布経路を利用する。mosh は現行の firewall 手順が実体へ署名を書き込むため、今回は Homebrew 補完とし、store の変更を伴う方法へ移さない。権限・署名・firewall 設定は自動適用へ紛れ込ませない。
- Homebrew は nix-darwin の homebrew 定義を正本にする。通常適用では `onActivation.autoUpdate = false`、`upgrade = false`、`cleanup = "none"`。導入一覧にないものの自動 uninstall / zap はしない。Homebrew 自体がない新規 Mac では、公式 bootstrap を先に行う手順を用意する。
- 共通ランタイムは既存の必要な major / minor とツール要件を確認して選ぶ。単に現行 mise の古い patch と一致させるための独自ビルドは増やさない。プロジェクト指定を尊重し、特定ツール専用ランタイムはそのパッケージへ閉じる。
- `scripts/dotfiles.sh` に小さな操作入口を用意する。`build` は固定構成の事前ビルド、`switch` は固定構成の適用、`update [all|ai|tool]` は対象の版定義 / lock の更新のみ。存在しない対象はエラーにし、一般 nixpkgs 内の任意パッケージを個別更新できるようには見せない。`ai` の実対象を表示する。
- 全体更新を一連で実行する手順は、明示的な update → build → 確認付き switch と、Homebrew 側の明示的更新をまとめる。通常 switch に更新を隠さない。Nix 管理した本体の自己更新や既存 installer は使わず、Herdr server 等の再起動は適用と区別する。

### 3. 設定・拡張・秘密

- Home Manager の既存モジュールで表現できる設定はそれを使い、独自スクリプト・指示・スキルは元の形式で store から配置する。共通 AGENTS の正本を増やさず、各エージェントの参照関係を維持する。
- アプリが書き込まないファイルは通常の宣言的配置とする。`fish_variables`、Pi の設定保存、Hermes の設定編集等は書き込み箇所を確認して扱いを分ける。ネイティブの設定 / state 分離を優先し、存在しない overlay 機能を仮定しない。
- 同一ファイルに固定設定と実行時変更が混在するものは、ファイル単位で所有権と再適用時の意味を記録する。必要なら非秘密の宣言から可変ファイルを生成するが、元ファイルを退避し、未知のキー・実秘密を黙って削除しない。汎用の独自 merge 基盤は作らない。アプリの永続設定変更を制限する必要がある場合は、その具体的な操作への影響を切替前に確認する。
- 外部スキルは取得元 revision と内容 hash を固定して `~/.agents/skills/` へ配置し、現行の利用先から参照する。Claude 固有スキルの同名優先、`.disabled` 等の非配布、Antigravity の共通参照を保ち、ディレクトリ全体の置換で他のスキルを隠さない。`skills-lock.json` の computedHash だけを再現用 lock と扱わず、最新版を取り直す experimental_install を新規 Mac の復元手順から外す。自作スキルと Hermes の自己更新データは区別する。
- Pi は固定した拡張パッケージをローカルパスとして参照する構成を優先し、依存を Nix 側で解決する。Herdr は3つの外部プラグインの revision を固定し、Zerdr 提供のローカルプラグインはアプリとの対応を保つ。書き込みを要求するプラグインは状態の保存先を分離する。
- `.env`・復号鍵・OAuth 認証を Nix の値、`home.file.source`、環境変数の静的定義、ソース入力に渡さない。dotenvx は runtime のファイルパスを読み、Keychain 失敗時は起動を止める。新しい配置でも元パス・symlink 実体・復号鍵の直接アクセス保護を維持する。
- shell / 非対話 / launchd のすべてで、安全な rm wrapper が通常 rm として解決される PATH を作る。Nix profile、Homebrew、mise の activation が優先順位を上書きしないことを確認する。保護 wrapper の実装を複数の起動経路へ重複させない。

### 4. Hermes と常駐サービス

- 本体パッケージとサービスの所有権を分離する。上流 Flake のパッケージを使い、gateway / dashboard の定義は Home Manager 側の一か所で所有する。既存の `hermes gateway install` による plist 再生成とは併用しない。
- 上流 services モジュールは Safehouse / dotenvx と停止順序をそのまま満たさないため、全面採用を前提にしない。パッケージを利用して既存の安全な起動契約を HM の launchd 定義へ移す方法を基本とし、独自のサービス管理基盤は作らない。
- build は停止せず先に完了させる。今回の停止済み Hermes はデータを保持してパッケージ / plist を配置し、停止・待機や自動起動は行わない。将来の稼働中更新は、利用者確認 → 正規停止 → 終了確認 → 必要な DB バックアップ → 切替 → 起動確認の順にする。旧本体と新本体が同じ DB を同時に開く時間を作らない。
- 現行 wait helper の「タイムアウトでも成功扱いで続行」は採用しない。停止失敗・待機時間超過なら切替を中止し、強制終了や継続を自動選択しない。既存の管理関数を移行時にも利用・更新し、外から launchctl を直接呼んで停止処理を飛ばさない。
- HM の launchd activation が定義の追加だけで停止済み Hermes を起動しない構成にする。今回と新規 Mac は明示的にサービス起動を有効化するまで自動ロードしない。将来の稼働中更新では、HM の再読み込みより前に正規停止が完了する順序を保証し、操作入口を通さない適用でも未停止なら中止する。
- Hermes の config / auth / DB / memory / skills / cron は実機の可変データとして保持し、宣言化する非秘密設定だけを明示する。既存実設定を無差別に読み込まず、必要な非秘密項目はユーザーが提供する安全な抜粋等で確認する。package の追加依存は利用機能と照合する。
- Hindsight の Docker サービスはそのまま独立した状態管理として扱う。Compose 定義は宣言的に配置し、イメージの tag に加えて取得 digest を固定する。データ volume・Codex 認証・Docker runtime は Nix 世代の復元に含めない。データ移行を伴う更新は別途停止・バックアップを確認する。

### 5. OS 設定と bootstrap

- macOS 設定は Dock / Finder / キーボード / トラックパッド / スクリーンショット等、再現に必要な非秘密のキーへ取得対象を絞る。nix-darwin 専用オプションを優先し、未対応項目だけ選別した preferences または手動手順にする。`defaults read` の全量取得や全 plist のコピーはしない。
- Apple ID・Touch ID・TCC・アクセシビリティ・署名鍵・VPN 認証・データ復元は手動作業として分離する。macOS preferences は宣言削除だけでは戻らない場合があるため、変更するキーの旧値・未設定状態を控えて戻し方を用意する。
- Nix bootstrap は公式の版固定済み aarch64-darwin 配布物と checksum を使う。導入版・hash は実装時に公式公開物から確定して記録し、浮動する install URL を無確認で実行しない。multi-user installer による APFS volume、mount、build users、daemon、shell 初期化の変更範囲を説明してから、人間が sandbox 外で実行する。
- macOS 26.2 の実機適合性は未検証。既存 Nix 残骸・OS 管理ファイルとの衝突があれば先に止める。UID / GID の固定値や既存 `/etc` ファイルの強制置換を参考例から流用しない。
- インストーラは初期導入に限定し、以後の Nix 本体・設定は nix-darwin へ渡す。現在の sandbox の回避、権限変更、Keychain 操作を bootstrap の副作用として無断実行しない。

## Tasks

実装 preflight: `master`、upstream `origin/master`、ahead/behind 0/0、staged 変更なし。review base は `ab60631218ce1544049dca60e143d25ac757f9bb`。本会話の dig / plan は未追跡。既存変更は Pi fast-mode の `desired: true → false` と settings の `lastChangelogVersion: 0.99.2 → 1.0.0`。現在値を維持して今回の移行へ取り込む承認は取得済み。動作中の Pi が fast-mode 設定を書き換えることがあるため、移行時にも最新差分を確認する。

- [ ] **対象の確定と導入対応**: 実機の非秘密の package / app metadata、`brew/Brewfile.example`、`config/.config/mise/config.toml`、管理済みのエージェント設定を照合し、本計画に初期移行表を追記する。
  - Homebrew は依存として入ったものと installed-on-request を区別する。leaves だけでは直接要求された依存パッケージを取りこぼすため、導入 metadata も参照する。Homebrew 外の npm / uv / mise / 手動アプリは metadata へ対象を絞る。
  - Git 外の実設定や秘密は読まず、判別できない用途・設定は確認する。既存 Pi 2ファイルの未コミット変更は退避・上書き・取り込みを無断で行わない。
- [ ] **Flake と bootstrap**: `flake.nix`、`flake.lock`、`config/nix/`、`scripts/bootstrap-nix.sh`、`scripts/dotfiles.sh` を作る。
  - まず root flake、共通 / ホスト分離、HM 統合、通常 build / switch の依存固定を成立させる。bootstrap は破壊的な自動修復を持たせず、再実行時は既存状態を検出する。
  - bootstrap を先行実装。公式 Nix 2.34.0 / aarch64-darwin の配布物と SHA-256 を固定し、実ダウンロードの checksum 一致を確認。`scripts/tests/test_bootstrap_nix.py` の8件と `bash -n scripts/bootstrap-nix.sh` が通過。Safehouse 拒否・明示実行・OS / CPU・既存状態・checksum / download 失敗・daemon / no-channel-add 引数をダミーの外部コマンドで検証した。その後、人間が Safehouse 外で導入し、`nix (Nix) 2.34.0` を確認。途中の `vifs` 待ちは macOS の許可ダイアログ待ちで、利用者の許可後に進行した。
  - `flake.nix` / `flake.lock` と `config/nix/{darwin,home,hosts}` の最小構成を実装。nixpkgs / nix-darwin / Home Manager の revision を固定し、非秘密の host JSON 2項目だけを store snapshot にする。`scripts/dotfiles.sh` / `dotfiles.py` の build は Git source の基準 lock 検査 → host override の graph 比較 → 同じ snapshot の flake check / build の順。公開 direct input の個別更新・all を実装。独立 package 更新の試作は標準パッケージへの統合に合わせて撤回し、AI 本体の導入時に必要な更新入口を接続する。switch は保護・サービス定義の統合後に接続するため現時点では公開しない。
  - 実 Nix を使う `scripts/tests/test_dotfiles_cli.py` の4件が通過。host 差替え、通常 build の lock 不変、未追跡ファイルの非混入、公開 URL 変更・lock entry 欠落の拒否、明示 update を確認。ダミー `.env` 作成は Safehouse に拒否されたため、その拒否を回避せず通常名の未追跡ダミーで非混入を検証した。
  - 実機の非秘密 host 値を `/tmp/dotfiles-machine.SyCOAn6p/host.json` に限定して事前ビルド。最小構成の flake check / build が通過し、`/nix/store/ysxr12iyc0c9h1wsjniq3kfilwkjqf25-darwin-system-26.11.4cff07d` を生成。activation は未実行。固定 nixpkgs が選ぶ Nix は 2.34.8 で、現在稼働中の 2.34.0 をまだ置き換えていない。
  - `AGENTS.md` は新しい正本・配布境界と食い違う箇所だけ更新する。共通エージェント指示の内容を移行に便乗して変更しない。
- [ ] **パッケージと更新単位**: `config/nix/packages/`、`config/nix/home/packages.nix`、`config/nix/darwin/homebrew.nix` に確定した導入対象を実装し、操作入口へ更新対象を接続する。
  - 安定して利用できる既存定義を使い、Nix 導入と最新機能への一斉アップグレードを混同しない。採用版の互換性と独立更新の成立を事前ビルドで確認する。
  - 一般 CLI 30件と共通ランタイム4件を `config/nix/home/packages.nix` へ追加。`config/nix/darwin/homebrew.nix` に55 cask、実機 `mas list` の22アプリ、補完 formula 7件を宣言。Homebrew は自動更新・upgrade・cleanup を無効にし、PostgreSQL の start/restart も無効にした。生成された activation の `HOMEBREW_NO_AUTO_UPDATE=1` / `--no-upgrade` と cleanup 指定なしを確認した。
  - `dotfiles build` が通過し、`/nix/store/9zjhm0kd3ki51h06v8yvbvawpvhddykb-darwin-system-26.11.4cff07d` を生成。生成 profile の fish 4.9.3 / Git 2.55.0 / Node 22.23.3 / Python 3.11.16 / Ruby 3.3.10 / Bun 1.4.2 / uv 0.12.17 / jq 1.8.2 の起動を確認。Bun は旧1.3.13からの minor 更新候補であり、利用互換性は切替前の確認対象。Homebrew bundle・activation・サービス操作は未実行。
  - gomi / dotenvx / Agent Safehouse の独立定義を試作したが、現行版維持は不要とのユーザー判断で撤回。3つとも `home/packages.nix` の標準パッケージへ統合し、個別 hash と nix-update 用の試作コード・追加テストを除去した。通常 build が成功し、`/nix/store/my4x19v9lcgvhmwai98r56bncdwah49y-darwin-system-26.11.4cff07d` を生成。共通 nixpkgs の更新で一緒に更新する。
  - 以前実行した全36テストは Safehouse のダミーごみ箱保護で2ケース・4 errors（`/tmp/dotfiles-tests.log`）。ユーザー指示により再実行はせず、今後の受入ゲートから外す。保護設定は変更していない。後片付けが拒否された一時ディレクトリ（`tmp8ud28y15`、`tmpgumdah3_`）は残したまま。
- [ ] **ユーザー設定と拡張の配置**: `config/nix/home/` と既存 `config/` の設定を接続し、共通指示、fish、エディタ、端末、エージェント設定、外部スキル / 拡張 / プラグインを配置する。
  - `fish_variables` は store 外の可変状態とし、宣言する PATH と旧 universal PATH の重複を整理する。実機の universal 値を無断で削除しない。fish plugin も revision を固定し、非Aqua shell の SSH socket 補完を保つ。書き換えられるアプリ設定の所有権を具体化し、新規配布先や duplicate plugin load を増やさない。未知の実ファイルに force overwrite しない。
  - `home/fish.nix` と `home/protection.nix` を追加。既存の fish 関数・補完・SSH socket 補完をファイル単位で配置し、bobthefish / fzf plugin は共通 nixpkgs の固定 source を使う。mise のグローバル tools をなくしてプロジェクト用途へ限定し、共通ランタイムは Nix profile を優先する。PATH の変更時にも `.local/bin` を先頭へ戻す handler を配置する。
  - rm の処理は既存実装を再利用し、生成物の shebang だけ Nix の Python に固定。gomi 設定と Safehouse の共通 wrapper / profile も store から配置する。秘密・認証・既存サービスを実行していない。`fish_variables` は追跡から除外したが、実ファイルは保持した。実機 config.fish は秘密を含む保護対象なので読まず、example 由来の共通設定との差分確認は切替前の人間の作業として残す。example の PGDATA は実機の DB 保存先と確認できないため採用しない。
  - 通常 build が成功し、`/nix/store/ddk55bg4jffh0xi2hmdggqmc1dpqqgkw-darwin-system-26.11.4cff07d` を生成。生成された33件の fish ファイルと共通 wrapper の構文、rm の Python 構文と interpreter を確認した。回帰テスト・ダミー試験は実行していない。その他の設定、AI 本体・拡張、Hermes のサービス統合は引き続き未完了で、実機へは未適用。
- [ ] **保護・起動・PATH の統合**: `run-with-agent-env.sh`、`__safehouse_args.fish`、対話 CLI 関数、gateway / dashboard wrapper、rm wrapper の参照先を Nix 環境へ接続する。
  - 共通ロジックとサービス固有の feature 差分を保つ。Safehouse の HOME / profile 順・秘密保護・TMPDIR 補正・環境継承・引数透過は既存実装と生成物を確認して維持する。共通ランタイム移行に伴う mise / Homebrew 固定パスを解消する。
- [ ] **Hermes のサービスと安全な適用**: `config/nix/home/hermes.nix`、`hermes-gateway.fish`、`hermes-dashboard.fish`、待機 helper へ、固定パッケージ・単一の plist 所有者・停止確認・起動失敗時の扱いを実装する。
  - 今回はサービスを起動しない配置を確認する。将来の稼働中更新では HM activation の順序を確認し、必要な停止・バックアップが失敗した場合に先へ進まない。単なるプロセスの二重起動だけでなく、同じ DB の同時利用を防ぐ。
- [ ] **macOS と手動復元手順**: `config/nix/darwin/` へ確認済みの OS 設定を追加し、`docs/setup.md` へ手動認証・権限・秘密復元・Xcode / SDK・mosh firewall・Docker / Tailscale 等の残作業を整理する。
  - 暗号化した共通 .env と Keychain の復元、アプリ個別認証、Hermes / Hindsight データの復元を混同しない。
- [ ] **事前ビルドと衝突・復旧準備**: Nix 導入後、全構成を build し、実 HOME の対象パスについてファイル種別・リンク先・所有権の metadata と生成予定の衝突を確認する。
  - 秘密の内容をログへ出さず、既存の実ファイルは退避先と復旧先を記録する。既存リンク・shell 初期化・plist・変更する preferences の戻し方を切替前に揃える。状態データのバックアップは停止後に行う。
- [ ] **集中切替と重複管理の解消**: 直前承認後、下記の切替手順で新構成へ移す。実動作確認後、Nix に移った旧導入物・共通 mise 管理・旧リンク配布を対象を明示して整理する。
  - アンインストール・破壊的操作は対象ごとに承認を得る。Homebrew の補完パッケージとその依存は残す。旧実行物の残置は短期の復旧保険として期限・用途を明記し、普段の PATH / 更新経路から外す。
- [ ] **運用文書と旧配布の終了**: `README.md`、`docs/setup.md`、`AGENTS.md` を更新し、`scripts/create-symlink.sh` / `create-skills-symlink.sh` / `copy.sh` 等の旧導入経路を呼び出し元ごと廃止・整理する。
  - 秘密の実ファイルや既存 backup を旧配布物と一緒に削除しない。Brewfile.example / skills-lock の役割は Nix 定義に移し、二つの正本を残さない。説明にはコードから分かる一覧を転記せず、操作と例外・復旧制約を残す。

### 初期移行表（棚卸し中）

実機 `brew info --json=v2 --installed` の metadata を確認。installed-on-request は44 formula、cask は59件。以下は導入元を確認した移行候補で、Nix の評価・実ビルド前に完了扱いしない。App Store は `mas list` で22件を照合済み。Homebrew 外の npm / uv / mise / 手動アプリの metadata 照合は残る。

| 現在の対象（Homebrew） | 移行先 / 固定単位 | 残る確認・例外 |
|---|---|---|
| actionlint, age, awscli, cocoapods, fastlane, fd, ffmpeg, fish, fzf, gh, git, git-lfs, gomi, imagemagick, jq, mas, mkcert, terminal-notifier, tmux, tree, uv, vim, worktrunk, yazi, zellij, zoxide | 共通 nixpkgs | Darwin 対応と実際のコマンド互換性 |
| agent-browser, ctx7, keifu, usage, zerdr | 既存 Nix 定義を優先、困難なら補完 | 現行版との差、配布・署名・プラグイン連携 |
| dotenvx, agent-safehouse | 共通 nixpkgs | gomi と合わせて現行版の維持より標準定義での管理を優先する |
| herdr 0.9.0, opencode 1.18.32, pi-coding-agent 1.0.0 | 独立した版定義 / 上流 Flake | 現行機能を落とす downgrade はしない |
| claude-code@latest, codex, antigravity-cli（cask） | 独立した CLI 配布物 | GUI cask と区別し、自己更新と固定を整合 |
| mosh | Homebrew | firewall 手順が配布実体へ署名するため |
| mise | Nix の CLI、プロジェクト用途のみ | 共通ランタイムの二重管理を解消 |
| fisher | Home Manager の fish plugin 宣言 | plugin revision を固定 |
| icu4c@76, libpq, oniguruma, pcre2, postgresql@17 | 用途確認後に確定 | 明示導入フラグがあるため依存として勝手に除外しない。DB / service / 開発用ライブラリの用途を区別 |
| その他55 cask、App Store 22件 | Homebrew 補完、導入一覧を Nix 管理 | 実機59 caskから上記3 CLIとCotEditorを除く。CotEditorは実機にApp Store receiptがあるためmasへ一本化。アプリ自動更新を許容 |

補足: 旧 `figma-beta` は tap metadata がなく、現在の公式 cask は有効な `figma@beta`（126.10.3）だった。Nix 定義には現行名を採用するが、現在の116.18.4のアプリとの衝突・導入経路整理は切替前に確認する。`sheltie` と `zerdr` は `ryonakae/tap` の完全修飾名を使用。生成 Brewfile は nix-darwin の既定でこの2パッケージに `trusted: true` を付けるため、適用時の変更範囲に含める。実適用はまだ行っていない。

依存 metadata 上、oniguruma は jq、pcre2 は fish / Git / glib / ripgrep が使用。icu4c@76 / libpq / postgresql@17 に直接依存する formula は見つからなかったが、開発プロジェクトや実 DB の用途を否定する根拠にはしない。

## 切替・復旧手順

1. **切替前**: 完成した構成を現在の Mac 向けに build。生成された activation とパッケージ参照を確認し、更新する入力・実機パス・サービス・preferences と旧構成への戻し方を用意する。破壊的な Homebrew cleanup や Nix GC は実行しない。
2. **承認と停止**: ユーザーへ影響を提示し、必要なエージェント・端末・アプリの停止を確認。現在の Hermes は停止済みのため停止・待機は不要。将来、稼働状態で更新する場合だけ管理関数で正規停止し、失敗したら中止する。実行中のエージェント自身が途切れる場合は、人間用の再開手順を先に渡す。
3. **状態保全**: 停止済み Hermes の DB・認証・memory 等には触れず、構成だけを移す。後で初回起動・schema 更新を行う前に、人間が sandbox 外で必要な状態を整合した形でバックアップする。関連 WAL 等を取りこぼさず、ログや Git / store へ内容を出さない。Hindsight のイメージやデータを変える場合は別途整合したバックアップを取る。既存の秘密・Keychain は変更しない。
4. **適用**: 確認済みの旧リンク / plist / shell 設定のみを退避して新構成を適用。既存実ファイルを一括強制上書きしない。秘密の参照と PATH を確認し、起動を承認されたサービスだけ起動する。停止済み Hermes は停止したままにする。
5. **スモーク確認**: 下記 Final Validation の実機項目を確認する。設定変更を伴う再起動・ログアウト等は必要なものだけ直前確認する。
6. **失敗時**: 新サービスを正規停止し、原因に応じて旧生成物 / 旧リンク / 旧 plist / 旧 preferences へ戻す。初回は以前の Nix 世代が存在しないので、退避した非 Nix 構成への復旧手順を使う。以後は保持した Nix 世代を使えるが、Homebrew アプリや OS preferences、DB は同じ操作で戻らない。
7. **DB を変更した場合**: 旧バイナリを新 schema の DB へそのまま向けない。必要なら停止状態で人間がバックアップを復元し、切替後の新規データが失われ得ることを確認してから実施する。自動 rollback で DB を巻き戻さない。
8. **整理**: 新構成の受入後、承認済みの旧パッケージ・配布経路を整理する。復旧用世代・バックアップの削除は移行成功と同時に自動実行しない。Nix 自体のアンインストールは通常の復旧手順にしない。

## Final Validation

ユーザーの追加指示により、回帰テスト・fixture・stub を用いた試験の追加と再実行は行わない。構文確認、ソースと生成物の確認、通常の Nix 評価・ビルドを使う。未実行の確認を成功したとは報告しない。

- [ ] **固定構成の事前ビルド**: `dotfiles build` で lock の整合確認と評価・ビルドを行う。build 中に activation や公開依存の更新を行わない。
- [ ] **構文・差分**: 変更した fish は `fish --no-execute`、shell は対応する `-n`、Nix は formatter と評価、文書は参照と `git diff --check`。Pi の既存変更を保持する。
- [ ] **配置・秘密・状態**: 宣言と生成物を確認し、秘密・認証・DB・可変状態を store に入れない。切替前に既存ファイルとの衝突と退避先を確認し、未知の実ファイルを上書きしない。
- [ ] **起動・サービス**: 生成された PATH、wrapper、plist、activation の内容を確認する。停止済み Hermes は起動しない。実サービスの利用確認は再開時に行い、移行のゲートにしない。
- [ ] **復旧と完成状態**: 初回は旧リンク・設定の退避物へ戻す手順を用意する。DB の復旧演習はしない。管理の正本と通常の更新経路を Nix に集約し、Homebrew 補完・手動操作・可変状態・未確認事項を明記する。実機への適用は直前承認後に行い、未適用や別 Mac での未実証を全体完了と扱わない。

## 実行上の境界と調査根拠

計画の独立 read-only レビューを実施。通常 build / switch の固定依存検証に関する指摘を修正し、再確認で Approved。これは計画のレビュー結果であり、Nix ビルド・テスト・実機適用の成功を示すものではない。

- 現在の作業環境は Safehouse 内、HERDR_ENV=1。Nix は人間による初回導入済み。現在のエージェント PATH にはないため `/nix/var/nix/profiles/default/bin/nix` を使い、daemon 接続と通常ビルドを確認済み。実機は macOS 26.2 / arm64。権限・セキュリティ設定変更、秘密操作をこの sandbox から試さない。必要な人間の sandbox 外操作と承認範囲を実行前に明示する。
- 既存未コミット変更は `config/.pi/agent/extensions/pi-gpt-fast-mode/config.json`、`config/.pi/agent/settings.json`。実装前に再確認し、対象に競合があれば勝手に上書きしない。
- 実装方式で要件を満たせない場合は停止して相談する。特に秘密保護の緩和、独立版固定の断念、サービスの強制停止、既存データの破棄を内部詳細として処理しない。
- [nix-darwin README](https://github.com/nix-darwin/nix-darwin/blob/master/README.md): rolling 系列、upstream Nix の管理、installer と interpreter の区別。公式はアンインストールの容易さから Lix installer を推奨しているが、本計画では合意済み upstream Nix の公式配布を使い、通常復旧をアンインストールに依存させない。
- [Nix binary installation](https://nix.dev/manual/nix/stable/installation/installing-binary): macOS multi-user、版固定配布、APFS / mount / daemon の変更範囲。本実装では macOS 26.2 で人間による導入と Nix 2.34.0 の応答を確認済み。
- [Nix flake metadata](https://nix.dev/manual/nix/stable/command-ref/new-cli/nix3-flake-metadata): JSON の lock graph、no-update と no-write の相違、override-input の意味を確認。
- [HM nix-darwin 統合](https://github.com/nix-community/home-manager/blob/master/docs/manual/installation/nix-darwin.md)、[launchd activation](https://github.com/nix-community/home-manager/blob/master/modules/launchd/default.nix)、[Homebrew module](https://github.com/nix-darwin/nix-darwin/blob/master/modules/homebrew.nix): 統合・再読み込み・更新 / cleanup の境界。
- Hermes / Herdr / Safehouse / Pi / skills の調査根拠と未検証事項は dig log に記録。公開 main/master は調査資料であり、適用時にそのまま浮動参照しない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
