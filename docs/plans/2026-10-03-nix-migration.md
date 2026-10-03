# Nix を中心とした Mac 環境への移行 Implementation Plan

## 現在地と再開手順

**実装承認済み・移行準備中。基盤は完了、設定・拡張の移行が途中。upstream Nix 自体は導入済みだが、nix-darwin / Home Manager の構成は一度も実機へ適用していない。**

- 今回の再開・review base: `0b581d340f06567478a7e86595d31affab885921`。開始時は `master` と `origin/master` が同期。T4 のアプリ設定・Herdr 設定の配置を追加し、部分構成のビルドと生成物を確認した。ユーザーから既存の移行コミットを含む commit / push の依頼を受けている。リモートとの同期状態は再開時に `git status -sb` で確認する。
- 実装・検証・承認状態の正本はこのプラン。[dig log](../dig/2026-10-03-nix-migration.md) は合意と調査の出典であり、調査当初の「Nix 未導入」等を現在の状態として扱わない。
- **進捗の更新場所は下の Tasks。** `[x]` は記載した成果物とその検証の完了を表し、実機適用の完了ではない。未完了項目には残作業・完了条件を記載する。撤回済みの試作は末尾の履歴に隔離した。

次のセッションは以下から再開する。

1. `git status --short` と直近の差分を確認する。保持する他プロセスの変更は Claude 設定。Pi 2ファイルの承認済み変更は T5 の配置・版固定に取り込んだ。本文の確認基準より後の変更があれば、実ファイルを優先して進捗を更新する。
2. **T3 の Hermes / agent-device 補完案はユーザーに提案済み・未回答。** 進捗照会やこの文書整理の依頼を、採用承認と解釈しない。承認後に限り該当2項目を実装する。
3. **次は T5 の Herdr 外部 plugin、T6 の起動経路を進める。** Pi の可変設定・指示文、自作12＋現行外部13スキル、Claude の Herdr hook と statusline 版固定を接続済み。Pi 拡張の新規取得・推移依存・全機能の復元検証は残る。
4. T6・T7 の起動契約を揃えた後に T9 の `switch` を接続する。部分構成のビルド成功だけで T10 の切替へ進まない。

### 再開時に保持する状態・操作境界

- Pi の承認済み変更（fast-mode の `desired: false`、settings の `lastChangelogVersion: 1.0.0`）は T5 の実装へ取り込んだ。動作中の Pi が更新するため、以降も編集・stage の直前に差分を確認し、他プロセスの変更を上書き・巻き戻し・一括 stage しない。
- Claude 設定の初回 `model: "fable"` 追加は `1f56deb` へ取り込み済み。その後の未コミット差分は他プロセスによるものとして保持する。最新の確認では `modelSettings.claude-fable-5-1.effortLevel: "high"` 追加と `model` の削除がある。今回のコミット対象に含めず、差分を再確認する。
- 最後に確認した環境は Safehouse 内・`HERDR_ENV=1`、macOS 26.2 / arm64。新セッションでは環境を再確認する。Nix は `/nix/var/nix/profiles/default/bin/nix` で利用できる。
- ユーザー指示により **回帰テスト・fixture・stub の追加と再実行はしない**。構文、差分、ソース・生成物の確認、Nix 評価・ビルドで検証する。
- この Mac に Hermes の既存環境はない。ここで停止・データ移行・初期化・自動起動をしない。別 Mac の稼働環境の移行は、その Mac で承認・停止・バックアップを確認する。
- 実機への適用、利用中のプロセスの停止・再起動、ログイン shell の変更、権限・秘密の操作、旧導入物の削除は未実施。必要な操作を具体化して直前承認を得る。切替承認は取得していない。今回の commit / push 承認は、実機適用やサービス操作の承認を含まない。

## Tasks

### T1. 対象の棚卸し — 進行中

- [x] Homebrew の導入 metadata と App Store 一覧を取得。installed-on-request は44 formula、cask は59件、App Store は22件。移行先は下の対応表に記録。
- [ ] Homebrew 外の npm / uv / mise / 手動導入物と、各アプリの拡張を照合する。依存だけのライブラリを直接利用ツールと混同せず、各対象の導入先・例外理由・未確認点が説明できれば完了。
  - 調査済み metadata は `/tmp/dotfiles-brew-inventory.json`。一時ファイルの存続を前提にせず、なければ非秘密の package metadata だけ再取得する。
  - Git 外の実 `config.fish` は秘密を含むため読まない。example と実設定の差分は T9 で人間に確認してもらう。example の PGDATA を実 DB の保存先と仮定しない。

### T2. Nix 基盤・固定ビルド・更新入口 — 完了

- [x] 公式 upstream Nix 2.34.0 の checksum 固定済み bootstrap を実装し、人間が sandbox 外で初回導入。daemon 接続を確認。`f358e81`。
- [x] `flake.nix` / `flake.lock`、nix-darwin + Home Manager、非秘密 host 入力を実装。`4f10ae9`。Darwin stateVersion は6、HM は `26.05`。
- [x] `scripts/dotfiles.{sh,py}` の `build` と `update [all|input]` を実装。通常 build は公開依存の lock を検査し、host leaf 以外の変更を拒否して同じ snapshot を check / build する。現在の構成でビルド成功。
- `switch` は **未実装・未公開**であり、T9 の残作業。この項目の完了に含めない。

### T3. パッケージと更新単位 — 進行中・2件は承認待ち

- [x] 一般 CLI・共通ランタイムと Homebrew 補完を宣言。`890ef27`。現在の正本は `config/nix/home/packages.nix` と `config/nix/darwin/homebrew.nix`。
- [x] gomi / dotenvx / Agent Safehouse、Claude Code / Codex / Pi / OpenCode / Herdr / Antigravity CLI を共通 nixpkgs の標準定義へ統一。`44688a4`、`23a7c38`。独自 package 定義・専用 updater は削除済み。
- [x] 55 cask・22 App Store アプリ・補完 formula 7件を宣言し、生成物を確認。Homebrew の自動更新・upgrade・cleanup と PostgreSQL の start/restart は無効。**宣言とビルドのみで、Homebrew bundle は未実行。**
- [ ] **承認待ち: Hermes** — 公式 Flake の `packages.aarch64-darwin.default` をパッケージのみ採用する案。root lock で入力を固定し、サービスモジュールは取り込まない。承認後に input 追加・評価・ビルドを行う。独自依存を未検証で共通 nixpkgs へ follows しない。
- [ ] **承認待ち: agent-device** — 既存 mise の npm backend を残す案。0.21.19 の macOS helper はパッケージ配下で Swift ビルドするため、単純な Nix store 配置はできない。承認後に native TOML の宣言、Node 要件、導入手順を接続する。npm の版固定と推移依存全体の固定を同一視しない。
- 補完案の根拠・公式出典は [dig log](../dig/2026-10-03-nix-migration.md) 冒頭。調査済みであり、同じ候補調査を最初からやり直す必要はない。

