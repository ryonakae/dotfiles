# Nix を中心とした Mac 環境への移行 Implementation Plan

## 現在地と再開手順

**Hermes の方針訂正（最新のユーザー指示）**: 別 Mac の利用本体は `ryonakae/hermes-agent` fork。公式本流を採用した旧実装を見直し、fork と既存 `hermes-gateway` / `hermes-dashboard` を再利用する。dotfiles の適用入口はサービスの利用状態を保存・管理せず、自動停止・再開もしない。配置上必要な場合の読み取り専用の停止確認とエラーに限定する。Q19 の選択は不要となり、専用 controller による運用管理を撤回する。以下の旧実装・成功ビルドは fork 版の動作証明ではない。まず T7 の修正計画を確認してから T9 へ戻る。

**実装承認済み・移行準備中。基盤は完了、設定・拡張の移行が途中。upstream Nix 自体は導入済みだが、nix-darwin / Home Manager の構成は一度も実機へ適用していない。**

- 直近の review base は `74bd8d6`、T6・T7 の実装 commit は `945d699`。固定ビルド・生成物確認と独立レビューが完了。リモートとの同期状態は再開時に `git status -sb` で確認し、未 push の既存コミットを無関係な変更と混同しない。
- 実装・検証・承認状態の正本はこのプラン。[dig log](../dig/2026-10-03-nix-migration.md) は合意と調査の出典であり、調査当初の「Nix 未導入」等を現在の状態として扱わない。
- **進捗の更新場所は下の Tasks。** `[x]` は記載した成果物とその検証の完了を表し、実機適用の完了ではない。未完了項目には残作業・完了条件を記載する。撤回済みの試作は末尾の履歴に隔離した。

次のセッションは以下から再開する。

1. `git status --short` と直近の差分を確認する。保持する他プロセスの変更は Claude 設定。Pi 2ファイルの承認済み変更は T5 の配置・版固定に取り込んだ。本文の確認基準より後の変更があれば、実ファイルを優先して進捗を更新する。
2. **Hermes の公式 Flake パッケージのみの採用・固定ビルドは完了。agent-device は npx 実行へ変更し、Shepherd は復元対象から除外する方針を承認済み。** ユーザー承認の Herdr 別ペイン（sandbox 外）で固定構成をビルドし、生成物を確認した。T6・T7 の起動・配置・停止処理を実装し、固定ビルドと独立レビューを通過した。Hermes の実起動・停止・実機適用は未実施。
3. **Zerdr は Homebrew 版、cua-driver スキルは復元する方針で承認済み。** T5 の Pi・スキル・Claude 依存と Git plugin 固定復元手順、T8 の限定 preferences 宣言を進めた。Pi 拡張の新規取得・全機能の復元検証、T9 の適用ゲート・衝突解消は未完了。
4. T9 の `switch` と衝突・退避・復旧準備から再開する。T7 の controller は新旧の所有関係が不明なら拒否するので、別 Mac の旧サービス移行を自動化済みと扱わない。部分構成のビルド成功だけで T10 の切替へ進まない。

### 再開時に保持する状態・操作境界

- Pi の承認済み変更（fast-mode の `desired: false`、settings の `lastChangelogVersion: 1.0.0`）は T5 の実装へ取り込んだ。動作中の Pi が更新するため、以降も編集・stage の直前に差分を確認し、他プロセスの変更を上書き・巻き戻し・一括 stage しない。
- Claude 設定の初回 `model: "fable"` 追加は `1f56deb` へ取り込み済み。その後の未コミット差分は他プロセスによるものとして保持する。別プロセスが変更し続けるため内容を推測せず、作業に必要な場合だけ確認する。今回のコミット対象には含めない。
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

### T3. パッケージと更新単位 — 実装済み対象の宣言・ビルド完了、棚卸しは T1

