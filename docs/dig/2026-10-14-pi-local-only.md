# dig log: ~/Dev/local 配下の Pi ローカルモデル環境

## 目的・前提・制約
- `~/Dev/local` とその配下で通常の `pi` を使い、oMLX の2モデルを利用する。対象外の Pi 設定は維持する。
- Pi 1.1.0 の `enabledModels` はモデル巡回・起動時選択のスコープであり、クラウド利用の禁止ではない。
- Pi のプロジェクト `.pi/settings.json` は起動ディレクトリ直下から読むため、親の設定を子へ継承する用途には使えない。
- 既存 fish は `mise activate fish` を使用する。mise による環境変数の切り替えを利用できる。

## 決定事項
- `~/Dev/local/mise.toml` で `PI_CODING_AGENT_DIR` を `~/Dev/local/.pi` に指定する。配下のどのサブディレクトリで起動しても同じ専用設定を参照する。`pi.fish` は変更しない。
  - 出典: Q1 の A、その後の「pi.fishを触らないで」「.piでいい」、mise 方式の説明に対する「その方式がいいです。それで進めて」。
- プロバイダーは `omlx`、URL は `http://127.0.0.1:8000/v1`、キーは環境変数 `OMLX_API_KEY` を参照する。秘密の値を保存・複製しない。
- モデルは LFM2.5-24B-A2B-MLX-4bit（context/output 131072/8192、デフォルト）と Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B（262144/81920）。
  - 出典: OpenCode と同じ2モデルを使う依頼と、その時点の設定。
- pi-subagents を読み込まない。その他の追加パッケージ、UI、共通指示、スキル、MCP は維持する。認証・履歴の保存先は分離する。
  - 出典: 元の無効化対象の指定と、通常設定をベースに pi-subagents のみ除外する[計画](../plans/2026-10-14-pi-local-only.md)への最終承認。
- `~/Dev/local/mise.toml` と `~/Dev/local/.pi` 全体は dotfiles で管理しない。配置済みリンクを標準 unapply して実ファイルに切り替える。ローカル専用 APPEND_SYSTEM.md には Subagents 節を含めず、通常環境の指示は変更しない。
  - 出典: レビュー後のユーザーの「~/Dev/local/.pi をdotfilesで管理しなくて良い」「~/Dev/local/mise.toml も管理の必要ない」。
- OpenCode はローカル LLM 用設定だけを戻す。oMLX 定義、既定モデル、provider 制限、execute deny、MCP の codemode=false を除去し、CUA・Context7・既存全許可・共通 AGENTS.md リンクは残す。
  - 出典: Q3 に対する A。
- 実装・配置・trust・検証まで行う。
  - 出典: 計画の最終確認に対する「ok」。

## 対象外
- クラウド推論の強制禁止。設定分離だけでは、共通環境からの API キーなどによるクラウド利用を阻止しないことを説明済みで、mise 方式が承認された。
- Pi 本体の改変、OS の通信遮断、既存認証の削除。
- oMLX の起動・停止、モデルのダウンロード。
- 他者による無関係な fish・Ghostty・flake.lock の変更。

## 撤回・置換済み
- 専用設定を `config/Dev/local/` からリンクする案は、すべて対象ディレクトリの実ファイルで管理する方式に置換。これに伴い専用配布のテストは残さず、環境・Pi 読み込みは作業中に実環境で検証する。
- 共有 APPEND_SYSTEM.md をリンクすると subagents 専用指示も入る問題を独立レビューで確認。通常環境の指示を移動する案は採用せず、管理外の専用本文にする。
- `pi.fish` の起動場所判定で切り替える案は、mise の環境変数切り替えに置換。
- `~/Dev/_sandbox/rename-video` だけを対象にする案は採用せず、`~/Dev/local` 配下を対象とする。
- `.pi-local` という専用名はユーザー希望により `.pi` に変更。
- 当初のクラウド利用の強制禁止は設定分離と区別した。標準 Extension API に全推論を拒否する共通フックは見当たらず、送信前イベントの例外も通知後に処理が続く。ランタイム改変は採用しない。
