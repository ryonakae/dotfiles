# 表示設定・スキン・ストリーミング

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#display-settings

## 表示設定

```yaml
display:
  tool_progress: all            # off | new | all | verbose
  tool_progress_command: false  # /verbose コマンド有効化
  streaming: false
  show_reasoning: false
  show_cost: false
  bell_on_complete: false
  compact: false
  resume_display: full          # full | minimal
  tool_preview_length: 0        # 0=無制限
  busy_input_mode: "interrupt"  # interrupt | queue | steer（v0.12.0）
  skin: default
  personality: "kawaii"
  language: en                  # en | zh | ja | de | es | fr | uk | tr ... (v0.13.0、16 ロケール v0.14.0、Desktop は v0.16.0 で zh 追加)
  timestamps: false             # v0.14.0
  theme: default                # default-large（18px）/ nous-blue / 等
```

## デフォルトインターフェース（v0.16.0）

```yaml
default_interface: cli          # cli | tui
```

`hermes` 起動時のデフォルト。`--cli` / `--tui` フラグで都度上書き。

## ストリーミング（ゲートウェイ）

```yaml
streaming:
  enabled: true
  transport: edit               # edit | off
  edit_interval: 0.3
  buffer_threshold: 40
  cursor: " ▉"
```
