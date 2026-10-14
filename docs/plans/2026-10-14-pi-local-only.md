# Pi ローカルモデル環境への切り替え Implementation Plan

## Requirements

設計経緯: [dig log](../dig/2026-10-14-pi-local-only.md)。直近の合意は以下を正とする。

- `~/Dev/local` を作り、通常の mise 有効な fish から、その直下・任意の子ディレクトリで `pi` を起動すると専用設定を使用する。`pi.fish` と通常の Pi 設定は変更しない。
- 専用設定元は `~/Dev/local/.pi`。oMLX の OpenAI 互換 API `http://127.0.0.1:8000/v1` と環境変数 `OMLX_API_KEY` を使う。実秘密は読まない・コピーしない。
- モデルは LFM2.5-24B-A2B-MLX-4bit（context 131072 / output 8192、デフォルト）と Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B（context 262144 / output 81920）。
- pi-subagents を読み込まない。依頼で無効化対象に挙げられていない通常の UI 設定・追加パッケージ・共通指示・スキル・MCP は、専用環境で利用できるようにする。pi-subagents 専用の設定・ツール指示は引き継がない。
- これは設定環境の分離であり、クラウド推論の強制禁止ではない。Pi 本体の改変、通信遮断、グローバル認証の削除はしない。mise 未有効・未 trust・明示的な子設定による上書きは自動切り替えの保証対象外。
- OpenCode はユーザーが選択した A の範囲で戻す。oMLX 定義、既定モデル、provider 制限、execute deny、MCP の codemode=false を削除する。CUA・Context7、全許可ルール、共通 AGENTS.md リンクは保持する。
- 既存の無関係な未コミット変更を維持する。モデルのダウンロードや oMLX サービス操作はしない。

## Implementation Decisions

- 非秘密の正本を `config/Dev/local/` に置き、ルート `mise.toml` から追跡ファイルごとに直接リンクする。`.pi` ディレクトリ自体はリンクせず、セッション・認証・パッケージなど実行時データが dotfiles に入らないようにする。
- 対象側 `mise.toml` の `[env]` で `PI_CODING_AGENT_DIR` をホーム基準の絶対パスへ解決する。リンク元のディレクトリを設定元に誤認しないことを検証する。
- Pi の公式 `models.json` 形式を使い、設定ファイルにキーの値を埋め込まない。専用 `settings.json` のモデルスコープを2モデルにする。既存パッケージのバージョンは維持し、pi-subagents を含めない。
- 共通 AGENTS.md 等は既存正本を参照し、本文を複製しない。専用 agent directory に通常環境の auth.json や sessions をリンクしない。
- `.pi` が専用 agent directory とプロジェクト設定の双方になり得るため、ルート起動と子ディレクトリ起動でパッケージの重複や設定差がないことを確認する。
- 実 HOME への適用は対象限定の mise dry-run を60秒制限で確認してから行う。force は使わない。対象 mise.toml の trust と起動確認は通常端末で行い、Herdr はこの作業用の別ペインを使う。

## Tasks

- Review base: `b4f7a18854bdab90641d2b01b30a52179dc2cab5`（開始時 `origin/master` と同一）。既存の対象外変更は fish/config.fish・Ghostty・flake.lock。OpenCode と mise の既存差分は本会話で承認済みの変更として保持・更新する。

- [x] 専用環境: `config/Dev/local/` に mise / Pi 設定を作成し、ルート `mise.toml` に直接リンク宣言を追加する。共通リソースの参照と pi-subagents の除外を設定する。
  - `scripts/tests/test_dotfiles_links.py` に配置と環境継承の2テストを追加。双方 Red → Green を確認し、全10件成功（36.553秒）。
  - Pi 1.1.0 の `ModelRuntime` で2モデルのスキーマ・URL・上限を検証し、`SettingsManager` でルート/別cwdのデフォルトと追加パッケージ5件（subagents 除外）を確認。認証読み取り・推論なし。
  - 共通 AGENTS.md・APPEND_SYSTEM.md・MCP・footer 設定は元の正本への直接リンク、通知 extension は既存パスを明示参照する。subagents の agent-tool-description.md / subagents.json / agents は参照しない。
- [x] OpenCode と案内: `config/.config/opencode/opencode.json` を A の範囲に戻す。`docs/apps.md` の Pi / oMLX 節を更新し、起動場所・初回 trust・サブディレクトリ・通常環境へ戻る手順と制限を説明する。dig log に今回の確定事項を反映する。
- [ ] 配置と動作確認: 新規配布ファイルを対象明示で Git 追跡し、mise の対象限定 dry-run / apply を実行する。対象設定を trust し、通常環境・ローカル直下・子ディレクトリの設定とツール読み込みを確認する。

## Final Validation

- [ ] 変更した JSON/TOML の構文、環境変数参照、モデルID・上限値、ドキュメントのリンクを検証し、`git diff --check` を通す。
- [x] `uv run --no-project python scripts/tests/test_dotfiles_links.py` を実行し、既存配置の回帰がなく、新規配置のリンク先とランタイムデータ分離が正しいことを確認する。
- [x] 一時 HOME の mise 環境で親設定を trust した後、対象ルート・複数階層下・対象外で `PI_CODING_AGENT_DIR` の解決を検証する。関係ない環境変数や秘密は出力しない。
- [ ] 実 HOME で対象リンクを検証する。通常の fish によるディレクトリ出入りで Pi の設定元が切り替わり、対象外で元に戻ることを確認する。Safehouse を含む既存起動経路で環境変数が維持されることも確認する。
- [ ] Pi の設定・リソース読み込みをルートと子ディレクトリから確認する。oMLX 2モデルが登録され、デフォルトが LFM、pi-subagents のツールと専用指示がないことを確認する。副作用のある不要な拡張実行やクラウド推論は行わない。
- [ ] oMLX が稼働済みならローカル2モデルの短い応答を確認する。未起動・未ロード・認証不足の場合は自動で設定変更せず、設定検証と実推論の未検証範囲を分けて報告する。
- [x] OpenCode のモデル制限と Code Mode 無効化がなくなり、MCP・既存全許可・共通指示リンクが保たれていることを差分で確認する。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
