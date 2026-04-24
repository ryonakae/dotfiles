# Ink TUI モード

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/tui

v0.11.0 で `hermes --tui` が React/Ink ベースに完全リライトされた。Python JSON-RPC バックエンド (`tui_gateway`) と TypeScript フロントエンド (`ui-tui/`) で構成される。

## 起動

```bash
hermes --tui
HERMES_TUI=1 hermes              # 環境変数でも有効化
```

## 主な機能

| 機能 | 説明 |
|------|------|
| Sticky composer | スクロール中も入力欄が固定 |
| Live streaming + OSC-52 | SSH 越しでもクリップボードコピー |
| ステータスバー | per-turn ストップウォッチ、git ブランチ、cwd |
| サブエージェント観測オーバーレイ | `delegate_task` の並列子プロセスをライブ表示 |
| `/clear` 確認ダイアログ | 誤クリア防止 |
| Light-theme preset | ダーク/ライト切替 |
| Slash command autocomplete | `complete.slash` RPC 経由 |
| Path autocomplete | `complete.path` RPC 経由 |
| Virtualized history | 長いセッションでも軽量 |

## アーキテクチャ

- `src/entry.tsx` — TTY 検出ゲート
- `src/app.tsx` — 状態機械（`app/event-handler`, `app/slash-handler`, `app/stores`, `app/hooks`）
- 永続的な `_SlashWorker` サブプロセスでスラッシュコマンドを処理
- コンポーネント分割: `branding.tsx`, `markdown.tsx`, `prompts.tsx`, `sessionPicker.tsx`, `messageLine.tsx`, `thinking.tsx`, `maskedPrompt.tsx`
- フック分割: `useCompletion`, `useInputHistory`, `useQueue`, `useVirtualHistory`

## クラシック CLI との違い

`--tui` を付けないとレガシーの prompt-toolkit ベース CLI で起動する。長期的にはクラシック CLI が deprecated 予定。

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| TUI が起動しない | TTY が無効。SSH の場合は `-t` オプションで PTY 確保 |
| 表示崩れ | `TERM=xterm-256color` を設定。Windows Terminal はリサイズ後に Ctrl+L |
| クリップボードが効かない | OSC-52 対応ターミナル (kitty / wezterm / iTerm2 / tmux 3.3+) を使用 |
| 入力遅延 | `ui-tui/` の virtual history が圧縮中。古いセッションは `/new` で分割 |