### T4. config ファイルの配置 — 進行中

- [x] `home/fish.nix`: fish 関数・補完・SSH socket 補完、bobthefish / fzf、mise / zoxide 連携。設定本文は `config/.config/fish/{shell-init,interactive-init}.fish` と `config/.config/mise/config.base.toml` に分離。`046d980`、`23257af`。
- [x] `home/protection.nix`: rm / gomi / Safehouse 共通 wrapper・profile を既存ファイルから配置。rm は shebang のみ Nix Python に固定。PATH 変更後も `.local/bin` を先頭へ戻す処理を配置。
- [x] `home/files.nix`: Ghostty / Worktrunk / Husky / Yazi、共通 AGENTS の各エージェントへの参照、共通・CLI 別通知スクリプトを配置。`d6159ed`。Yazi の git / smart-enter / full-border は `pkgs.yaziPlugins`、smart-leave は既存 Lua。
- [x] Vim は「ほぼ使わないため管理しやすさ優先」というユーザー承認に従い、外部プラグインなしの最小構成へ変更。既存の標準 `pkgs.vim` と `home/files.nix` による `.vimrc` の配置だけを使用する。NeoBundle / NeoComplete / Copilot 等の専用設定、試作の `home/vim.nix` と限定 unfree 許可を除去。基本の表示・検索・インデント設定を残した。review base は `7785d62`。現行 HOME も `.vimrc` の正本へリンクしているため、次回起動から最小設定になる。旧 `~/.vim/bundle` の実体は未削除。
- [x] Zellij / ZAM は未使用のため削除するユーザー承認を取得。Nix・Brewfile example の導入宣言、Zellij config / dev layout、fish の `zl` 関数を削除。生成環境に本体・設定・関数が含まれないことを確認。Ghostty の Option 設定値は維持し、コメントだけ汎用化。review base は `f99a92c`。実機の本体・保存セッション・ZAM の私的プロジェクトは削除せず、汎用 `use-zellij` スキルと無効化済みの Pi 命名設定も残す。
- [x] Zed / Claude / OpenCode / pi-auto-name の設定を `home/files.nix` から既存ファイルのまま配置。通常の `home.file` / `xdg.configFile` を使用し、生成された4ファイルと正本の一致を確認。アプリ内からの永続設定変更の扱いは切替前に確認する。Claude の Herdr hook・statusline 依存は T5 で接続済み。
- [x] Pi の `settings.json` は `home/pi.nix` から標準 `mkImpureConfigMerger` で書き込み可能な実ファイルへ配置する構成を追加。起動時・`/settings` の書き込みを妨げる store symlink は作らない。実際の適用は T9・T10。
- [x] Herdr の `config.toml`、plugin 設定2ファイル、補助スクリプト2ファイルを個別に接続。生成された5ファイルとの一致と shell script の実行権限を確認。plugin 本体・tests・session・log は含めない。plugin 本体は T5、サーバーへの設定反映は T9・T10 と分ける。
- 完了条件: T1 で確認した config ファイルすべてに配置・例外対応・不要・手動のいずれかの扱いが付き、必要な生成物を確認できる。具体的な支障があるファイルの例外対応と、拡張の完了判定は T5。
- 移行中の注意: `fish_variables` は追跡から除外済みだが実ファイルを保持。旧 mise `config.toml` は現行環境用として未変更。新しい `config.base.toml` は適用後に HOME 側の `mise/config.toml` となる。旧ファイルの整理は T10・T11。

### T5. 配布の例外対応・拡張・スキル — 進行中

- [x] Zed / Pi の標準 HM モジュールを調査。Zed は `mutableUserSettings` がある一方、Pi は設定を store にリンクする方式。汎用 `lib.hm.generators.mkImpureConfigMerger` は experimental と明記されている。
- [x] Pi の `settings.json`、`extensions/pi-footer.json`、`extensions/pi-gpt-fast-mode/config.json` に実際の書き込み経路を確認し、標準 `lib.hm.generators.mkImpureConfigMerger` を接続。固定済み HM の experimental API を使い、独自 merge は作らない。再適用時は定義値が優先、未定義キーは保持、配列は定義値に置換。新規ファイルは600、既存の mode は保持。設定削除は実ファイルのキー削除を意味しない。
  - `checkPiConfigPaths` は write boundary より前に、対象と親ディレクトリが別の実体へリンクしていれば中止する。既存リンクを通じて正本や store を書き換えない。初回は T9 で旧リンクを退避し、アプリを止めて書き込み可能な実ファイルを準備する。標準 merger は完全なロックではないため、再適用時も Pi 停止が必要。review base は `c7855a0`。
- [x] Claude の `herdr-agent-state.sh` を `pkgs.herdr.src` の公式 asset から executable として配置。本体と同じ nixpkgs lock に従い、独自生成・転載・版別 override は作らない。Herdr の installer は hook / settings に書き込むので、Nix 管理へ切替後の Claude integration には併用しない。
- [x] statusline は標準 npm 経路のまま、現行キャッシュと一致する `ccstatusline@2.2.30` に固定。固定 nixpkgs には未収録、公開 metadata は runtime dependency なし。npm tarball の integrity と現行4ファイルの byte 一致を確認。初回 npx 取得は runtime に残り、Nix build / activation ではインストールしない。Claude の別プロセス変更は保持し、この command 1行だけを index へ取り込む。
- [x] `home/skills.nix` で自作12スキルを共通・Claude 向けの個別ディレクトリとして配置。Claude 固有の同名優先とドット始まり除外を維持。親ディレクトリ全体や `synced` を置き換えない。Antigravity は既存どおり共通置き場への参照リンクで、正本自体は store に配置。
- [x] `home/external-skills.nix` で現行の外部13スキル（12 repo）を commit と展開後 hash で固定し、標準 `fetchFromGitHub` と個別 `home.file` で接続。公開 HEAD と一致する9件に加え、herdr / tdd / worktrunk / readme-creator は現行内容に一致する過去 commit を特定した。内容の更新や別スキルへの置換はしない。skill-creator の `.pyc` 2件だけは生成キャッシュとして復元しない。
- [ ] `config/skills-lock.json` は14登録・13 repoで、うち `cua-driver` は現行 HOME に未配置。復元対象へ戻すかを確認し、旧 lock の廃止は T11 で行う。computedHash は revision / Nix hash として使わない。
- [x] Pi の `APPEND_SYSTEM.md` / `agent-tool-description.md` / `subagents.json` / agent 定義3件 / 通知拡張を通常配置。`subagents.json` は上流がユーザー側を読み取り、UI の保存はプロジェクト側に行うことを確認。npm 7件は既存導入版、pi-subagents は導入済み commit `be898c753e9eb32cf1315f63b1c1f5ef0cf6f782` に native settings で固定し、公開取得可能性を確認。
- [ ] Pi 外部拡張の新規取得・実行時機能の復元を確認する。標準 Pi は npm / Git の可変インストール先を使用し、activation からネットワーク取得や自己更新は実行しない。トップレベルの版固定は推移依存全体の固定ではない。現行の導入実体は Nix Pi 0.99.1 の loader で10 entry point をエラー・警告なしに読み込めたが、新規依存解決・認証付き機能は未検証。
- [ ] Herdr の外部 plugin 3つと Zerdr 提供 plugin を接続。取得 revision、アプリとの対応、可変状態を確認する。plugin 実体・session・log を Git 管理へ追加しない。
- 完了条件: 認証・状態を store に入れず、必要な設定と拡張を復元できる。永続設定変更を制限する場合は、その具体的な影響を切替前に説明・確認する。

