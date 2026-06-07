# Hermes Desktop App

> v0.16.0 「The Surface Release」で導入。Electron ベースのネイティブアプリ。

## 概要

macOS / Linux / Windows のネイティブ Electron アプリ。CLI / TUI に加えて 3 つ目の主要インターフェース。Cmd+K palette、drag-and-drop、status bar の model picker、concurrent multi-profile sessions、in-app self-update を備える。Simplified Chinese 翻訳（typed i18n layer）対応。

## インストール

公式リリースページからプラットフォーム別バイナリをダウンロード:

- macOS: `.dmg`
- Linux: `.AppImage` または `.deb` / `.rpm`
- Windows: `.exe`

ログは `~/.hermes/logs/desktop.log` に出力。`hermes debug share` / `/debug` / `hermes logs` で含まれる。

## 主要機能

| 機能 | 説明 |
|-----|-----|
| **in-app self-update** | GitHub Releases を見て差分更新 |
| **Cmd+K command palette** | 全コマンド・セッション・スキル横断検索 |
| **drag-and-drop** | ファイルを drop してコンテキストに添付 |
| **clipboard image paste** | Cmd+V で画像直接貼り付け |
| **status bar の inline model picker** | YOLO toggle 込み |
| **background needs-input indicator** | 別セッションでユーザー入力待ちを通知 |
| **session-list overhaul** | アーカイブ、検索、cross-profile `@session` リンク |
| **concurrent multi-profile sessions** | 同時に複数プロファイルのセッションを開ける |
| **per-profile remote gateway** | 各プロファイルが独自リモートホスト |
| **microphone entitlement (macOS)** | ボイスモード用 |
| **thinking block streaming 中も open 維持** | 推論内容を継続表示 |

## リモート gateway 接続

Desktop アプリから自宅サーバー / hosted / チームメイトの Hermes に接続できる:

- OAuth（Nous Portal）
- username/password（self-hosted OIDC provider、generic provider 対応）
- WebSocket 経由でセッション同期

```
[Settings] → [Profile] → [Remote Gateway] → [Connect]
```

self-hosted で OAuth client を登録する場合:

```bash
hermes dashboard register
```

## 多言語対応

`display.language` 設定または Appearance settings で切替（v0.16.0 時点で英語デフォルト、Simplified Chinese 翻訳追加）。

## トラブルシューティング

| 症状 | 対処 |
|-----|-----|
| アプリが起動しない | `~/.hermes/logs/desktop.log` を確認 |
| リモート接続できない | OAuth scope / firewall / WebSocket URL を確認 |
| update が失敗する | OS 標準の手段で再インストール |
| マイクが使えない（macOS） | System Settings → Privacy → Microphone で許可 |
