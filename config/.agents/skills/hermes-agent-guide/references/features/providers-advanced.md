# Tool Gateway・プロバイダールーティング・フォールバック・クレデンシャルプール

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/provider-routing / https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers / https://hermes-agent.nousresearch.com/docs/user-guide/features/credential-pools

## Tool Gateway (Nous Portal)

Nous の有料サブスクリプション機能。Web 検索、画像生成、TTS、ブラウザを個別の API キーなしで利用できる。

### 設定

各ツールセットの設定で `use_gateway: true` を指定:

```yaml
web:
  use_gateway: true
image_gen:
  use_gateway: true
tts:
  use_gateway: true
browser:
  use_gateway: true
```

有効化は `hermes tools` または `hermes model` から設定可能。`hermes status` で現在の状態を確認。

## プロバイダールーティング

OpenRouter 利用時のみ有効。リクエストのルーティング戦略を制御する。

```yaml
provider_routing:
  sort: "price"                 # price / throughput / latency
  only: ["anthropic", "openai"] # ホワイトリスト
  ignore: ["together"]          # ブラックリスト
  order: ["anthropic"]          # 優先順位
  require_parameters: true
  data_collection: "deny"
```

## フォールバックプロバイダー

3 層のフォールバック構成: クレデンシャルプール → プライマリフォールバック → 補助フォールバック。

HTTP 429, 500, 502, 503, 401, 403, 404 エラー時にトリガー。セッション中のフォールバックはワンショット（1回のみ）。補助タスク（委譲等）は独立した自動検出チェーンを持つ。

```yaml
fallback_model:
  provider: "openrouter"
  model: "anthropic/claude-sonnet-4"
```

## クレデンシャルプール

同一プロバイダーに対して複数の API キーを管理し、レート制限を回避する。

### 管理コマンド

```bash
hermes auth add        # API キー追加
hermes auth list       # 登録済みキー一覧
hermes auth remove     # キー削除
hermes auth reset      # 使用統計リセット
```

### ローテーション戦略

```yaml
credential_pool_strategies:
  openai: "round_robin"       # fill_first (デフォルト) / round_robin / least_used / random
```

キーは `~/.hermes/auth.json` に保存される。