### T6. 保護・起動・PATH の統合 — 進行中

共通ファイルの配置は T4 で完了。残るのは起動経路全体の接続確認。

- [ ] `run-with-agent-env.sh`、`__safehouse_args.fish`、対話 CLI 関数の実行先を確認し、不要な mise / Homebrew 固定パスを解消する。引数・終了・signal の透過、秘密の直接アクセス保護、復号失敗時の停止を維持する。
- [ ] T7 のサービス wrapper と、HOME 許可・profile 順・環境継承・TMPDIR 補正を照合する。サービスが対話用 feature を省く差分は維持する。
- 完了条件: shell / 非対話 / launchd の生成された実行経路で、Nix 本体の利用と rm 保護の優先順位を説明できる。実秘密の読み取りや保護ポリシーの緩和で検証を通さない。

### T7. Hermes サービス・Hindsight — 停止待機のみ修正済み

Hermes 本体の追加は T3 の承認に依存。ここではこの Mac のサービスを起動しない構成を作る。

- [ ] `config/nix/home/hermes.nix` と既存 gateway / dashboard wrapper・管理関数を接続し、plist の所有者を一つにする。現在の wrapper は `~/.hermes/hermes-agent/venv/bin/hermes` 前提なので、パッケージ追加だけで済ませない。
- [x] `__hermes_gateway_wait_pid_die.fish` のタイムアウトを失敗に変更し、stop / restart / update の全3呼び出しで後続の bootout / bootstrap / 本体更新を中止する。source・生成配置の fish 構文、byte 一致、差分、固定 lock ビルドで確認。実サービス・待機の動作検証や回帰テストは実施していない。
- [ ] 正規停止コマンド自体の失敗、状態取得失敗、HM の再読み込みを含む切替全体の停止ゲートを確定する。今回の修正は待機 timeout の扱いのみ。
- [ ] ホストごとの利用状態を扱い、未使用・停止中のサービスが定義追加だけで自動ロードされないようにする。利用中の別 Mac のデータを保持し、初期化・上書きしない。
- [ ] Hindsight の `config/.hermes/services/docker-compose.yml` と image digest を固定し、Docker・volume・認証は Nix 世代から分離する。`config/.hermes/SOUL.md` の配置と、旧 `mise.toml` の扱いも確定する。
- 完了条件: 生成された wrapper / plist / activation の確認とビルドが通る。別 Mac の実機移行・稼働確認は、その Mac での作業として残し、この Mac の準備のゲートにしない。

### T8. macOS 設定・手動復元 — 未着手

- [ ] Dock / Finder / キーボード / トラックパッド / スクリーンショット等の必要な非秘密キーだけを調査し、`config/nix/darwin/` に宣言する。preferences 全量を取得しない。
- [ ] Xcode / SDK、Apple ID、Touch ID、TCC、署名、VPN、秘密・Keychain、Docker 等の手動復元を `docs/setup.md` に整理する。
- 完了条件: 宣言対象と手動対象が明確で、変更する OS キーの旧値・未設定状態と戻し方を T9 へ渡せる。

### T9. 適用入口・衝突確認・復旧準備 — 未完了

- [x] **ここまでの部分構成**を通常 build で検証。最新の成功成果物は下記「検証記録」。完成構成の受入ビルドとは区別する。
- [ ] T6・T7 と整合する `switch` を `scripts/dotfiles.{sh,py}` に実装。build と同じ lock 検査・snapshot を使い、未停止サービスや危険な衝突があれば適用を中止する。
- [ ] 配置先のファイル種別・リンク先・所有権を確認し、旧リンク・実ファイル・Fisher / Yazi plugin・shell 初期化・plist の退避先と復旧先を決める。未知のファイルを force overwrite しない。
  - Zellij 削除後、`~/.config/fish/functions/zl.fish` と `~/.config/zellij/config.kdl` に削除済み正本へのリンクを確認。ホーム側は未変更。切替時にこの既知の旧リンクの整理を確認する。Brewfile の実ファイル、インストール済み本体、保存セッション・履歴は今回変更していない。
- [ ] Pi の可変設定3パスの旧リンクと、自作スキルの共通・Claude 各12リンク、Antigravity の参照を確認して初回の退避・復旧手順を用意する。外部13スキルの既存実ディレクトリは個別に確認・退避し、未管理スキルや Claude の `synced` はまとめて置き換えない。Pi の設定保存と適用の競合を避ける停止手順も含める。
- [ ] 人間に実 `config.fish` との差分を確認してもらい、旧 universal PATH・PGDATA 等の未確認値を整理する。
- [ ] T1〜T8 の準備完了後、完成構成をビルドし、生成物・OS 変更範囲・初回の非 Nix 構成への復旧手順を確認する。
- 完了条件: 切替時に変更するものと戻し方をユーザーへ具体的に提示できる。`switch` の実行は T10 の承認後。

### T10. 集中切替・重複管理の解消 — 未着手・直前承認が必要

- [ ] 下記の切替・復旧手順に従い、必要な停止・退避・適用を実行する。エージェント自身が中断される場合の再開手順を先に渡す。
- [ ] 実機で PATH・保護・主要導線を確認し、問題があれば該当する復旧手順を使う。変更を伴う再起動・ログアウト等は直前確認する。
- [ ] 受入後、対象を明示して承認済みの旧導入物・共通 mise 管理・旧配布を整理する。バックアップ・Nix 世代の自動削除、破壊的な Homebrew cleanup はしない。
- 完了条件: 日常の実行・更新経路が新構成へ移り、補完ツール以外の長期二重管理が残らない。この Mac の Hermes は起動しない。

