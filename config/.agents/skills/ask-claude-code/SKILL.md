---
name: ask-claude-code
description: |
  Claude Code に外部視点での調査・レビュー・セカンドオピニオンを求めるスキル。コードレビュー、設計相談、アーキテクチャの相談、実装の妥当性検証、原因調査、仕様調査、代替案の提案、潜在的な問題の発見を行う。
  「Claude Codeに調査を依頼して」「Claude Codeにレビューをお願いして」「Claude Codeの意見も聞いて」「セカンドオピニオンが欲しい」「別のAI視点で確認して」といった依頼時に使用する。
---

# Claude Code セカンドオピニオン

## 概要

Claude Code CLI の非対話モード（`-p`）で直接実行して、外部視点でのセカンドオピニオンを得る。セカンドオピニオン用途では、不足情報を推測で補完しない。不足情報がある場合は通常テキストで確認質問を返し、その時点で終了する。

## 使い方

Bash ツールで `claude -p` を実行する。`AskUserQuestion` は無効化し、読み取り系ツールに限定する。必要に応じて事前に Read / Grep / Glob でコンテキストを収集し、プロンプトに含める。

### コマンド例

```bash
# 推奨: 非推測 + AskUserQuestion抑制 + ストリーミング表示
claude -p "質問内容" \
  --tools "Read,Grep,Glob" \
  --disallowedTools AskUserQuestion \
  --append-system-prompt "不足情報は推測で補わない。必要な確認事項は通常テキストで質問として返し、その時点で終了する。" \
  --output-format stream-json \
  --include-partial-messages \
  --verbose

# パイプでコンテキストを渡す
cat src/file.ts | claude -p "このコードをレビューして"

# モデルを指定
claude -p "質問内容" --model sonnet

# テキスト出力の簡易版
claude -p "質問内容" \
  --tools "Read,Grep,Glob" \
  --disallowedTools AskUserQuestion \
  --append-system-prompt "不足情報は推測で補わない。必要な確認事項は通常テキストで質問として返し、その時点で終了する。"

# 自動化で終了条件を強くしたい場合のみ
claude -p "質問内容" --max-turns 3
```

### 有用なオプション

| オプション | 説明 |
| --- | --- |
| `-p` / `--print` | 非対話モード（必須） |
| `--model <model>` | モデル指定（例: `haiku`, `sonnet`, `opus`） |
| `--tools <tools>` | 使用可能なツールを限定する（例: `"Read,Grep,Glob"`） |
| `--disallowedTools <tools>` | 使用禁止ツールを指定する（例: `AskUserQuestion`） |
| `--append-system-prompt <prompt>` | 既定システムプロンプトに追記する |
| `--output-format <format>` | 出力形式（`text`, `json`, `stream-json`） |
| `--include-partial-messages` | `stream-json` で部分出力を含める |
| `--verbose` | `stream-json` 利用時の詳細出力（この環境では併用が必要） |
| `--max-turns <n>` | ターン数を制限する（必要な場合のみ） |
| `--add-dir <dirs>` | 追加ディレクトリへのアクセスを許可 |

## いつ使うか

- 複数の実装方針で迷う時
- 重要な設計判断・アーキテクチャ選択の前
- コードレビューのダブルチェック
- ユーザーが「セカンドオピニオンが欲しい」とリクエストした時

## いつ使わないか

- 単純で明確な実装タスク
- 既に方針が決まっており追加意見が不要な場合

## 回答の分析と統合

Claude Code の回答を受け取ったら、以下の形式でユーザーに報告する：

```markdown
# Claude Code セカンドオピニオン結果

## 質問内容
[Claude Code に投げた質問]

## 回答サマリー
[主要なポイントを箇条書き]

## 既存分析との比較
### 共通の指摘
- [両方が指摘した点]

### 独自の視点
- [Claude Code だけが指摘した点]

### 推奨アクション
[統合した上での具体的な推奨事項]
```

## 注意事項

- Claude Code は独立したプロセスとして実行される。現在の会話の文脈は引き継がれないため、必要な情報はすべてプロンプトに含めること
- 機密情報（API キー、パスワード等）はプロンプトに含めないこと
- セカンドオピニオン用途では、不足情報を推測で補完しない。必要な場合は通常テキストで確認質問を返させること
- `AskUserQuestion` を許可すると外部実行側の都合で待ちに見えるケースがあるため、このスキルでは `--disallowedTools AskUserQuestion` を推奨する
- 進捗可視化が必要な場合は `--output-format stream-json --include-partial-messages --verbose` を使うこと
- Claude Code の回答は参考情報として扱い、最終判断はプロジェクトのコンテキストを踏まえて行うこと