- [x] 一般 CLI・共通ランタイムと Homebrew 補完を宣言。`890ef27`。現在の正本は `config/nix/home/packages.nix` と `config/nix/darwin/homebrew.nix`。
- [x] gomi / dotenvx / Agent Safehouse、Claude Code / Codex / Pi / OpenCode / Herdr / Antigravity CLI を共通 nixpkgs の標準定義へ統一。`44688a4`、`23a7c38`。独自 package 定義・専用 updater は削除済み。
- [x] 55 cask・22 App Store アプリ・補完 formula 7件を宣言し、生成物を確認。Homebrew の自動更新・upgrade・cleanup と PostgreSQL の start/restart は無効。**宣言とビルドのみで、Homebrew bundle は未実行。**
- [x] **Hermes パッケージの採用・固定ビルド** — 公式 Flake の `packages.aarch64-darwin.default` のみを `home.packages` へ追加し、input と root lock を接続した。サービスモジュール・独自 package 定義は追加せず、独自依存を未検証で共通 nixpkgs へ follows しない。既存4 input の内容保持、構文、固定 snapshot の評価・ビルド、生成 CLI の参照先を確認。Safehouse の公開ソース参照拒否後、ユーザー承認の Herdr 別ペインで検証した。review base は `f71f25d`。サービス接続・実起動は T6・T7 に残る。
- [x] **agent-device のグローバル管理を廃止** — ユーザー指示で mise の `npm:agent-device` 宣言を削除し、自作 `use-agent-device` スキルと `.ad` 実行例を `npx --yes agent-device` へ変更。独自の版固定・更新制限は設けない。Node は npx とは別に要件を満たすものを選ぶ。外部の公式スキルは変更せず、そこでの CLI 表記も npx に読み替える。npm cache・状態は残る。実機の既存導入物は未アンインストール。
- [x] **Shepherd を復元対象から除外** — ユーザー指示で本体・専用 Node runtime の補完を取りやめ、Herdr plugin の復元コマンドを削除。本体の既存 wrapper、稼働 daemon、実 registry / checkout / state は未変更。無効化済みの team スキルと調査履歴は配布対象外のまま保持する。
- [x] **Zerdr は Homebrew 版を採用** — ユーザー承認により既存の `ryonakae/tap/zerdr` 宣言を維持。復元手順で `brew --prefix` から本体のパスを明示し、開発版を拾わないようにした。nix-darwin が導入対象を宣言し、実体・更新は Homebrew が管理する。現 Herdr manifest の開発 checkout 参照は未変更で、切替時の再登録は T5・T10 に残す。
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
- [x] `home/external-skills.nix` で既存の外部13スキル（12 repo）を commit と展開後 hash で固定し、標準 `fetchFromGitHub` と個別 `home.file` で接続。公開 HEAD と一致する9件に加え、herdr / tdd / worktrunk / readme-creator は現行内容に一致する過去 commit を特定した。内容の更新や別スキルへの置換はしない。skill-creator の `.pyc` 2件だけは生成キャッシュとして復元しない。
- [x] **cua-driver スキルの復元宣言・ビルド** — ユーザー承認により、`home/external-skills.nix` に公式 `trycua/cua` のスキルを追加。取得対象は公開 commit `3a784c5c32fc834f387f47f4835dd869ef505eee` の `libs/cua-driver/rust/Skills/cua-driver`。既存の共通・Claude 向け個別配置へ接続し、固定ビルドと11ファイル×2配置の一致を確認。外部14スキル（13 repo）、自作を含め共通・Claude 各26スキルになった。本体の導入・GUI 操作・実 HOME への適用は含めない。旧 `config/skills-lock.json` の computedHash は revision / Nix hash として使わず、旧 lock の廃止は T11 で行う。
- [x] Pi の `APPEND_SYSTEM.md` / `agent-tool-description.md` / `subagents.json` / agent 定義3件 / 通知拡張を通常配置。`subagents.json` は上流がユーザー側を読み取り、UI の保存はプロジェクト側に行うことを確認。npm 7件は既存導入版、pi-subagents は導入済み commit `be898c753e9eb32cf1315f63b1c1f5ef0cf6f782` に native settings で固定し、公開取得可能性を確認。
- [ ] Pi 外部拡張の新規取得・実行時機能の復元を確認する。標準 Pi は npm / Git の可変インストール先を使用し、activation からネットワーク取得や自己更新は実行しない。トップレベルの版固定は推移依存全体の固定ではない。現行の導入実体は Nix Pi 0.99.1 の loader で10 entry point をエラー・警告なしに読み込めたが、新規依存解決・認証付き機能は未検証。
- [x] Herdr の Git plugin は標準 `install --ref <commit>` の復元手順を `docs/setup.md` に固定。当初の3件から、ユーザー指示で Shepherd を除いた2件を復元対象とする。現 metadata / HEAD / clean 状態を調べ、親側でも公開 commit アーカイブの manifest と主要ファイル7件を照合。再 install で `--ref` を省略すると HEAD へ移ること、有効化を伴うこと、build / activation から実行しないことを明記した。
- [ ] Git plugin の実機導入と機能確認。Agent Context は同一 release から binary / checksum を取得し、source commit 固定は binary の完全な immutable hash 固定ではない。Shepherd の復元は対象外。
- [ ] 承認済みの Homebrew 版 Zerdr の標準 `setup install` で manifest と登録を復元する。現開発 executable の絶対パスは配布しない。setup は Zed tasks にも書くが、現Nix配置は Zed settings のみで tasks は管理していない。
- Agent Context / Worktrunk の tracked config には本番実装の書き込み経路がなく、個別の読み取り専用配置を維持する。registry、checkout、state は可変で残す。plugin 実体・session・log は Git / store へ取り込まない。
- 完了条件: 認証・状態を store に入れず、必要な設定と拡張を復元できる。永続設定変更を制限する場合は、その具体的な影響を切替前に説明・確認する。

