# Hermes Agent インストール・初期セットアップ

> 参照元: https://hermes-agent.nousresearch.com/docs/getting-started/installation / quickstart / termux / nix-setup / updating / learning-path
> 対応バージョン: v0.16.0（`v2026.6.5` 「The Surface Release」）

## 標準インストール (Linux / macOS / WSL2)

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc          # or source ~/.zshrc
```

インストーラーが `uv`, Python 3.11, Node.js, ripgrep, ffmpeg を自動でインストールする。前提条件は Git のみ。

### PyPI からのインストール（v0.14.0+）

```bash
pip install hermes-agent
# または
uv pip install hermes-agent
```

`pip install hermes-agent` で起動可能。`[all]` extras は v0.14.0 から軽量化済み（重い backend は lazy-install、tiered install fallback）。

## Hermes Desktop App（v0.16.0+）

macOS / Linux / Windows のネイティブ Electron アプリ。詳細は `references/features/desktop.md`。

- macOS: `.dmg` を公式リリースページからダウンロード
- Linux: `.AppImage` または `.deb` / `.rpm`
- Windows: `.exe` インストーラー
- in-app self-update（GitHub Releases を見て差分更新）
- リモート Hermes（自宅サーバー / hosted / チームメイト）へ OAuth or username/password で接続

## 初回セットアップ

```bash
hermes portal             # Quick Setup via Nous Portal（v0.16.0、推奨）
# あるいは個別ウィザード:
hermes model              # プロバイダー選択（OpenRouter, Anthropic, Codex OAuth, SuperGrok OAuth, Nous Portal 等）
hermes tools              # 有効化するツールセットを選択
hermes setup              # メッセージング・プラグイン等の総合ウィザード
```

`hermes portal` は Nous Portal の OAuth を経由して数秒でセットアップが完了する（v0.16.0 から推奨）。

### デフォルトインターフェース選択（v0.16.0）

```yaml
# config.yaml
default_interface: tui    # cli | tui
```

`hermes --cli` / `hermes --tui` で都度上書き可能。

## Termux (Android)

```bash
pkg update && pkg install git curl python rust libffi openssl
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

- Termux 専用 constraints (`constraints-termux.txt`) で依存解決
- ターミナルバックエンドは `local` のみ動作（docker / ssh / modal は不可）
- 通知音は無効化（`bell_on_complete: false` を推奨）
- v0.15.0+: スクロールバック保持 + touch-friendly defaults

## Nix セットアップ

リポジトリに `flake.nix` が同梱。

```bash
nix run github:NousResearch/hermes-agent
# または開発シェル
nix develop github:NousResearch/hermes-agent
```

`HERMES_HOME` を任意のパスに上書きすると、Nix 構成下でも config を自由に配置できる。
`extraDependencyGroups` で追加グループを指定可能（v0.14.0）。

## 更新

```bash
hermes update             # 最新版へインプレース更新
hermes update --check     # 更新可否のみ確認（v0.12.0）
hermes update --yes       # 確認スキップ（v0.13.0）
hermes update --branch <name>  # 特定ブランチに切替（v0.15.0）
hermes update --pin v2026.6.5  # 特定バージョンに固定
hermes status             # 現在のバージョン・更新可否を確認
```

`scripts/install.sh` を再実行しても更新できる。設定 (`~/.hermes/`) は保持される。
Hermes Desktop はアプリ内 self-update を使う（CLI と独立）。

## Learning path（公式推奨学習順序）

1. **Quickstart** — `hermes portal` で 5 秒モデル設定 + 1 ターン会話
2. **CLI / TUI モード** — `hermes`, `/help`, `/model`, `/tools` で基本操作
3. **Hermes Desktop** — ネイティブ App でリモート gateway 接続 / multi-profile（v0.16.0）
4. **メモリと SOUL** — `MEMORY.md`, `SOUL.md` の編集
5. **MCP / スキル追加** — `hermes mcp`（カタログピッカー）, `hermes skills install`
6. **`/goal` / Kanban** — `/goal` での永続目標、`hermes kanban swarm` でマルチエージェント並列実行
7. **Cron / 委譲** — 自動化と並列処理（`no_agent` mode で watchdog パターン）
8. **メッセージング Gateway** — 23 プラットフォームの常駐運用
9. **プラグイン / ACP** — 拡張点と IDE 統合
10. **Curator** — `hermes curator` でスキルライブラリ自動メンテナンス

## アンインストール

```bash
hermes uninstall           # バイナリと PATH を削除
rm -rf ~/.hermes           # 設定・セッション・メモリも完全削除する場合
```

Hermes Desktop は OS 標準のアンインストール手順（macOS: アプリ削除、Windows: 設定 → アプリ、Linux: `.AppImage` の削除）。
