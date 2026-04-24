# Hermes Agent インストール・初期セットアップ

> 参照元: https://hermes-agent.nousresearch.com/docs/getting-started/installation / quickstart / termux / nix-setup / updating / learning-path

## 標準インストール (Linux / macOS / WSL2)

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc          # or source ~/.zshrc
```

インストーラーが `uv`, Python 3.11, Node.js, ripgrep, ffmpeg を自動でインストールする。前提条件は Git のみ。

## 初回セットアップ

```bash
hermes model              # プロバイダー選択（OpenRouter, Anthropic, Codex OAuth 等）
hermes tools              # 有効化するツールセットを選択
hermes setup              # メッセージング・プラグイン等の総合ウィザード
```

## Termux (Android)

```bash
pkg update && pkg install git curl python rust libffi openssl
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

- Termux 専用 constraints (`constraints-termux.txt`) で依存解決
- ターミナルバックエンドは `local` のみ動作（docker / ssh / modal は不可）
- 通知音は無効化（`bell_on_complete: false` を推奨）

## Nix セットアップ

リポジトリに `flake.nix` が同梱。

```bash
nix run github:NousResearch/hermes-agent
# または開発シェル
nix develop github:NousResearch/hermes-agent
```

`HERMES_HOME` を任意のパスに上書きすると、Nix 構成下でも config を自由に配置できる。

## 更新

```bash
hermes update             # 最新版へインプレース更新
hermes update --pin v2026.4.23   # 特定バージョンに固定
hermes status             # 現在のバージョン・更新可否を確認
```

`scripts/install.sh` を再実行しても更新できる。設定 (`~/.hermes/`) は保持される。

## Learning path（公式推奨学習順序）

1. **Quickstart** — 5 分でモデル設定 + 1 ターン会話
2. **CLI モード** — `hermes`, `/help`, `/model`, `/tools` で基本操作
3. **TUI モード** — `hermes --tui` で React/Ink 製 TUI を体験
4. **メモリと SOUL** — `MEMORY.md`, `SOUL.md` の編集
5. **MCP / スキル追加** — `hermes mcp add`, `hermes skills install`
6. **Cron / 委譲** — 自動化と並列処理
7. **メッセージング Gateway** — Telegram / Discord 等の常駐運用
8. **プラグイン / ACP** — 拡張点と IDE 統合

## アンインストール

```bash
hermes uninstall           # バイナリと PATH を削除
rm -rf ~/.hermes           # 設定・セッション・メモリも完全削除する場合
```
