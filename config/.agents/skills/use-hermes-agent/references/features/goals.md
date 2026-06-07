# `/goal` / `/subgoal` / `/undo` — 永続目標と取消

## 概要

| コマンド | 導入 | 用途 |
|---------|------|-----|
| `/goal <description>` | v0.13.0 | クロスターン永続目標を登録（Ralph loop） |
| `/subgoal <text>` | v0.14.0 | active `/goal` に criteria 追加 |
| `/undo [N]` | v0.16.0 | 過去 N ターンを取り消し |

## `/goal` — Ralph loop

```
/goal アプリのパフォーマンスを 30% 改善するまで、計測→ボトルネック特定→修正→検証 を繰り返す
```

ターンをまたいで永続化される first-class primitive。各ターン開始時に goal が再投入される。goal が満たされた、または `/goal clear` で明示終了するまで継続。

### 動作

1. `/goal` で目標を登録 → セッション状態に永続化
2. 通常通り会話・ツール実行を進める
3. 各ターンの先頭で「現在の目標」がコンテキストに injection される
4. エージェントが目標達成と判断すると `goal_complete` を発火、または手動で `/goal clear`

## `/subgoal` — criteria 追加

active `/goal` に対して追加 criteria を加える:

```
/subgoal データベースクエリの p95 を 200ms 以下にする
/subgoal バンドルサイズを 500KB 以下にする
```

サブゴールも goal と同様にターン横断で残る。

## `/undo [N]`

```
/undo            # 直前のメッセージを 1 つ取消
/undo 5          # 過去 5 ターン分を取消
```

v0.16.0 で N 指定が可能になった。`/retry` とは異なり、エージェントの応答だけでなく自分のメッセージも含めて巻き戻す。

## Kanban との連携（v0.16.0）

```yaml
kanban:
  goal_mode: true       # card を `/goal` loop で実行
```

Kanban の card を 1 つの goal loop として実行できる。長時間タスク（migrate、refactor、debug 等）の自走に向く。

## 注意事項

- goal がコンテキストの top に常駐するので、長い goal description は token 消費が増える
- `/undo` は agent 出力した tool call の副作用（書き込んだファイル等）はロールバックしない。`/rollback` のチェックポイント（v0.13.0 で書き直し）を併用する
