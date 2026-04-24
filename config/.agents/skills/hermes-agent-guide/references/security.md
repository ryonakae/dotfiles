# セキュリティモデル統合ガイド

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/security / SECURITY.md

## 7 層防御アーキテクチャ

| 層 | 役割 | 主な実装 |
|----|------|---------|
| 1. ユーザー認可 | 誰がエージェントに話しかけられるか | `*_ALLOWED_USERS`, `GATEWAY_ALLOWED_USERS`, DM ペアリング |
| 2. 危険コマンド承認 | 破壊操作の human-in-the-loop | `approvals.mode: manual/smart/off` |
| 3. コンテナ分離 | ターミナル/コード実行の隔離 | Docker / Singularity / Modal / Daytona バックエンド |
| 4. MCP 認証フィルタ | ツール起動時の env 分離 | `mcp_servers.<name>.env` で限定的に渡す |
| 5. コンテキストファイルスキャン | プロンプトインジェクション検出 | Tirith 検出器（`security.tirith_enabled`） |
| 6. クロスセッション分離 | データの session_id スコープ | SQLite + per-session memory |
| 7. 入力サニタイゼーション | 作業ディレクトリ/パス検証 | `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.kube/`, `$HERMES_HOME/.env` 等への自動ブロック |

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
