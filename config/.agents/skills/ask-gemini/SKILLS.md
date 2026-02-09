---
name: ask-gemini
description: Geminiに意見を聞く、セカンドオピニオンを求める。コードレビュー、設計相談、アーキテクチャの相談、別のAIの意見が欲しいときに使用。「Geminiに聞いて」「別の意見」「セカンドオピニオン」などのリクエストで起動。
allowed-tools: Bash, Read, Glob, Grep
---

# Ask Gemini - Geminiに意見を聞くスキル

このスキルはGemini MCP Toolを使って、別のAIの意見を取得します。Gemini MCP ToolはModel Context Protocol（MCP）サーバーで、ClaudeからGeminiの機能を直接利用できます。

## 前提条件

以下がインストールされている必要があります：

1. **Node.js** v16.0.0以上
2. **Google Gemini CLI** - [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)
3. **Gemini MCP Tool** - [jamubc/gemini-mcp-tool](https://github.com/jamubc/gemini-mcp-tool)

### セットアップ

```bash
# Gemini CLIのインストール
npm install -g @google/gemini-cli

# Claude CodeでのMCP設定（推奨）
claude mcp add gemini-cli -- npx -y gemini-mcp-tool

# または Claude Desktop設定ファイルに追加
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json
```

## 使い方

### 自然言語での質問（推奨）

Claudeは自動的にGeminiを使うべきタイミングを判断します：

```
- "Geminiを使ってこのコードを説明して"
- "Geminiに大規模なプロジェクトを分析してもらって"
- "Geminiに最新のニュースを検索してもらって"
```

### スラッシュコマンド

#### `/gemini-cli:analyze`

ファイル分析や質問を行う。`@`シンタックスでファイルを参照できます：

```
/gemini-cli:analyze @src/main.js このコードを説明して
/gemini-cli:analyze @src/*.ts セキュリティ問題を見つけて
/gemini-cli:analyze @. このディレクトリを要約して
/gemini-cli:analyze 認証の実装方法を教えて
```

#### `/gemini-cli:sandbox`

コードを安全な環境で実行：

```
/gemini-cli:sandbox Pythonでフィボナッチ数列を生成して実行
/gemini-cli:sandbox @script.py このスクリプトを安全にテストして
```

#### `/gemini-cli:ping`

接続テスト：

```
/gemini-cli:ping
/gemini-cli:ping "Hello from Gemini!"
```

#### `/gemini-cli:help`

ヘルプ情報を表示：

```
/gemini-cli:help
```

### ファイル参照の`@`シンタックス

- `@README.md` - 単一ファイル
- `@src/*.js` - ワイルドカード
- `@**/*.test.js` - 再帰的検索
- `@src/` - ディレクトリ全体
- `@.` - カレントディレクトリ

### モデルの選択

自然言語でモデルを指定できます：

```
"Gemini Flashを使って素早く分析して"
"Gemini Proで詳細に解析して"
```

利用可能なモデル：

- **gemini-2.5-pro** - 複雑な分析、大規模コードベース向け（デフォルト）
- **gemini-2.5-flash** - 素早いレビュー、シンプルな説明向け

## 実行手順

1. **質問内容を確認する**
   - コードレビュー、設計相談、デバッグなど目的を把握

2. **関連ファイルを収集する**（必要に応じて）
   - Readツールで対象ファイルを確認
   - パスを`@`シンタックスで参照可能にする

3. **適切な形式でGeminiに質問する**
   - 自然言語または`/gemini-cli:analyze`コマンドを使用
   - ファイル参照には`@`を使用

4. **Geminiの回答を取得・伝達**
   - Geminiからの回答をユーザーに伝える

5. **補足意見を追加**（必要に応じて）
   - Claudeとしての視点や追加のアドバイスを提供
   - 両者の意見が異なる場合は、両方の視点を提示

## コードレビューの例

```
/gemini-cli:analyze @src/api/handler.js 以下の観点でレビューしてください：
- セキュリティ問題
- パフォーマンスの懸念
- コードスタイルの一貫性
- エラーハンドリングの不足
```

## 設計・アーキテクチャ相談の例

```
/gemini-cli:analyze @package.json @src/**/*.js このプロジェクトのアーキテクチャを分析して、以下を評価してください：

考慮すべき点：
- スケーラビリティ
- 保守性
- パフォーマンス
- セキュリティ
```

## デバッグの例

```
/gemini-cli:analyze @logs/error.log @src/api/handler.js
なぜ"undefined is not a function"エラーが発生しているか説明して
```

## 注意事項

- Gemini MCP Toolは自動的にClaudeと統合されているので、通常はツールの存在を意識する必要はありません
- Geminiは大規模なコンテキストウィンドウ（2M tokens for Pro, 1M for Flash）を持つため、プロジェクト全体の分析が可能です
- Sandboxモードを使用すると、コードを安全に実行・テストできます
- Geminiの提案を鵜呑みにせず、その根拠や理由を理解してください
- Geminiの回答とClaudeの意見が異なる場合、両方の視点を比較検討してください
- 最終的な判断は、両者の意見を総合的に評価した上で、自分で下してください

## トラブルシューティング

### "Command not found: gemini"

Gemini CLIがインストールされていません：

```bash
npm install -g @google/gemini-cli
gemini --version  # 確認
```

### "MCP server not responding"

1. 設定ファイルのJSONシンタックスを確認
2. Claude Desktop/Codeを完全に再起動
3. `/mcp`コマンドでgemini-cliが有効か確認

### より詳しい情報

- [公式ドキュメント](https://jamubc.github.io/gemini-mcp-tool/)
- [GitHubリポジトリ](https://github.com/jamubc/gemini-mcp-tool)
- [トラブルシューティングガイド](https://jamubc.github.io/gemini-mcp-tool/resources/troubleshooting)
