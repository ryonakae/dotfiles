# エージェント向け運用条件

変更・適用・復旧の判断基準。編集・検証の共通規則は `AGENTS.md`。

## 管理元と変更範囲

| 対象 | 正本・管理主体 |
|---|---|
| 通常 CLI / GUI / App Store アプリ | `brew/Brewfile.{default,private,work}`。標準 Homebrew Bundle |
| 通常設定・自作スクリプト・自作スキル | `config/`。構成別 `mise.<name>.toml` の配置宣言 |
| 共通 runtime | `config/.config/mise/config.base.toml`。mise の exact 版 |
| 外部スキル・fish / Yazi plugin | 構成別 mise の repos と配置宣言（fish は glob、他は選択） |
| macOS preferences | 構成別 mise の defaults と `scripts/macos-settings.sh` |
| Hermes 本体 | `mise.hermes.toml` の repos・task、指定 fork の標準 shell installer |
| Hermes launcher / wrapper / plist | Git 正本の直接リンクと `scripts/hermes_plists.py` の通常ファイル配置 |

- Bash / fish / mise / usage は Homebrew。mise は更新可能だが、共通 runtime の指定版は setup で変更しない。Intel 用 Homebrew は追加しない。
- 標準 Bundle で導入・更新し、`--no-upgrade` や自動 cleanup は使わない。宣言削除をアンインストールとみなさず、対象を指定して削除する。PostgreSQL のデータ・サービスや未宣言アプリをついでに削除・停止しない。

## setup と部分操作

コマンドの正本は[初回セットアップ](../../../../docs/setup.md)と[日常操作](../../../../docs/usage.md)。独自入口は全体 setup だけ。部分操作・本体更新は標準 brew / mise を使う。

- `scripts/dotfiles.sh` は CLT の `/usr/bin/python3` を使う。初回に fish / mise / Homebrew の導入済みを要求しない。
- 未指定・未知・重複の構成は変更前に拒否する。ユーザー指定順を維持し、不明な構成から default へ切り替えない。
- 対象 checkout と `-E` で構成を固定し、継承された `MISE_ENV` や別 cwd による追加構成・プロジェクト設定の混入を防ぐ。private 単独を共通設定・runtime の導入に読み替えない。
- 確認語は、最初の全体承認と dry-run 後の配置承認の2回。単独実行時の確認は残す。Hermes plist は差分がある場合だけ確認する。
- 外部 source の初回取得前に full dry-run 成功を必須にしない。
- private だけ Hermes 用宣言を trust し、install task を呼ぶ。完了判定は既知 checkout の origin/branch・標準完了 marker の HEAD・実行ファイルを照合する。通常 repos 更新と分離し、`command -v hermes` で導入判定しない。包括的な `mise upgrade` を setup に入れない。
- サービスの自動停止・再開、Dock/端末の自動再起動、cleanup を setup に追加しない。macOS 設定の画面反映は完了時に Mac の再起動を案内する。setup の再実行を無変更の冪等操作と説明しない。

### 実機操作の承認

- 秘密・権限・OS設定・サービス・バックアップ・削除は、対象を示して直前にも承認を得る。編集・計画承認だけで実機操作をしない。
- setup は対象ユーザーの通常対話端末で行い、全体を sudo で起動しない。Herdr のペインへの実操作委譲にも承認が必要。
- 変更・衝突する対象だけ保全する。全アプリ停止、HOME 全量バックアップ、無関係な導入物の全件棚卸しは求めない。
- 未知のファイル・リンク、既存 backup、確認後の変更を上書きしない。秘密・認証・session・DB・管理外の兄弟は保持する。

### 失敗と復旧

ユーザーへは[トラブル対応](../../../../docs/troubleshooting.md)を案内する。

- 適用は非原子的。終了コード・失敗段階・完了済み段階と、失敗段階内の部分変更を確認する。後続へ進まず、自動再試行・rollback はしない。
- 配置だけ失敗したら成功済みアプリ更新や repos 更新を繰り返さない。runtime 失敗時は配置も繰り返さず対象 install だけ再開する。
- 以前の状態への復旧では、リンクの所有解除と本文・アプリ・状態の復旧を分ける。構成の再適用で全状態が戻るとは扱わない。

### sudo 認証

承認後、最初の昇格直前に標準 sudo で認証し、必要な処理中だけキャッシュを維持する。完了・エラー・割込み時には維持処理を終了する。パスワード保存、expect、sudoers 変更、全体 root 実行はしない。

cask などがキャッシュを失効させて更新に失敗した場合は、警告して維持を止め、setup は続ける。実行中の sudo は通常どおり入力を求め、次の sudo 段階は入口の標準認証で再入力する。

## mise の配置

