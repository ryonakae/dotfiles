# マルチエージェント Kanban

> v0.13.0 「The Tenacity Release」で本格導入、v0.15.0 「The Velocity Release」でプラットフォーム化（104 PRs）。

## 概要

Durable な Kanban ボードで複数エージェントの並列タスク実行を管理する。heartbeat / reclaim / zombie 検出 / 未完了終了の自動ブロック / per-task retries / hallucination 回復ゲートを備え、1 install で多 kanban 対応。

v0.15.0 で `hermes kanban swarm` による orchestrator auto-decomposition、worktree per task、scheduled tasks、claim TTL、retry fingerprinting、stale-task detection、respawn guards、drag-to-delete を追加。

## 基本概念

| 概念 | 説明 |
|-----|-----|
| Board | Kanban ボード本体。プロジェクトごと/profile ごとに分離可能 |
| Card | 1 タスク。担当エージェント・モデル override・スキル指定・worktree 設定を持つ |
| Lane | `todo` → `ready` → `in_progress` → `verify` → `done` などのレーン |
| Heartbeat | 担当エージェントの生存確認 |
| Reclaim | stale heartbeat の card を別エージェントに再割当 |
| Swarm | root + parallel workers + verifier + synthesizer + blackboard で構成される自動グラフ |

## CLI

```bash
hermes kanban list [--sort]
hermes kanban swarm                      # Swarm v1 グラフ作成（v0.15.0）
hermes kanban promote [--ids id1,id2]    # 手動 todo → ready（v0.15.0）
hermes kanban archive [--rm]             # アーカイブ / hard-delete
```

セッション内では `/kanban` で開く。

## 設定例

```yaml
kanban:
  enabled: true
  notification_sources: ["telegram", "slack"]   # クロスプロファイル通知
  auto_promote_children: false
  max_in_progress: 5                            # 並列実行上限
  claim_ttl: 600                                # stale-task 検出（秒）
  default_assignee: "agent-a"                   # v0.16.0
  goal_mode: false                              # card を `/goal` loop で実行（v0.16.0）
```

## Swarm パターン（v0.15.0）

`hermes kanban swarm` は以下のグラフを自動生成:

```
root
  ├─ worker A ┐
  ├─ worker B ┼─→ verifier ─→ synthesizer
  └─ worker C ┘
                  ↕
              blackboard
```

- **root**: タスクを decompose
- **workers**: 並列実行（worktree 隔離オプション）
- **verifier**: hallucination 回復ゲート
- **synthesizer**: 結果統合
- **blackboard**: workers が情報共有する shared scratchpad

## トラブルシューティング

| 症状 | 対処 |
|-----|-----|
| Stale task が増える | `claim_ttl` を短く、`hermes kanban list --sort` で確認 |
| Worker が同じ retry を繰り返す | retry fingerprinting で検出されない場合は手動 `archive` |
| 並列実行で衝突する | `worktree` オプションを有効化、`max_in_progress` を下げる |
| ボードが見えない | `kanban.enabled: true` と `/kanban` で開く |
