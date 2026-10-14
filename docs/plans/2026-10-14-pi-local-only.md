# Pi ローカルモデル環境への切り替え Implementation Plan

## Requirements

設計経緯: [dig log](../dig/2026-10-14-pi-local-only.md)。実装中のユーザーの管理範囲変更を反映した以下を正とする。

- `~/Dev/local` を作り、mise 有効な通常の fish からその直下・任意の子ディレクトリで `pi` を起動すると専用設定を使用する。`pi.fish` と通常の Pi 設定は変更しない。
- `~/Dev/local/mise.toml` と `~/Dev/local/.pi` 全体は dotfiles で管理せず、実ファイルとして保持する。初期に配置したリンクは宣言を削除する前に標準 unapply する。既存の認証・履歴・取得済みパッケージは変更しない。
- 専用設定元は `~/Dev/local/.pi`。oMLX の OpenAI 互換 API `http://127.0.0.1:8000/v1` と環境変数 `OMLX_API_KEY` を使う。秘密の値を保存・複製しない。
- モデルは LFM2.5-24B-A2B-MLX-4bit（context/output 131072/8192、デフォルト）と Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B（262144/81920）。
- pi-subagents とその専用設定・ツール指示を読み込まない。その他の既存 UI・追加パッケージ・共通指示・スキル・MCP は利用できるようにする。ローカル APPEND_SYSTEM.md は Subagents 節を除いた専用本文にする。
- これは設定・認証保存先の分離であり、クラウド推論の強制禁止ではない。Pi 本体改変・通信遮断は対象外。mise 未有効・未 trust・明示的な子設定による上書きは保証対象外。
- OpenCode は oMLX 定義、既定モデル、provider 制限、execute deny、MCP の codemode=false を除去し、CUA・Context7・既存全許可・共通 AGENTS.md リンクを保持する。
- モデルのダウンロード、oMLX サービス操作、既存の無関係な変更は対象外。

## Implementation Decisions

- 対象 `mise.toml` の `[env]` で `PI_CODING_AGENT_DIR` をホーム基準の絶対パスへ解決する。
- Pi 公式 `models.json` と専用 `settings.json` を使用し、通常の auth.json / sessions は共有しない。既存の追加パッケージ5件のバージョンと通知 extension 参照を維持する。
- `.pi` が agent directory と project directory の双方になるルート起動と、子ディレクトリ起動でリソース一覧の一致を検証する。
- 実 HOME の管理解除は対象限定で60秒制限の dry-run / unapply を行い、force を使わない。解除済み宛先に実ファイルを作り、mise 設定を trust する。
- 専用環境の設定と再作成用の配布宣言・恒久テストはリポジトリに残さない。実環境での一度きりの検証と、既存 dotfiles 配置の回帰確認を行う。

## Tasks

Review base: `b4f7a18854bdab90641d2b01b30a52179dc2cab5`（開始時 origin/master と同一）。無関係な fish/config.fish・Ghostty・flake.lock の変更は除外。

- [x] 専用環境の作成と管理解除。
  - 初期実装 `f337d11` でファイル単位リンクを配置。配置・継承テスト2件を Red → Green、全10件成功。
  - ユーザーの管理範囲変更後、管理対象7リンクのみ dry-run / unapply し、非秘密の設定を同位置に実ファイルで保存。通常の指示・認証・履歴は変更せず、ローカル APPEND_SYSTEM.md の Subagents 節だけ除去。
  - リポジトリの `config/Dev/local/` とその配置宣言・追加した専用配布テストを除去。OpenCode 共通指示リンクは維持。
- [x] OpenCode と案内。
  - ローカルモデル指定・制限を除去。`docs/apps.md` に管理外のローカル環境、mise trust、通常/子ディレクトリ/非対話起動、制限を記載。dig log の最終決定を更新。
- [ ] 実環境・回帰検証と独立レビュー。
  - 初期の配置テスト10件と Pi スキーマ検査成功。現在の管理外構成では以下を検証する。

## Final Validation

- [x] JSON/TOML 構文、リンク・参照、`git diff --check`。
- [x] 現行 `uv run --no-project python scripts/tests/test_dotfiles_links.py`：8件成功（34.382秒）。ログ `/tmp/pi-local-unmanaged-tests.log`。通常配置への回帰なし。
- [x] 実 HOME の7設定が symlink ではなく実ファイルで、`.pi/npm` の取得済みパッケージが保持されていること。
- [ ] 通常の fish で対象ルート・子ディレクトリ・対象外への移動により設定元が切り替わり、外では元に戻ること。Safehouse 経由でも維持されること。
- [x] Pi SDK の実ロード：ルート/子で同一の7拡張・28スキル、追加ツールは vcc_recall のみ、Agent / SubagentWorkflow / get_subagent_result / steer_subagent なし。専用 AGENTS.md と Subagents 節のない APPEND_SYSTEM.md を読み込む。モデル2件、デフォルト LFM。ログ `/tmp/pi-local-resources.log`。
- [ ] oMLX が稼働済みなら2モデルの短い応答を確認。未起動・未ロード・認証不足は勝手に変更せず未検証範囲として報告する。
- [x] OpenCode の設定初期化範囲、MCP・全許可・共通指示リンクの維持を差分で確認。

## Review

- 初回固定範囲 base → `f337d11e0f885954f0205ac89eea55aa676d8992` の独立レビューで、共有 APPEND_SYSTEM.md から subagents 指示が混入する high を採用。それ以外の確定 finding はなし。
- 修正には共通指示の編集が必要と判断して停止し、ユーザーへ確認。ユーザーは専用 APPEND_SYSTEM.md を選び、さらに `~/Dev/local` の全設定を管理外とするよう仕様変更を承認した。共通指示の編集案は不採用。
- 管理外の専用本文と実ロードにより初回 finding の解消を確認。新仕様で最終差分全体を独立レビューする。push は全ゲート通過後。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
