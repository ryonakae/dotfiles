# イベントフック

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks

## Gateway フック

`~/.hermes/skills/<skill>/HOOK.yaml` + `handler.py` でイベント駆動処理を定義:

```yaml
# HOOK.yaml
name: auto-translate
events:
  - message_received
  - message_sent
platforms:
  - telegram
  - discord
```

```python
# handler.py
async def handle(event, context):
    if event.type == "message_received":
        # メッセージ受信時の処理
        return {"action": "prepend_prompt", "content": "翻訳して: "}
    return None
```

## 利用可能なイベント

| イベント | タイミング |
|---------|-----------|
| `message_received` | メッセージ受信時 |
| `message_sent` | メッセージ送信時 |
| `session_start` | セッション開始時 |
| `session_end` | セッション終了時 |
| `tool_call` | ツール呼び出し時 |
| `error` | エラー発生時 |
| `cron_trigger` | cron タスク発火時 |

## Shell hooks (v0.11.0)

Python プラグインを書かなくても、シェルスクリプトを直接ライフサイクルフックとして登録できる。

```yaml
# ~/.hermes/config.yaml
hooks:
  shell:
    - event: pre_tool_call
      command: "/usr/local/bin/audit-tool.sh"
      env:
        - HERMES_TOOL_NAME      # フック側に渡される環境変数
    - event: post_tool_call
      command: "logger -t hermes 'tool finished'"
    - event: on_session_start
      command: "~/scripts/notify-session.sh"
```

スクリプトは標準入出力で JSON を授受する。非ゼロ終了で `pre_tool_call` を veto できる。

## プラグインフック

```python
# ~/.hermes/plugins/my_plugin/plugin.py
from hermes.plugin import HermesPlugin, hook

class MyPlugin(HermesPlugin):
    name = "my_plugin"

    @hook("pre_tool_call")
    async def before_tool(self, tool_name, tool_input):
        # ツール呼び出し前の処理
        return tool_input  # 変更可能

    @hook("post_tool_call")
    async def after_tool(self, tool_name, tool_input, tool_output):
        # ツール呼び出し後の処理
        return tool_output

    @hook("pre_llm_call")
    async def before_llm(self, messages):
        # LLM 呼び出し前にメッセージを加工
        return messages

    @hook("post_llm_call")
    async def after_llm(self, response):
        # LLM レスポンス後の処理
        return response

    @hook("session_start")
    async def on_session_start(self, session):
        pass

    @hook("session_end")
    async def on_session_end(self, session):
        pass
```