- アプリ・設定ディレクトリ単位の `symlink-each` / Git manifest を使う。親ディレクトリ置換は追加しない。
- 自作の配布対象は Git 追跡ファイル。example・秘密・実行時状態を含めない。`exclude` は配布不要物と別宣言の対象に限る。
- 所有記録の欠落・不正時には配置先全体の走査が残る。`exclude` で初回走査が止まると仮定せず、内部状態を手動生成しない。
- glob の source は apply 開始時に展開される。同じ apply で作る宛先を source にすると2回目まで反映されないため使わない。bootstrap では repos 取得後に再展開されるので、clone 済み checkout は source にできる。
- manifest 内の追跡ファイル増減は apply、新規宛先は宣言も更新する。
- 未知の実体・リンクの自動拒否を仮定しない。dry-run と人による確認を通す。アプリがリンクを通常ファイルへ置換した場合も保持して確認する。
- Karabiner は[公式仕様](https://karabiner-elements.pqrs.org/docs/manual/misc/configuration-file-path/)に合わせてディレクトリ全体を symlink。apply にサーバー再起動を組み込まない。

## 外部・自作スキル

更新手順は[外部スキルと plugin](../../../../docs/usage.md#外部スキルと-plugin-を更新する)。

- 取得元・ブランチは `[bootstrap.repos]`、選択・配布先は `[dotfiles]`。同一 repository は共通 checkout を使う。専用 lock・独自 updater を追加しない。
- 新規スキルを自動追加しない。必要な外部スキルだけ明示配置し、自作所有の宛先に二重配置しない。
- repos 宣言削除だけでは checkout を削除しない。
- 自作の配置・削除は `AGENTS.md` のスキル節に従う。スキル単位の unapply は共通・Claude の両方に行う。Claude は `~/.claude/skills/`。管理外の兄弟や Claude の `synced` を保持する。
- `npx skills` を併用しない。

## shell・ランタイム・plugin

- Homebrew fish と plugin の初期化を使い、対話 mise / zoxide の二重 activation を避ける。非対話・launchd は明示 PATH と mise shims。プロジェクト版選択と起動 cwd を維持する。
- 宣言済み方式と別の plugin manager を重ねない。fish plugin は `~/.local/share/fish-plugins/` の checkout を glob で全て配置するため、追加は repos 宣言だけでよい。Yazi は共通 checkout から使う plugin だけ明示配置する。
- runtime の exact pin、Ruby `compile = true` とビルド依存を維持する。AWS CLI は `aqua:aws/aws-cli` と `symlink_bins = true`、同梱 Python を使い、Homebrew へ重複宣言しない。`~/.aws` は保持する。
- Cua installer の既存 PATH 追加、`~/.local/bin` や universal PATH を一括削除・変更しない。
- 最新版・解決先・使用版・管理元提供版を分ける。更新済みと希望版の取得・動作成功を区別し、更新して希望版に届かない場合は対応を相談する。

## エージェントと常駐サービス

手順は[アプリ別設定](../../../../docs/apps.md)、環境変数は[環境変数の管理](../../../../docs/secrets.md)。

### Hermes

- 専用 mise task から `ryonakae/hermes-agent` の `ryonakae` ブランチの標準 installer を呼ぶ。checkout は `~/Dev/private/hermes-agent`（データの置き場 `~/.hermes` の外）に置く。独自 plugin・依存ビルド処理は追加しない。通常 setup は初回だけ、更新は別 task。dirty・未知・途中状態では停止し、復旧は[標準段階の手動実行](../../../../docs/troubleshooting.md#hermes-の導入更新が途中で止まった)で行う。
- 初回だけ `venv` 段階（Python の準備）を実行し、更新では依存の同期から始める。標準完了 marker は操作前に無効化し、全対象段階の成功後だけ作成する。自動 stash/reset・retry・rollback は行わず、同時 setup/install/update は避ける。
- installer の `python-deps`・`products`・`complete` 段階を使い、`config`（初期設定の生成）・gateway・Desktop 段階は呼ばない。PATH 追記が fish の既存設定で不要になるよう `SHELL` を fish に固定して呼び、`config.fish` に `~/.local/bin` の `fish_add_path` 行がなければ導入前に止める。専用 uv/runtime は標準 installer に任せ、共通 runtime の exact pin を変えない。agent-browser・cua-driver は Hermes が固定した版を installer に管理させ（cua-driver は PATH の別実体を使わない）、依存 fallback の警告は隠さない。
- 起動時の自動導入・更新、PATH の別 Hermes への fallback、Hermes の cwd 変更を追加しない。
- wrapper・GUI domain 操作補助は Git 正本。Safehouse の HOME 許可・環境継承・profile 順・サービス feature 差分、引数・終了コードを維持する。
- plist は通常ファイル。symlink・未知の実体・所有の問題は停止し、手動差分を確認なしで上書きしない。比較失敗は停止し、mise の自動ロードする LaunchAgent 管理へ移さない。
- 追加依存・全機能確認を導入の前提にしない。
- `hermes gateway install`、installer の全体 main、別 venv 管理を重ねない。
- 管理関数は対象ユーザーの `gui/<UID>` を固定し、操作元の managername だけで判断しない。失敗時に別ドメインや直接起動へ fallback しない。

### Claude・Pi・Herdr

- Herdr hook は二重登録しない。
- Pi は live link と標準パッケージ管理を使い、認証・session を配布しない。
- Herdr plugins の一覧・ref は `mise.default.toml` の `herdr:plugins` task が正本。checkout / state / session / log は可変データとして保持する。
- Zerdr は Homebrew 本体がローカル plugin と Zed tasks を生成する。通常設定配布と二重所有させない。

## macOS 設定

- mise の named keys で意味が変わる場合は raw defaults を使う。キー・値・型は一次資料で確認する。
- defaults を root の preferences に書かない。補完は小さな標準 CLI スクリプトに限り、`apply` 確認を維持する。
- Dock の手動導入対象を勝手に追加・削除しない。TCC・認証は手動許可のままにする。
- 適用前に対象だけ旧値・型・未設定状態を記録する。宣言を戻すだけで preferences が戻ると扱わない。
