# コード実行

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/code-execution

## hermes_tools モジュール

`execute_code` 内で使用可能な Python モジュール:

```python
from hermes_tools import web_search, web_extract, read_file, patch_file
from hermes_tools import terminal, memory, todo, delegate_task
from hermes_tools import vision_analyze, image_generate, text_to_speech
```

## 実行モード

```yaml
agent:
  code_execution:
    mode: "project"             # project: プロジェクトディレクトリで実行
                                # strict: 隔離された一時ディレクトリで実行
```

## リソース制限

```yaml
agent:
  code_execution:
    timeout: 300                # 実行タイムアウト（秒）
    max_memory: 512             # メモリ上限 (MB)
    max_output: 65536           # 出力サイズ上限（バイト）
```

## セキュリティモデル

- `strict` モード: ネットワークアクセス制限、ファイルシステムは一時ディレクトリのみ
- `project` モード: プロジェクトディレクトリにアクセス可能、ネットワーク利用可
- いずれのモードでもシステムコマンドの直接実行は不可（`terminal` ツールを使用）
