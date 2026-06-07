# Open WebUI

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui

API サーバーとして統合。Chat Completions API / Responses API に対応。

## セットアップ

1. `hermes acp serve` で API サーバーを起動
2. Open WebUI の設定で Hermes の API エンドポイントを登録
3. Docker 環境では Hermes コンテナのネットワークを Open WebUI と共有

## 機能

- マルチユーザープロファイル対応
- Admin UI からの設定管理
- Chat Completions API と Responses API の両方をサポート
