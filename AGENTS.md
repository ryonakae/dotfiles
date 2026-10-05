# dotfiles

macOS 用の個人設定。導入は [README.md](README.md)、手動の初期設定・復元は [docs/setup.md](docs/setup.md) を参照。

## 編集

- ホーム側を経由せず、`config/` 内の正本を編集する。
- マシン固有値・秘密は Git 管理外の実ファイルへ置き、管理するのは値を含まない `*.example`。マシン非依存の定数は wrapper に置く。
- 共通エージェント指示の正本は `config/.agents/AGENTS.md`。各エージェント側の symlink を実ファイルに置き換えない。
- Hermes の認証・memory・session・自己更新する hooks / cron / skills、Herdr の plugins 実体・session・log は管理対象に加えない。
- README とこのファイルに、コードで分かる設定値・ファイル一覧・処理説明を転記しない。判断理由、手動操作、事故を避ける制約だけ残す。

## 検証

変更したファイルの構文、差分、関連テストを確認する。配布やサービス再起動は検証だけを目的に実行しない。

- fish: `fish --no-execute`、shell: shebang に対応する shell の `-n`。
- 起動 wrapper・Nix 操作入口: `scripts/tests/` の関連する `test_*.py` を `uv run --no-project python` で実行する。Nix CLI の統合テストは実 Nix が必要で、未導入による skip を成功と扱わない。
- Nix: [事前ビルド](docs/setup.md#nix-の事前ビルド)を使う。Git ソースに含める新規ファイルは対象を明示して追加し、Git 外の設定を store へ取り込まない。
- 文書: 参照パス・リンクと `git diff --check`。

`remove-broken-symlinks.sh` は削除を伴うため、読み取り専用の検証には使わない。
Nix の bootstrap は人間が sandbox 外で実行する。[初回導入](docs/setup.md#nix-の初回導入)に従い、検証目的に実インストーラを起動しない。

## スキル

- `config/.agents/skills/` は自作のみ。外部スキルの追加・更新は [配布手順](docs/setup.md#外部スキル)に従う。
- 外部スキルの registry 更新と root Flake の更新は別操作。管理方式の移行・復元に内容の更新を混ぜず、既存 revision を維持する。
- 自作スキルは Home Manager で正本への個別 live link を配布する。無効化は `.disabled/` へ移動する。
- 共通スキルの配置先は `~/.agents/skills/`。Claude 専用の同名優先と Antigravity CLI の共通参照を維持し、配布先を増やさない。

## 起動・保護設定の変更

- 対話 CLI の wrapper から承認モード・内蔵 sandbox を変える引数を自動追加しない。利用者の指定と各 CLI の設定に任せる。
- `__safehouse_args.fish` と `safe-hermes-gateway.sh` / `safe-hermes-dashboard.sh` の HOME 許可・環境継承・profile 順・feature 指定を合わせて確認する。サービスが対話用 feature を省く差分は維持する。
- 保護ポリシーは互換性優先。秘密の保存場所を確認せず既存の deny を削除しない。`~/.hermes` は汎用 deny の例外となる信頼領域なので、保護対象の置き場にしない。
- ポリシー変更は次回起動から適用される。現在の sandbox 制限を回避しない。
- 実秘密の移行、Keychain 登録・バックアップ、ごみ箱の復元・掃除は人間が sandbox 外で行う。
- Hermes のサービス操作は `hermes-gateway` / `hermes-dashboard` から fork 標準処理を使う。dotfiles の適用処理に自動停止・再開や状態保存を追加しない。直接の `launchctl` や installer による plist 再生成で管理を迂回せず、停止仕様・退避は [移行時の制約](docs/setup.md#更新停止既存環境の移行)に従う。
- Herdr プラグインには復元用 lock がない。追加・削除したら [導入一覧](docs/setup.md#herdr)を更新する。worktree の作成・削除には Herdr 本体の機能を使わず Worktrunk を使う。
- Pi の `extensions/` に通知処理を置く場合も、`hooks/` という名前のディレクトリを作らない。Pi が extension として自動読み込みするため。
