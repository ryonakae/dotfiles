# ツールセット一覧・バックグラウンドプロセス管理

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/tools / https://hermes-agent.nousresearch.com/docs/reference/tools-reference

## ツールセット一覧

| ツールセット | 主要ツール | 説明 |
|------------|-----------|------|
| `web` | `web_search`, `web_extract` | Web 検索・ページ抽出 |
| `terminal` | `terminal`, `process` | コマンド実行・プロセス管理 |
| `file` | `read_file`, `patch` | ファイル読み書き |
| `browser` | `browser_navigate`, `browser_snapshot`, `browser_vision` | ブラウザ自動化 |
| `vision` | `vision_analyze` | 画像分析 |
| `image_gen` | `image_generate` | 画像生成（FAL.ai） |
| `tts` | `text_to_speech` | テキスト音声変換 |
| `todo` | `todo` | タスク管理 |
| `memory` | `memory` | 永続メモリ |
| `session_search` | `session_search` | 過去セッション検索 |
| `skills` | `skills_list`, `skill_view`, `skill_manage` | スキル管理 |
| `cronjob` | `cronjob` | スケジュールタスク |
| `code_execution` | `execute_code` | Python コード実行 |
| `delegation` | `delegate_task` | サブエージェント委譲（最大3並列） |
| `clarify` | `clarify` | ユーザーに確認 |
| `moa` | `send_message` | メッセージ送信 |
| `homeassistant` | `ha_list_entities`, `ha_get_state`, `ha_call_service`, `ha_list_services` | HA 制御 |
| `rl` | `rl_*` | RL トレーニング |

## バックグラウンドプロセス管理

```python
terminal(command="pytest -v tests/", background=true)
# 返値: {"session_id": "proc_abc123", "pid": 12345}

process(action="list")       # 実行中プロセス一覧
process(action="poll", session_id="proc_abc123")   # ステータス確認
process(action="wait", session_id="proc_abc123")   # 完了待機
process(action="log", session_id="proc_abc123")    # 全出力表示
process(action="kill", session_id="proc_abc123")   # 終了
process(action="write", session_id="proc_abc123", data="y")  # 入力送信
```
