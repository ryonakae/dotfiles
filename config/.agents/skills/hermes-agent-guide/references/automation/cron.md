# Cron / スケジュールタスク

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

## スケジュール形式

```
# 標準 cron 式 (分 時 日 月 曜日)
0 9 * * *          # 毎日 9:00
*/30 * * * *       # 30分ごと
0 9 * * 1-5        # 平日 9:00

# プリセット
@hourly            # 毎時
@daily             # 毎日 0:00
@weekly            # 毎週日曜 0:00
@monthly           # 毎月1日 0:00

# 間隔指定
@every 15m         # 15分ごと
@every 2h          # 2時間ごと
```

## CLI 管理

```bash
hermes cron list
hermes cron add "daily-report" --schedule "0 9 * * *" --prompt "日次レポートを作成"
hermes cron remove "daily-report"
hermes cron run "daily-report"     # 手動実行
hermes cron enable "daily-report"
hermes cron disable "daily-report"
```

## スキルの添付

```yaml
# ~/.hermes/cron/daily-report.yaml
name: daily-report
schedule: "0 9 * * *"
prompt: "日次レポートを作成してください"
skill: "report-generator"         # スキルを添付
delivery:
  platform: telegram              # 結果の送信先
  channel: "-100123456789"
  silent: false                   # true: プラットフォームへの送信を抑制
```

## [SILENT] 抑制

プロンプトに `[SILENT]` を含めると、タスク実行結果をプラットフォームに送信しない。内部処理やファイル更新のみ行うタスクに有用。

## プログラマティック管理

`cronjob` ツールでエージェント会話中にスケジュールを管理可能:

```python
cronjob(action="list")
cronjob(action="create", name="cleanup", schedule="0 3 * * *", prompt="一時ファイルを削除")
cronjob(action="delete", name="cleanup")
```
