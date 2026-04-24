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
hermes cron list                                    # ジョブ一覧
hermes cron create                                  # インタラクティブ作成ウィザード
hermes cron edit "daily-report"                     # ジョブ編集
hermes cron remove "daily-report"                   # 削除
hermes cron run "daily-report"                      # 手動実行
hermes cron pause "daily-report"                    # 一時停止
hermes cron resume "daily-report"                   # 再開
hermes cron status                                  # スケジューラ状態
hermes cron tick                                    # 手動で 1 サイクル実行（デバッグ用）
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

## wakeAgent ゲート (v0.11.0)

ジョブに事前実行スクリプトを付け、その exit code でエージェントを起動するかどうかを判断できる。条件付き発火に有効（コスト削減）。

```yaml
name: alert-on-error
schedule: "*/5 * * * *"
pre_script: "~/scripts/check-errors.sh"     # exit 0 = wake agent / 非ゼロ = skip
prompt: "直近 5 分間のエラーを要約してください"
```

`HERMES_CRON_SCRIPT_TIMEOUT` でスクリプトタイムアウト秒を制御（デフォルト 120）。

## per-job enabled_toolsets (v0.11.0)

ジョブ単位でツールセットを限定し、トークン消費を抑える。

```yaml
name: pricing-update
schedule: "@daily"
prompt: "競合の価格を取得して pricing.csv を更新"
enabled_toolsets: [web, file]                # terminal, browser 等は無効化
```

## プログラマティック管理

`cronjob` ツールでエージェント会話中にスケジュールを管理可能:

```python
cronjob(action="list")
cronjob(action="create", name="cleanup", schedule="0 3 * * *", prompt="一時ファイルを削除")
cronjob(action="delete", name="cleanup")
```
