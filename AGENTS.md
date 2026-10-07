# dotfiles

macOS 用の個人設定。概要は [README.md](README.md)。導入・更新・復元、Nix / Homebrew / mise の操作、外部スキル管理では [dotfiles-setup](.agents/skills/dotfiles-setup/SKILL.md) を読む。人間向け手順も同スキルの [references/setup.md](.agents/skills/dotfiles-setup/references/setup.md) を正本とする。

## 編集

- ホーム側を経由せず、`config/` 内の正本を編集する。通常配置はルートの `mise.toml`、アプリ導入一覧は Nix 宣言を正本とし、自前 Brewfile やコピー運用を追加しない。
- 通常設定の本文編集は即時反映。アプリ・設定ディレクトリ単位の Git manifest で配置し、HOME 一括の symlink-each は使わない。既存 manifest 内の追跡ファイル増減は mise apply、個別リンク・管理ディレクトリの追加は `mise.toml` も更新する。削除・改名は宣言を消す前に対象を標準 unapply する。
- 未知の実体を force で置換せず、Nix build / switch に apply や runtime install を組み込まない。初回の管理記録欠落時には配置先全体の走査があるため、所有解除前に実 HOME の mise dry-run を時間制限付きで完了確認する。既知の旧 HM 衝突以外の問題やタイムアウトがあれば switch しない。後続成功は保証せず、切替中の新規アプリ起動を避ける。失敗時は現状を確認し、所有リンク引渡し・旧世代復旧は承認下で行う。自動 rollback・独自配置ツールは追加しない。
- 非秘密の Nix ホスト定義は Git 管理する。それ以外のマシン固有値・秘密は Git 管理外の実ファイルへ置き、管理するのは値を含まない `*.example`。マシン非依存の定数は wrapper に置く。
- 共通エージェント指示の正本は `config/.agents/AGENTS.md`。各エージェント側の symlink を実ファイルに置き換えない。
- Hermes の認証・memory・session・自己更新する hooks / cron / skills、Herdr の plugins 実体・session・log は管理対象に加えない。
- README とこのファイルに、コードで分かる設定値・ファイル一覧・処理説明を転記しない。進捗は計画に記録し、日常手順へ混ぜない。

## 検証

変更したファイルの構文、差分、関連テストを確認する。配布やサービス再起動は検証だけを目的に実行しない。

- fish: `fish --no-execute`、shell: shebang に対応する shell の `-n`。
- 起動 wrapper・Nix 操作入口: `scripts/tests/` の関連する `test_*.py` を `uv run --no-project python` で実行する。Nix CLI の統合テストは実 Nix が必要で、未導入による skip を成功と扱わない。
- Nix: `dotfiles-setup` のビルド手順を使う。Git ソースへ含める新規ファイルは対象を明示して追加し、Git 外の設定を store へ取り込まない。
- 文書・スキル: 参照パス・リンク、手順と現行コードの整合、`git diff --check`。

Nix の bootstrap は人間が sandbox 外で実行し、検証目的で起動しない。

## スキル

- このリポジトリ専用のスキルは `.agents/skills/` が正本。`.claude/skills/` から相対 symlink で参照し、HOME への配布対象とは分ける。
- `config/.agents/skills/` は他のプロジェクトでも使う自作スキルのみ。外部スキルの追加・更新・復元は `dotfiles-setup` に従う。
- 自作スキルは mise の共通・Claude 向け2 glob で追跡ファイルごとに正本へ直接リンクする。通常の追加で名前を列挙しない。削除・`.disabled/` への移動前に対象を unapply し、外部スキルとの優先関係が変わる場合だけ Nix 側も適用する。
- 共通の配置先は `~/.agents/skills/`。Claude 専用の同名優先と Antigravity CLI の共通参照を維持し、配布先を増やさない。

## 起動・保護設定の変更

- `__safehouse_args.fish` と `safe-hermes-gateway.sh` / `safe-hermes-dashboard.sh` の HOME 許可・環境継承・profile 順・feature 指定を合わせて確認する。サービスが対話用 feature を省く差分は維持する。
- 保護ポリシーは互換性優先。秘密の保存場所を確認せず既存の deny を削除しない。`~/.hermes` は汎用 deny の例外となる信頼領域なので、保護対象の置き場にしない。
- ポリシー変更は次回起動から適用される。現在の sandbox 制限を回避しない。
- 実秘密の移行、Keychain 登録・バックアップ、ごみ箱の復元・掃除は人間が sandbox 外で行う。
- Hermes のサービス操作は `hermes-gateway` / `hermes-dashboard` から fork 標準処理を使う。dotfiles の適用処理に自動停止・再開や状態保存を追加しない。直接の `launchctl` や installer による plist 再生成で管理を迂回しない。
- Herdr の Claude hook は Homebrew 本体の標準 integration installer で管理する。実設定への適用は別途承認し、既存 settings 差分を保持する。
- Herdr プラグインには復元用 lock がない。追加・削除したら同梱手順の導入一覧を更新する。worktree の作成・削除には Herdr 本体の機能を使わず Worktrunk を使う。
- Pi の `extensions/` に通知処理を置く場合も、`hooks/` という名前のディレクトリを作らない。Pi が extension として自動読み込みするため。
