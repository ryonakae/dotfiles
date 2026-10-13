# OpenCode の LM Studio 専用設定 Implementation Plan

## Requirements

- OpenCode の LLM 推論先をローカルの LM Studio だけに限定する。クラウド LLM へフォールバックさせず、Context7 MCP などの外部ツールは引き続き利用可能にする。
- 初期モデルは追加済みの `Foresee/Qwen3.8-9B-heretic-uncensored-4bit-MTPLX`。モデルの追加ダウンロードは行わない。
- dotfiles 管理は既存の Homebrew アプリ宣言と OpenCode 設定に限定する。LM Studio のモデル読み込み・サーバー起動は GUI で行い、専用関数・常駐設定・モデル運用の自動化は追加しない。
- 既存の権限設定の意味、Context7 の環境変数参照、Safehouse 起動経路を維持する。既存の `config/.config/fish/config.fish` の変更には触れない。
- [議論の記録](../dig/2026-10-13-local-llm-opencode.md)を参照。要件・計画と下記の検証条件変更はユーザー承認済み。

## Implementation Decisions

- 実機確認済み: OpenCode v2.0.25、LM Studio 0.4.26+4、Apple M6 / 32GB。アプリは既に Homebrew 宣言・導入済みなので、Nix と mise の変更・再適用は不要。
- `config/.config/opencode/opencode.json` を v2 形式へ合わせる。`experimental.policies` の `provider.use` で `*` を deny し、その後 `lmstudio` のみ allow する。単に既定モデルを指定するだけではクラウド利用防止にならない。
- LM Studio の接続先は `http://127.0.0.1:1234/v1`。組み込みのモデル検出を使い、既定モデルの ID は OpenCode が実際に検出する値で確定する。ディスク上の名前から推測しない。
- v1 の `permission` と MCP 定義は、v2 の `permissions` と `mcp.servers` へ意味を保って移行する。実装前に公式スキーマと MCP の現行仕様を確認する。認証情報の値を読んだり出力したりしない。
- ファイルは既存の直接リンク配置を維持する。設定編集は実環境に即時反映され得るため編集前に知らせる。設定のためのサービス再起動や配布処理は実行しない。
- LM Studio の GUI 操作はユーザーに案内する。未起動ならユーザーの起動を待って接続確認し、未検証を成功として扱わない。

## Tasks

- Review base: `8cd6abb3ba4ce83dabc9802293b64911223d842a`。開始時点は `master` と `origin/master` の ahead/behind が 0/0、staged 変更なし。

- [x] ローカル専用の OpenCode 設定: `config/.config/opencode/opencode.json` に上記設定を反映する。
  - 変更前に JSON 構文と現行スキーマとの互換性を確認する。モデル ID の確定には LM Studio の起動後の検出結果を使う。
  - 全 provider 禁止 → LM Studio のみ許可の順序、既存 MCP と権限の維持を差分で確認する。
  - 反映済み: v2 の permissions / mcp.servers、localhost endpoint、provider.use ポリシー。JSON 構文と旧設定との比較で Context7 定義・権限の維持を確認済み。ユーザーの GUI 起動後、通常の `opencode models` で検出した `lmstudio/qwen3.8-9b-heretic-uncensored-mtplx` を既定 model に設定し、`opencode reload` で反映済み。
- [x] 利用手順: `docs/apps.md` に LM Studio / OpenCode の項目を追加する。
  - GUI で既存モデルを読み込み、localhost のサーバーを起動し、OpenCode でモデルを確認して会話する手順を簡潔に記す。
  - サーバー未起動・モデル未検出時の確認先を示す。自動起動やモデル設定の管理機構は追加しない。
  - GUI 起動、モデル選択、設定再読み込み、接続失敗時の確認手順を追記済み。ユーザーの画面と実機での応答・ツール実行で確認済み。

## Final Validation

- [x] JSON 構文: `uv run --no-project python -m json.tool config/.config/opencode/opencode.json` → 正常終了。公開スキーマが v1 のため、v2 公式ドキュメントと実機の設定解釈・動作確認による代替をユーザー承認済み。
- [x] 実機設定の解釈: ヘルプで確認した `opencode debug config` の利用方法で設定ソースを確認し、秘密値を出力しない範囲で設定・ポリシー警告を確認する。自動検出完了後の `opencode models` → 利用可能モデルが LM Studio に限定され、既存モデルが検出される。設定表示だけでポリシー有効性を確認済みとしない。
- [x] クラウド利用禁止: ヘルプで構文を確認した明示モデル指定でクラウドモデルを選択しても、推論リクエストを送らず利用不可となることを確認する。確認が安全に実施できない場合は実行せず、理由と未検証範囲を記録する。
- [x] 接続・ツール実行: ユーザーが LM Studio を起動後、通常の Safehouse 経由の OpenCode で短い応答と一時 fixture の読み取り・編集を確認する。モデルの登録情報 `trainedForToolUse=true` だけを成功根拠にしない。実プロジェクトの編集や秘密の読み取りは依頼しない。
- [x] 回帰・範囲: Context7 定義と環境変数参照、既存権限の意味が維持されている。LM Studio 内部設定・Nix・mise・fish・Safehouse を変更していない。
- [x] 文書と差分: リンク・掲載操作と実際の挙動を照合し、今回の変更ファイルに限定した `git diff --check` が成功する。新規文書も差分確認対象に含める。既存 fish 変更による全体チェックの失敗を対象外にすることをユーザー承認済み。

