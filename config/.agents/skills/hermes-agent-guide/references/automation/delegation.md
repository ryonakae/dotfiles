# サブエージェント委譲

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation

## 単一タスク委譲

```python
delegate_task(
    task="このプロジェクトのテストを全て実行し、失敗があれば原因を分析",
    context="Python 3.11 プロジェクト、pytest 使用",
    toolsets=["terminal", "file", "web"]    # 使用許可するツールセット
)
```

## 並列タスク

最大 3 つの並列サブエージェントを起動可能:

```python
delegate_task(
    tasks=[
        {"task": "フロントエンドのテスト実行", "toolsets": ["terminal", "file"]},
        {"task": "バックエンドのテスト実行", "toolsets": ["terminal", "file"]},
        {"task": "依存関係の脆弱性チェック", "toolsets": ["terminal", "web"]}
    ]
)
```

## コンテキストルール

- サブエージェントは親の会話履歴を引き継がない
- `context` パラメータで必要な情報を明示的に渡す
- サブエージェントは完了後に結果を親に返す
- サブエージェントの出力はトークン制限あり

## ブロック対象ツールセット

サブエージェントでは以下のツールセットが使用不可:

- `delegation` (再帰的委譲の防止)
- `clarify` (ユーザーに質問不可)
- `moa` (メッセージ送信不可)

## 深度制限

デフォルトの最大委譲深度は 1（サブエージェントからさらに委譲不可）。`config.yaml` で変更可能:

```yaml
agent:
  max_delegation_depth: 2
```

## モデルオーバーライド

```python
delegate_task(
    task="コスト効率の良いモデルで簡単なタスクを処理",
    model="anthropic/claude-sonnet-4-20250514"     # サブエージェント用モデル指定
)
```

## delegate_task vs execute_code

| 用途 | 推奨ツール |
|------|-----------|
| 調査・分析・複数ステップの判断が必要 | `delegate_task` |
| 定型処理・データ変換・計算 | `execute_code` |
| ファイル操作を伴う作業 | `delegate_task` |
| 外部 API 呼び出しのみ | `execute_code` |
