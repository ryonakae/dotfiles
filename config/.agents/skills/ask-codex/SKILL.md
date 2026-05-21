---
name: ask-codex
description: OpenAI Codex に外部視点での調査・レビュー・セカンドオピニオンを依頼するスキル。「Codexに調査を依頼して」「Codexにレビューをお願いして」「Codexの意見も聞いて」「セカンドオピニオンが欲しい」「別のAI視点で確認して」といった依頼時に使用する。
---

# Codex セカンドオピニオン

## 概要

OpenAI Codex CLI の非対話モード（`codex exec`）で直接実行して、外部視点でのセカンドオピニオンを得る。`-C` でプロジェクトパスを渡せばファイルを直接参照させることもできる。

## 実行手順

Bash ツールで `codex exec` を実行する。必要に応じて事前に Read / Grep / Glob でコンテキストを収集し、プロンプトに含める。

### 推奨コマンド

```bash
# 推奨: 承認待ちなし + 読み取り専用
codex -a never exec -s read-only "質問内容"

# Agent Safehouse 内から実行する場合
/usr/local/bin/codex -a never exec -s danger-full-access "質問内容"

# パイプでコンテキストを渡す
echo "質問内容" | codex exec -

# 作業ディレクトリを指定してプロジェクトを参照させる
codex exec -C /path/to/project "このプロジェクトをレビューして"

# 読み取り専用サンドボックスで実行（セカンドオピニオン用途に推奨）
codex exec -s read-only "質問内容"

# モデルを指定
codex exec -m gpt-5.3-codex "質問内容"
```

### オプション

| オプション | 説明 |
| --- | --- |
| `exec` | 非対話サブコマンド（必須） |
| `-a` / `--ask-for-approval never` | 承認待ちなしで実行（`exec` の前に置く） |
| `-m` / `--model <model>` | モデル指定（例: `gpt-5.3-codex`） |
| `-C` / `--cd <dir>` | 作業ディレクトリ指定（プロジェクト参照用） |
| `-s` / `--sandbox read-only` | 読み取り専用サンドボックス（セカンドオピニオン用途に最適） |
| `-o` / `--output-last-message <file>` | 最後のメッセージをファイルに出力 |
| `--add-dir <dir>` | 追加ディレクトリへの書き込みアクセスを許可 |

## 利用タイミング

- 複数の実装方針で迷う時
- 重要な設計判断・アーキテクチャ選択の前
- コードレビューのダブルチェック
- ユーザーが「セカンドオピニオンが欲しい」とリクエストした時

## 非推奨ケース

- 単純で明確な実装タスク
- 既に方針が決まっており追加意見が不要な場合

## レポート形式

Codex の回答を受け取ったら、以下の形式でユーザーに報告する：

```markdown
# Codex セカンドオピニオン結果

## 質問内容
[Codex に投げた質問]

## 回答サマリー
[主要なポイントを箇条書き]

## 既存分析との比較
### 共通の指摘
- [両方が指摘した点]

### 独自の視点
- [Codex だけが指摘した点]

### 推奨アクション
[統合した上での具体的な推奨事項]
```

## 注意事項

- Codex は独立したプロセスとして実行される。現在の会話の文脈は引き継がれないため、必要な情報はすべてプロンプトに含めるか `-C` でプロジェクトパスを指定すること
- 機密情報（API キー、パスワード等）はプロンプトに含めないこと
- `-a` / `--ask-for-approval` はグローバルオプションなので、`codex exec` の後ろではなく `exec` の前に指定すること
- 通常テキスト出力では最終応答が主に表示される。必要に応じて `2>&1` で標準エラーも回収すること
- `stream disconnected before completion` が発生した場合は通信要因のため再実行すること

## Agent Safehouse 環境で使う時の注意

- Agent Safehouse 内で動いている場合、`-s read-only` は Codex 内部の `sandbox-exec` が外側 Safehouse とネストして `sandbox_apply: Operation not permitted` になることがある
- このエラーは対象ファイルの権限ではなく nested sandbox の制約として扱う
- すでに外側 Safehouse に守られている前提で、Agent Safehouse 内から呼ぶ時だけ `/usr/local/bin/codex -a never exec -s danger-full-access -C /path "質問内容"` のように Codex 内部 sandbox を無効化する
- fish の `codex` wrapper はさらに Safehouse をネストするため、Agent Safehouse 内からは使わない

- Codex の回答は参考情報として扱い、最終判断はプロジェクトのコンテキストを踏まえて行うこと
