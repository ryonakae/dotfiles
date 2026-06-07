# Hermes Agent トラブルシューティング

> 参照元: https://hermes-agent.nousresearch.com/docs/reference/faq

## インストール

| 問題 | 解決策 |
|-----|------|
| `hermes: command not found` | `source ~/.bashrc` or `source ~/.zshrc` |
| Python バージョン古い | Python 3.11+ が必要。`uv` が自動インストール |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Permission denied | `sudo` 不要。`~/.local/bin` にインストールされる |

## プロバイダー・モデル

| 問題 | 解決策 |
|-----|------|
| `/model` でプロバイダーが1つしかない | セッション外で `hermes model` を実行して新プロバイダー追加 |
| API key not working | `hermes config show` で確認、`hermes model` で再設定 |
| Model not found | `hermes model` でモデル再選択 |
| Rate limiting (429) | 待機して再試行、プラン変更、別プロバイダー使用 |
| Context length exceeded | `/compress` 実行、より大きいコンテキストのモデルに切替 |
| Error 400 | モデル名ミスマッチ。`hermes model` で再設定 |

## ターミナル

| 問題 | 解決策 |
|-----|------|
| 危険コマンドブロック | 承認プロンプトで `y` を入力 |
| sudo 不動作（ゲートウェイ） | `SUDO_PASSWORD` を `.env` に設定 |
| Docker 接続不可 | `docker info` 確認、`sudo usermod -aG docker $USER` |

## メッセージング

| 問題 | 解決策 |
|-----|------|
| ボット無応答 | `hermes gateway status` 確認、ログ確認 |
| メッセージ未配信 | ボットトークン確認、ネットワーク確認 |
| ゲートウェイ起動失敗 | 依存関係インストール確認、ポート競合確認 |
| WSL でゲートウェイ切断 | `hermes gateway run`（フォアグラウンド）を使用 |
| macOS でツール未検出 | `hermes gateway install` 再実行（PATH 再キャプチャ） |

## MCP

| 問題 | 解決策 |
|-----|------|
| 接続不可 | `uv pip install -e ".[mcp]"` 確認、`node --version` 確認 |
| ツール未表示 | フィルタ設定確認、`enabled: false` 確認、`/reload-mcp` |
| タイムアウト | タイムアウト値増加、サーバープロセス確認 |
| Docker 内で `npx`/`node` not found | v0.15.1 で `/usr/local/bin` 解決追加。最新化 |
| `false OAuth success` 表示 | v0.16.0 で修正済み。最新化 |
| Stale pipe / session expired | v0.13.0+ で stale-pipe retries に対応。再接続で復帰 |

## Hermes Desktop

| 問題 | 解決策 |
|-----|------|
| アプリ起動しない | `~/.hermes/logs/desktop.log` 確認 |
| リモート gateway 接続失敗 | OAuth scope / firewall / WebSocket URL 確認、`hermes dashboard register` でクライアント登録 |
| update 失敗 | OS 標準で再インストール |
| マイク使えない（macOS） | System Settings → Privacy → Microphone 許可 |
| 401 reload loop（dashboard） | v0.15.1 で修正済み |

## Kanban / Curator

| 問題 | 解決策 |
|-----|------|
| Stale task 多発 | `claim_ttl` 短縮、`hermes kanban list --sort` で確認 |
| Worker が同じ retry を繰り返す | 手動 `archive --rm` |
| Worker SIGTERM で終わらない | v0.15.1 で intermediate プロセスの SIGTERM 吸収修正済み |
| Curator が大事なスキルを prune | `protect_built_in: true`、`hermes curator status` を手動確認 |

## パフォーマンス

| 問題 | 解決策 |
|-----|------|
| レスポンス遅い | 小さいモデル使用、ツールセット削減、ネットワーク確認 |
| トークン使用量高い | `/compress` 実行、`/usage` で確認 |
| セッション長すぎ | `/compress` 実行、新セッション開始 |

## ボイスモード

| 問題 | 解決策 |
|-----|------|
| No audio device | `brew install portaudio` (macOS) / `apt install portaudio19-dev` (Linux) |
| VC で聞こえない | `DISCORD_ALLOWED_USERS` 確認、ミュート確認 |
| 応答しない | STT 確認: `faster-whisper` インストール or API キー設定 |
| Whisper ゴミテキスト | より静かな環境、`silence_threshold` 調整 |

## 診断コマンド

```bash
hermes doctor              # 依存関係・設定診断
hermes doctor --fix        # 自動修復試行
hermes status              # ステータス確認
hermes status --deep       # 詳細チェック
hermes dump                # サポート用ダンプ
hermes debug share         # デバッグレポートアップロード（v0.13.0 で redaction 通過）
hermes audit               # supply-chain audit (OSV.dev、v0.15.0)
hermes prompt-size         # プロンプトサイズ診断（v0.16.0）
hermes logs                # agent.log 表示
hermes logs gateway -f     # ゲートウェイログフォロー
hermes logs errors -n 100  # エラーログ最新100行
```