### T6. 保護・起動・PATH の統合 — 宣言・生成物の確認済み

共通ファイルの配置は T4 で完了。残るのは起動経路全体の接続確認。今回の review base は `74bd8d6`。

`home/fish.nix` で管理 CLI / Safehouse / Hermes の実行先を Nix パスへ接続し、`home/protection.nix` で dotenvx を固定。プロジェクト用 PATH 全体は置換しない。サービス wrapper は旧 mise / venv 前提を外し、dashboard の TMPDIR 補正を追加した。`home/hermes.nix` でサービス側も Nix の実行先へ接続し、固定ビルドと生成物の構文・参照確認を通過。実機 PATH の衝突・初回切替は T9・T10 に残る。

- [x] `run-with-agent-env.sh`、`__safehouse_args.fish`、対話 CLI 関数の実行先を確認し、不要な mise / Homebrew 固定パスを解消する。引数・終了・signal の透過、秘密の直接アクセス保護、復号失敗時の停止を維持する。
- [x] T7 のサービス wrapper と、HOME 許可・profile 順・環境継承・TMPDIR 補正を照合する。サービスが対話用 feature を省く差分は維持する。
- 完了条件: shell / 非対話 / launchd の生成された実行経路で、Nix 本体の利用と rm 保護の優先順位を説明できる。実秘密の読み取りや保護ポリシーの緩和で検証を通さない。

### T7. Hermes サービス・Hindsight — fork と既存スクリプトへ修正中

実装承認済み、今回の review base は `6b8021a`。旧 `945d699` の専用 controller と本流採用は撤回対象で、旧ビルド・レビュー記録は下の履歴に残す。最新の停止仕様は Implementation Decisions 4 と dig log の決定事項を正本とする。

- [ ] `flake.nix` / `flake.lock`: `github:ryonakae/hermes-agent/ryonakae` の `2a485666e6754ec8e8a0ba9b383ea1eb6e518f14`（`sha256-35HGnPLz0FOWmLA1FtwGD8i1H1YjUUNc3ru+mKR+mMw=`）へ変更済み。共通 nixpkgs / nix-darwin / Home Manager / host node は変更なし。fork 同梱の aarch64-darwin パッケージを使い、独自 package は作らない。通常 build は実行中で、完了確認待ち。
- [ ] `hermes-gateway.fish` / `hermes-dashboard.fish`: `74bd8d6` の launchd + fork 標準 CLI の経路へ戻し、Nix 実行先とエラー伝播を接続した。restart は stop が成功した場合だけ start。自己更新は Nix の更新・ビルドを案内する。
- [ ] `home/hermes.nix`: 599行の `hermes-service.py` と専用 Python / psutil 環境を撤去し、`check-stopped.sh` の読み取り専用確認へ置換した。GUI session の launchd 登録・判別可能な Hermes プロセスを確認し、未停止・取得失敗・未知の形式はエラー。PID・子プロセスの追跡、状態保存、停止・再開はしない。
- [ ] 生成物・最終ビルド・独立レビューを確認する。fish / shell / Nix の構文と差分検査は通過。最初の fork build は旧 controller を含む snapshot のため、成功しても最終構成の検証とは区別する。ログは `/tmp/dotfiles-hermes-fork.71SzyJwq/build.log`、終了コードは同ディレクトリの `build.exit`。
- [x] Hindsight の Compose と SOUL の配置、image digest は変更なし。Docker の volume・認証・起動は配置と分離する。

