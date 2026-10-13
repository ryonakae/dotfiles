# エージェント向け運用条件

ユーザー向け手順は [README](../../../../README.md) から参照する。この資料は、変更・適用・移行を担当するエージェントの判断基準。ユーザーへ通読を求めない。

## 管理元と変更範囲

| 対象 | 正本・管理主体 |
|---|---|
| macOS・Nix・Homebrew 本体・Bash / fish / mise と補完依存 | Nix / nix-darwin / nix-homebrew |
| 通常 CLI / GUI / App Store アプリ | `nix/darwin/homebrew.nix`。導入・更新は Homebrew |
| 共通ランタイム | `config/.config/mise/config.base.toml`。導入は mise |
| 通常設定・自作スクリプト・自作スキル | `config/`。配置宣言はルート `mise.toml` |
| Hermes fork・生成 wrapper / plist・停止検査、外部スキル・fish / Yazi plugin | Nix / Home Manager |

- Bash は nix-darwin の標準導入・初期化、`usage` は Home Manager の mise モジュールによる導入を維持する。Homebrew へ重複宣言しない。
- Homebrew は `autoUpdate = false` / `upgrade = false` / `cleanup = "none"`。tap は Homebrew 管理、Intel 用 Homebrew は追加しない。本体の移行条件は[既存環境の移行](../../../../docs/migration.md#homebrew-を引き継ぐ場合)。
- アプリ宣言の削除をアンインストールとみなさない。PostgreSQL のデータ・サービス、未宣言の導入物をついでに削除・停止しない。依存ライブラリは依存元に任せ、直接一覧へ重ねない。
- Nix 管理の Yazi plugin を `ya pkg` で重ねて更新しない。

## Nix の検証・適用

コマンドの正本は[日常操作](../../../../docs/usage.md#nix-を更新適用する)。初回導入は[セットアップ](../../../../docs/setup.md)を案内する。

- `scripts/dotfiles.sh` は CLT の `/usr/bin/python3` を使う。mise の配置やプロジェクトの Python を前提にしない。
- ホスト定義は `nix/hosts/`、構成選択は `flake.nix` の `darwinConfigurations`。構成名は英字または `_` で始め、以降は英数字・`_`・`-`。不明な構成から default へ自動で切り替わらない。
- 非秘密のユーザー名・HOME は Git 管理する。適用前に実機との一致を確認する。
- build は検査・ビルドのみ。switch は指定成果物のみを適用し、現在の checkout を再評価・再ビルドしない。setup は build → switch → 確認付き mise 配置 → リンク検証 → HOME からの mise install。候補の Nix 版 mise を使い、sudo は付けない。chsh は含めない。
- update だけが lock を更新する。復元には update を混ぜない。新規 Nix ファイルは対象を明示して Git に追加し、`path:.` で未追跡ファイルを取り込まない。
- switch の成果物メタデータには構成・ソース・対象ユーザー・HOME・停止検査・mise が入る。メタデータがない旧成果物や GC 済み成果物は再ビルドする。store 内にあるだけで未知の成果物を信頼しない。
- setup はビルド時の `mise.toml` と checkout を照合し、候補の mise で当該設定だけを trust する。配置本文は live checkout の `config/`。dry-run は60秒制限付き、apply は別承認。
- build / switch に設定配置や runtime install を組み込まない。

### 実機操作の承認

- 検証と適用を分ける。秘密・権限・OS設定・サービス・バックアップの操作は範囲を確認して承認を得る。計画承認だけで実機操作をしない。
- setup / switch は対象ユーザーの通常対話端末で行い、スクリプト全体を sudo で起動しない。Safehouse 内の制限を回避しない。
- Herdr が利用可能でも、ペインへ実操作を渡すには依頼・承認が必要。そうでなければ通常端末のコマンドをユーザーへ案内する。
- 一律の全アプリ停止・全設定バックアップ・未宣言ツールの全件棚卸しは求めない。競合する対象だけ確認する。認証・session・DB・管理外の兄弟・共有正本を一括移動しない。
- `/etc/bashrc`・`/etc/zshrc` の通常ファイルだけ、内容と退避先を表示して別承認で保存する。既存退避先、未知のリンク、確認後の変更、退避失敗では停止する。手動退避を重ねない。
- Home Manager / nix-darwin の標準検査を force や一括退避で通さない。mise の配置先も別に確認する。

### 失敗と復旧

ユーザーへは[トラブル対応](../../../../docs/troubleshooting.md)の該当箇所を案内する。

- 適用は非原子的。system profile は activation より前に更新される。profile の存在だけを成功とせず、終了コード・current-system・変更済み範囲を確認する。
- 標準 `check` / `--dry-run` activation を安全な事前検査として実行しない。検証目的の実機適用・サービス再起動・GC は行わない。
- 失敗後は自動再試行・rollback をしない。設定配置だけが失敗した場合に成功済みの switch を繰り返さない。runtime install の失敗時は配置も繰り返さず、install だけを再開する。
- [移行・復旧](../../../../docs/migration.md)では、リンクの所有引渡しと本文・アプリ・状態の復元を分ける。旧 Nix 世代で全状態が戻るとは扱わない。
- 旧 HM からの初回移行では、所有解除前の実 HOME dry-run の完了を確認する。既知の旧 HM 衝突以外の問題や timeout があれば switch しない。後続の成功は保証せず、切替中に新しい実体ができた場合も保持する。
- 初回移行の経緯が必要な場合だけ[過去の検討](../../../../docs/plans/archived/2026-10-03-initial-migration-procedures.md)を参照する。現在の操作許可には使わない。

### sudo 認証

適用・shell 退避の承認と Hermes 停止検査後、最初の昇格直前に `sudo -v` で認証する。適用中だけ `sudo -n -v` で更新し、完了・エラー・中断時に更新処理を終了する。build・mise 配置中は維持しない。

更新終了はキャッシュの即時失効ではない。同じ端末の別操作も再認証なしで実行できる場合がある。更新失敗時は実行中の適用結果を回収し、後続へ進まない。パスワード保存・expect・sudoers 変更は行わず、認証1回を保証しない。App Store 認証は別扱い。

## mise の配置

- アプリ・設定ディレクトリ単位の `symlink-each` / Git manifest を使う。HOME 一括の配置、親ディレクトリの置換、自前コピー運用は追加しない。
- 配布対象は Git 追跡ファイル。Nix ソース・生成 wrapper・example・秘密・実行時状態を含めない。`exclude` は追跡済みの配布不要物と別宣言の対象に限る。
- [mise PR #11549](https://github.com/jdx/mise/pull/11549) 後も、所有記録の欠落・不正時は配置先全体の走査が残る。`exclude` で初回走査を止められるとは扱わず、内部状態を手動生成しない。
- 本文編集は即時反映。既存 manifest 内の追跡ファイル増減は apply、新しい宛先は宣言更新も必要。個別リンク・管理ディレクトリの削除や改名は宣言を消す前に標準 unapply する。
- 未知の実体・リンクを自動拒否すると仮定しない。dry-run と人による確認を通し、force や一括退避を使わない。アプリがリンクを実ファイルへ置換した場合も保持して確認する。
- Karabiner だけは[公式仕様](https://karabiner-elements.pqrs.org/docs/manual/misc/configuration-file-path/)に合わせてディレクトリ全体の `symlink`。JSON 単体リンクでは変更検知が働かない。旧配置の解除、実体の保全、配置後のサーバー再起動は別承認にする。apply に再起動を組み込まない。

## 外部・自作スキル

ユーザーの更新手順は[外部スキル](../../../../docs/usage.md#外部スキルを更新する)。

- 外部取得元・探索範囲は `nix/skill-sources/`、revision / hash は `nix/skill-sources.lock.json`、選択・配布先は `nix/home/skills.nix`。同じ repository の取得元は共有する。root Flake input や独自 updater・子 Flake を追加しない。
- `skills-sources-lock` は npins ベースの標準全件更新。全取得元の解決後に専用 lock を置き換える。宣言変更時も実行し、全体の revision と選択集合を確認する。管理ライブラリの `update agent-skills` とは別。
- `enableAll` で新規スキルを無条件追加しない。外部は標準 `structure = "link"` で store へリンク。日常更新での管理リンク置換と、初回の未知の実体の保全を区別する。
- 自作は共通・Claude 向け2 glob で配置する。Nix は mise の対象を参照して二重所有を避け、自作優先・Claude 専用同名優先を維持する。通常追加で名前を列挙しない。
- Claude 専用の同名スキルは専用 source と `mode = "symlink-each"` / `manifest = "git"` の明示宛先で共通 glob を override する。
- スキル単位の削除・改名・`.disabled/` 移動は先に対象を unapply。共通・Claude の両方を確認し、外部との優先関係が変わる場合だけ Nix 側も適用する。
- 共通配置は `~/.agents/skills/`、Claude は `~/.claude/skills/`。Antigravity CLI は `~/.gemini/antigravity-cli/skills` から共通集合を参照する。Hermes / Pi 専用・Antigravity IDE 用へ増やさない。隠しディレクトリは配布せず、管理外の兄弟や Claude の `synced` を保持する。
- 復元に `npx skills` や旧 lock の取得・コピーを併用しない。実行時キャッシュを固定版として復元しない。

## shell・ランタイム

- fish の Git 正本から HM の `nix-init.fish` を source する。外部 plugin・標準 `conf.d` は Nix、対話時の mise / zoxide activation は Git 側。Fisher・二重 activation を追加せず、`fish_variables`・履歴を管理しない。
- 対話 shell は mise activation、非対話・launchd は明示 PATH の mise shims。プロジェクト固有の版選択を維持し、起動 cwd を配置用リポジトリへ変えない。
- runtime の exact pin は `config/.config/mise/config.base.toml`。Ruby の `compile = true` とビルド依存を維持する。
- AWS CLI は mise の `aqua:aws/aws-cli`。同梱 Python と `symlink_bins = true` を使い、開発用 Python を置換しない。Homebrew へ重複宣言せず、`~/.aws` の設定・認証キャッシュを保持する。
- npm / uv の導入済みという事実だけで管理対象へ追加しない。`~/.local/bin` や universal PATH を一括削除・変更しない。Hermes 専用実体を指す古い Node / npm リンクは関連項目だけ確認・保全する。
- 版差の調査では解決先・使用版・管理元の提供版を分ける。上流の最新版だけで lock 収録版を断定しない。同名の別ソフトに注意し、更新先の定義を確認する。更新しても希望版に届かない場合は対応を相談する。

## エージェントと常駐サービス

利用手順は[アプリ別設定](../../../../docs/apps.md)。秘密の初回設定・更新は[共通 API キー](../../../../docs/secrets.md)を参照する。秘密の値を取得して確認しない。

### Hermes

- fork の `ryonakae` ブランチを lock で固定し、同梱 Flake を使う。Home Manager が生成 wrapper / plist・停止検査を管理し、SOUL・Compose は mise。サービスモジュールは取り込まない。
- `voice` グループは fork 標準 override で除外。Apple Silicon で CTranslate2 の検証依存を通じた PyTorch ソースビルドが必要になり得るため。Hindsight・メッセージング・TTS 用の追加グループは維持する。
- `hermes gateway install` による plist 再生成、旧 installer、専用 mise / venv の復元を併用しない。認証・DB・memory・session・cache は store に入れない。
- サービス操作は既存管理関数から fork 標準処理を使う。停止 controller、自動停止・再開・状態保存・バックアップを適用処理へ追加しない。
- 起動定義が実配置と同じなら停止確認・再配置を省く。本体・wrapper・PATH の store 参照を含む定義が変わる場合と初回配置だけ、GUI セッションで launchd 登録・判別可能なプロセスの停止を確認する。plist 所有・symlink・手動変更の保護は維持し、比較エラーは中断する。検査自体は停止せず、全子プロセスの追跡は保証しない。
- 未知の plist、旧 mise / venv の整理はその環境で対象限定の承認を得る。Hindsight の停止・データ移行は別承認。Compose の tag / digest 固定を volume 復元の保証としない。

### Claude・Pi・Herdr

- Herdr hook は Homebrew 本体同梱の同版を標準 integration で導入する。旧 HM hook と併用せず、settings の symlink を通した Git 正本への変更を確認する。別版の Nix ソースから抽出せず、plugin 導入も抱き合わせない。
- Claude statusline は設定の npm version 固定、取得は通常の npx。Nix build / activation で導入しない。
- Pi 設定は live link。merger・通常ファイルへの複製を追加せず、本文編集のための一律停止を求めない。認証・session は移行用設定や store に含めない。
- Pi 拡張の npm version / Git commit 固定は、推移依存全体や全機能の復元を保証しない。Pi の管理先で取得し、Nix build / activation で更新しない。
- Herdr plugins の一覧と ref は[アプリ別設定](../../../../docs/apps.md#herdr)を正本にする。registry / checkout / state / session / log は可変データ。Nix から導入せず、source commit 固定を binary の固定出力保証とみなさない。
- Zerdr の本体は Homebrew、ローカル plugin は本体が `~/Library/Application Support/dev.ryonakae.zerdr/` に生成する。Zed tasks を Nix 管理へ追加しない。

## macOS 設定

- `nix/darwin/preferences.nix` は既定値との差分を管理する。固定版 nix-darwin の説明等で既定値と確認できたものだけ省く。地域・機器依存や不明なものは保持する。オプションの `default = null` は macOS 既定値の根拠にしない。
- 標準オプションで表現できる範囲だけ管理し、独自適用スクリプトや未指定キーへの推測値を追加しない。キーボードのリピート値は整数型で書き込まれる。
- 適用前に変更対象の旧値・型・未設定状態を記録する。宣言や Nix 世代を戻すだけで preferences が戻るとは扱わない。再起動・ログアウト・権限復元はユーザーへ確認する。
- TCC・認証を preferences の全量コピーで移さない。Dock 項目の宣言はアプリ本体の導入ではない。
