# Nix を中心とした Mac 環境への移行 Implementation Plan

## 現在地と再開手順

**Homebrew 本体の管理変更（ユーザー承認済み）**: `nix-homebrew` を追加し、本体の導入・版固定も Nix に含める。新規 Mac での Homebrew 公式 bootstrap は不要となる。既存 Homebrew は `autoMigrate` で引き継ぎ、tap と formula / cask / App Store アプリの一覧は既存の nix-darwin 定義を維持する。自動 upgrade・cleanup は追加しない。実機への移行は未実施で、初回適用前に Homebrew 管理部分の退避・復旧範囲を確認する。

**設定配置の方針変更（ユーザー承認済み）**: Q12 の旧 immutable 方式と Pi の merger 例外を撤回し、追跡済み設定・自作スキル・静的スクリプトは `config.lib.file.mkOutOfStoreSymlink` による `~/dotfiles/config/` への live link に変更する。checkout は README と同じ `~/dotfiles`、実パスは `homeDirectory` から作る。内容編集・アプリのリンク先への書き込みは Git 差分となり、Nix 再適用は不要。Nix が管理するのはリンクで、本文は Git で戻し、Nix 世代の rollback では戻らない。本体・外部 plugin・外部スキルは固定 store 管理、Nix パス / shebang の置換が要る wrapper・fish 関数、macOS 宣言・生成 fish config は store 生成を維持する。新方式の実装・固定ビルド・生成物確認は完了し、T4 / T5 / T9 と「live link 方式の検証記録」に記録した。過去の配置検証は旧方式の記録と区別する。実機適用は未承認・未実施。

**Hermes の方針訂正（最新のユーザー指示）**: 別 Mac の利用本体は `ryonakae/hermes-agent` fork。公式本流を採用した旧実装を見直し、fork と既存 `hermes-gateway` / `hermes-dashboard` を再利用する。dotfiles の適用入口はサービスの利用状態を保存・管理せず、自動停止・再開もしない。配置上必要な場合の読み取り専用の停止確認とエラーに限定する。Q19 の選択は不要となり、専用 controller による運用管理を撤回する。以下の旧実装・成功ビルドは fork 版の動作証明ではない。`default` から `voice` だけ除外する追加承認を反映し、T7 のビルド・生成物確認を完了した。

**実装承認済み・移行準備中。基盤は完了、設定・拡張の移行が途中。upstream Nix 自体は導入済みだが、nix-darwin / Home Manager の構成は一度も実機へ適用していない。**

- fork 対応・controller 撤去は `6b8021a..1e25f86` を独立レビュー済み。追加の `voice` 除外は `a7ac812..c07b186` を独立レビュー済みで、指摘なし。固定ビルド・生成物確認も完了した。T9 の確認付き switch 入口は `2a307cc..a458e00` を独立レビュー済みで、指摘なし。リモートとの同期状態は再開時に `git status -sb` で確認し、未 push の既存コミットを無関係な変更と混同しない。
- 実装・検証・承認状態の正本はこのプラン。[dig log](../dig/2026-10-03-nix-migration.md) は合意と調査の出典であり、調査当初の「Nix 未導入」等を現在の状態として扱わない。
- **進捗の更新場所は下の Tasks。** `[x]` は記載した成果物とその検証の完了を表し、実機適用の完了ではない。未完了項目には残作業・完了条件を記載する。撤回済みの試作は末尾の履歴に隔離した。

### 再開方針：必要最小限の確認から実機切替へ進む

ユーザーは、準備の調査・文書化・レビューを繰り返すより、早期の実機切替を優先するよう指示した。live link 方式への実装変更は承認済みだが、停止・退避・実機適用の承認ではない。

再開を指示されたら、次の順に進める。