公開 fork の gateway stop / dashboard --stop には timeout 後の強制終了がある。ユーザーから、その挙動も fork 標準に任せることへの `ok` を取得済み。旧 Q18 の自動強制終了禁止は置換された。独自の運用 controller や fork への追加機能で停止を再実装しない。実サービスでの停止成功・DB バックアップの整合性を未検証のまま保証しない。

plist は既知の生成物だけユーザー所有の実ファイルへ配置し、標準 HM launchd activation には登録しない。Disabled / RunAtLoad / KeepAlive は既存の配置分離構成を維持し、明示的な start / stop が enable / disable を行う。未知の既存 plist の退避と別 Mac の実機移行は未実施。

回帰テスト・fixture・stub の追加や再実行、実サービス操作・実機適用は行わない。既存の fork build は承認済み Herdr 別ペイン `w3W:pA` で継続中。Safehouse 内での build 診断用 process 一覧は `Operation not permitted` のため取得できず、同環境での再試行はしていない。

### T8. macOS 設定・手動復元 — 宣言・文書化済み、実適用は T10

- [x] Dock / Finder / キーボード / トラックパッド / スクリーンショットの非秘密30キーを個別に読み、値のある18キーを `darwin/preferences.nix` の標準オプション16項目へ宣言。トラックパッド2項目は標準モジュールが内蔵/Bluetooth双方へ書く。未設定12キーには値を新設せず、preferences 全量は取得していない。具体的な復旧用控えは下記。
- [x] Xcode / SDK、Apple ID、Touch ID、TCC、署名、VPN、秘密・Keychain、Docker、未宣言の UI 設定の手動復元を `docs/setup.md` に整理した。
- 完了条件: 宣言対象と手動対象が明確で、変更する OS キーの旧値・未設定状態と戻し方を T9 へ渡せる。

### T9. 適用入口・衝突確認・復旧準備 — 未完了

固定 nix-darwin の入口を調査済み。標準 `switch` に検査済み source / host snapshot を渡し、標準の世代登録を維持できる。profile 登録は activation より前で、適用は非トランザクショナル。`activate` 単独は世代を登録しない。標準 `check` / dry-run の activation を読み取り専用検査として実行しない。最新指示により、入口は Hermes の起動状態を保存・管理せず、必要な停止確認とエラーに限定する。Q19 の選択は撤回。T7 の fork 対応・縮小後に再開し、T9 のコード編集・適用は未実施。

- [x] **ここまでの部分構成**を通常 build で検証。最新の成功成果物は下記「検証記録」。完成構成の受入ビルドとは区別する。
- [ ] T6・T7 と整合する `switch` を `scripts/dotfiles.{sh,py}` に実装。build と同じ lock 検査・snapshot を使い、未停止サービスや危険な衝突があれば適用を中止する。
- [ ] 配置先のファイル種別・リンク先・所有権を確認し、旧リンク・実ファイル・Fisher / Yazi plugin・shell 初期化・plist の退避先と復旧先を決める。未知のファイルを force overwrite しない。
  - Zellij 削除後、`~/.config/fish/functions/zl.fish` と `~/.config/zellij/config.kdl` に削除済み正本へのリンクを確認。ホーム側は未変更。切替時にこの既知の旧リンクの整理を確認する。Brewfile の実ファイル、インストール済み本体、保存セッション・履歴は今回変更していない。