### T11. 運用文書・旧配布の終了 — 進行中

- [x] bootstrap、build / update、標準管理・native 設定ファイルの方針を文書化。`README.md`、`docs/setup.md`、`AGENTS.md` と本プランを更新済み。
- [ ] T9 の完成後に適用・更新・復旧・手動作業の手順を確定。T10 後に `create-symlink.sh` / `create-skills-symlink.sh` / `copy.sh` 等の旧配布経路と呼び出し元を整理する。
- [ ] `Brewfile.example` / `skills-lock.json` 等の旧正本の役割を終了し、移行後の正本を一つにする。秘密の実ファイル・既存 backup は削除対象に含めない。
- 完了条件: 新規 Mac の復元と日常運用が文書から辿れ、実装と説明が一致する。全体完了時にのみ本プランを archive する。

## Requirements

- 現在と今後の Apple Silicon Mac を、ツール・アプリ・ユーザー設定・macOS 設定を含めて再構築できるようにする。実機で意図的に導入されたものを基準とし、Brewfile.example だけを移す構成にしない。依存ライブラリと直接利用するツール、名称変更・別系列を区別する。
- upstream Nix の multi-user daemon、Flakes、nix-darwin、統合した Home Manager を構成の中心にする。ツールは原則 Nix、macOS 対応・保守負担に問題があるものは Homebrew / App Store 等で補完し、導入一覧の正本を Nix に集約する。
- 共通 nixpkgs は rolling 系列を使い、通常の適用は flake.lock で固定済みの標準パッケージから行う。AI ツールも原則として nixpkgs 単位でまとめて更新し、個別・AI グループ更新は必須にしない。外部拡張・プラグイン・スキルの固定にも既存の標準管理を優先する。一般 GUI アプリの自動更新は許容し、flake.lock による同一版復元とは区別する。
- 設定はリポジトリを編集して適用する方式を基本にする。通常の設定・スクリプト本文は .fish / .toml / .json 等の元の形式で管理する。Nix は導入・連携・配置の指定を中心とし、Nix 固有の値や OS 宣言を除いて本文を埋め込まない。既存の即時反映方式を残すためだけの out-of-store link は使わない。
- Node / Python / Ruby / Bun の共通環境は Nix に移す。mise は既存プロジェクトが必要とする用途に限る。別プロジェクトの設定を無断で変更しない。
- dotenvx + Keychain + Safehouse を維持する。機密ファイルの直接アクセスを拒否し、共通ツール用の値は sandbox 外で復号して起動時に注入する。注入済み環境変数の利用は許容し、完全隔離を追加要件にしない。プロジェクト用秘密を共通ファイルへ混ぜない。
- 通常 rm の gomi 転送、失敗時に実 rm へ戻さないこと、Hermes の正規停止と DB 保全を維持する。互換性優先の Safehouse 設計と既存の意図的な例外を狭めず、対話 CLI に承認モード・内蔵 sandbox の強制引数を追加しない。
- 準備・ビルド・復旧準備の後、現在の Mac をなるべくまとめて完全切替する。長期二重管理を完成形としない。停止・再起動・ログアウト・OS 再起動は必要性を示して実行直前に確認する。
- 秘密、認証、memory、session、DB、cache、アプリ生成データは設定世代の復元対象と分離する。実秘密の移行・Keychain 登録・バックアップは人間が sandbox 外で行う。設定の復元とデータの巻き戻しを混同しない。
- Intel / Linux / WSL、macOS 自体の再インストール、Mac 全体の完全復元、無関係な開発プロジェクトの Nix 化は対象外。

## Implementation Decisions

### 1. 構成と管理境界

- ルートに `flake.nix` / `flake.lock` を置き、設定の正本は `config/nix/` と既存 `config/` の明示したファイルにする。`config/nix/darwin/` は OS・Homebrew、`config/nix/home/` は標準パッケージの選択とユーザー設定の配置を担当する。専用の package 定義ディレクトリは設けない。汎用フレームワークや全パッケージの独自再実装は作らない。
- 基本入力は `nixpkgs-unstable`、nix-darwin `master`、Home Manager `master`。後二者の nixpkgs は共通入力へ follows する。上流 Flake の独自依存は、互換性を確認せず一律 follows しない。初回に解決した revision を lock し、適用時に更新しない。
- 通常 build / switch は、公開 input の lock 追加・再解決が必要なら中止する。`--no-write-lock-file` 単独を固定の保証にしない。まず host override なしの `nix flake metadata --no-update-lock-file --json` で基準 lock の整合を確認する。次に非 Flake の host 入力だけを明示 override した解決済み metadata の lock graph を基準と照合し、host leaf 以外の node / edge / revision / hash に差があれば中止する。検査したソースとホストの store snapshot を build / switch で共用し、再評価による別入力への切替を避ける。公開依存の変更は明示的 update に限定する。
- `nixpkgs.hostPlatform = "aarch64-darwin"`、`home-manager.useGlobalPkgs` / `useUserPackages` を利用する。system / home の stateVersion は初回採用時の互換性基準として固定し、更新のたびに最新値へ変えない。unfree は必要なパッケージへ限定する。
- ユーザー名・HOME 等の非秘密のマシン固有値は共通設定から分離する。既存規約どおり実値は Git 外、値を含まない `*.example` は `config/nix/hosts/` に置く。専用のローカル path input と明示的な override で渡し、build / switch が同じホスト入力を使うようにする。秘密や私的データをこの入力へ混ぜない。ホスト入力は store に入る非秘密の構成情報であり、依存 lock に実機の絶対パスを保存しない。
- Git 管理の flake ソースと、必要なファイルだけの参照を使う。`config/` 全体や HOME を path source として取り込まない。Git 外の実 `.env` 等を含み得る `path:.` の安易な利用を避ける。初回の新規 Nix ファイルが Git ソースに含まれることを確認し、秘密を含む一括 stage で解決しない。

### 2. パッケージと更新

