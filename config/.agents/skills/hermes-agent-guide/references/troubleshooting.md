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
hermes debug share         # デバッグレポートアップロード
hermes logs                # agent.log 表示
hermes logs gateway -f     # ゲートウェイログフォロー
hermes logs errors -n 100  # エラーログ最新100行
```