- [ ] Pi の可変設定3パスの旧リンクと、自作スキルの共通・Claude 各12リンク、Antigravity の参照を確認して初回の退避・復旧手順を用意する。外部13スキルの既存実ディレクトリは個別に確認・退避し、未管理スキルや Claude の `synced` はまとめて置き換えない。新規 cua-driver の配置先が未作成かも適用直前に再確認する。Pi の設定保存と適用の競合を避ける停止手順も含める。
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

- 本体は `ryonakae/hermes-agent` fork 同梱の Flake パッケージを利用する。公式本流への置換や独自 package / updater は行わず、公開 input と依存を root lock で固定する。
- 起動・停止・再起動は既存の `hermes-gateway` / `hermes-dashboard` から fork 標準 CLI と launchd を使う。timeout 後の強制終了を含む fork 標準の停止仕様はユーザー承認済み。旧 Q18 の強制終了禁止と独自 controller は撤回し、dotfiles で停止アルゴリズムを再実装しない。コマンドの失敗は後続操作へ伝播する。
- Q17 の配置と運用の分離は維持する。wrapper / plist の生成・必要最小限の配置は Home Manager が担当し、Hermes に標準 HM launchd activation を使わない。installer による plist 再生成とは併用しない。未知の実ファイルは強制上書きしない。
- 配置上必要な確認は、write boundary 前の読み取り専用チェックで行う。未停止・取得失敗・未知の形式ならエラーにするだけで、適用入口と activation から停止・再開しない。適用前の利用状態を保存して後で復元する仕組みや、PID / 子プロセス管理は追加しない。
- この Mac は Hermes 未使用。配置だけでは起動せず、既存データの移行・初期化・自動起動をしない。別 Mac の停止・バックアップ・適用・再開は人間の別操作とし、それぞれ直前に承認を得る。初回起動・schema 更新より前に必要なデータを保全し、Nix 世代を戻す操作を DB の巻き戻しと混同しない。
- config / auth / DB / memory / skills / cron は実機の可変データとして残す。非秘密の明示した設定だけを配置し、実設定や秘密を無差別に読み込まない。Safehouse / dotenvx の保護・環境継承・サービスと対話用 feature の差は維持する。
- Hindsight は独立した Docker 運用とし、Compose と image digest だけを宣言する。volume・認証・Docker runtime は Nix 世代から分離し、停止・データ移行・起動を自動化しない。

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
| Hermes | 公式 Flake のパッケージのみ | 採用・固定ビルド済み。サービス接続は T7 |
| agent-device | npx で都度実行 | mise 宣言は削除。版・Node 要件と起動方法は自作スキルに記載 |
| @ryonakae/shepherd（npm） | 復元対象から除外 | Herdr plugin と専用 runtime の復元も取りやめ。実機削除は別操作 |
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
| T2 の基盤、T3 の実装済みパッケージ、T4 の配置 | `dotfiles build` の lock 検査・評価・ビルド成功。Pi・スキル・Claude 依存、gateway timeout、macOS preferences 宣言までの部分構成に加え、Hermes 本体も同じ lock 検査・snapshot・check/build 処理で検証 |
| 最新 Darwin 成果物 | `/nix/store/vxvdvlvffr0lf9kaiy2lvb1w6sxg5izy-darwin-system-26.11.4cff07d` |
| 対応する Home Manager 成果物 | `/nix/store/kyrg9a2gn3dd6hh3gryp2vpaqm8s8xcb-home-manager-generation` |
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
- 実 HOME の外部スキル実体は未変更。初回の衝突解消・退避・参照更新、旧取得手順の廃止は未完了。cua-driver の復元は後続で承認された。スキル内部の CLI コマンド実行・回帰テスト・fixture・stub は実施していない。

### Claude 依存の検証記録

- `d7421c1..8e74f44` を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。本体と asset の取得元、配置と既存参照、statusline の1行変更、installer との所有権の説明を確認。公開ソース・npm・生成物の検証は親側が担当。
- 固定 lock の通常 build 成功。生成 hook は標準 Herdr 0.9.1 の公式 asset と byte 一致・実行可能で、`sh -n` と埋め込み Python の構文検査が成功。生成 settings は正本と一致し、statusline の固定版指定を確認。npm 公開 tarball は registry integrity を検証し、現行キャッシュの4ファイルと一致。JSON parse・Nix format・差分検査も成功。
- Herdr install / hook 実行 / Claude 再起動 / npx 再インストール / 実機適用は行っていない。ビルドは他プロセスの Claude 設定差分も含むが、コミットは statusline の1行だけで、その他は未コミットのまま保持する。