- 初期の移行表を本計画のタスク内へ記録し、各直接導入対象について「現在の導入元・移行先・固定単位・例外理由」を確定してから切替する。別の恒久的な手書きパッケージ一覧は増やさず、導入後の正本は Nix 定義とする。
- AI を含む CLI は共通 nixpkgs の標準定義を優先する。本体のバージョン・hash・依存解決はパッケージ側に任せ、設定ファイルの配布とは分離する。個別更新のためにソース・バイナリ配布物・nixpkgs input をツール別に持たない。
- Herdr も nixpkgs 標準定義を使う。gomi / dotenvx / Agent Safehouse を含め、現行版と一致させる override は作らない。Hermes など未収録・非対応の対象は、公式 Flake や Homebrew 等の補完方法を調べ、難しい理由と代案を示して相談する。
- agent-device も標準パッケージ管理での対応を先に調べる。未収録なら npm 等の公式導入方法を候補にし、独自 Nix 定義を作る前に相談する。Apple helper の runtime install / codesign が store 内へ書き込む構成は採用せず、署名・権限操作は導入とは分ける。
- GUI / App Store アプリと Xcode / SDK は macOS の配布経路を利用する。mosh は現行の firewall 手順が実体へ署名を書き込むため、今回は Homebrew 補完とし、store の変更を伴う方法へ移さない。権限・署名・firewall 設定は自動適用へ紛れ込ませない。
- Homebrew は nix-darwin の homebrew 定義を正本にする。通常適用では `onActivation.autoUpdate = false`、`upgrade = false`、`cleanup = "none"`。導入一覧にないものの自動 uninstall / zap はしない。Homebrew 自体がない新規 Mac では、公式 bootstrap を先に行う手順を用意する。
- 共通ランタイムは既存の必要な major / minor とツール要件を確認して選ぶ。単に現行 mise の古い patch と一致させるための独自ビルドは増やさない。プロジェクト指定を尊重し、特定ツール専用ランタイムはそのパッケージへ閉じる。
- `scripts/dotfiles.sh` に小さな操作入口を用意する。`build` は固定構成の事前ビルド、`switch` は固定構成の適用、`update [all|input]` は公開 input の lock 更新のみ。`update nixpkgs` で標準パッケージ群をまとめて更新する。存在しない対象はエラーにし、`update ai` やツール名での単独更新は提供しない。
- 全体更新を一連で実行する手順は、明示的な update → build → 確認付き switch と、Homebrew 側の明示的更新をまとめる。通常 switch に更新を隠さない。Nix 管理した本体の自己更新や既存 installer は使わず、Herdr server 等の再起動は適用と区別する。

### 3. 設定・拡張・秘密

- 本体はパッケージ管理、設定・スクリプトの配布は Home Manager と役割を分ける。通常の設定本文は元の形式のファイルを正本にし、Home Manager はそれを読み込み・配置する。既存モジュールはパッケージ・プラグインの導入、shell 連携等に利用する。Nix profile や interpreter の store パス、nix-darwin の OS 宣言は Nix に残す。設定を配布するために本体パッケージを独自化しない。共通 AGENTS の正本を増やさず、各エージェントの参照関係を維持する。
- **基本は config ファイルをリポジトリで管理し、そのまま Home Manager の標準機能で配布する。** Zed / Pi / Claude 等もこの原則で進める。アプリごとの全設定の分類・分割や可変設定の設計を、配布に先立つ必須作業にしない。
- 認証・履歴・session・DB・cache、`fish_variables` 等の状態は配布対象に入れない。アプリ自身による書き込みが必要で、読み取り専用配置では具体的に支障が出る config だけ例外として標準機能で対応する。根拠のない overlay や独自 merge 処理は作らず、元ファイルや未知のキー・実秘密を黙って上書きしない。アプリからの設定変更を一律に禁止せず、制限が必要なら具体的な影響を切替前に確認する。
- 外部スキルは取得元 revision と内容 hash を固定して `~/.agents/skills/` へ配置し、現行の利用先から参照する。Claude 固有スキルの同名優先、`.disabled` 等の非配布、Antigravity の共通参照を保ち、ディレクトリ全体の置換で他のスキルを隠さない。`skills-lock.json` の computedHash だけを再現用 lock と扱わず、最新版を取り直す experimental_install を新規 Mac の復元手順から外す。自作スキルと Hermes の自己更新データは区別する。
- Pi / Herdr の拡張は標準の拡張管理と、その参照設定の配布を優先する。版・revision の固定が標準機能で可能か確認し、独自ビルドや専用の配布処理が必要になる場合は相談する。Zerdr 提供のローカルプラグインはアプリとの対応を保つ。書き込みを要求するプラグインは状態の保存先を分離する。
- `.env`・復号鍵・OAuth 認証を Nix の値、`home.file.source`、環境変数の静的定義、ソース入力に渡さない。dotenvx は runtime のファイルパスを読み、Keychain 失敗時は起動を止める。新しい配置でも元パス・symlink 実体・復号鍵の直接アクセス保護を維持する。
- shell / 非対話 / launchd のすべてで、安全な rm wrapper が通常 rm として解決される PATH を作る。Nix profile、Homebrew、mise の activation が優先順位を上書きしないことを確認する。保護 wrapper の実装を複数の起動経路へ重複させない。

### 4. Hermes と常駐サービス

- 本体パッケージとサービスの所有権を分離する。標準管理が難しい場合の導入方法は別途相談し、gateway / dashboard の定義は Home Manager 側の一か所で所有する。既存の `hermes gateway install` による plist 再生成とは併用しない。
- 上流 services モジュールは Safehouse / dotenvx と停止順序をそのまま満たさないため、全面採用を前提にしない。パッケージを利用して既存の安全な起動契約を HM の launchd 定義へ移す方法を基本とし、独自のサービス管理基盤は作らない。
- build は停止せず先に完了させる。この Mac には Hermes の既存環境がないため、パッケージ / 起動定義を用意し、停止・データ移行・自動起動は行わない。初期設定は利用開始時に行う。別の Mac の稼働中環境へ適用するときは、利用者確認 → 正規停止 → 終了確認 → 必要な DB バックアップ → 切替 → 起動確認の順にする。旧本体と新本体が同じ DB を同時に開く時間を作らない。
- 現行 wait helper の「タイムアウトでも成功扱いで続行」は採用しない。停止失敗・待機時間超過なら切替を中止し、強制終了や継続を自動選択しない。既存の管理関数を移行時にも利用・更新し、外から launchctl を直接呼んで停止処理を飛ばさない。
- HM の launchd activation が定義の追加だけで未使用・停止中の Hermes を起動しない構成にする。この Mac と新規 Mac は明示的にサービス起動を有効化するまで自動ロードしない。将来の稼働中更新では、HM の再読み込みより前に正規停止が完了する順序を保証し、操作入口を通さない適用でも未停止なら中止する。
- Hermes の config / auth / DB / memory / skills / cron は実機の可変データとして保持し、宣言化する非秘密設定だけを明示する。既存実設定を無差別に読み込まず、必要な非秘密項目はユーザーが提供する安全な抜粋等で確認する。package の追加依存は利用機能と照合する。
- Hindsight の Docker サービスはそのまま独立した状態管理として扱う。Compose 定義は宣言的に配置し、イメージの tag に加えて取得 digest を固定する。データ volume・Codex 認証・Docker runtime は Nix 世代の復元に含めない。データ移行を伴う更新は別途停止・バックアップを確認する。

