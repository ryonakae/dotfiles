# ntfy 統合

> v0.15.0 で 23 番目のプラットフォームとして追加（plugin 経由）。

## 概要

[ntfy.sh](https://ntfy.sh) を使った push 通知。アカウント登録不要で「topic 名」を共有するだけで通知が届く。1 方向通知（hermes → mobile / desktop）に特化。

## 前提条件

- ntfy.sh の public インスタンス、または self-hosted ntfy server
- ntfy アプリ（iOS / Android / Web / CLI）

## `.env`

```bash
# 公開 ntfy.sh 利用時はトークン不要
NTFY_BASE_URL=https://ntfy.sh
NTFY_TOPIC=hermes-<random-suffix>      # 推測されにくい topic 名を使う
NTFY_AUTH_TOKEN=                       # self-hosted で auth 有効化時のみ
```

## `config.yaml`

```yaml
platforms:
  ntfy:
    enabled: true
    home_channel: "hermes-<random-suffix>"
    streaming: false
```

## メッセージ送信パターン

```bash
hermes send ntfy <topic> "デプロイ完了"
```

cron から定期通知:

```yaml
# ~/.hermes/cron/morning-summary.yaml
schedule: "0 8 * * *"
prompt: "今日のスケジュール要約"
delivery:
  platform: ntfy
  target: hermes-<random-suffix>
```

## アクセス制御

- ntfy.sh public instance では「topic 名 = アクセス権」。**推測されにくい長い topic 名を使う**こと
- self-hosted ntfy server に切替して ACL / auth で保護するのが安全
- 機密情報はメッセージ本文に書かない

## 注意事項

- 1 方向通知のみ。inbound（ntfy → hermes）は未サポート
- v0.15.0 で plugin として実装（コアからは分離）