### macOS preferences の検証・復旧用控え

- `8e74f44..3af1942` を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。宣言16項目・旧値と型・未設定12キー・Dock再起動と復旧の説明を確認。実機の読取・生成物・build の検証は親側が担当。
- 固定 lock の通常 build 成功。生成 activation の18個の defaults plist を parse し、現在の個別キー値と一致を確認。指定された Nix Bash の構文検査、Nix format、差分検査も成功。標準の Dock 再起動が生成されることを確認したが、activation / defaults write / killall は実行していない。
- 以下は 2026-10-03 の準備時点の読取値。T9・T10 直前に再確認し、後から変更された値をこの控えで上書きしない。Nix 標準型に従い、float のリピート値・サイズは integer、integer の Clicking は boolean になる。値は維持するが、厳密に戻す場合は以下の旧型も復元する。

| domain | key | 旧型・値 |
|---|---|---|
| NSGlobalDomain | AppleShowAllExtensions | boolean true |
| NSGlobalDomain | InitialKeyRepeat / KeyRepeat | float 15 / 2 |
| NSGlobalDomain | NSAutomaticCapitalizationEnabled / NSAutomaticPeriodSubstitutionEnabled / NSAutomaticSpellingCorrectionEnabled | boolean false |
| com.apple.dock | autohide | boolean true |
| com.apple.dock | tilesize | float 64 |
| com.apple.dock | show-recents / mru-spaces | boolean false |
| com.apple.finder | ShowPathbar / ShowStatusBar | boolean true |
| com.apple.finder | FXPreferredViewStyle / FXDefaultSearchScope | string Nlsv / SCcf |
| com.apple.AppleMultitouchTrackpad / com.apple.driver.AppleBluetoothMultitouch.trackpad | Clicking | integer 0 |
| com.apple.AppleMultitouchTrackpad / com.apple.driver.AppleBluetoothMultitouch.trackpad | TrackpadThreeFingerDrag | boolean false |

- 読み取ったが未設定で、今回は宣言しないキー: NSGlobalDomain の ApplePressAndHoldEnabled / NSAutomaticDashSubstitutionEnabled / NSAutomaticQuoteSubstitutionEnabled / com.apple.swipescrolldirection、Dock の orientation / magnification / largesize / minimize-to-application、Finder の AppleShowAllFiles、screencapture の type / location / disable-shadow。
- preferences の宣言削除・旧 Nix 世代への切替だけを復旧とみなさない。旧値は対象別に正しい型で戻し、元が未設定なら対象キーだけ削除する。Dock 再起動や必要な logout は T10 直前承認の対象。入力ソース・Dock の並び等は個別手動復元とし、全 plist コピーを手順にしない。

### Herdr plugin の調査・固定手順

- `3af1942..0702bb5` の復元手順・判断事項を独立した read-only reviewer が確認し、新規の blocking/high・decision required・medium/low 指摘なし。既知の補完・本体・実行元の判断は未解決のまま保持。公開ソース・実 metadata の検証は親側が担当。
- 固定 Herdr 0.9.1 の source で `--ref` checkout、registry 保存、再 install、config/state 分離を確認。調査当時の Git plugin 3件は通常の untracked を含め clean。registry 上はこの3件と Zerdr の全4件が enabled。その後 Shepherd は復元対象から除外したが、実 registry は変更していない。ignored build artifact の健全性は保証せず、公開 commit archive の manifest・主要7ファイルと現実体の一致を別途確認した。
- tracked config 2件は Agent Context の read/mtime監視と Worktrunk の設定読取だけで、本番の書込処理は別state領域。書き込み可能にする根拠はなく、既存T4配置を変更しない。
- 公開 Zerdr v0.8.0 source では、標準 setup が実行元を含む manifest を生成して Herdr に link し、Zed tasks を merge する。その後 Homebrew 版の採用が承認されたが、現 manifest の開発版参照からの切替は未実施。実plugin install・link・setup・サービス操作・テストは行っていない。