### 5. OS 設定と bootstrap

- macOS 設定は Dock / Finder / キーボード / トラックパッド / スクリーンショット等、再現に必要な非秘密のキーへ取得対象を絞る。nix-darwin 専用オプションを優先し、未対応項目だけ選別した preferences または手動手順にする。`defaults read` の全量取得や全 plist のコピーはしない。
- Apple ID・Touch ID・TCC・アクセシビリティ・署名鍵・VPN 認証・データ復元は手動作業として分離する。macOS preferences は宣言削除だけでは戻らない場合があるため、変更するキーの旧値・未設定状態を控えて戻し方を用意する。
- Nix bootstrap は公式の版固定済み aarch64-darwin 配布物と checksum を使う。導入版・hash は実装時に公式公開物から確定して記録し、浮動する install URL を無確認で実行しない。multi-user installer による APFS volume、mount、build users、daemon、shell 初期化の変更範囲を説明してから、人間が sandbox 外で実行する。
- macOS 26.2 / arm64 で Nix の導入と構成のビルドは確認済み。nix-darwin / Home Manager の実適用は未確認。既存 Nix 残骸・OS 管理ファイルとの衝突があれば先に止める。UID / GID の固定値や既存 `/etc` ファイルの強制置換を参考例から流用しない。
- インストーラは初期導入に限定し、以後の Nix 本体・設定は nix-darwin へ渡す。現在の sandbox の回避、権限変更、Keychain 操作を bootstrap の副作用として無断実行しない。

## 移行対応表（T1・T3 の補足）

実機 `brew info --json=v2 --installed` の metadata を確認。installed-on-request は44 formula、cask は59件。標準パッケージと Homebrew 宣言のビルドは完了しているが、導入対象の照合と実適用は未完了。App Store は `mas list` で22件を照合済み。Homebrew 外の npm / uv / mise / 手動アプリの metadata 照合は残る。

| 現在の対象（Homebrew） | 移行先 / 固定単位 | 残る確認・例外 |
|---|---|---|
| actionlint, age, awscli, cocoapods, fastlane, fd, ffmpeg, fish, fzf, gh, git, git-lfs, gomi, imagemagick, jq, mas, mkcert, terminal-notifier, tmux, tree, uv, vim, worktrunk, yazi, zoxide | 共通 nixpkgs | Darwin 対応と実際のコマンド互換性 |
| agent-browser, ctx7, keifu, usage | 共通 nixpkgs に実装済み | 実適用・利用確認はこれから |
| zerdr | Homebrew の `ryonakae/tap/zerdr` に宣言済み | アプリ提供 plugin との整合は T5 |
| dotenvx, agent-safehouse | 共通 nixpkgs | gomi と合わせて現行版の維持より標準定義での管理を優先する |
| herdr, opencode, pi-coding-agent | 共通 nixpkgs の標準定義 | 本体と設定配置を分離し、現行版維持の override は作らない |
| claude-code@latest, codex, antigravity-cli（cask） | 共通 nixpkgs の標準定義 | GUI cask と区別し、旧 CLI 導入物の整理は切替後 |
| Hermes, agent-device | 補完案の承認待ち | 調査済み。未回答の提案と採用条件は T3 |
| mosh | Homebrew | firewall 手順が配布実体へ署名するため |
| mise | Nix の CLI、プロジェクト用途のみ | 共通ランタイムの二重管理を解消 |
| fisher | Home Manager の fish plugin 宣言 | plugin revision を固定 |
| icu4c@76, libpq, oniguruma, pcre2, postgresql@17 | Homebrew 補完として宣言済み | 用途が完全には判明していないため除外しない。DB / service の状態確認は切替前 |
| zellij / ZAM | 移行対象外 | 未使用のため管理設定・導入宣言を削除する承認済み。実機の本体・データ削除は未実施 |
| その他55 cask、App Store 22件 | Homebrew 補完、導入一覧を Nix 管理 | 実機59 caskから上記3 CLIとCotEditorを除く。CotEditorは実機にApp Store receiptがあるためmasへ一本化。アプリ自動更新を許容 |

補足: 旧 `figma-beta` は tap metadata がなく、現在の公式 cask は有効な `figma@beta`（126.10.3）だった。Nix 定義には現行名を採用するが、現在の116.18.4のアプリとの衝突・導入経路整理は切替前に確認する。`sheltie` と `zerdr` は `ryonakae/tap` の完全修飾名を使用。生成 Brewfile は nix-darwin の既定でこの2パッケージに `trusted: true` を付けるため、適用時の変更範囲に含める。実適用はまだ行っていない。

依存 metadata 上、oniguruma は jq、pcre2 は fish / Git / glib / ripgrep が使用。icu4c@76 / libpq / postgresql@17 に直接依存する formula は見つからなかったが、開発プロジェクトや実 DB の用途を否定する根拠にはしない。

## 切替・復旧手順（T10・まだ実行しない）

1. **切替前**: 完成した構成を現在の Mac 向けに build。生成された activation とパッケージ参照を確認し、更新する入力・実機パス・サービス・preferences と旧構成への戻し方を用意する。破壊的な Homebrew cleanup や Nix GC は実行しない。
2. **承認と停止**: ユーザーへ影響を提示し、必要なエージェント・端末・アプリの停止を確認。この Mac は Hermes 未使用のため停止・待機は不要。別の Mac の稼働中環境へ適用する場合は、利用者確認後に管理関数で正規停止し、失敗したら中止する。実行中のエージェント自身が途切れる場合は、人間用の再開手順を先に渡す。
3. **状態保全**: この Mac には Hermes の既存データがなく、移行やバックアップは不要。別の Mac の既存環境では DB・認証・memory 等を保持し、停止後、新しい本体の初回起動・schema 更新より前に、人間が sandbox 外で必要な状態を整合した形でバックアップする。関連 WAL 等を取りこぼさず、ログや Git / store へ内容を出さない。Hindsight のイメージやデータを変える場合は別途整合したバックアップを取る。既存の秘密・Keychain は変更しない。
4. **適用**: 確認済みの旧リンク / plist / shell 設定のみを退避して新構成を適用。既存実ファイルを一括強制上書きしない。秘密の参照と PATH を確認し、起動を承認されたサービスだけ起動する。この Mac の Hermes は起動しない。別の Mac では適用前の利用状態と利用者の承認に従う。
5. **スモーク確認**: 下記「検証記録と最終完了条件」の実機項目を確認する。設定変更を伴う再起動・ログアウト等は必要なものだけ直前確認する。
6. **失敗時**: 新サービスを正規停止し、原因に応じて旧生成物 / 旧リンク / 旧 plist / 旧 preferences へ戻す。初回は以前の Nix 世代が存在しないので、退避した非 Nix 構成への復旧手順を使う。以後は保持した Nix 世代を使えるが、Homebrew アプリや OS preferences、DB は同じ操作で戻らない。
7. **DB を変更した場合**: 旧バイナリを新 schema の DB へそのまま向けない。必要なら停止状態で人間がバックアップを復元し、切替後の新規データが失われ得ることを確認してから実施する。自動 rollback で DB を巻き戻さない。
8. **整理**: 新構成の受入後、承認済みの旧パッケージ・配布経路を整理する。復旧用世代・バックアップの削除は移行成功と同時に自動実行しない。Nix 自体のアンインストールは通常の復旧手順にしない。

