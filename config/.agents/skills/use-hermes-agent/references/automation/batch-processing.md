# バッチ処理

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/batch-processing

## データセット形式

```jsonl
{"input": "この文章を要約してください: ...", "metadata": {"id": 1}}
{"input": "この文章を翻訳してください: ...", "metadata": {"id": 2}}
```

## 設定

```bash
hermes batch run \
  --input dataset.jsonl \
  --output results.jsonl \
  --prompt "以下の指示を処理してください" \
  --concurrency 5 \
  --checkpoint batch_checkpoint.json
```

## 出力形式

```jsonl
{"input": "...", "output": "...", "metadata": {"id": 1}, "status": "success", "tokens": 1234}
{"input": "...", "output": "...", "metadata": {"id": 2}, "status": "error", "error": "..."}
```

## チェックポイント・リジューム

- `--checkpoint` を指定すると進捗が自動保存される
- 中断後に同じコマンドを再実行すると未処理分から再開
- `--resume` フラグで明示的にリジューム

## 品質フィルタリング

```bash
hermes batch run \
  --input dataset.jsonl \
  --output results.jsonl \
  --filter-quality 0.7          # 品質スコア 0.7 未満を再処理
```