### Hermes パッケージ追加の検証記録

- ユーザーの「hermesはそれでok」で公式 Flake のパッケージのみの採用を承認。`flake.nix` / `flake.lock` / `home/packages.nix` と更新手順を変更。`home-manager.extraSpecialArgs` の既存 `inputs` を使用し、公式サービスモジュールは import していない。wrapper・plist・実 HOME は未変更。
- root lock の Hermes は `3251a180f01ad21ae059862997307bf75f3e3f0a`。Nix が既存 nixpkgs / HM の node 名を変更したが、root から解決した既存4 input の内容は変更前と完全一致。通常 build と同じ `locked_source` の host leaf 以外の不変検査も通過。
- 当初は空き容量約3.1 GiBと Safehouse の参照拒否で中断。ユーザーが容量を確保し、sandbox 外での評価、続いて実ビルドを承認した。実ビルド前の空きは約34 GiB。現 lock の構成は dry-run で1,261 derivation と807取得 path（712.4 MiB download / 2.7 GiB unpacked）を要求した。
- 現 lock の固定 source snapshot と非秘密 host で `darwinConfigurations.mac.system.drvPath` を評価したところ、`/nix/store/kgy3pr5z9l4cangknb37d3aalx5lp0vz-source/.envrc` の参照が `Operation not permitted` で失敗。権限・policy を変更せず、その時点では評価を中断した。Nix format・差分検査は成功。
- 承認された sandbox 外の評価は `allow-import-from-derivation=false` で成功。続く実ビルドも、通常入口の `locked_source` による host leaf 以外の不変検査を通し、同じ snapshot に `flake check` / `build --no-link` を実行して成功。root lock の byte 不変も確認。snapshot は `/nix/store/hkajg0vfb9sa2ay32sbzy7vlf6310jjf-source`、ログと結果は `/tmp/dotfiles-hermes-build.F14YGKOK/`。現行 Claude の未コミット設定も snapshot に含むが、コミット対象からは除外する。
- HM の `hermes` / `hermes-agent` / `hermes-acp` は `/nix/store/6rpwq8raqms4pqzac6v5gb3jxykqcx6n-hermes-agent-0.0.0/bin/` を参照。公式の install stamp は固定 commit・`distribution=nix`・`updateMechanism=external`。表示版 `0.0.0` は上流定義のままで、独自 override はせず commit を識別子にする。3 wrapper と Darwin / HM activation の指定 shell による構文検査を通過。生成 launch agent は0件。
- 実装 commit `1cdc4b5`。`f71f25d..1cdc4b5` の5ファイルをビルド後に独立した read-only reviewer が確認し、新規の blocking/high・decision required・medium/low 指摘なし。既存 input の保持、package-only の接続、ビルド済みとサービス未接続の区別を確認。評価・ビルド・生成物の確認は親側が担当し、レビュー側では再実行していない。
- 実 HOME への適用、Hermes の初期化・起動、サービス操作、回帰テスト、GC・データ削除は未実施。T6・T7 のサービス接続と T9・T10 の切替は別途残す。

### agent-device の npx 化・Shepherd の復元廃止

- review base は `5f35d54`。変更対象は mise の1宣言、自作 `use-agent-device` の本文と `.ad` reference、Herdr 復元手順、このプラン。Nix の新規定義・専用 wrapper は増やさない。
- 公式 Installation にある npx 実行を使う。ユーザー指示に従い、版固定や更新制限を追加しない。Node 22.12以上（Webは24以上）の前提、cacheと状態が残ること、doctorのdaemon置換への注意を維持する。
- mise TOML とスキルの YAML metadata を parseし、スキル・reference の fish コードブロック4件の構文、相対リンク、差分を確認。CLI の mise 宣言と Shepherd の復元コマンド、実行例の bare CLI / mise 起動が残らないことを確認した。変更は設定と運用文書で、Nix の再ビルド・npx の実取得は行っていない。
- 実機アンインストール、plugin の無効化・削除、daemon 停止、npx による取得・起動、Simulator 操作、回帰テストは未実施。実体の整理は T10・T11 で対象と停止条件を確認してから行う。