## 検証記録と最終完了条件

### 現在までに確認できた範囲

| 対象 | 実行結果・根拠 |
|---|---|
| T2 の基盤、T3 の実装済みパッケージ、T4 の配置 | `dotfiles build` の lock 検査・評価・ビルド成功。Pi・スキル・Claude 依存配置と gateway 待機 timeout 修正までの部分構成 |
| 最新 Darwin 成果物 | `/nix/store/iy8myc09vvq61n0dqyd6xs54jnvz653g-darwin-system-26.11.4cff07d` |
| 対応する Home Manager 成果物 | `/nix/store/jizf1lsbvndqwjhl7rz60wr80w4vj3wp-home-manager-generation` |
| fish / shell / Python / TOML / Nix | 変更時に構文・format・差分を確認。生成された fish の読み込み順序と rm の interpreter も確認 |
| `home/files.nix` の配置 | 既存の AGENTS / Yazi の検証に加え、今回追加した9ファイルと正本の byte 一致・shell script の実行権限を確認。Nix format、JSON / TOML / Python / shell 構文、差分を確認。Zed は JSONC のため JSON parser では検証せず、元ファイルとの一致のみ |
| 実機適用・GUI・サービス | **未実施**。ビルド成功はこれらの成功を意味しない |

同じ実機でのビルドに使用したコマンド:

```fish
bash scripts/dotfiles.sh build --host /tmp/dotfiles-machine.SyCOAn6p
```

