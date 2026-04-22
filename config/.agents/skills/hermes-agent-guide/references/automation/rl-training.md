# RL トレーニング

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/rl-training

## 概要

Hermes Agent はコード実行環境を使った強化学習 (RL) トレーニングをサポート。エージェントの行動を評価・改善するためのツールセット `rl` を提供する。

## ツール

| ツール | 説明 |
|-------|------|
| `rl_create_env` | トレーニング環境の作成 |
| `rl_step` | 環境でアクションを実行 |
| `rl_reset` | 環境リセット |
| `rl_observe` | 現在の状態を観察 |
| `rl_reward` | 報酬関数の定義・評価 |

## ワークフロー

1. `rl_create_env` で環境定義
2. `rl_reset` で初期化
3. `rl_observe` → アクション決定 → `rl_step` のループ
4. `rl_reward` で結果評価