### Zerdr の実行元確定・cua-driver スキル復元

- review base は `99cd316`。Zerdr の既存 Homebrew 宣言を維持し、復元手順で Homebrew prefix 配下の実行ファイルを明示する。Herdr の登録と Zed tasks を変更する `setup install` は未実行。
- cua-driver スキルは現在の HOME に存在しないため、旧導入内容との一致は保証せず、公開 commit のスキル（metadata 0.33.0）を復元する。公開 archive の展開後 hash で固定し、11ファイル・相対リンク先の存在・symlink がないことを確認した。公式スキルの本文は改変しない。
- 通常の `scripts/dotfiles.sh build --host /tmp/dotfiles-machine.SyCOAn6p` を Herdr 別ペインで実行し成功。ログは `/tmp/dotfiles-cua-build.OLJA1iTc/build.log`、snapshot は `/nix/store/a1pipxx0y088rd4z2yg9x4a09246iid6-source`。root lock は未変更。Claude の他プロセス変更は snapshot に含むが、コミットからは除外する。
- 生成された共通・Claude 各26スキルで cua-driver の11ファイル×2が公開ソースと byte / 実行ビット一致。前回の agent-device npx 化も両配置の本文・reference が正本と一致。Nix format、Zerdr 復元コマンドの fish 構文、差分を確認。Zerdr の本体・登録、cua-driver 本体、稼働プロセス・権限、実 HOME は未変更。GUI 操作・回帰テストは実施していない。
- 実装 commit `da0a558`。`99cd316..da0a558` と先行の `5f35d54..99cd316` の npx 化・Shepherd 復元廃止を独立した read-only reviewer が確認し、新規の blocking/high・decision required・medium/low 指摘なし。公開取得・生成物・build は親側が検証し、レビュー側では再実行していない。

### T6・T7 の起動経路・停止処理の検証記録

- review base は `74bd8d6`。通常の固定 lock build を承認済みの Herdr 別ペインで実行し成功。ログは `/tmp/dotfiles-hermes-services.ZRhCAt20/build.log`。root lock の SHA256 は `b9d00d6546aa0c4c00f73024aee9a5b52309d297f96cd92d2c77965082fe2864` のまま。build snapshot には他プロセスの Claude 設定も含むが、コミット対象にはしない。
- 生成された標準 HM LaunchAgents は0件。別の `hermes-launch-agents` には対象2 plist があり、単一の Nix store wrapper・明示 HOME / HERMES_HOME / PATH・Disabled / RunAtLoad / KeepAlive を確認。停止確認 → write boundary → linkGeneration → plist 配置の順を確認した。配置処理は状態の検査とコピーだけを行い、サービスを操作しない。
- 生成 controller の置換後本文、fish 管理関数、SOUL、Compose は正本と一致。対話 CLI / dotenvx / サービスの Nix 実行先、rm 最優先の PATH、旧 mise / venv / wait helper の非配布を確認。wrapper の HOME 許可・環境継承・profile 順とサービス別 feature は維持している。
- Python のインメモリ構文コンパイル、fish / shell / YAML / Nix の構文・format・差分検査、生成 activation の指定 Nix Bash による構文検査を通過。controller 自体は実行していない。既存 launchctl の読み取り専用 metadata では現在のセッションと同 UID の asuser が Aqua であることだけを確認し、root 経由の実 activation は未検証。
- 実装 commit `945d699`。`74bd8d6..945d699` の15ファイルを独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。build・外部ソース・生成物検証は親側の実行結果で、reviewer は再実行していない。
- 実起動・停止・SIGTERM・Hermes 初期化・Compose 実行・実機適用・回帰テスト・fixture・stub は未実施。launchd 診断形式、厳格な process census、稼働中 state 更新との互換性は実機での確認が必要。既知の管理定義だけを扱い、管理外の書き換え・並行管理操作・観測前に service tree を離れたプロセスの追跡を保証しない。旧サービスの自動移行を完了扱いにしない。

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