1. **既存状態の確認**: `git status -sb` と直近の差分を確認し、Claude / Pi の他プロセス変更を保持する。Homebrew の暫定保持5件除外は `e439e32`、退避・復旧手順は `3e940ac` にコミット済み。未 push のコミットを再作成しない。
2. **切替を妨げる点だけ確認**: 旧 Nix daemon の復元元・登録状態・復元操作と、候補が実際に変更する system 設定の条件を限定確認する。HOME の既知の衝突対象は既存の調査・[退避手順](../setup.md#初回の退避台帳と停止前の引継ぎ)を使い、直前の変化だけ確認する。秘密・権限・sandbox 制限により人間が必要な操作は、対象と手順をまとめて渡す。新たな全件棚卸しや、解決済みの設計検討は行わない。
3. **候補の一括提示**: live link 方式への変更と5件除外を含む固定ビルド・変更分の生成物確認は完了済み。追加した nix-homebrew の検証結果は下記の記録を確認し、候補に変更がなければ繰り返さない。停止対象、個別の退避先、適用操作、失敗時の戻し方、Pi 等の終了後に人間が実行する手順を一度に提示し、具体的な操作範囲の承認を得る。
4. **退避 → 適用 → 動作確認**: 承認後は T10 の初回 `switch` と PATH・rm 保護・主要 CLI / アプリの確認まで続ける。T5 の拡張の実導入・実行時確認はこの切替作業に組み込み、全機能の事前検証が終わるまで適用を待つ進め方はしない。失敗や未知の衝突が出た場合だけ、その箇所で止めて原因と復旧を判断する。
5. **切替成功後の整理**: 旧ツール・重複管理・旧配布経路の整理と、運用文書の仕上げは受入後に行う。未確認機能は記録して残し、成功扱いにはしない。

成功済みのビルド・生成物確認・レビューは、後続変更や実機の変化で無効になった範囲だけ追加確認する。手順の書き直しや小刻みなレビューを、実退避・適用へ進む前提に増やさない。安全確認・必要なバックアップ・具体的な操作の直前承認は省略しない。この Mac では Hermes を起動しない。

### 再開時に保持する状態・操作境界

- Pi の承認済み変更（fast-mode の `desired: false`、settings の `lastChangelogVersion: 1.0.0`）は T5 の実装へ取り込んだ。動作中の Pi が更新するため、以降も編集・stage の直前に差分を確認し、他プロセスの変更を上書き・巻き戻し・一括 stage しない。
- Claude 設定の初回 `model: "fable"` 追加は `1f56deb` へ取り込み済み。その後の未コミット差分は他プロセスによるものとして保持する。別プロセスが変更し続けるため内容を推測せず、作業に必要な場合だけ確認する。今回のコミット対象には含めない。
- 最後に確認した環境は Safehouse 内・`HERDR_ENV=1`、macOS 26.2 / arm64。新セッションでは環境を再確認する。Nix は `/nix/var/nix/profiles/default/bin/nix` で利用できる。
- ユーザー指示により **回帰テスト・fixture・stub の追加と再実行はしない**。構文、差分、ソース・生成物の確認、Nix 評価・ビルドで検証する。
- この Mac に Hermes の既存環境はない。ここで停止・データ移行・初期化・自動起動をしない。別 Mac の稼働環境の移行は、その Mac で承認・停止・バックアップを確認する。
- 実機への適用、利用中のプロセスの停止・再起動、ログイン shell の変更、権限・秘密の操作、旧導入物の削除は未実施。必要な操作を具体化して直前承認を得る。切替承認は取得していない。今回の commit / push 承認は、実機適用やサービス操作の承認を含まない。

## Tasks

### T1. 対象の棚卸し — 完了（共通環境に限定）

- [x] Homebrew の導入 metadata と App Store 一覧を取得。installed-on-request は44 formula、cask は59件、App Store は22件。移行先は下の対応表に記録。
- [x] Homebrew 外の npm / uv / mise / 主要手動配置先を照合。ユーザー承認により、インストール済み・グローバル配置・Nix 未宣言という理由だけで dotfiles の管理漏れと扱わない。共通環境は合意済みの対象だけを管理し、他プロジェクトのツール・runtime は各プロジェクトの設定と mise 等に任せる。未宣言分の全件分類・追加調査を切替条件にせず、棚卸しはここで終了する。既存実体・プロジェクト設定は変更・削除しない。合意済みの Pi / Herdr 等の拡張は T5 の範囲で扱い、未知のアプリ拡張まで調査を広げない。
  - 調査済み metadata は `/tmp/dotfiles-brew-inventory.json`。一時ファイルの存続を前提にせず、なければ非秘密の package metadata だけ再取得する。
  - Git 外の実 `config.fish` は秘密を含むため読まない。example と実設定の差分は T9 で人間に確認してもらう。example の PGDATA を実 DB の保存先と仮定しない。

### T2. Nix 基盤・固定ビルド・更新入口 — 完了

- [x] 公式 upstream Nix 2.34.0 の checksum 固定済み bootstrap を実装し、人間が sandbox 外で初回導入。daemon 接続を確認。`f358e81`。
- [x] `flake.nix` / `flake.lock`、nix-darwin + Home Manager、非秘密 host 入力を実装。`4f10ae9`。Darwin stateVersion は6、HM は `26.05`。
- [x] `scripts/dotfiles.{sh,py}` の `build` と `update [all|input]` を実装。通常 build は公開依存の lock を検査し、host leaf 以外の変更を拒否して同じ snapshot を check / build する。現在の構成でビルド成功。
- `switch` の入口は T9 で実装済み。切替準備と実機への適用は未完了で、この項目の完了に含めない。

### T3. パッケージと更新単位 — 実装済み対象の宣言・ビルド完了、棚卸しは T1

- [x] 一般 CLI・共通ランタイムと Homebrew 補完を宣言。`890ef27`。現在の正本は `config/nix/home/packages.nix` と `config/nix/darwin/homebrew.nix`。
- [x] gomi / dotenvx / Agent Safehouse、Claude Code / Codex / Pi / OpenCode / Herdr / Antigravity CLI を共通 nixpkgs の標準定義へ統一。`44688a4`、`23a7c38`。独自 package 定義・専用 updater は削除済み。
- [x] 当初の55 cask・22 App Store アプリ・補完 formula 7件を宣言し、生成物を確認。その後 Unity CLI を追加し、現在は56 cask。ユーザー承認により暫定保持の `icu4c@76` / `libpq` / `oniguruma` / `pcre2` / `postgresql@17` を直接宣言から外し、formula は mosh / Zerdr の2件とした。依存はパッケージ管理に任せ、必要な直接導入は移行時に手動で行う。1Password CLI / gcloud は Homebrew cask 管理を維持する。Homebrew の自動更新・upgrade・cleanup は無効。実機の削除・DB 操作・サービス停止は行わない。**Homebrew bundle は未実行。5件除外後の構文・単体評価は実施し、全体ビルドは次回へまとめる。**
- [x] **Hermes パッケージの採用・固定ビルド** — 公式 Flake の `packages.aarch64-darwin.default` のみを `home.packages` へ追加し、input と root lock を接続した。サービスモジュール・独自 package 定義は追加せず、独自依存を未検証で共通 nixpkgs へ follows しない。既存4 input の内容保持、構文、固定 snapshot の評価・ビルド、生成 CLI の参照先を確認。Safehouse の公開ソース参照拒否後、ユーザー承認の Herdr 別ペインで検証した。review base は `f71f25d`。サービス接続・実起動は T6・T7 に残る。
- [x] **agent-device のグローバル管理を廃止** — ユーザー指示で mise の `npm:agent-device` 宣言を削除し、自作 `use-agent-device` スキルと `.ad` 実行例を `npx --yes agent-device` へ変更。独自の版固定・更新制限は設けない。Node は npx とは別に要件を満たすものを選ぶ。外部の公式スキルは変更せず、そこでの CLI 表記も npx に読み替える。npm cache・状態は残る。実機の既存導入物は未アンインストール。
- [x] **Shepherd を復元対象から除外** — ユーザー指示で本体・専用 Node runtime の補完を取りやめ、Herdr plugin の復元コマンドを削除。本体の既存 wrapper、稼働 daemon、実 registry / checkout / state は未変更。無効化済みの team スキルと調査履歴は配布対象外のまま保持する。
- [x] **Unity CLI の Homebrew 宣言・ビルド** — ユーザー承認により `homebrew.nix` の cask に `unity-cli` を追加。更新は Homebrew に任せ、公式 installer・`unity self-update`・独自 Nix package は併用しない。Editor / modules と認証・Hub の状態は本体管理から分離する。旧 `~/.unity/bin/unity` と fish の PATH 設定の整理は T9・T10 に残し、実機は変更しない。`--zap` が Hub の状態も削除する注意を `docs/setup.md` に記載。`nix-instantiate --parse` と当該モジュール単体の strict JSON 評価が成功し、cask が56件、`unity-cli` が1件、Hub と自動更新・upgrade・cleanup 無効の維持を確認した。`git diff --check` も成功。承認済みの別ペインで構成全体の固定 build が成功し、生成 Brewfile に `unity-cli` と `unity-hub` が含まれることを確認した。宣言・ビルドは完了、実導入と旧配置の整理は T9・T10 に残る。`18d72cb..4d99014` を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。レビューはリポジトリ内のソースに限定し、公式配布情報・実機 fish の調査と宣言評価は親側の確認結果と区別する。
- [x] **Zerdr は Homebrew 版を採用** — ユーザー承認により既存の `ryonakae/tap/zerdr` 宣言を維持。復元手順で `brew --prefix` から本体のパスを明示し、開発版を拾わないようにした。nix-darwin が導入対象を宣言し、実体・更新は Homebrew が管理する。現 Herdr manifest の開発 checkout 参照は未変更で、切替時の再登録は T5・T10 に残す。
- 補完案の根拠・公式出典は [dig log](../dig/2026-10-03-nix-migration.md) 冒頭。調査済みであり、同じ候補調査を最初からやり直す必要はない。

### T4. config ファイルの配置 — live link の生成物確認済み

先頭項目が新方式の検証。それ以降の `[x]` は旧配置方式の実装・検証履歴として残す。

- [x] 追跡済み設定・静的スクリプトを `config.lib.file.mkOutOfStoreSymlink` で `homeDirectory` 由来の `~/dotfiles/config/` へ接続する。置換が不要な fish 関数も live link とし、shell-init / interactive-init の非 Nix 本文は live source する。Nix executable パス・shebang の置換が必要な wrapper / fish 関数、macOS 宣言・生成 fish config は store 生成を維持する。変更した配置のリンク先と、store 生成を残す参照を確認する。

- [x] `home/fish.nix`: fish 関数・補完・SSH socket 補完、bobthefish / fzf、mise / zoxide 連携。設定本文は `config/.config/fish/{shell-init,interactive-init}.fish` と `config/.config/mise/config.base.toml` に分離。`046d980`、`23257af`。
- [x] `home/protection.nix`: rm / gomi / Safehouse 共通 wrapper・profile を既存ファイルから配置。rm は shebang のみ Nix Python に固定。PATH 変更後も `.local/bin` を先頭へ戻す処理を配置。
- [x] `home/files.nix`: Ghostty / Worktrunk / Husky / Yazi、共通 AGENTS の各エージェントへの参照、共通・CLI 別通知スクリプトを配置。`d6159ed`。Yazi の git / smart-enter / full-border は `pkgs.yaziPlugins`、smart-leave は既存 Lua。
- [x] Vim は「ほぼ使わないため管理しやすさ優先」というユーザー承認に従い、外部プラグインなしの最小構成へ変更。既存の標準 `pkgs.vim` と `home/files.nix` による `.vimrc` の配置だけを使用する。NeoBundle / NeoComplete / Copilot 等の専用設定、試作の `home/vim.nix` と限定 unfree 許可を除去。基本の表示・検索・インデント設定を残した。review base は `7785d62`。現行 HOME も `.vimrc` の正本へリンクしているため、次回起動から最小設定になる。旧 `~/.vim/bundle` の実体は未削除。
- [x] Zellij / ZAM は未使用のため削除するユーザー承認を取得。Nix・Brewfile example の導入宣言、Zellij config / dev layout、fish の `zl` 関数を削除。生成環境に本体・設定・関数が含まれないことを確認。Ghostty の Option 設定値は維持し、コメントだけ汎用化。review base は `f99a92c`。実機の本体・保存セッション・ZAM の私的プロジェクトは削除せず、汎用 `use-zellij` スキルと無効化済みの Pi 命名設定も残す。
- [x] Zed / Claude / OpenCode / pi-auto-name の設定を `home/files.nix` から既存ファイルのまま配置。旧方式の通常の `home.file` / `xdg.configFile` を使用し、生成された4ファイルと正本の一致を確認。現行方針ではこれらも live link とし、アプリからリンク先への書き込みを Git 差分として扱う。新方式の確認は上の完了項目。Claude の Herdr hook・statusline 依存は T5 で接続済み。
- [x] 旧方式では Pi の `settings.json` に標準 `mkImpureConfigMerger` を追加した。これは撤回済みで、新方式の実装・検証は T5、実際の適用は T9・T10。
- [x] Herdr の `config.toml`、plugin 設定2ファイル、補助スクリプト2ファイルを個別に接続。生成された5ファイルとの一致と shell script の実行権限を確認。plugin 本体・tests・session・log は含めない。plugin 本体は T5、サーバーへの設定反映は T9・T10 と分ける。
- 完了条件: T1 で確認した config ファイルすべてに配置・例外対応・不要・手動のいずれかの扱いが付き、必要な生成物を確認できる。具体的な支障があるファイルの例外対応と、拡張の完了判定は T5。
- 移行中の注意: `fish_variables` は追跡から除外済みだが実ファイルを保持。旧 mise `config.toml` は現行環境用として未変更。新しい `config.base.toml` は適用後に HOME 側の `mise/config.toml` となる。旧ファイルの整理は T10・T11。

### T5. 配布の例外対応・拡張・スキル — 進行中

版固定の実装済み部分は維持し、設定・自作スキルの配置は live link 方針へ変更する。残る新規取得・実導入・実行時機能の確認は T10 の切替作業で行い、T5 全項目の事前完了を初回適用の条件にしない。未確認事項は下のチェックを残して追跡する。

- [x] 旧 immutable / merger 方式の調査として Zed / Pi の標準 HM モジュールを確認。Zed は `mutableUserSettings` がある一方、Pi は設定を store にリンクする方式。汎用 `lib.hm.generators.mkImpureConfigMerger` は experimental と明記されている。
- [x] 旧方式では Pi 設定3件の書き込み経路を確認し、標準 `lib.hm.generators.mkImpureConfigMerger` と `checkPiConfigPaths` を接続した。review base は `c7855a0`。この merger・通常ファイル化方式は撤回済みであり、旧検証を新方式の成功根拠にしない。
- [x] Pi の `settings.json`、`extensions/pi-footer.json`、`extensions/pi-gpt-fast-mode/config.json` を通常の live link に変更し、`mkImpureConfigMerger` / `checkPiConfigPaths` / `piMutableSettings` を削除する。設定3件の標準 HM 配置と旧 merger / checker 不在を確認する。初回の旧リンク・非秘密内容の保全は T9。アプリのリンク先への書き込みは Git 差分となり、日常の内容変更で Pi 停止・Nix 再適用・旧正本への手動取り込みは不要。アプリがリンクを置換した場合の衝突は標準検査で保持する。
- [x] Claude の `herdr-agent-state.sh` を `pkgs.herdr.src` の公式 asset から executable として配置。本体と同じ nixpkgs lock に従い、独自生成・転載・版別 override は作らない。Herdr の installer は hook / settings に書き込むので、Nix 管理へ切替後の Claude integration には併用しない。
- [x] statusline は標準 npm 経路のまま、現行キャッシュと一致する `ccstatusline@2.2.30` に固定。固定 nixpkgs には未収録、公開 metadata は runtime dependency なし。npm tarball の integrity と現行4ファイルの byte 一致を確認。初回 npx 取得は runtime に残り、Nix build / activation ではインストールしない。Claude の別プロセス変更は保持し、この command 1行だけを index へ取り込む。
- [x] `home/skills.nix` で自作12スキルを共通・Claude 向けの個別ディレクトリとして配置。Claude 固有の同名優先とドット始まり除外を維持。親ディレクトリ全体や `synced` を置き換えない。Antigravity は既存どおり共通置き場への参照リンクで、旧方式では自作正本も store に配置した。
- [x] 自作スキルの個別配置を追跡済み正本への live link へ変更し、Claude 固有の同名優先・非配布ディレクトリの除外・Antigravity の共通参照を確認する。外部スキルの revision / hash 固定と store 配置は維持する。
- [x] `home/external-skills.nix` で既存の外部13スキル（12 repo）を commit と展開後 hash で固定し、標準 `fetchFromGitHub` と個別 `home.file` で接続。公開 HEAD と一致する9件に加え、herdr / tdd / worktrunk / readme-creator は現行内容に一致する過去 commit を特定した。内容の更新や別スキルへの置換はしない。skill-creator の `.pyc` 2件だけは生成キャッシュとして復元しない。
- [x] **cua-driver スキルの復元宣言・ビルド** — ユーザー承認により、`home/external-skills.nix` に公式 `trycua/cua` のスキルを追加。取得対象は公開 commit `3a784c5c32fc834f387f47f4835dd869ef505eee` の `libs/cua-driver/rust/Skills/cua-driver`。既存の共通・Claude 向け個別配置へ接続し、固定ビルドと11ファイル×2配置の一致を確認。外部14スキル（13 repo）、自作を含め共通・Claude 各26スキルになった。本体の導入・GUI 操作・実 HOME への適用は含めない。旧 `config/skills-lock.json` の computedHash は revision / Nix hash として使わず、旧 lock の廃止は T11 で行う。
- [x] Pi の `APPEND_SYSTEM.md` / `agent-tool-description.md` / `subagents.json` / agent 定義3件 / 通知拡張を通常配置。`subagents.json` は上流がユーザー側を読み取り、UI の保存はプロジェクト側に行うことを確認。npm 7件は既存導入版、pi-subagents は導入済み commit `be898c753e9eb32cf1315f63b1c1f5ef0cf6f782` に native settings で固定し、公開取得可能性を確認。
- [ ] Pi 外部拡張の新規取得・実行時機能の復元を確認する。標準 Pi は npm / Git の可変インストール先を使用し、activation からネットワーク取得や自己更新は実行しない。トップレベルの版固定は推移依存全体の固定ではない。現行の導入実体は Nix Pi 0.99.1 の loader で10 entry point をエラー・警告なしに読み込めたが、新規依存解決・認証付き機能は未検証。
- [x] Herdr の Git plugin は標準 `install --ref <commit>` の復元手順を `docs/setup.md` に固定。当初の3件から、ユーザー指示で Shepherd を除いた2件を復元対象とする。現 metadata / HEAD / clean 状態を調べ、親側でも公開 commit アーカイブの manifest と主要ファイル7件を照合。再 install で `--ref` を省略すると HEAD へ移ること、有効化を伴うこと、build / activation から実行しないことを明記した。
- [ ] Git plugin の実機導入と機能確認。Agent Context は同一 release から binary / checksum を取得し、source commit 固定は binary の完全な immutable hash 固定ではない。Shepherd の復元は対象外。
- [ ] 承認済みの Homebrew 版 Zerdr の標準 `setup install` で manifest と登録を復元する。現開発 executable の絶対パスは配布しない。setup は Zed tasks にも書くが、現Nix配置は Zed settings のみで tasks は管理していない。
- Agent Context / Worktrunk の tracked config は個別の live link とする。旧調査では本番実装の書き込み経路がないことを確認したが、読み取り専用配置を現行要件にはしない。registry、checkout、state は可変で残す。plugin 実体・session・log は Git / store へ取り込まない。
- 完了条件: 認証・状態を store に入れず、必要な設定と拡張を復元できる。live link の内容変更とリンク置換時の衝突、store 固定の対象を区別して説明できる。

### T6. 保護・起動・PATH の統合 — 宣言・生成物の確認済み

共通ファイルの配置は T4 で完了。残るのは起動経路全体の接続確認。今回の review base は `74bd8d6`。

`home/fish.nix` で管理 CLI / Safehouse / Hermes の実行先を Nix パスへ接続し、`home/protection.nix` で dotenvx を固定。プロジェクト用 PATH 全体は置換しない。サービス wrapper は旧 mise / venv 前提を外し、dashboard の TMPDIR 補正を追加した。`home/hermes.nix` でサービス側も Nix の実行先へ接続し、固定ビルドと生成物の構文・参照確認を通過。実機 PATH の衝突・初回切替は T9・T10 に残る。

- [x] `run-with-agent-env.sh`、`__safehouse_args.fish`、対話 CLI 関数の実行先を確認し、不要な mise / Homebrew 固定パスを解消する。引数・終了・signal の透過、秘密の直接アクセス保護、復号失敗時の停止を維持する。
- [x] T7 のサービス wrapper と、HOME 許可・profile 順・環境継承・TMPDIR 補正を照合する。サービスが対話用 feature を省く差分は維持する。
- 完了条件: shell / 非対話 / launchd の生成された実行経路で、Nix 本体の利用と rm 保護の優先順位を説明できる。実秘密の読み取りや保護ポリシーの緩和で検証を通さない。

### T7. Hermes サービス・Hindsight — 構成検証・独立レビュー済み、実機未適用

実装 commit は `1e25f86`、今回の review base は `6b8021a`。独立した read-only reviewer がこの範囲を確認し、blocking/high・decision required・medium/low の指摘なし。これはソースレビューで、全ビルドや実サービスの検証とは区別する。旧 `945d699` の専用 controller と本流採用は撤回対象で、旧ビルド・レビュー記録は下の履歴に残す。最新の停止仕様は Implementation Decisions 4 と dig log の決定事項を正本とする。

- [x] `flake.nix` / `flake.lock`: `github:ryonakae/hermes-agent/ryonakae` の `2a485666e6754ec8e8a0ba9b383ea1eb6e518f14`（`sha256-35HGnPLz0FOWmLA1FtwGD8i1H1YjUUNc3ru+mKR+mMw=`）へ変更済み。共通 nixpkgs / nix-darwin / Home Manager / host node は変更なし。fork 同梱の aarch64-darwin パッケージを使い、独自 package は作らない。標準 `override` で `default` の `voice` だけ除外し、共通の `_module.args.hermes` を導入一覧・fish・サービス wrapper で使用する。固定 build は成功。
- [x] `hermes-gateway.fish` / `hermes-dashboard.fish` のソース接続・構文・独立レビュー: `74bd8d6` の launchd + fork 標準 CLI の経路へ戻し、Nix 実行先とエラー伝播を接続した。restart は stop が成功した場合だけ start。自己更新は Nix の更新・ビルドを案内する。
- [x] `home/hermes.nix` の配置分離・構文・評価・独立レビュー: 599行の `hermes-service.py` と専用 Python / psutil 環境を撤去し、`check-stopped.sh` の読み取り専用確認へ置換した。GUI session の launchd 登録・判別可能な Hermes プロセスを確認し、未停止・取得失敗・未知の形式はエラー。PID・子プロセスの追跡、状態保存、停止・再開はしない。
- [x] `voice` 除外版の固定ビルド・生成物を確認した。fish / shell / Nix の構文、lock 不変、導入本体・対話 CLI・管理関数・サービス wrapper の参照先一致、plist flags、activation の順序、controller 不在、SOUL / Compose の正本一致を確認。venv の配布 metadata で Hindsight・Discord・Telegram・Slack・Edge TTS・ElevenLabs・dashboard 依存の保持と、ローカル音声依存の不在を確認。
- [x] `a7ac812..c07b186` の `voice` 除外変更を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。レビュー側はソースのみを確認し、親側が実行したビルド・生成物検査とは区別する。
- [x] Hindsight の Compose と SOUL の配置、image digest は変更なし。Docker の volume・認証・起動は配置と分離する。

公開 fork の gateway stop / dashboard --stop には timeout 後の強制終了がある。ユーザーから、その挙動も fork 標準に任せることへの `ok` を取得済み。旧 Q18 の自動強制終了禁止は置換された。独自の運用 controller や fork への追加機能で停止を再実装しない。実サービスでの停止成功・DB バックアップの整合性を未検証のまま保証しない。

plist は既知の生成物だけユーザー所有の実ファイルへ配置し、標準 HM launchd activation には登録しない。Disabled / RunAtLoad / KeepAlive は既存の配置分離構成を維持し、明示的な start / stop が enable / disable を行う。未知の既存 plist の退避と別 Mac の実機移行は未実施。

回帰テスト・fixture・stub の追加や再実行、実サービス操作・実機適用は行っていない。先行2件の fork build（旧 controller 版と `voice` 含有版）はともに exit 0。ログは `/tmp/dotfiles-hermes-fork.71SzyJwq/{build,final-build}.log` だが、現在の構成の受入根拠とは区別する。

`voice` 除外版のログ・生成物検査は `/tmp/dotfiles-hermes-no-voice.ayEb74RJ/` の `preflight.log`、`final-build.log`、`inspect.py`、`artifacts.json` に記録。実構成の dry-run は Hermes 環境・ラッパー・Home Manager 等の24 derivation で、PyTorch の構築を含まなかった。`dotfiles build` は1分以内に exit 0、root lock SHA256 は `6d7c28a5e15bbc7037913dd0b1e0782baf12d39e49d936ddd9b13fb52181988d` のまま。これは既存の依存成果物を再利用した結果であり、別 Mac の初回所要時間は未確認。パッケージ単体の依存グラフにも PyTorch / CTranslate2 は含まれない。使用した作業用ペイン `w3W:pA` / `w3W:pB` は終了後に閉じた。push と Plan archive は未実施。

35行の生成 checker `/nix/store/npjybps6vhaxa7gidwsw5xfw0qdr373n-hermes-check-stopped` は正本との本文一致・指定 Nix Bash の構文検査に成功。承認済み別ペインで読み取り専用実行し、Hermes 未使用のこの Mac の GUI セッションでは exit 0（`preflight.exit`）を確認。Hermes 本体・activation は実行していない。検査用 `w3W:pC` は終了・閉鎖済み。Safehouse 内での build 診断用 process 一覧は `Operation not permitted` のため取得できず、同環境では再試行せず、許可された別ペインで build に関する process metadata だけを確認した。

### T8. macOS 設定・手動復元 — 宣言・文書化済み、実適用は T10

- [x] Dock / Finder / キーボード / トラックパッド / スクリーンショットの非秘密30キーを個別に読み、値のある18キーを `darwin/preferences.nix` の標準オプション16項目へ宣言。トラックパッド2項目は標準モジュールが内蔵/Bluetooth双方へ書く。未設定12キーには値を新設せず、preferences 全量は取得していない。具体的な復旧用控えは下記。
- [x] Xcode / SDK、Apple ID、Touch ID、TCC、署名、VPN、秘密・Keychain、Docker、未宣言の UI 設定の手動復元を `docs/setup.md` に整理した。
- 完了条件: 宣言対象と手動対象が明確で、変更する OS キーの旧値・未設定状態と戻し方を T9 へ渡せる。

### T9. 適用入口・衝突確認・復旧準備 — 入口実装済み、切替準備は未完了

固定 nix-darwin の入口を調査済み。標準 `switch` に検査済み source / host snapshot を渡し、標準の世代登録を維持できる。profile 登録は activation より前で、適用は非トランザクショナル。`activate` 単独は世代を登録しない。標準 `check` / dry-run の activation を読み取り専用検査として実行しない。最新指示により、入口は Hermes の起動状態を保存・管理せず、必要な停止確認とエラーに限定する。Q19 の選択は撤回。T7 完了後、`2a307cc` を review base として適用入口を実装した。対象ユーザーでの対話実行に限定し、Safehouse / root / 非対話を拒否する。既存の Hermes 停止チェック以外にプロセス管理を追加せず、ファイル衝突は標準 activation 内で検査する。全変更前の衝突拒否や自動退避・復旧は保証しない。実適用は未実施。独立した read-only reviewer が `2a307cc..a458e00` を確認し、blocking/high・decision required・medium/low の指摘なし。レビューはリポジトリ内のソースに限定し、外部の固定 Nix 実装や生成物は親側の調査・検証と区別する。

- [x] **ここまでの部分構成**を通常 build で検証。旧方式の成功成果物は下記「検証記録」。live link 方式の受入ビルドとは区別する。
- [x] `scripts/dotfiles.py` に確認付き `switch` を追加。build と同じ lock 検査・snapshot・check/build を使用し、候補と旧 profile を表示してから明示入力を求める。既存 Hermes check に失敗すれば sudo / profile 更新へ進まない。標準 `darwin-rebuild switch` へ同じ source / host を渡し、世代登録を維持する。ネイティブのファイル衝突検査でエラーになった場合、先行した変更は自動で戻さない。
- [ ] 配置先のファイル種別・リンク先・所有権を確認し、旧リンク・実ファイル・Fisher / Yazi plugin・shell 初期化・plist の退避先と復旧先を決める。未知のファイルを force overwrite しない。
  - [x] 旧方式の HOME / system の退避ルート、対象別の保存内容、Pi 設定の通常ファイル化、失敗段階別の復旧順序、中断後の引継ぎを `docs/setup.md` に記載した。今回の方針変更で Pi の通常ファイル化は撤回し、文書は旧リンクと必要な非秘密内容を保全して標準 HM 配置へ引き渡す手順へ更新した。新方式の生成物との照合は下の完了項目。review base は `5113cfdd1b0be0c4a0b1d0a4175e4eca7fbd64e1`。ユーザーは既存の Homebrew 関連文書差分を保持した追記を承認した。実機の退避・復旧を検証済みとは扱わない。
  - [ ] 人間が旧 daemon plist の実行先・launchd 登録状態と復元操作、build users / PAM / SSH / TCC の変更条件を確認し、対象ごとの私有台帳とバックアップを準備する。実 `config.fish` はエージェントから再取得せず、人間が保全する。
  - 旧 immutable / merger 方式の生成物の HOME 配置135パスを内容を読まずに棚卸しした。旧リンク108、実ディレクトリ16（外部スキル13・Yazi plugin 3）、実ファイル1（Herdr hook）、未作成9、取得不能1。`dd9b0ba` からの再開時も種別・リンク先は同じで、確認できた既存対象はすべて本人所有、HOME より下の親経路に symlink はなかった。実 `config.fish` は前回 lstat が `Operation not permitted` だったため再試行しない。記録は `/tmp/dotfiles-collision-inventory-resumed.json`。実退避や内容比較は未実施。
  - Zellij 削除後、`~/.config/fish/functions/zl.fish` と `~/.config/zellij/config.kdl` に削除済み正本へのリンクを確認。ホーム側は未変更。切替時にこの既知の旧リンクの整理を確認する。Brewfile の実ファイル、インストール済み本体、保存セッション・履歴は今回変更していない。
- [x] live link 方針に合わせた Pi 設定3パス、自作・外部スキル、Antigravity 参照の初回退避・復旧手順を最新生成物と照合した。実 HOME の直前確認と退避・復旧は未実施。旧リンクと必要な非秘密内容を保全して標準 HM 配置へ引き渡し、0600通常ファイル化・merge・旧正本への手動取り込みは行わない。外部スキルの実ディレクトリは個別退避し、未管理スキル・`synced` は保持する。初回の停止はリンク退避時の書き込み競合回避に限定し、日常の内容編集で全アプリを止めない。復旧はリンクと本文を分け、本文は Git で戻す。cua-driver 両配置が未作成であることも適用直前に再確認する。
  - 旧方式で確認した Pi 設定3ファイルはすべてリポジトリへの旧リンク、Hermes plist 2件は未作成。Antigravity CLI の参照は `~/.gemini/antigravity-cli/skills` → `~/.agents/skills`。実停止・個別退避・新方式の適用は未実施。
- [x] 実 `config.fish` の非秘密差分をユーザーに確認。追加で引き継ぐ設定はないとの回答。以前記載していた `HOMEBREW_GITHUB_API_TOKEN` / `CONTEXT7_API_KEY` / `TYPESAFE_API_KEY` は dotenvx 管理へ移行済み。実ファイル・秘密の値は取得していない。
- [ ] 旧 universal PATH 等の shell 状態を整理する。`18d72cb` からの再開時に PATH 関連4キーだけを選別して確認し、保存済み `PATH` と `fish_user_paths` を検出した。旧 mise shims・存在しない anyenv のパス、PostgreSQL・Antigravity 等の追加パスが残る。値の変更・実 shell 起動による優先順位確認は未実施。詳細は下記「旧 fish 初期化・PATH の追加確認」。example の PGDATA を実 DB 保存先と仮定しない。
- [ ] 実際の OS 変更範囲・初回復旧に必要な保全を確認する。最新構成の固定ビルド・変更分の生成物確認は完了済み。T1〜T8 の全項目完了待ちにはせず、適用前に必要な安全確認と、T10 で行う実行時確認を分ける。
- 検証: Python の in-memory compile、Bash 構文、CLI help、固定 build が成功。`switch_target` の対象ユーザー / HOME 照合と生成済み checker の参照を読み取り専用で確認。ログは `/tmp/dotfiles-switch-preparation.Y3SZjkuN/`。build は既存の Darwin 成果物 `920lv1d788i2510q217sgynxq8kgvzfp` を再利用し、root lock は不変。`switch` 本体・sudo・activation・回帰テスト・fixture / stub は実行していない。
- 完了条件: 切替時に変更するものと戻し方をユーザーへ具体的に提示できる。`switch` の実行は T10 の承認後。

### T10. 集中切替・重複管理の解消 — 未着手・直前承認が必要

- [ ] 必要な停止・退避・適用と復旧の操作範囲を一度に提示し、承認後に下記の手順で初回 `switch` まで進める。エージェント自身が中断される場合は、人間が実行する手順と再開方法を停止前に渡す。
- [ ] 適用に続けて実機で PATH・rm 保護・主要 CLI / アプリを確認し、T5 の Pi 拡張・Herdr plugin・Homebrew 版 Zerdr の復元と利用確認を行う。問題があれば該当する復旧手順を使い、未確認機能は記録する。提示済みの範囲を超える停止・再起動・ログアウト等が必要になった場合は改めて直前確認する。
- [ ] 受入後、対象を明示して承認済みの旧導入物・共通 mise 管理・旧配布を整理する。バックアップ・Nix 世代の自動削除、破壊的な Homebrew cleanup はしない。
- 完了条件: 日常の実行・更新経路が新構成へ移り、補完ツール以外の長期二重管理が残らない。この Mac の Hermes は起動しない。

### T11. 運用文書・旧配布の終了 — 進行中

- [x] bootstrap、build / update、標準管理・native 設定ファイルの方針を文書化。`README.md`、`docs/setup.md`、`AGENTS.md` と本プランを更新済み。
- [ ] T9 では実行に必要な退避・適用・復旧手順だけを用意し、T10 の受入後に実施結果を反映して運用文書を仕上げる。同じ段階で `create-symlink.sh` / `create-skills-symlink.sh` / `copy.sh` 等の旧配布経路と呼び出し元を整理する。文書の仕上げを初回適用の前提にしない。
- [ ] `Brewfile.example` / `skills-lock.json` 等の旧正本の役割を終了し、移行後の正本を一つにする。秘密の実ファイル・既存 backup は削除対象に含めない。
- 完了条件: 新規 Mac の復元と日常運用が文書から辿れ、実装と説明が一致する。全体完了時にのみ本プランを archive する。

## Requirements

- 現在と今後の Apple Silicon Mac の、合意済みの共通ツール・アプリ・ユーザー設定・macOS 設定を再構築できるようにする。実機の導入状況は確認材料とするが、インストール済みの全製品を管理対象にはしない。他プロジェクト用のツール・runtime は各プロジェクトの設定と mise 等に任せ、グローバル配置や Nix 未宣言だけを根拠に dotfiles の管理漏れと扱わない。未宣言分の全件分類・追加調査は切替条件にしない。既存実体を無断で削除せず、依存ライブラリと直接利用ツール、名称変更・別系列を区別する。
- upstream Nix の multi-user daemon、Flakes、nix-darwin、統合した Home Manager を構成の中心にする。ツールは原則 Nix、macOS 対応・保守負担に問題があるものは Homebrew / App Store 等で補完し、導入一覧の正本を Nix に集約する。
- 共通 nixpkgs は rolling 系列を使い、通常の適用は flake.lock で固定済みの標準パッケージから行う。AI ツールも原則として nixpkgs 単位でまとめて更新し、個別・AI グループ更新は必須にしない。外部拡張・プラグイン・スキルの固定にも既存の標準管理を優先する。一般 GUI アプリの自動更新は許容し、flake.lock による同一版復元とは区別する。
- 追跡済み設定・自作スキル・静的スクリプトは元の形式で管理し、Home Manager の `config.lib.file.mkOutOfStoreSymlink` で `~/dotfiles/config/` への live link を配置する。実パスは `homeDirectory` から作り、checkout の固定位置は既存 README に合わせる。通常の内容編集・アプリからのリンク先への書き込みは Git 差分となり、Nix 再適用は不要。Nix はリンクの配置を管理し、本文は Git で復元する。Nix 世代の rollback で本文が戻るとは扱わない。Nix 本体・外部 plugin・外部スキルは固定 store 管理、Nix パス / shebang の置換が必要な wrapper・fish 関数、macOS 宣言・生成 fish config は store 生成に残す。
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
- Homebrew は nix-darwin の homebrew 定義を正本にする。通常適用では `onActivation.autoUpdate = false`、`upgrade = false`、`cleanup = "none"`。導入一覧にないものの自動 uninstall / zap はしない。Homebrew 本体は `nix-homebrew` で導入・版固定し、新規 Mac で別途公式 bootstrap は行わない。既存環境は `autoMigrate` で引き継ぐ。tap は可変管理を維持し、Intel 用 Homebrew は追加しない。Homebrew 配下のアプリの版固定とは区別する。
- 共通ランタイムは既存の必要な major / minor とツール要件を確認して選ぶ。単に現行 mise の古い patch と一致させるための独自ビルドは増やさない。プロジェクト指定を尊重し、特定ツール専用ランタイムはそのパッケージへ閉じる。
- `scripts/dotfiles.sh` に小さな操作入口を用意する。`build` は固定構成の事前ビルド、`switch` は固定構成の適用、`update [all|input]` は公開 input の lock 更新のみ。`update nixpkgs` で標準パッケージ群をまとめて更新する。存在しない対象はエラーにし、`update ai` やツール名での単独更新は提供しない。
- 全体更新を一連で実行する手順は、明示的な update → build → 確認付き switch と、Homebrew 側の明示的更新をまとめる。通常 switch に更新を隠さない。Nix 管理した本体の自己更新や既存 installer は使わず、Herdr server 等の再起動は適用と区別する。

### 3. 設定・拡張・秘密

- 本体はパッケージ管理、設定・スクリプトの配布は Home Manager と役割を分ける。通常の設定本文は元の形式の追跡済みファイルを正本にし、Home Manager は標準の `mkOutOfStoreSymlink` で live link を配置する。既存モジュールはパッケージ・プラグインの導入、shell 連携等に利用する。Nix profile や interpreter の store パス、nix-darwin の OS 宣言は Nix に残す。設定を配布するために本体パッケージを独自化しない。共通 AGENTS の正本を増やさず、各エージェントの参照関係を維持する。
- **基本は追跡済み config ファイルへの live link を Home Manager の標準機能で管理する。** Zed / Pi / Claude 等もこの原則で進める。Pi 設定3件も通常のリンクとし、`mkImpureConfigMerger` / `checkPiConfigPaths` / `piMutableSettings` は削除する。アプリごとの全設定分類・分割や独自 merge 基盤は作らない。
- 認証・履歴・session・DB・cache、`fish_variables` 等の状態は配布対象に入れない。初回は旧リンクと必要な非秘密内容を保全し、標準 HM 配置へ引き渡す。0600通常ファイル化・merge・旧正本への手動取り込みは不要。リンク退避時は競合回避のため書き込み元を止めるが、日常の内容変更で全アプリ停止は求めない。アプリがリンクを置換した場合の衝突を保持し、未知の実体・元ファイル・実秘密を強制上書きしない。
- 外部スキルは取得元 revision と内容 hash を固定して `~/.agents/skills/` へ配置し、現行の利用先から参照する。Claude 固有スキルの同名優先、`.disabled` 等の非配布、Antigravity の共通参照を保ち、ディレクトリ全体の置換で他のスキルを隠さない。`skills-lock.json` の computedHash だけを再現用 lock と扱わず、最新版を取り直す experimental_install を新規 Mac の復元手順から外す。自作スキルは追跡済み正本への live link とし、外部スキルの固定 store 配置や Hermes の自己更新データと区別する。
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

実機 `brew info --json=v2 --installed` の metadata を確認。installed-on-request は44 formula、cask は59件。標準パッケージと Homebrew 宣言のビルドは完了しているが、導入対象の照合と実適用は未完了。App Store は `mas list` で22件を照合済み。Homebrew 外の npm / uv / mise / 主要手動配置先の metadata 照合結果は下記に記録。未宣言分を追加の切替条件にはしない。合意済みの拡張だけ T5 で扱う。

| 現在の対象（Homebrew） | 移行先 / 固定単位 | 残る確認・例外 |
|---|---|---|
| actionlint, age, awscli, cocoapods, fastlane, fd, ffmpeg, fish, fzf, gh, git, git-lfs, gomi, imagemagick, jq, mas, mkcert, terminal-notifier, tmux, tree, uv, vim, worktrunk, yazi, zoxide | 共通 nixpkgs | Darwin 対応と実際のコマンド互換性 |
| agent-browser, ctx7, keifu, usage | 共通 nixpkgs に実装済み | 実適用・利用確認はこれから |
| zerdr | Homebrew の `ryonakae/tap/zerdr` に宣言済み | アプリ提供 plugin との整合は T5 |
| dotenvx, agent-safehouse | 共通 nixpkgs | gomi と合わせて現行版の維持より標準定義での管理を優先する |
| herdr, opencode, pi-coding-agent | 共通 nixpkgs の標準定義 | 本体と設定配置を分離し、現行版維持の override は作らない |
| claude-code@latest, codex, antigravity-cli（cask） | 共通 nixpkgs の標準定義 | GUI cask と区別し、旧 CLI 導入物の整理は切替後 |
| Hermes | `ryonakae/hermes-agent` fork 同梱 Flake のパッケージ | `voice` のみ除外。既存管理関数への接続・固定ビルド・生成物確認済み（T7） |
| Unity CLI（旧 standalone installer） | Homebrew `unity-cli` cask、Nix に導入宣言 | 承認済み。旧本体・PATH の整理と実機適用は T9・T10 |
| agent-device | npx で都度実行 | mise 宣言は削除。版・Node 要件と起動方法は自作スキルに記載 |
| @ryonakae/shepherd（npm） | 復元対象から除外 | Herdr plugin と専用 runtime の復元も取りやめ。実機削除は別操作 |
| mosh | Homebrew | firewall 手順が配布実体へ署名するため |
| mise | Nix の CLI、プロジェクト用途のみ | 共通ランタイムの二重管理を解消 |
| fisher | Home Manager の fish plugin 宣言 | plugin revision を固定 |
| 1password-cli, gcloud-cli | Homebrew cask | 共通ツールとして管理継続をユーザー承認済み |
| icu4c@76, libpq, oniguruma, pcre2, postgresql@17 | 直接の管理対象外 | ユーザー承認により宣言から除外。依存としての導入はパッケージ管理に任せ、必要なら移行時に手動導入。実機・DB・サービスは削除・停止しない |
| zellij / ZAM | 移行対象外 | 未使用のため管理設定・導入宣言を削除する承認済み。実機の本体・データ削除は未実施 |
| その他55 cask、App Store 22件 | Homebrew 補完、導入一覧を Nix 管理 | 実機59 caskから上記3 CLIとCotEditorを除く。CotEditorは実機にApp Store receiptがあるためmasへ一本化。アプリ自動更新を許容 |

補足: 旧 `figma-beta` は tap metadata がなく、現在の公式 cask は有効な `figma@beta`（126.10.3）だった。Nix 定義には現行名を採用するが、現在の116.18.4のアプリとの衝突・導入経路整理は切替前に確認する。`sheltie` と `zerdr` は `ryonakae/tap` の完全修飾名を使用。生成 Brewfile は nix-darwin の既定でこの2パッケージに `trusted: true` を付けるため、適用時の変更範囲に含める。実適用はまだ行っていない。

過去の依存 metadata では oniguruma は jq、pcre2 は fish / Git / glib / ripgrep が使用していた。icu4c@76 / libpq / postgresql@17 の利用元は確定していないが、ユーザーは5件とも直接管理せず必要時の手動導入とする方針を承認した。利用元の全件調査を切替条件にせず、既存の DB・導入実体は保持する。

## Homebrew 外の導入物の棚卸し

`f95fb3c` 後の調査。実行したのは `uv tool list`、配置先の metadata・package.json の名前と版の取得、Nix 宣言との照合のみ。通常の shell 初期化、ツールの更新・削除・実行テストは行っていない。既存プロジェクト内や npx cache の依存は共通導入物に数えない。

**扱いの訂正（ユーザー承認済み）**: 以下は配置の観測記録であり、管理漏れ・追加必須・切替阻害の一覧ではない。「未確定」は導入目的を調べていないという意味に限る。共通環境として別途合意しない限り新規宣言を追加せず、他プロジェクト用は各プロジェクトの設定と mise 等に任せる。未宣言分の全件分類・追加調査は行わず、既存実体は保持する。手動 GUI の候補もこの調査を理由に移行範囲へ自動追加しない。

| 導入元 | 宣言にない対象 | 観測記録（追加作業の要求ではない） |
|---|---|---|
| npm global | `@google/gemini-cli`、`eas-cli`、`@expo/ngrok`、`@vscode/vsce`、`fixpack`、`npm-check-updates`、`sort-package-json` | 復元要否・管理方法が未確定。Node の複数版にある同名パッケージは重複として集約 |
| Yarn global | `create-hono` 0.8.1 | 復元要否が未確定。単発 generator を恒久導入へ自動追加しない |
| uv tool | `aider-chat` 0.84.0、`specify-cli` 0.0.22 | どちらも未宣言。復元要否・管理方法が未確定 |
| mise | Dart、Deno、Flutter、just、lefthook、pnpm、prek、Rust、SwiftFormat、SwiftLint、Yarn | インストール実体あり、共通 Nix 宣言なし。プロジェクト指定で使うものは既存方針どおり mise を残せるが、各対象がプロジェクト専用かは未確認 |
| Cargo / rustup | rustup と toolchain 用リンク、`cross` / `cross-util` | 未宣言。mise の Rust も併存。既存 toolchain は削除しない |
| `/usr/local/bin` の通常ファイル | `fswatch`、FTDI helper、`tailscale`、組織向け診断・保護用コマンド | tailscale はアプリ宣言あり。残りは由来・復元要否が未確定。組織管理と思われるものを独断で再配布・削除しない |

既に扱いが決まっている対象:

- npm の `agent-browser` / `@openai/codex` / `opencode-ai`、手動 `~/.local/bin/agy` は Nix 宣言で対応。`agy.*.old` は旧本体の残存で別製品ではない。
- `agent-device` は npx、Shepherd は復元対象外で承認済み。npm の `npm` / `corepack` は Node 同梱品として区別する。
- mise の Bun / Node / Python / Ruby は共通 Nix runtime 宣言済み、usage も Nix 宣言済み。旧バージョンの存在だけを復元要求としない。
- `~/.local/bin` の node / npm / npx は旧 mise shim へのリンク、python3.11 は uv 管理 Python へのリンク。切替時の優先順位整理対象。rm は管理済み wrapper。
- Unity CLI は Homebrew 補完で承認・宣言済み。Antigravity / Antigravity IDE の手動 bin は前項の PATH 調査対象で、CLI と GUI を混同しない。
- `/usr/local/bin` の Docker / Cursor / Zed / Spark 等はアプリ内本体へのリンク。OrbStack / Trae へのリンクも残るが、今回の `/Applications` 一覧に対応アプリはなく、導入済み本体とは数えない。Jamf / ClamAV / Cloudflare 等は組織管理の可能性があり、一般 CLI として自動追加しない。

取得範囲は Homebrew・mise 各実 Node 版・`~/.local` の global node_modules、Yarn global、uv tools、mise installs、`~/.local/bin`、`~/.cargo/bin`、`/usr/local/bin`、`/Applications` と `~/Applications`。`~/bin` / `~/go/bin` / `~/.bun/bin` / `~/.deno/bin` と pnpm / Bun の標準 global 配置先は今回確認した場所にはなかった。npmrc 等の認証設定やプロジェクトは読まず、独自 prefix が他に存在しないことまでは保証しない。

手動 GUI は `/Applications` の名称を既存 Homebrew metadata と App Store receipt の有無に照合した。Nix の cask 宣言にない主な候補は Antigravity IDE、Acall Desktop、Bang & Olufsen、Bluesky、Cavalry、CleanArchiver、Cloudflare WARP、ColorNavigator 7、ColorSing、HUAWEI AI Life、IWLTBAP LUT Generator、Maxon / Maxon Autograph、OneDrive、Paper、Pencil、Qfinder Pro、Rakuro、SwitchBot、VOICEVOX、zoom.us、ZXP Installer。Adobe / Blackmagic / DaVinci / Unity Editor の製品群、組織の管理・保護アプリ、Google のショートカットや Chrome profile 用アプリ、OS / SDK の付属アプリは個別パッケージ宣言の漏れとは即断しない。`~/Applications` には Chrome Apps と Claude Code URL Handler がある。これらの利用要否・手動復元の区分は未確定であり、削除候補の一覧ではない。

## 切替・復旧手順（T10・まだ実行しない）

1. **切替前**: 完成した構成を現在の Mac 向けに build。生成された activation とパッケージ参照を確認し、更新する入力・実機パス・サービス・preferences と旧構成への戻し方を用意する。破壊的な Homebrew cleanup や Nix GC は実行しない。
2. **承認と停止**: ユーザーへ影響を提示し、必要なエージェント・端末・アプリの停止を確認。この Mac は Hermes 未使用のため停止・待機は不要。別の Mac の稼働中環境へ適用する場合は、利用者確認後に管理関数で正規停止し、失敗したら中止する。実行中のエージェント自身が途切れる場合は、人間用の再開手順を先に渡す。
3. **状態保全**: この Mac には Hermes の既存データがなく、移行やバックアップは不要。別の Mac の既存環境では DB・認証・memory 等を保持し、停止後、新しい本体の初回起動・schema 更新より前に、人間が sandbox 外で必要な状態を整合した形でバックアップする。関連 WAL 等を取りこぼさず、ログや Git / store へ内容を出さない。Hindsight のイメージやデータを変える場合は別途整合したバックアップを取る。既存の秘密・Keychain は変更しない。
4. **適用**: 確認済みの旧リンク / plist / shell 設定のみを退避して新構成を適用。既存実ファイルを一括強制上書きしない。秘密の参照と PATH を確認し、起動を承認されたサービスだけ起動する。この Mac の Hermes は起動しない。別の Mac では適用前の利用状態と利用者の承認に従う。
5. **スモーク確認**: 下記「検証記録と最終完了条件」の実機項目を確認する。設定変更を伴う再起動・ログアウト等は必要なものだけ直前確認する。
6. **失敗時**: 新サービスを正規停止し、原因に応じて旧生成物 / 旧リンク / 旧 plist / 旧 preferences へ戻す。初回は以前の Nix 世代が存在しないので、退避した非 Nix 構成への復旧手順を使う。以後は保持した Nix 世代を使えるが、live link 先の本文は Git で別に戻す。Homebrew アプリや OS preferences、DB も同じ操作で戻らない。
7. **DB を変更した場合**: 旧バイナリを新 schema の DB へそのまま向けない。必要なら停止状態で人間がバックアップを復元し、切替後の新規データが失われ得ることを確認してから実施する。自動 rollback で DB を巻き戻さない。
8. **整理**: 新構成の受入後、承認済みの旧パッケージ・配布経路を整理する。復旧用世代・バックアップの削除は移行成功と同時に自動実行しない。Nix 自体のアンインストールは通常の復旧手順にしない。

## 検証記録と最終完了条件

未変更範囲の結果は再利用し、追加調査・レビュー・テストを切替の前提に増やさない。

### nix-homebrew 追加後の検証記録（最新候補）

- 固定 lock の `dotfiles build --host /tmp/dotfiles-machine.SyCOAn6p` が終了コード0で成功。成果物は `/nix/store/cdsxh5l5al5riqmjv89fxyl5sxxdk3jx-darwin-system-26.11.4cff07d`。ログは `/tmp/dotfiles-nix-homebrew-build.log`。
- lock に `nix-homebrew` とその `brew-src` だけを追加し、既存依存の固定値は不変。Homebrew 本体は7.0.4。生成 Brewfile は前候補と同一で、自動 update / upgrade / cleanup 無効を維持した。
- 生成 activation は Homebrew 導入予定の指定で未導入検査を通し、`setup-homebrew` → `brew bundle` の順になる。対象は `/opt/homebrew`、所有者は host の username。Intel 用 prefix と固定 tap は追加していない。Nix format、差分、生成 setup script の Bash 構文検査を通過。
- `autoMigrate` は既存 Homebrew の Git 追跡ファイル・`.git`・残存 vendor を削除して本体を置換する。Cellar / Caskroom・tap 等は保持する設計だが、本体のローカル変更は保持しない。T9 の初回退避・復旧確認に含め、実適用前に操作範囲の承認を得る。実 Homebrew の変更・移行・起動は未実施。

### live link 方式の検証記録

- `bash scripts/dotfiles.sh build --host /tmp/dotfiles-machine.SyCOAn6p` が終了コード0で成功。lock 検査・snapshot・flake check・固定ビルドを実行し、`flake.lock` は不変。Homebrew の暫定保持5件除外も含む。
- Darwin 成果物: `/nix/store/gagas7xpj3b75lbp8lkc5hn1i01lcj7g-darwin-system-26.11.4cff07d`。対応する HM 成果物: `/nix/store/vnapx3fnmqw2kc5ng8dxph0ccfc879r2-home-manager-generation`。
- `home-files` の138配置中85件が `~/dotfiles/config/` の存在する追跡済み正本への live link。Pi 設定3件、通常設定、自作スキル、置換不要の fish 関数を含む。外部スキル・Yazi plugin と Nix 固有の生成物は store 配置を維持。Antigravity は共通スキル置き場への参照を維持する。
- Pi の merger・`checkPiConfigPaths`・`piMutableSettings` が生成 activation にないことを確認。生成 fish config は shell-init / interactive-init の正本を source する。生成 config・Nix 置換8関数の fish 構文、HM activation の指定 Bash による構文検査、変更した Nix 7ファイルの parse / format を通過。
- live script への `executable = true` は HM の build-time copy を誘発したため除去し、正本の権限を継承する。通知4スクリプトは追跡済みの実行権限を保持。Herdr の補助スクリプトは既存どおり `sh` 経由で実行する。再ビルドで成功を確認し、実ファイルの権限は変更していない。
- 自作12スキルの共通・Claude 各配置が正本を参照し、非配布ディレクトリを含まないことを確認。現在は Claude 固有のローカルスキルディレクトリがなく、同名優先は既存コードを維持している。
- `4489dd1` に対する Nix 7ファイルの未コミット差分を独立した read-only reviewer が確認し、blocking/high・decision required・medium/low の指摘なし。ビルド・生成物の検証はメイン担当の実行結果と区別する。
- 成功ログは `/tmp/dotfiles-live-links.YC8XuhiW/final-build.log`、終了コードは同ディレクトリの `final-build.exit`。一時ログ・store 成果物の永続保持は保証しない。
- 実 HOME の適用、アプリからの保存、停止・退避・復旧は未実施。Claude / Pi の並行変更を保持し、回帰テストの追加・再実行は行っていない。

### 旧 immutable / merger 方式で確認できた範囲

以下の成果物・配置検証は live link 方針変更前の履歴。パッケージ等の未変更範囲は再利用し、新方式の確認結果とは区別する。

| 対象 | 実行結果・根拠 |
|---|---|
| T2 の基盤、T3 の実装済みパッケージ、T4 の配置 | `dotfiles build` の lock 検査・評価・ビルド成功。Pi・スキル・Claude 依存、gateway timeout、macOS preferences 宣言までの部分構成に加え、Hermes 本体も同じ lock 検査・snapshot・check/build 処理で検証 |
| 旧方式の Darwin 成果物（fork / voice 除外・Unity CLI 宣言追加） | `/nix/store/46ag235bdr3bwg2b3y9nyzwf5mjww9y6-darwin-system-26.11.4cff07d` |
| 対応する Home Manager 成果物 | `/nix/store/8dcbikjbxvyfi7jg1mi5k9725i5pkgxj-home-manager-generation` |
| fish / shell / Python / TOML / Nix | 変更時に構文・format・差分を確認。生成された fish の読み込み順序と rm の interpreter も確認 |
| `home/files.nix` の配置 | 既存の AGENTS / Yazi の検証に加え、今回追加した9ファイルと正本の byte 一致・shell script の実行権限を確認。Nix format、JSON / TOML / Python / shell 構文、差分を確認。Zed は JSONC のため JSON parser では検証せず、元ファイルとの一致のみ |
| 実機適用・GUI・サービス | **未実施**。ビルド成功はこれらの成功を意味しない |

同じ実機でのビルドに使用したコマンド:

```fish
bash scripts/dotfiles.sh build --host /tmp/dotfiles-machine.SyCOAn6p
```

この一時 host ディレクトリや store 成果物は消えている可能性がある。host 入力がなければ [セットアップ手順](../setup.md#nix-の事前ビルド) に従い、非秘密の `username` / `homeDirectory` だけを持つ入力を用意する。bootstrap をやり直さない。新規の参照ファイルは対象を明示して Git に追加してからビルドする。未追跡ファイルを含めるために `path:.` を使わない。

### 旧方式の部分構成レビュー

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

### Pi・自作スキルの検証記録（旧 immutable / merger 方式）

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
- tracked config 2件は Agent Context の read/mtime監視と Worktrunk の設定読取だけで、本番の書込処理は別state領域と確認した。旧方式では読み取り専用配置を維持したが、最新方針では T4 の live link へ変更する。
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

### T9 の初回復旧準備（旧 immutable / merger 方式の調査記録）

最新の調査基準は `5113cfdd1b0be0c4a0b1d0a4175e4eca7fbd64e1`。開始時の upstream は `origin/master`、ahead/behind は0/0、staged 変更なし。Claude / Pi 設定、Homebrew 宣言と関連文書に既存差分があり、ユーザー承認に従い既存差分を保持して文書のみ更新する。退避・復旧手順の正本は [セットアップ手順](../setup.md#初回の退避台帳と停止前の引継ぎ)。以下は観測と未確認範囲であり、実退避の台帳の代わりではない。

**HOME の確認**

- 既存 HM 成果物 `8dcbikjbxvyfi7jg1mi5k9725i5pkgxj` の `home-files` は135配置先。Pi 可変設定3件と Hermes plist 2件を加えた140対象は、リンク111、実ディレクトリ16、通常ファイル1、未作成11、人間による確認待ち1。Antigravity の参照は通常配置135件に含まれる。確認できた既存対象は本人所有、HOME 以下の親経路に別実体へのリンクなし。内容は取得せず、実 `config.fish` は以前の拒否を尊重して再取得・再試行していない。
- 実ディレクトリは外部スキル13件と Yazi の `full-border.yazi` / `git.yazi` / `smart-enter.yazi`。通常ファイルは `.claude/hooks/herdr-agent-state.sh`。Pi 3件はリポジトリへの旧リンク、Antigravity は共通スキルへのリンクのまま。cua-driver の共通・Claude 両配置、Hermes plist 2件は未作成。
- 通常配置以外に HM activation が作る `~/Applications/Home Manager Apps` と `~/Library/Fonts/HomeManager` も未作成。生成 activation の `copyApps` / font hook は rsync の `--delete` を含むため、直前に既存実体があれば止める条件を追加した。
- HM profile の候補（`~/.local/state/nix/profiles/home-manager`、旧 `~/.local/state/home-manager/profiles/home-manager`、`/nix/var/nix/profiles/per-user/<user>/home-manager`）と HOME / 旧 global の `current-home` GC root は未作成。`~/.nix-profile` は `~/.local/state/nix/profiles/profile` へのリンクで、後者は未作成。汎用 Nix profile を HM の初回生成物として削除しない。
- 固定 plugin source と既存の非秘密ファイルを再照合。fzf は `conf.d/fzf.fish` と9関数の計10件が一致。bobthefish は9関数中5件一致、`__bobthefish_glyphs.fish` / `fish_greeting.fish` / `fish_mode_prompt.fish` / `fish_prompt.fish` の4件は異なる。すべて本人所有の通常ファイルで、旧内容を保全して個別退避する。以前の「fzf 関数10件」は初期化ファイルを含む合計との混同で、関数は9件へ訂正した。旧 Unity 初期化と既知の Zellij リンクも残っており、移動・PATH 変更はしていない。

**system の確認と復旧順序**

- `/etc` 20配置先の従来記録は `/tmp/dotfiles-system-collision-metadata.json`。既存4件と未作成16件、対応する退避名は未作成。後続の限定 hash 比較で bashrc / zshrc は不一致、zprofile / nix.conf は一致（下記「棚卸し終了後のビルドと適用前の実衝突」）。今回実 `/etc` の内容・hash は再取得していない。既知 hash 一致のファイルも保全対象とした。
- 読み取り専用の独立調査は既存の生成 activation と標準処理を確認。親も daemon 配置順と起動時の再適用処理を読んだ。`org.nixos.activate-system` は system profile を読み、current-system と `/etc` を再設定する。初回の途中失敗でも、末尾まで到達したかだけでは変更済み範囲を判定できない。復旧はこの登録を先に解除し、旧設定・daemon、HOME、profile / GC root、synthetic 設定の順で対象別に戻す。
- `/Library/LaunchDaemons/org.nixos.nix-daemon.plist` は root 所有0644の通常ファイル。default profile は root profile へのリンク、root profile は `profile-3-link` を参照。独立調査で旧 store environment `qs84cyfhvpn6mcs80i5vh47vsf976197` と installer plist の存在を確認したが、実配置との同一性・実行先・launchd 登録状態は未確認。元の実ファイルを人間が保全し、復元操作を確定するまで適用へ進まない。
- 今回親が追加確認した `/var/lib/linux-builder`、`/Applications/Nix Apps`、`/Library/Fonts/Nix Fonts`、`/etc/hosts.before-nix-darwin`、activate-system plist は未作成。独立調査でも system profile・`/run`・current-system・current-system GC root は未作成。候補 activation 冒頭の linux-builder 削除と Apps / Fonts 同期を変更範囲へ追加した。
- build users / group の更新、PAM・SSH・TCC の条件付き変更は実機の条件成立が未確認。秘密・権限・サービスの操作をエージェントが実行せず、人間が対象を絞って確認・承認する。標準 uninstaller は今回以外の退避や shell 設定も変更し、途中失敗では旧 daemon 復元が省略され得るため初回復旧の既定手段にしない。

根拠は既存 system `46ag235bdr3bwg2b3y9nyzwf5mjww9y6` の `activate`（冒頭、service 配置、HM 呼出し）、生成 `wilxng1wk5a2fk22rv4gnndr94cmncv4-activate-system-start`、上記 HM の `activate`（profile / GC root、copyApps、font hook）、リポジトリの `home/pi.nix` / `home/files.nix`。公開 HM のファイル衝突資料も確認し、手動の対象別退避方針を維持した。`git diff --check` と2文書のローカル Markdown 参照9件（anchor を含む）の実在確認は成功。独立した read-only reviewer が今回の文書差分とリポジトリ内の配置定義を確認し、blocking/high・decision required・medium/low の指摘なし。既存の Homebrew 文書差分と設定3ファイルは対象外、実 HOME / system・外部 store はレビュー側では未検証。新たな build・回帰テスト・通常 shell の起動・実退避・サービス操作・適用・復旧演習は行っていない。T9 全体は未完了。

### 旧 fish 初期化・PATH の追加確認

調査基準は `18d72cb785a0365df10e7b01cd3f27db9025fed1`。開始時の upstream は `origin/master`、ahead/behind は0/0。Claude 設定と Pi fast-mode の既存変更は保持し、取り込まない。現在の Homebrew fish は4.6.0。既存の HM 成果物と HOME の非秘密の初期化ファイルを読み取り比較し、設定を source したり通常の fish を起動したりしていない。

- `conf.d/fzf.fish` と `functions/__fzf*.fish` 9件の計10件は、固定 HM 成果物が参照する fzf source と byte 一致。新構成の `plugin-fzf.fish` も同じ `conf.d/fzf.fish` を source するため、旧ファイルを残すと初期化が二重になる。切替時の個別退避対象に含める。
- bobthefish の通常ファイル9件のうち5件は固定 source と一致し、`__bobthefish_glyphs.fish` / `fish_greeting.fish` / `fish_mode_prompt.fish` / `fish_prompt.fish` は異なる。旧版との差か個別変更かは未確定で、旧ファイルを保全せず捨てない。HM の plugin loader は user functions の後ろへ store の functions を追加するため、旧関数を残すだけでは新 plugin へ完全に切り替わらない。
- `fish_frozen_key_bindings.fish` は fish 4.3 への移行時に生成されたもので、起動時に universal `fish_key_bindings` を消す。`fish_frozen_theme.fish` は色設定を global scope へ移した生成物。どちらも Fisher の配布物ではなく、新構成の管理対象でもない。旧 plugin と一括退避しない。
- `functions/fish_logo.fish` と `completions/fish_logo.fish` は固定 plugin に同名ファイルがなく、由来・復元要否は未確認。未知のファイルとして保持する。
- `conf.d/unity-cli.fish` は `~/.unity/env.fish` を source し、その内容は `~/.unity/bin` を PATH へ追加するだけだった。同ディレクトリに `unity` が存在する。Unity Hub とは別の CLI。公式の standalone installer と配置が一致するが、現本体の版は未確認。ユーザーが利用継続と Homebrew 補完を承認したため、`unity-cli` cask の宣言へ追加した。本体の実行や導入・削除はしていない。

universal variables は `fish_variables` 全文を出力せず、`PATH` / `fish_user_paths` / `fish_function_path` / `fish_complete_path` の行だけを抽出した。後二者は該当行なし。公式 fish の資料では `--no-config` は universal variables も無効にするため、そのモードの `set` 出力を実機の保存値確認には使わない。

- 保存済み `PATH` には `~/.local/share/mise/shims`、Homebrew と system の標準パス、`~/.anyenv/bin`、`/opt/homebrew/opt/mise/bin` がある。`~/.anyenv/bin` は現時点で存在しない。保存値であり、稼働中 shell の実効 PATH と同一とは限らない。
- `fish_user_paths` は PostgreSQL 17 の bin、Antigravity IDE と Antigravity の各 bin、`~/.local/bin`、Android platform-tools、Android Studio の Java bin、`/usr/local/sbin`。Antigravity の2ディレクトリにはそれぞれ `agy-ide` / `antigravity-ide`、`agy` / `antigravity` がある。両者を同じ不要パスとして扱わない。
- 新構成は Nix の profile を前方へ移し、最後と PATH 変更時に `~/.local/bin` を先頭へ戻すが、旧 universal 値を削除しない。mise shims から他プロジェクト用コマンドが引き続き解決されること自体は許容し、合意済みの共通ツールと rm の実行先が妨げられる場合だけ整理する。PostgreSQL の PATH 維持は DB 保存先・サービス利用状況の確認を代替しない。

T9 は未完了。universal 値の変更と旧ファイルの退避は行っていない。Unity CLI の宣言追加は承認後に実施したが、実機切替は別操作。system 側の復旧手順も未確定のまま。fish 調査では新たな build・回帰テスト・実機適用は実施せず、取得済み生成物との比較だけを行った。

### 棚卸し終了後のビルドと適用前の実衝突

ユーザーは追加の網羅的検証より切替を進めるよう指示し、他プロジェクト用導入物の全件分類を切替条件から外すことを承認した。T1 は完了。共通環境の範囲を増やす棚卸しを再開せず、合意済み構成の適用に必要な退避・停止へ進む。秘密・権限・削除・サービス操作の具体的な実行条件は維持する。

- 通常の `bash scripts/dotfiles.sh build --host /tmp/dotfiles-machine.SyCOAn6p` が exit 0。公開 lock 検査・flake check・build を通過。ログは `/tmp/dotfiles-final-build.A2q3Qr/build.log`、source snapshot は `/nix/store/z63f6hznh3c2ka4wsmfj1bpxggsgbq16-source`。root lock SHA256 は `6d7c28a5e15bbc7037913dd0b1e0782baf12d39e49d936ddd9b13fb52181988d` で不変。承認済みの Herdr 別ペイン `w3W:pH` を使用し、完了後に閉鎖した。
- 生成 Brewfile `/nix/store/9b978fh3bbif80xqrflnjc68n82byq44-Brewfile` に Unity CLI / Hub を確認。Homebrew bundle・activation は未実行。Claude / Pi の既存未コミット設定も snapshot に含まれるが、コミット対象には含めない。
- 最新の activation が持つ既知 hash と `/etc` の既存4ファイルを、内容を出力せず比較した。`/etc/bashrc` / `/etc/zshrc` は不一致で標準衝突検査により中止する対象。`/etc/zprofile` / `/etc/nix/nix.conf` は一致。4件とも `.before-nix-darwin` は未作成。`/etc/profile` に installer の `etc/profile.d/nix-daemon.sh` 参照はなかった。これは対象を絞った確認で、activation 全体を実行した検証ではない。
- 実退避では、未知内容の `/etc/bashrc` / `/etc/zshrc` を私有バックアップへ保全してから標準の `.before-nix-darwin` へ移し、HOME 衝突対象・Pi 可変設定も保全する。実行前に上記「T9 の初回復旧準備」の旧 daemon 等の残る確認を終える。root 所有ファイルの退避と Pi 終了を伴うため、人間の操作と切替直前の具体的な承認が必要。既存ファイルを force overwrite しない。

### 残る最終確認

以下は移行全体の受入条件であり、すべてを初回適用前に満たす条件ではない。適用前は T9 の安全確認・固定ビルド・復旧準備、適用後は T5・T10 の実行時確認、受入後は T11 の整理という順に進める。部分構成での成功や確認の後回しを理由に、未完了項目へチェックしない。

- [ ] T9: 完成構成の lock 整合・評価・ビルドと、最後に変更したファイルの構文・差分が通る。build では activation・依存更新を実行しない。
- [ ] T5・T9: 秘密・認証・DB・可変状態を store に入れず、配置の所有権・衝突・退避・再適用時の扱いが明確。
- [ ] T6・T7・T9: 生成された PATH・wrapper・plist・activation が保護と停止順序を守り、未使用の Hermes を起動しない。
- [ ] T10: 承認後の実機適用・主要導線の確認が完了し、初回復旧手順と実施結果が記録されている。DB 復旧演習は行わない。
- [ ] T11: 旧配布の終了、手動作業・補完・未実証範囲の明記、実装側の必須レビューが完了。

構文確認は fish の `fish --no-execute`、shebang に対応した shell の `-n`、Python / TOML の parse、Nix formatter / 評価を使う。文書は参照先と `git diff --check` を確認する。通過済みの検証は、後続変更・失敗・未解決の懸念がない限り繰り返さない。

## 履歴・撤回済み事項（再開タスクではない）

- **Q12 の immutable / Pi merger 方式の撤回**: 設定本文の store 固定と Pi 設定3件の merger / checker 例外を撤回し、追跡済み正本への標準 HM live link に変更する。自作スキルも live link とし、本体・外部 plugin・外部スキル・Nix パス置換が必要な生成物の store 管理は維持する。旧検証記録は履歴であり、新方式の完了を示さない。

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