この一時 host ディレクトリや store 成果物は消えている可能性がある。host 入力がなければ [セットアップ手順](../setup.md#nix-の事前ビルド) に従い、非秘密の `username` / `homeDirectory` だけを持つ入力を用意する。bootstrap をやり直さない。新規の参照ファイルは対象を明示して Git に追加してからビルドする。未追跡ファイルを含めるために `path:.` を使わない。

### 今回の部分構成レビュー

- `0b581d3..1f56deb` を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。既存の hook / plugin / 可変設定の残作業を含む全移行の完了承認ではない。
- Vim はプラグイン維持から最小構成へ方針変更を承認済み。`7785d62..505c0a0` を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。ビルド・構文・生成物の確認も成功。Zellij / ZAM は削除方針へ変更済みで、取得方法の判断は不要。push・実機適用・Plan archive は未実施。

- `c7855a0..b811f39`（Pi・自作スキル）と `b811f39..4273041`（gateway timeout）を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。標準 merger 実装・生成物の動作や実サービスはレビュー側では再実行せず、親側のビルド・ソース確認と区別する。gateway の既存の停止コマンド失敗・PID取得失敗は T7 の残作業。

### Vim の検証記録

- 通常の固定 lock ビルドに成功。上表の Darwin / HM 成果物へ `.vimrc` が byte 一致で配置され、Vim は標準 `vim-9.2.1001` へ解決されることを確認。
- 一時 HOME・空の環境で生成 `.vimrc` を標準 Vim に読ませ、非対話起動が正常終了。行番号・2スペースのインデント・expandtab を確認し、NeoBundle / NeoComplete / Copilot コマンドが未登録であることを確認。Nix format と差分検査も成功。回帰テスト・fixture・stub は追加・再実行していない。
- ビルドは作業ツリーの未コミット Claude 設定も参照するが、その差分は今回のコミット対象に含めない。Pi 2ファイルと合わせて保持する。実機適用・既存プロセス停止・旧 plugin 削除は未実施。

### Zellij / ZAM 削除の検証記録

- `f99a92c..35a8a5c` を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。削除範囲と残す実機データ・旧リンクの境界を確認済み。
- 固定 lock の通常 build 成功。上表の HM 成果物に `home-path/bin/zellij`、`home-files/.config/fish/functions/zl.fish`、`home-files/.config/zellij` が存在しないことを確認。
- 生成 Ghostty 設定は正本と一致し、Option 設定値は変更なし。生成 fish 設定の `fish --no-execute`、Brewfile example の `ruby -c`、Nix format、差分検査を通過。
- 汎用スキル・履歴・無効化済みの Pi 命名設定を除き、管理中の設定・スクリプト・導入宣言に Zellij / ZAM / `zl` の実行参照が残らないことを確認。回帰テスト追加・再実行、配布・サービス操作・実機アンインストールは未実施。

### Pi・自作スキルの検証記録

- 固定 lock の通常 build 成功。Pi 静的7ファイルは正本と一致し、可変3ファイルは `home-files` の store symlink 対象にない。生成 activation は旧リンク検査 → write boundary → linkGeneration → merger の順で、shebang の Nix Bash 5.3 で構文検査成功。macOS 既定 Bash 3 では HM 既存の `-v` 構文を解釈できないため、生成物の指定 shell を使う。
- 自作12スキルの共通・Claude 配置を確認し、Git 管理ファイル延べ226件が byte 一致。`.disabled` を含めず、親全体を symlink にしないこと、Antigravity が共通置き場を参照することを確認。Nix format・JSON parse・差分検査も成功。
- Pi の固定候補は導入済み metadata と npm 公開 version / integrity、Git 公開 HEAD を照合。Nix Pi 0.99.1 の loader を一時 HOME・空環境・offline で使用し、外部8パッケージ＋通知拡張の10 entry point を errors/warnings なしでロード。現在の依存実体での初期化確認であり、取得からの完全復元・UI 操作・認証付き動作を保証しない。
- merger の実 HOME への適用、停止・再起動、外部パッケージの再インストール、回帰テスト・fixture・stub は実施していない。現行 Claude の未コミット差分もビルド snapshot に含まれるが、コミット対象からは除外する。

### 外部スキルの検証記録

- `4273041..d7421c1` を独立した read-only reviewer が確認し、新規の blocking/high・medium/low 指摘なし。cua-driver の既知の判断待ちは現行13件の固定を妨げないこと、優先順位・個別配置・取得元とサブパスの整合を確認。外部取得・内容一致の検証は親側が担当。
- 公開 Git と commit 指定アーカイブで現行13スキルを照合。HEAD と不一致の4件は depth=256 の blob-filtered clone で過去 tree を比較し、一致 commit のアーカイブでも全ファイル・実行ビット一致を確認。GitHub API は匿名 rate limit の403だったため公開 Git を利用し、認証・権限は変更していない。
- 固定 lock の通常 build が全12ソースの `fetchFromGitHub` を含め成功。生成された共通・Claude 各25スキルのうち外部13件・延べ140ファイルが現行配布内容と byte / 実行ビット一致。親ディレクトリ全体を置き換えず、`.disabled`・Python cacheを含めないことを確認。Nix format・差分検査も成功。
- 実 HOME の外部スキル実体は未変更。初回の衝突解消・退避・参照更新、未配置 cua-driver の判断、旧取得手順の廃止は未完了。スキル内部の CLI コマンド実行・回帰テスト・fixture・stub は実施していない。

### Claude 依存の検証記録

- 固定 lock の通常 build 成功。生成 hook は標準 Herdr 0.9.1 の公式 asset と byte 一致・実行可能で、`sh -n` と埋め込み Python の構文検査が成功。生成 settings は正本と一致し、statusline の固定版指定を確認。npm 公開 tarball は registry integrity を検証し、現行キャッシュの4ファイルと一致。JSON parse・Nix format・差分検査も成功。
- Herdr install / hook 実行 / Claude 再起動 / npx 再インストール / 実機適用は行っていない。ビルドは他プロセスの Claude 設定差分も含むが、コミットは statusline の1行だけで、その他は未コミットのまま保持する。

### 残る最終確認

以下は完成構成の受入条件。部分構成での成功を理由にチェックしない。

- [ ] T9: 完成構成の lock 整合・評価・ビルドと、最後に変更したファイルの構文・差分が通る。build では activation・依存更新を実行しない。
- [ ] T5・T9: 秘密・認証・DB・可変状態を store に入れず、配置の所有権・衝突・退避・再適用時の扱いが明確。
- [ ] T6・T7・T9: 生成された PATH・wrapper・plist・activation が保護と停止順序を守り、未使用の Hermes を起動しない。
- [ ] T10: 承認後の実機適用・主要導線の確認が完了し、初回復旧手順と実施結果が記録されている。DB 復旧演習は行わない。
- [ ] T11: 旧配布の終了、手動作業・補完・未実証範囲の明記、実装側の必須レビューが完了。

構文確認は fish の `fish --no-execute`、shebang に対応した shell の `-n`、Python / TOML の parse、Nix formatter / 評価を使う。文書は参照先と `git diff --check` を確認する。通過済みの検証は、後続変更・失敗・未解決の懸念がない限り繰り返さない。

## 履歴・撤回済み事項（再開タスクではない）

- **Vim plugin 維持案の撤回**: 旧10 plugin と NeoComplete を Nix で配置する試作はビルドできたが、NeoComplete が Vim 8.2.1066 以降を拒否するため受入を中止。その後ユーザーが管理しやすさを優先し、外部プラグインなしの最小構成を承認した。個別取得定義・Lua 対応 Vim・移行用分岐は不要となり撤去済み。互換性回避や旧版固定を再開しない。

- **実装開始時の記録**: review base は `ab60631218ce1544049dca60e143d25ac757f9bb`。開始時の「ahead/behind 0/0」「計画は未追跡」は現在には適用しない。Q16 と計画への「ok」で実装承認済み。
- **独立 package 管理の撤回**: gomi / dotenvx / Safehouse の独立定義は `44688a4` で撤回。AI の独立定義を加えた `b9f7ab5` は `23a7c38` で置換。現行版合わせの override、`config/nix/packages/`、nix-update app、`update ai` / ツール別更新は復活させない。
- **古い検証記録**: bootstrap 8件、初期 CLI 統合4件は当時通過。その後の全36テストはダミー Trash 保護で2ケース・4 errors となったが、ユーザー指示でテスト追加・再実行を受入条件から外した。sandbox 外での再試験承認待ちではない。
- **拒否された一時ファイルの後片付け**: `/tmp/dotfiles-tests.log` に記録。macOS の一時ディレクトリ配下の `tmp8ud28y15` / `tmpgumdah3_` は当時残置。制限を回避して削除せず、通常の移行完了条件に追加しない。
- **初回導入の待ち**: installer の `vifs` 待ちは macOS の許可ダイアログ待ちで、人間の許可後に解消。再インストールや volume 修復は不要だった。
- 初期計画の独立レビューは lock 検査の指摘修正後に Approved。これは当時の計画レビューであり、現在の全実装のレビュー・実機適用完了を示さない。過去の中間 build path・版・失敗修正の詳細は対応コミットを参照し、現行の到達点と混在させない。

## 調査根拠

- [nix-darwin README](https://github.com/nix-darwin/nix-darwin/blob/master/README.md): rolling 系列、upstream Nix の管理、installer と interpreter の区別。公式はアンインストールの容易さから Lix installer を推奨しているが、本計画では合意済み upstream Nix の公式配布を使い、通常復旧をアンインストールに依存させない。
- [Nix binary installation](https://nix.dev/manual/nix/stable/installation/installing-binary): macOS multi-user、版固定配布、APFS / mount / daemon の変更範囲。本実装では macOS 26.2 で人間による導入と Nix 2.34.0 の応答を確認済み。
- [Nix flake metadata](https://nix.dev/manual/nix/stable/command-ref/new-cli/nix3-flake-metadata): JSON の lock graph、no-update と no-write の相違、override-input の意味を確認。
- [HM nix-darwin 統合](https://github.com/nix-community/home-manager/blob/master/docs/manual/installation/nix-darwin.md)、[launchd activation](https://github.com/nix-community/home-manager/blob/master/modules/launchd/default.nix)、[Homebrew module](https://github.com/nix-darwin/nix-darwin/blob/master/modules/homebrew.nix): 統合・再読み込み・更新 / cleanup の境界。
- Hermes / Herdr / Safehouse / Pi / skills の調査根拠と未検証事項は dig log に記録。公開 main/master は調査資料であり、適用時にそのまま浮動参照しない。

## 進捗の更新ルール

各タスクは記載した成果物と検証が揃ってから `[x]` にする。途中なら該当する小項目だけを完了にし、残作業・承認待ちを維持する。作業後は Tasks の状態と最新の検証記録を更新し、古い状態の文章を追記で残さない。要件、対象外、公開契約の変更はユーザーへ確認する。

最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通り、T10・T11 を含む移行が完了したら、計画を同名のまま `docs/plans/archived/` へ移す。
