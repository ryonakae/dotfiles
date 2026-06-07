# セキュリティモデル統合ガイド

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/security / SECURITY.md

## 多層防御アーキテクチャ

| 層 | 役割 | 主な実装 |
|----|------|---------|
| 1. ユーザー認可 | 誰がエージェントに話しかけられるか | `*_ALLOWED_USERS`, `GATEWAY_ALLOWED_USERS`, `allowed_channels`/`allowed_chats`/`allowed_rooms`、DM ペアリング |
| 2. 危険コマンド承認 | 破壊操作の human-in-the-loop | `approvals.mode: manual/smart/off`、`DANGEROUS_PATTERNS`（docker restart/stop/kill が v0.16.0 で追加） |
| 3. コンテナ分離 | ターミナル/コード実行の隔離 | Docker / Singularity / Modal / Daytona バックエンド |
| 4. MCP 認証フィルタ | ツール起動時の env 分離 | `mcp_servers.<name>.env` で限定的に渡す、mTLS（v0.15.0） |
| 5. コンテキストファイルスキャン | プロンプトインジェクション検出 | Tirith 検出器、cron prompt-injection scan（v0.13.0）、invisible unicode sanitize（v0.16.0）、Promptware/Brainworm chokepoint（v0.15.0） |
| 6. クロスセッション分離 | データの session_id スコープ | SQLite + per-session memory |
| 7. 入力サニタイゼーション | 作業ディレクトリ/パス検証 | `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.kube/`, `$HERMES_HOME/.env`, `bws_cache.json` 等への自動ブロック |
| 8. シークレット redaction | ツール出力 / debug share マスキング | `redaction.enabled`（v0.13.0 でデフォルト ON）、`hermes debug share` 時の redaction |
| 9. SSRF 対策 | URL アクセス制限 | browser cloud-metadata SSRF floor（v0.13.0）、URL SSRF check を event loop 外（v0.16.0） |
| 10. supply-chain audit | 依存関係の脆弱性検査 | `hermes audit`（OSV.dev、v0.15.0） |

## 承認モード

```yaml
approvals:
  mode: manual                # manual=毎回確認 / smart=危険時のみ / off=常時許可
  smart_dangerous_patterns:
    - "rm -rf"
    - "sudo"
    - "chmod 777"
```

セッション内で `/yolo` で `off` 相当に切替（次セッションでは元に戻る）。`hermes --yolo` でセッション開始時から無効化。

## シークレットの秘匿

```yaml
security:
  redact_secrets: true              # ツール出力からシークレット形式の文字列をマスク
  tirith_enabled: true              # プロンプトインジェクション検出
  website_blocklist:
    enabled: true
    domains: ["evil.example.com"]
```

`redact_secrets` は API キー風文字列、JWT、AWS アクセスキー、SSH 秘密鍵などのパターンを検出して `***REDACTED***` に置換する。

## コンテキスト参照のブロック

`@file:`, `@folder:` でアクセス禁止のパス:

- `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.kube/`
- `$HERMES_HOME/.env`, `$HERMES_HOME/auth.json`
- `.git/config`（リモート URL に資格情報が埋まっているケース対策）

これらは透過的にブロックされ、ユーザーに通知される。

## MCP の権限境界

MCP サーバーは `mcp_servers.<name>.env` で渡された環境変数しか見えない。プロセス全体の `.env` にアクセスできない。

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_PERSONAL_ACCESS_TOKEN}"   # これだけ
    # ANTHROPIC_API_KEY, AWS_REGION 等は渡らない
```

## Gateway のアクセス制御

```bash
# プラットフォーム別許可リスト
TELEGRAM_ALLOWED_USERS=12345,67890
DISCORD_ALLOWED_USERS=11111
DISCORD_ALLOWED_ROLES=222,333

# グローバル許可リスト（全プラットフォーム）
GATEWAY_ALLOWED_USERS=12345
```

DM ペアリング:

```bash
hermes pairing list                           # 待機中のペアリング要求
hermes pairing approve telegram ABC12DEF      # 承認
hermes pairing revoke telegram 12345          # 既存ペアリング取消
```

`unauthorized_dm_behavior: pair` でペアリング待機、`ignore` で完全無視。

## Gateway 自己破壊防止 (v0.11.0)

エージェントが `terminal` 経由で gateway 自身を `kill` できないようにブロックされた（PID 検出）。`hermes gateway stop` を案内する。

## Webhook 署名検証

```yaml
platforms:
  webhooks:
    routes:
      github:
        secret: "${WEBHOOK_SECRET}"           # X-Hub-Signature-256 検証
        verify_signature: true
```

GitHub (`X-Hub-Signature-256`)、GitLab (`X-Gitlab-Token`)、汎用 HMAC をサポート。

## Bitwarden Secrets Manager（v0.15.0）

1 つの `BWS_ACCESS_TOKEN` で全クレデンシャルを Bitwarden Secrets Manager から fetch:

```yaml
secrets:
  bitwarden:
    enabled: true
    organization_id: ...
    override_existing: false
```

ファイルへの API キー直書きを避けられる。`bws_cache.json` は file-safety read guard 対象（v0.16.0）。

## 脆弱性 / CVE 履歴

- **CVE-2026-48710 (Starlette BadHost)** — v0.16.0 でパッチ済み（Starlette ≥1.0.1 pin）
- **v0.13.0 セキュリティ波** — 8 P0 closure:
  - redaction デフォルト ON
  - Discord ロール allowlist をギルドスコープに
  - WhatsApp で見知らぬ相手をデフォルト拒否
  - `auth.json` と MCP OAuth の TOCTOU 修正
  - browser cloud-metadata SSRF floor 強制
  - cron prompt-injection scan
  - `hermes debug share` アップロード時 redaction
- **v0.14.0** — sudo brute-force ブロック、3 件の dangerous-command bypass 修正、tool error sanitization
- **v0.15.0** — Promptware/Brainworm chokepoint 防御、control-plane file 保護、xAI OAuth `base_url` を `x.ai` 起源に固定、deadtoken quarantine
- **v0.16.0** — Bedrock inference bearer token を subprocess env から strip、mutation-verifier footer の file paths を neutralize、Honcho startup を fail open に、2 P0 + 62 P1 closure、16 security tagged

## オプション: agent-safehouse 連携

macOS では `agent-safehouse` (sandbox-exec ベース) を `hermes` 起動の外側に被せて、システムレベルの追加サンドボックスを掛けられる。`config/.config/agent-safehouse/hermes-overrides.sb` 参照。

## 監査ログ

```bash
hermes logs                                   # 全ログ
hermes logs gateway -f                        # Gateway リアルタイム
hermes logs errors -n 100                     # エラー直近 100 件
hermes logs tools                             # ツール呼び出しログ
```

`security.audit_log: true` でツール呼び出し・承認・拒否を `~/.hermes/logs/audit.log` に記録。
