# dotfiles

macOS 用の個人設定。ユーザー向け手順の入口は [README.md](README.md)。エージェントが導入・更新・復元、Homebrew / mise、外部スキルを扱うときは [dotfiles-setup](.agents/skills/dotfiles-setup/SKILL.md) を読む。

## 編集

- ホーム側を経由せず、`config/` 内の正本を編集する。配置・外部 repos・macOS defaults は構成別 `mise.<name>.toml`、アプリ一覧は `brew/Brewfile.<name>`。ルート `mise.toml` は構成非依存のみとし、共通リソースは `mise.default.toml` に置く。コピー運用・独自配置ツールを追加しない。
- 本文編集は即時反映。配置の追加・削除は mise を使い、個別リンクや管理ディレクトリの削除・改名は、宣言を消す前に標準 unapply する。HOME 一括の symlink-each は使わない。
- 全体入口は setup のみ。全構成を明示し、private/work へ default を自動追加しない。部分操作・明示更新は標準 brew / mise。setup に cleanup・サービス再起動を追加しない。
- 共通 runtime の exact 版を維持し、Hermes は専用 mise task から指定 fork の標準 installer で初回導入する。本体更新は別 task。通常 repos 更新へ混ぜず、起動時に導入・更新しない。外部スキル・fish/Yazi plugin は取得元ブランチの最新版追従を許容する。
- 未知の実体を force で置換しない。自動再試行・rollback は追加しない。
- 非秘密の適用対象定義は Git 管理する。マシン固有値・秘密は Git 管理外の実ファイルへ置き、値のない `*.example` だけを管理する。マシン非依存の定数は wrapper に置く。
- 共通エージェント指示の正本は `config/.agents/AGENTS.md`。各エージェント側の symlink を実ファイルに置き換えない。
- Hermes の認証・memory・session・自己更新する hooks / cron / skills、Herdr の plugins 実体・session・log は管理対象に加えない。

## 検証

変更したファイルの構文、差分、関連テストを確認する。配布やサービス再起動は検証目的では実行しない。

- fish は `fish --no-execute`、shell は shebang に対応する shell の `-n`。
- 起動 wrapper・setup 入口は `scripts/tests/` の関連 `test_*.py` を `uv run --no-project python` で実行する。必要な実ツールがないための統合テスト skip は成功と扱わない。
- TOML と Brewfile は標準ツールの構文表示・dry-run で確認する。実 HOME の apply や installer 起動を検証の代わりにしない。
- 文書・スキルはリンク・参照パス、掲載コマンドと現行コードの整合、`git diff --check`。

## 文書

- `docs/` はユーザー向け。例外はトラブル対応、内部制約はスキル側へ分ける。ユーザーへエージェント用資料の通読を求めない。
- エージェント向け判断基準は [スキルの運用条件](.agents/skills/dotfiles-setup/references/setup.md)。ユーザー手順のコマンドを複製せず、必要な箇所へリンクする。
- README とこのファイルに、コードで分かる設定値・全ファイル一覧・処理説明を転記しない。進捗は計画に記録し、日常手順へ混ぜない。

## スキル

- このリポジトリ専用は `.agents/skills/` が正本。`.claude/skills/` の相対 symlink で参照し、HOME への配布対象とは分ける。
- `config/.agents/skills/` は他プロジェクトでも使う自作スキルのみ。外部の追加・更新・復元は dotfiles-setup に従う。
- 自作は mise の共通・Claude 向け2 glob で追跡ファイルごとに直接リンクする。通常追加で名前を列挙しない。削除・`.disabled/` 移動は先に対象を unapply し、外部との優先関係が変わる場合は構成別の外部配置宣言も確認する。
- 共通配置先は `~/.agents/skills/`。Claude 専用同名優先と Antigravity CLI の共通参照を維持し、配布先を増やさない。

## 起動・保護設定

- `__safehouse_args.fish` と `safe-hermes-gateway.sh` の HOME 許可・環境継承・profile 順・feature を合わせて確認する。サービスが対話用 feature を省く差分は維持する。
- ポリシー変更は次回起動から適用される。現在の sandbox 制限を回避しない。実秘密の移行、Keychain 登録・バックアップはユーザーが通常端末で行う。
- Hermes は `hermes-gateway` から fork 標準処理で操作する。自動停止・再開・状態保存を適用処理に追加せず、直接の launchctl や installer の plist 再生成で管理を迂回しない。
- Herdr plugin の追加・削除時は `mise.default.toml` の `herdr:plugins` task と[導入手順](docs/apps.md#herdr)を更新する。worktree の作成・削除は Herdr 本体ではなく Worktrunk を使う。
- Pi の `extensions/` に `hooks/` という名前のディレクトリを作らない。通知処理も extension として自動読込されるため。
