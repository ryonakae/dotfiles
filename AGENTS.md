# dotfiles

macOS 用の個人設定。ユーザー向け手順の入口は [README.md](README.md)。エージェントが導入・更新・復元、Nix / Homebrew / mise、外部スキルを扱うときは [dotfiles-setup](.agents/skills/dotfiles-setup/SKILL.md) を読む。

## 編集

- ホーム側を経由せず、`config/` 内の正本を編集する。配置はルート `mise.toml`、アプリ一覧は Nix 宣言。自前 Brewfile・コピー運用・独自配置ツールを追加しない。
- 本文編集は即時反映。配置の追加・削除は mise を使い、個別リンクや管理ディレクトリの削除・改名は、宣言を消す前に標準 unapply する。HOME 一括の symlink-each は使わない。
- build は検査・ビルドのみ、switch は指定成果物の適用のみ、setup は両者と確認付き配置・共通ランタイム導入。build / switch に apply・runtime install を追加しない。
- 未知の実体を force で置換しない。旧 HM からの所有移行は[運用条件](.agents/skills/dotfiles-setup/references/setup.md#失敗と復旧)に従い、所有解除前の実 HOME dry-run を時間制限付きで確認する。自動再試行・rollback は追加しない。
- 非秘密の Nix ホスト定義は Git 管理する。それ以外のマシン固有値・秘密は Git 管理外の実ファイルへ置き、値のない `*.example` だけを管理する。マシン非依存の定数は wrapper に置く。
- 共通エージェント指示の正本は `config/.agents/AGENTS.md`。各エージェント側の symlink を実ファイルに置き換えない。
- Hermes の認証・memory・session・自己更新する hooks / cron / skills、Herdr の plugins 実体・session・log は管理対象に加えない。

## 検証

変更したファイルの構文、差分、関連テストを確認する。配布やサービス再起動は検証目的では実行しない。

- fish は `fish --no-execute`、shell は shebang に対応する shell の `-n`。
- 起動 wrapper・Nix 操作入口は `scripts/tests/` の関連 `test_*.py` を `uv run --no-project python` で実行する。実 Nix がないための統合テスト skip は成功と扱わない。
- Nix はスキルの build 手順を使う。新規ファイルは対象を明示して Git に追加し、Git 外の設定を store に取り込まない。bootstrap はユーザーが sandbox 外で実行し、検証目的では起動しない。
- 文書・スキルはリンク・参照パス、掲載コマンドと現行コードの整合、`git diff --check`。

## 文書

- `docs/` はユーザー向け。操作と成功の確認を順に書き、例外はトラブル対応、内部制約はスキル側へ分ける。ユーザーへエージェント用資料の通読を求めない。
- エージェント向け判断基準は [スキルの運用条件](.agents/skills/dotfiles-setup/references/setup.md)。ユーザー手順のコマンドを複製せず、必要な箇所へリンクする。
- README とこのファイルに、コードで分かる設定値・全ファイル一覧・処理説明を転記しない。進捗は計画に記録し、日常手順へ混ぜない。

## スキル

- このリポジトリ専用は `.agents/skills/` が正本。`.claude/skills/` の相対 symlink で参照し、HOME への配布対象とは分ける。
- `config/.agents/skills/` は他プロジェクトでも使う自作スキルのみ。外部の追加・更新・復元は dotfiles-setup に従う。
- 自作は mise の共通・Claude 向け2 glob で追跡ファイルごとに直接リンクする。通常追加で名前を列挙しない。削除・`.disabled/` 移動は先に対象を unapply し、外部との優先関係が変わる場合だけ Nix 側も適用する。
- 共通配置先は `~/.agents/skills/`。Claude 専用同名優先と Antigravity CLI の共通参照を維持し、配布先を増やさない。

## 起動・保護設定

- `__safehouse_args.fish` と `safe-hermes-gateway.sh` / `safe-hermes-dashboard.sh` の HOME 許可・環境継承・profile 順・feature を合わせて確認する。サービスが対話用 feature を省く差分は維持する。
- ポリシー変更は次回起動から適用される。現在の sandbox 制限を回避しない。実秘密の移行、Keychain 登録・バックアップはユーザーが通常端末で行う。
- Hermes は `hermes-gateway` / `hermes-dashboard` から fork 標準処理で操作する。自動停止・再開・状態保存を適用処理に追加せず、直接の launchctl や installer の plist 再生成で管理を迂回しない。
- Herdr の Claude hook は Homebrew 本体の標準 integration installer。実設定への適用は別承認し、既存 settings 差分を保持する。
- Herdr plugin の追加・削除時は [導入一覧](docs/apps.md#herdr)を更新する。worktree の作成・削除は Herdr 本体ではなく Worktrunk を使う。
- Pi の `extensions/` に `hooks/` という名前のディレクトリを作らない。通知処理も extension として自動読込されるため。
