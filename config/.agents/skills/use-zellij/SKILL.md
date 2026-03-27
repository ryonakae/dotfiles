---
name: use-zellij
description: Zellij の CLI 制御とセッション運用を行うスキル。`zellij` コマンドや `zellij action` で、セッションの作成・attach・一覧・終了、pane/tab/floating pane の操作、出力監視、`config.kdl` の調整を行いたいときに使う。外部プロセスから Zellij を制御するときや設定・運用を整えるときに使い、layout や swap layout の適用・編集にも対応する。
---

# Use Zellij

## Overview

Zellij を主に CLI 制御と KDL 編集から扱う。セッション、タブ、ペイン、フローティングペイン、レイアウト、設定を分けて考え、必要な参照だけ読んで作業する。

## 基本方針

- まず対象が `セッション運用`, `CLI 制御`, `レイアウト編集`, `設定変更` のどれかを切り分ける。
- 具体的なフラグ、JSON フィールド、終了コードを使う前に `zellij --version` と対象 subcommand の `--help` を確認し、参照資料と差分があればローカルのヘルプ出力を優先する。
- 自動化では `zellij --session <name> action ...` を基本形にし、生成された pane/tab ID を保持する。
- シェル依存を避けたいときは `new-pane -- <command>` や `run -- <command>` を優先する。`paste` や `send-keys` は既存シェル状態を使う必要があるときだけ使う。
- 既存セッションを壊す変更の前に `list-panes --json`, `list-tabs --json`, `dump-layout` で現在状態を確認する。
- レイアウトはゼロから書き始めるより `zellij setup --dump-layout default` や `zellij setup --dump-swap-layout default` を土台にする。
- 人間向けショートカットやモード操作には依存しない。エージェントから再現可能な CLI と KDL 編集を優先する。

## 進め方

1. 対象の Zellij バージョン、セッション名、現在地を把握する。セッション管理や CLI 操作なら `references/cli-control.md` を読む。
2. ペイン、タブ、フローティングペインの状態変更や整理を行うなら `references/panes-tabs-and-floating.md` を読む。
3. `.kdl` の layout / swap layout / template / `cwd` 合成を扱うなら `references/layouts-and-swap-layouts.md` を読む。
4. `config.kdl`、`default_layout`、復元、クリップボード、マウス、Web 共有を扱うなら `references/configuration-and-sessions.md` を読む。

## よくある判断

- 実行中セッションへ非対話で何かする:
  `references/cli-control.md` の「機械操作の基本ループ」と「主要 action 一覧」を先に読む。
- ペインやタブの再配置、フローティング化、リサイズをしたい:
  `references/panes-tabs-and-floating.md` の「CLI recipe」と「フローティングペイン操作」を読む。
- 新規レイアウトを作る:
  `references/layouts-and-swap-layouts.md` の「レイアウト構文」と「実用パターン」を読む。
- 復元や welcome screen を整える:
  `references/configuration-and-sessions.md` の「セッション管理」と「復元関連オプション」を読む。

## Reference Files

- `references/cli-control.md`
  CLI の全体像、トップレベルコマンド、`zellij action` の分類、観測・入力・レイアウト適用の基本形を読む。
- `references/panes-tabs-and-floating.md`
  ペイン/タブ/フローティングペインの状態モデル、主要 action、CLI recipe を読む。
- `references/layouts-and-swap-layouts.md`
  KDL レイアウト、テンプレート、`floating_panes`, `default_tab_template`, swap layout, `cwd` 合成を読む。
- `references/configuration-and-sessions.md`
  `config.kdl` の場所、主要オプション、welcome screen、session-manager、復元、Web 共有を読む。
