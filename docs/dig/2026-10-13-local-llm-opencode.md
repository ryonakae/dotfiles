# dig log: LM Studio と OpenCode のローカル LLM 環境

## 目的・前提・制約
- LM Studio にローカル LLM を追加し、ローカル API サーバーを経由して OpenCode から利用する。
- dotfiles 管理は Homebrew のアプリ宣言と OpenCode の設定に限定する。
- 実機確認: OpenCode v2.0.25、Apple M6、メモリ32GB、LM Studio 0.4.26+4。lms は PATH にはないが ~/.lmstudio/bin/lms に存在する。
- lms ls --llm --json で既存モデルを確認: Foresee/Qwen3.8-9B-heretic-uncensored-4bit-MTPLX。約5.6GB、4bit、trainedForToolUse=true。登録情報に加え、ユーザーの通常端末から OpenCode の読み取り・書き込みを確認済み。
- nix/darwin/homebrew.nix に opencode と lm-studio の宣言がある。
- config/.config/opencode/opencode.json に権限設定とリモート Context7 MCP がある。
- config/.config/fish/config.fish に既存の未コミット変更があり、今回の作業では保持する。
- 実装着手後、OpenCode の v2 設定と LM Studio 専用ポリシーを反映した。追加のモデル取得は行わず、ユーザーが GUI でサーバーを起動した。検証経過は [計画](../plans/archived/2026-10-13-local-llm-opencode.md) に記録する。

## 決定事項
- 最初は既存の Foresee/Qwen3.8-9B-heretic-uncensored-4bit-MTPLX を使用し、接続とツール呼び出しを確認する。追加ダウンロードは行わず、品質に不満があればモデル変更を検討する。
  - 出典: Q3 に対してユーザーが A を選択。
- Homebrew で LM Studio / OpenCode を管理し、OpenCode の設定を dotfiles 管理する。LM Studio のモデル追加・サーバー起動・メモリ設定はアプリ側で扱う。
  - 出典: ユーザーが「brewでアプリ管理して、opencodeの設定が管理できればいいくらい」と範囲を指定。
- LLM の推論だけローカル専用にし、Context7 MCP・Web検索・パッケージ取得などの外部通信は許可する。クラウド LLM は利用しない。
  - 出典: Q1 に対してユーザーが A を選択。
- OpenCode はローカル LLM 専用にする。
  - 出典: ユーザーの初回依頼。
- 利用するローカル実行環境は LM Studio。
  - 出典: ユーザーの訂正・確認。

## 実装確認
- ユーザーは要件・計画と、公開 v1 スキーマの代替検証および既存 fish 変更を除く差分チェックを承認済み。
- OpenCode v2 は LM Studio 自動検出に対応。experimental.policies の provider.use で全 provider を deny した後 lmstudio のみ allow する設定を反映済み。standalone でクラウドモデルの選択拒否を確認済み。
- OpenCode 設定を Context7 と権限設定の意味を保って v2 形式へ移行済み。検出されたモデル ID を既定値へ設定し、応答とツール実行を確認済み。初回は表示用の行番号をコピーしたが、行番号を含めない指示で再実行し、実ファイルの完全一致を確認した。

## 対象外
- LM Studio 専用の起動・停止関数、常駐定義、モデル取得・読み込み・解放の自動化。
- LM Studio の内部設定、モデル本体、キャッシュ、履歴の Git 管理。

## 撤回・置換済み
- LM Studio の設定やモデル運用まで広く dotfiles 管理する提案は、ユーザーの範囲指定により取り下げた。Q2 の起動方式選択は dotfiles の設計事項としては不要。

## 参照
- https://opencode.ai/v2/docs/models
- https://opencode.ai/v2/docs/providers
- https://opencode.ai/v2/docs/policies
- https://opencode.ai/v2/docs/config
- https://lmstudio.ai/docs/developer/core/server