## 検証経過

- `uv run --no-project python -m json.tool config/.config/opencode/opencode.json` 成功。旧 MCP 定義との一致、権限の意味、ポリシー順序、接続先を Python の比較で確認済み。
- `opencode models --standalone` は正常終了、モデル表示なし。LM Studio の `http://127.0.0.1:1234/api/v1/models` は curl exit 7（接続不可）。サーバー・モデルは起動していない。
- `opencode run --standalone --model openai/gpt-5.2 'Reply only OK.'` は exit 1、`Model unavailable: openai/gpt-5.2`。推論開始前のモデル解決で拒否された。
- `opencode debug config` は変更後も旧設定の正規化結果を返した。通常のバックグラウンドサーバーの再読み込みと設定再確認が必要。サービス再起動はしていない。
- 公開 `https://opencode.ai/config.json` は取得できたが、root の Config は v1 形式（permission / provider / mcp 直下）で、v2 docs と不一致。`https://opencode.ai/v2/config.json` は 404。v2 スキーマ検証は実施できず、ユーザー承認により v2 公式ドキュメントと実機の設定解釈・動作確認で代替した。
- 対象2ファイルの `git diff --check` は成功。全体チェックは既存の `config/.config/fish/config.fish:74: new blank line at EOF` で失敗。この他者変更は修正しない。
- ユーザーが GUI でサーバーを起動済み。`/api/v1/models` の既存モデルを確認した。通常の `opencode models` で `lmstudio/qwen3.8-9b-heretic-uncensored-mtplx` を検出し、既定値へ追加した。
- `opencode reload` 後に `opencode debug config` で model / providers / policies / permissions / mcp の正規化結果を確認。モデル一覧が LM Studio のみであること、`opencode run --model opencode/big-pickle 'Reply only OK.'` が exit 1 / Model unavailable となることを確認。
- 自動検出の完了前に `opencode models --standalone` が空で終了する挙動と、reload 直後の一覧に一時的に OpenCode のモデルが表示される挙動を観測した。安定後の通常一覧と明示選択拒否は確認済み。文書では通常の `opencode models` を使い、起動直後は検出完了後に再確認する。
- Safehouse wrapper 経由の smoke test は exit 71 / `sandbox-exec: sandbox_apply: Operation not permitted`。現在の sandbox 内からの二重起動で失敗し、LLM へのリクエストには到達していない。回避・再試行はしていない。fixture は `/tmp/opencode-local-smoke.skBqPe`、ログは同ディレクトリの `run.log`。output.txt は未作成。
- ユーザーの通常 fish 端末から smoke test を実行し、既定の Qwen モデルによる Read / Write / DONE 応答を確認。ただし実ファイル比較は失敗: input.txt は `local-smoke-7319\n`、output.txt は `1: local-smoke-7319\n`。読み取りツールの表示用行番号を本文としてコピーした可能性があり、完全一致の検証は未通過。出力をエージェント側で修正して成功扱いにはしない。
- 行番号を本文に含めない明示指示でユーザーが再実行済み。実ファイルを比較し、input.txt と output.txt が末尾改行を含め17 bytesで完全一致した。通常の fish / Safehouse 経由で、既定ローカルモデルの応答・読み取り・書き込みを確認済み。曖昧な読み取り表示を本文と誤認するモデルの傾向は残る。
- 最新設定の JSON 構文、既定 model、変更した設定・利用文書の `git diff --check` は成功。
- 2026-10-13: 上記のスキーマ検証代替・対象限定の差分チェックをユーザーが承認し、独立レビュー・commit・push の続行を承認した。
- 残工程: local commit、独立レビュー、計画アーカイブ、push。

## References

- [OpenCode v2 config](https://opencode.ai/v2/docs/config)
- [OpenCode v2 policies](https://opencode.ai/v2/docs/policies)
- [OpenCode v2 models](https://opencode.ai/v2/docs/models)
- [OpenCode v2 permissions](https://opencode.ai/v2/docs/permissions)
- [LM Studio local server](https://lmstudio.ai/docs/developer/core/server)

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
