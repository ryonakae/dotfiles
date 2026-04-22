# メモリ設定・コンテキスト圧縮・ファイル読み取り制限

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#memory-configuration

## メモリ設定

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200       # ~800 トークン
  user_char_limit: 1375         # ~500 トークン
  provider: ""                  # 空=ビルトイン, honcho | openviking | mem0 等
```

## コンテキスト圧縮

```yaml
compression:
  enabled: true
  threshold: 0.50               # コンテキストの 50% で圧縮
  target_ratio: 0.20
  protect_last_n: 20

auxiliary:
  compression:
    model: "google/gemini-3-flash-preview"
    provider: "auto"
```

## ファイル読み取り制限

```yaml
file_read_max_chars: 100000     # デフォルト ~25-35K トークン
```
