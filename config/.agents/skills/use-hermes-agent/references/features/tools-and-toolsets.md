# ツールセット一覧・バックグラウンドプロセス管理

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/tools / https://hermes-agent.nousresearch.com/docs/reference/tools-reference

## ツールセット一覧

| ツールセット | 主要ツール | 説明 |
|------------|-----------|------|
| `web` | `web_search`, `web_extract`, `web_browse` | Web 検索・抽出・閲覧（v0.13.0 で split） |
| `terminal` | `terminal`, `process` | コマンド実行・プロセス管理 |
| `file` | `read_file`, `write_file`, `patch` | ファイル読み書き。post-write delta lint（v0.13.0）、LSP semantic diagnostics（v0.14.0）、`read_file` の compact 行番号 gutter（v0.16.0、~14% トークン削減） |
| `browser` | `browser_navigate`, `browser_snapshot`, `browser_vision`, `browser_console`, `browser_cdp` | ブラウザ自動化 |
| `vision` | `vision_analyze` | 画像分析 |
| `image_gen` | `image_generate` | 画像生成（FAL/Krea、pluggable） |
| `tts` | `text_to_speech` | テキスト音声変換 |
| `todo` | `todo` | タスク管理 |
| `memory` | `memory` | 永続メモリ |
| `session_search` | `session_search` | 過去セッション検索（v0.15.0 で 4,500× 高速化） |
| `skills` | `skills_list`, `skill_view`, `skill_manage` | スキル管理 |
| `cronjob` | `cronjob` | スケジュールタスク |
| `code_execution` | `execute_code` | Python コード実行 |
| `delegation` | `delegate_task` | サブエージェント委譲。`max_spawn_depth` 上限撤廃（v0.16.0） |
| `clarify` | `clarify` | ユーザーに確認（Telegram/Discord で native ボタン UI、v0.14.0） |
| `moa` | `send_message` | メッセージ送信 |
| `homeassistant` | `ha_list_entities`, `ha_get_state`, `ha_call_service`, `ha_list_services` | HA 制御 |
| `rl` | `rl_*` | RL トレーニング |
| `x_search` | `x_search` | X (Twitter) 検索（v0.14.0） |
| `video` | `video_analyze`, `video_generate` | 動画理解（v0.13.0）/ 動画生成（v0.14.0） |
| `computer_use` | `computer_use` | 仮想 PC 操作（cua-driver で non-Anthropic provider 対応、v0.14.0） |

## バックグラウンドプロセス管理

```python
terminal(command="pytest -v tests/", background=true)
# 返値: {"session_id": "proc_abc123", "pid": 12345}
# v0.15.0: background=true 時に警告が出る

process(action="list")       # 実行中プロセス一覧
process(action="poll", session_id="proc_abc123")   # ステータス確認
process(action="wait", session_id="proc_abc123")   # 完了待機
process(action="log", session_id="proc_abc123")    # 全出力表示
process(action="kill", session_id="proc_abc123")   # 終了
process(action="write", session_id="proc_abc123", data="y")  # 入力送信
```

## ファイル書込み後の検証（v0.13.0+）

- **post-write delta lint** — `write_file` + `patch` で Python/JSON/YAML/TOML をチェック（v0.13.0）
- **LSP semantic diagnostics on every write** — 実 language server を実行（v0.14.0）
- **per-turn file-mutation verifier footer** — 変更ファイルパスを集約（v0.14.0、v0.16.0 で neutralize 処理追加）
- **`patch`**: indent/CRLF preservation、per-file failure escalation（v0.15.0）
