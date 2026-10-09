---
name: use-agent-safehouse
description: |
  Agent Safehouse（macOS 向け sandbox-exec ベースのエージェントサンドボックスツール）をセットアップ・設定・運用するためのスキル。ポリシー構築、デバッグ、カスタマイズに対応。
  ユーザーが agent-safehouse / safehouse コマンド / sandbox-exec ポリシーを使うとき、`Operation not permitted` や `deny(` を含むサンドボックス拒否エラーをデバッグするとき、`--enable` の選定や `--append-profile` でカスタム .sb オーバーレイを作成するとき、.safehouse ファイルや local-overrides.sb を編集するとき、エージェントのファイルシステムアクセスを macOS カーネルレベルで制限したいときに使う。一般的な Linux sandbox や Docker/VM の質問には使わない。
---

# Agent Safehouse ガイド

Agent Safehouse は macOS ネイティブの `sandbox-exec` を利用した、LLM コーディングエージェント向けサンドボックスツール。カーネルレベルで deny-first のファイルシステム制限を適用し、依存関係ゼロで動作する。

## トラブルシュート：症状別ルーティング

| 症状 | まず試すこと | 詳細の参照先 |
|------|-------------|-------------|
| `Operation not permitted` エラー | 起動引数と最終profileの順序を確認し、標準機能・残るdeny・不足grantを切り分ける | 本ファイルの「一次診断手順」 |
| どのパスが拒否されたか不明 | `/usr/bin/log stream` で deny ログをストリーム | `references/debugging-and-testing.md` |
| `--enable` で何を有効化すべきか不明 | 本ファイルの「--enable で有効化できる機能」一覧を確認 | — |
| カスタム `.sb` ポリシーの書き方 | パスマッチャー（literal/subpath/prefix/regex）を確認 | `references/policy-and-customization.md` |
| 特定エージェント固有の問題 | 本ファイルの「対応エージェント」表で内蔵サンドボックスの有無を確認 | `references/agent-investigations.md` |
| LLM でプロファイルを自動生成したい | 検出コマンドを実行し、プロファイル生成プロンプトに従う | `references/llm-profile-generator.md` |
| ポリシーの順序・優先度の問題 | ポリシーレイヤーの「後のルールが優先」原則を確認 | `references/policy-and-customization.md` |

### 一次診断手順

問題発生時はこの順序で進める：

1. 失敗command、エラーに現れたpath・操作、実際の起動引数を確認する。単独の `safehouse` 呼び出しと、この環境のwrapperが生成するpolicyは異なる。
2. 同じ起動引数で **`safehouse --stdout <command>`** を使い、生成policyと最終profileの順序を確認する。これはcommandを実行しない。**`--explain`** はstderrへサマリを出すだけで、commandを指定すると実行もする。拒否操作の再試行には使わない。
3. 必要なら **`/usr/bin/log stream`** で既存の拒否ログを確認する。実秘密へのprobeや無断の迂回は行わない。
4. 標準の `--enable` とgrantで対応できるかを確認し、残るdenyとの衝突なら理由と承認が必要な最小変更を提示する。実行中のsandboxのpolicyは更新できず、変更は次回起動から反映される。

### `.env` / 鍵ファイルの拒否が残る場合

機密・個人データの独自 deny は撤廃済み。新しい起動では、HOME や許可された一時ディレクトリのダミー `.env` を名前だけで拒否しない。以前から動いているプロセスには旧 policy が残るため、正本と起動時の設定を区別する。実秘密を probe せず、再起動や追加 grant が必要ならユーザーへ確認する。

### Hermes の parallel test runner と kanban write guard を併用する場合

`scripts/run_tests_parallel.py` は test file ごとに pytest subprocess を起動する。全 subprocess へ同じ `PYTEST_ADDOPTS=--basetemp=...` を渡すと、各 pytest が同じ directory を削除・再作成してraceするため、共有 `--basetemp` は使わない。

また、`TMPDIR=~/.hermes/...` だけでは `tests/conftest.py` の kanban write guard が一時DBを実 `~/.hermes` 配下と判定して拒否する。短いTMPDIRとkanban guardを併用するには、pre-sandboxのcustom homeとkanban deny sentinelを兄弟pathへ分ける：

既存の実データへ書かないテスト専用pathを確認したうえで使う例：

```fish
mkdir -p "$HOME/.hermes/t/home"
env HERMES_HOME="$HOME/.hermes/t/home" \
  HERMES_KANBAN_HOME="$HOME/.hermes/t/deny" \
  TMPDIR="$HOME/.hermes/t" \
  PYTEST_ADDOPTS='' \
  HERMES_TEST_WORKERS=8 \
  uv run python scripts/run_tests_parallel.py
```

`tests/conftest.py` は `HERMES_KANBAN_HOME` をimport時にdeny rootとしてcaptureし、各test開始時には環境から消す。そのため実test DBはTMPDIRへ書ける一方、deny sentinel配下への誤書込みは拒否される。`TMPDIR`を短くすることでmacOSのAF_UNIX socket path上限も回避できる。

この構成を使う場合は、必要な範囲の代表testで確認する。フルsuiteは完了条件にしない。上の `env` 指定を同じように付けて実行する：

```fish
uv run python -m pytest -q \
  tests/agent/test_codex_stream_activity_watchdog.py \
  tests/gateway/test_kanban_notifier_zero_sub_gate.py \
  tests/gateway/test_scale_to_zero.py
```

## 設計哲学

- **deny-first**: デフォルトで全アクセスを拒否し、必要なものだけ明示的に許可する
- **実用的な被害軽減**: 絶対的な隔離ではなく、プロンプトインジェクションや誤操作時の被害範囲を最小化する
- このdotfiles環境は普段の開発の互換性を優先し、HOME RW、`wide-read`、全環境継承、既存の `process-control` と広域IPC許可を維持する。`allow default` や `/` のRWには変更しない
- 機密・個人データの独自 deny は設けない。Safehouse 内の `rm` は Homebrew の `gtrash put` へ転送し、`/bin/rm` 実行を拒否する。Safehouse 外の通常端末では wrapper から `/bin/rm` を実行する。ごみ箱 payload の直接読み取り・上書き・削除は拒否し、復元・掃除は人間が sandbox 外で行う。gomi と既存データは保持する
- 独自の管理wrapper・policyディレクトリの編集禁止、保護対象の親とごみ箱ルートのrename禁止は撤廃する。完全な迂回封鎖は保証しない
- ネットワーク経由のデータ流出、サンドボックスエスケープ、許可済みチャネルの悪用は防げない

## 隔離モデルの位置づけ

| 観点 | VM | コンテナ | Safehouse |
|------|-----|---------|-----------|
| 隔離境界 | ゲスト OS | プロセス namespace/cgroup | macOS Seatbelt ポリシー |
| カーネル分離 | あり | なし（ホスト共有） | なし（ホスト共有） |
| ファイルシステム | ゲストのみ | コンテナ FS | deny-first + 明示的 allow |
| オーバーヘッド | 高 | 低〜中 | 非常に低 |
| ワークフロー互換性 | 低 | 中 | 高 |

最強の保護には VM 内で Safehouse を併用するレイヤードアプローチを推奨。

## インストール

```bash
# Homebrew（推奨）
brew install eugene1g/safehouse/agent-safehouse

# スタンドアロン
curl -fsSL https://agent-safehouse.dev/install.sh | sh
# ~/.local/bin/safehouse にインストールされる
```

## 基本的な使い方

```bash
# カレントディレクトリで Claude を起動
safehouse claude --dangerously-skip-permissions

# 追加の書き込みディレクトリを許可
safehouse --add-dirs=/path/to/other claude

# 読み取り専用ディレクトリを追加
safehouse --add-dirs-ro=/path/to/readonly claude

# カスタムポリシーを追加適用
safehouse --append-profile=my-policy.sb claude

# workdir 設定ファイルを信頼
safehouse --trust-workdir-config claude

# ワーキングディレクトリを明示指定
safehouse --workdir=/path/to/project claude

# ポリシーを出力して確認
safehouse --stdout claude
safehouse --explain claude
```

## 環境変数の渡し方

```bash
# 全環境変数を透過（秘密情報も含まれるので注意）
safehouse --env claude

# ファイルから環境変数をソース
safehouse --env=.env claude

# 特定の変数のみ選択的に渡す
safehouse --env-pass=ANTHROPIC_API_KEY,OPENAI_API_KEY claude
```

この環境のwrapperは互換性のため `--env` で全環境を継承する。ファイルへの直接アクセス拒否とは別の境界なので、継承した秘密値をログや応答へ出さない。

## オプション一覧

| フラグ | 説明 |
|--------|------|
| `--add-dirs=PATHS` | 書き込み可能ディレクトリを追加 |
| `--add-dirs-ro=PATHS` | 読み取り専用ディレクトリを追加 |
| `--workdir=DIR` | ワーキングディレクトリを指定 |
| `--trust-workdir-config` | `<workdir>/.safehouse` 設定を読み込み |
| `--append-profile=PATH` | カスタム `.sb` ポリシーを追加（繰り返し指定可） |
| `--allow-profile-writes` | appendしたprofileファイルへの標準deny-writeを省く。別途書き込みgrantは必要 |
| `--allow-workdir-config-writes` | `<workdir>/.safehouse` への標準deny-writeを省く |
| `--env` | ホスト環境変数を全て透過 |
| `--env=FILE` | ファイルから環境変数をソース |
| `--env-pass=NAMES` | 指定変数のみ透過 |
| `--output=PATH` | ポリシーをファイルに出力（実行も行う） |
| `--stdout` | ポリシーをstdoutに出力し、commandは実行しない |
| `--explain` | workdir・grant・profile選択のサマリをstderrに表示。command指定時は実行もする |
| `--enable=FEATURE` | オプション機能を有効化 |

### --enable で有効化できる機能

公式のfeature名は `shell-init`、`agent-browser`、`wide-read` を使う。主な機能は次のとおり：

`docker`, `kubectl`, `shell-init`, `agent-browser`, `clipboard`, `herdr`, `launch-services`, `macos-gui`, `electron`, `chromium-headless`, `chromium-full`, `playwright-chrome`, `ssh`, `gpg`, `gpu`, `process-control`, `lldb`, `vscode`, `xcode`, `wide-read`, `keychain`, `1password`, `cloud-credentials`, `cloud-storage`, `all-agents`, `all-apps`

全一覧と依存featureは [公式options](https://agent-safehouse.dev/docs/options.html) で確認する。

## デフォルトのアクセス制御

### 許可されるもの（デフォルト）

- workdir への読み書き
- Git 関連メタデータ（worktree 含む）
- macOS/システム/ツールチェーンのランタイム読み取り
- コマンドラインツール（git, make, clang 等）の実行
- プロセス実行・fork
- ネットワークアクセス（デフォルトオープン）
- 一時ディレクトリ

### ブロックされるもの（デフォルト）

- `~/.ssh` 秘密鍵
- シェル初期化ファイル（`.bashrc`, `.zshrc` 等）
- ブラウザデータ（Cookie、履歴、ブックマーク）
- クリップボードアクセス
- ホストプロセス列挙
- Xcode 開発ルート（完全版）
- raw デバイスアクセス
- `$HOME` の再帰的読み取り

### オプトイン（明示的に有効化が必要）

ブラウザ自動化、クリップボード統合、クラウド認証情報、Docker ソケット、Xcode ルート、LLDB、Keychain アクセス、広範な HOME 読み取り

## ワーキングディレクトリの設定ファイル

プロジェクトルートに `.safehouse` ファイルを配置：

```
add-dirs-ro=/path/to/shared/libs
add-dirs=/path/to/output
```

`--trust-workdir-config` フラグで読み込む。

## ローカルオーバーライド

マシン固有の例外を `~/.config/agent-safehouse/local-overrides.sb` に記述。

## Git Worktree サポート

workdir が Git worktree の場合、Safehouse は自動的に：
- 共有 Git メタデータへのアクセスを許可
- 他の worktree パスへの読み取り専用アクセスを付与

worktree を安定した親ディレクトリ配下で作成する場合は `--add-dirs-ro` で親を指定。

## デスクトップアプリケーション対応

自動的にアプリバンドルを認識（Claude Desktop、VS Code 等）：

```bash
safehouse -- /Applications/Claude.app/Contents/MacOS/Claude
```

Electron アプリには `--no-sandbox` フラグを維持してネストされたサンドボックスの初期化を防止。

## ポリシーアーキテクチャ

ポリシーは以下のレイヤーで組み立てられる（後のルールが優先）：

1. `00-base.sb` — デフォルト deny、ヘルパー関数、HOME 置換トークン
2. `10-system-runtime.sb` — macOS ランタイムバイナリ、一時ディレクトリ、IPC
3. `20-network.sb` — ネットワークポリシー
4. `30-toolchains/*.sb` — Apple, Node, Python, Go, Rust, Bun, Java, PHP, Perl, Ruby
5. `40-shared/*.sb` — クロスエージェント共有モジュール
6. `50-integrations-core/*.sb` — Git, SSH agent, worktree 等
7. `55-integrations-optional/*.sb` — `--enable` でオプトイン
8. `60-agents/*.sb` — コマンド名でエージェント別プロファイルを選択
9. `65-apps/*.sb` — アプリバンドル別プロファイル
10. 設定/環境変数/CLI グラント
11. 追加プロファイル（この環境では `compatibility.sb` → `local-overrides.sb`）
12. appendしたprofileの標準書き込み保護と、最後のterminal deny（`.safehouse` の保護）。それぞれ対応するopt-outで省略可能

**順序が重要**: 後のルールが優先。予期しない動作はまず順序を確認。

詳細は `references/policy-and-customization.md` を参照。

## デバッグ（サンドボックス拒否の調査）

`Operation not permitted` エラーが発生した場合の調査手順：

```bash
# ライブで拒否ログをストリーム
/usr/bin/log stream --style compact \
  --predicate 'eventMessage CONTAINS "Sandbox:" AND eventMessage CONTAINS "deny("'

# 特定 PID パターンでフィルタ
/usr/bin/log stream --style compact \
  --predicate 'eventMessage CONTAINS "Sandbox: 2.1.34(" AND eventMessage CONTAINS "deny("'

# カーネルレベルの拒否を監視
/usr/bin/log stream --style compact \
  --predicate '(processID == 0) AND (senderImagePath CONTAINS "/Sandbox")'
```

**重要**: `/usr/bin/log` のフルパスを使うこと（シェルの `log` エイリアスと区別するため）。

### 拒否ログからルールへの変換

| ログの操作 | sandbox ポリシールール |
|------------|----------------------|
| ファイル操作 | `(allow <operation> (literal "<path>"))` |
| sysctl | `(allow sysctl-read (sysctl-name "<name>"))` |
| mach-lookup | `(allow mach-lookup (global-name "<name>"))` |

### ノイズ除去

dtracehelper や Apple サービスのフォルスポジティブを除外。`DYLD_USE_DTRACE=0` で dtrace を抑制可能。

詳細は `references/debugging-and-testing.md` を参照。

## カスタマイズ

6つの拡張ポイント：

1. `--append-profile` で読み込むカスタム `.sb` オーバーレイに認証情報拒否を追加
2. `profiles/20-network.sb` でネットワーク動作を調整
3. `profiles/40-shared/` で共有クロスエージェントルールを変更
4. `profiles/60-agents/` にエージェントプロファイルを追加
5. `profiles/65-apps/` にデスクトップアプリプロファイルを追加
6. `profiles/30-toolchains/` にツールチェーンプロファイルを追加

**この環境の原則**: 開発の互換性を優先し、OS重要領域への書き込み範囲とごみ箱の保護を維持する。標準機能と最終profile順から原因を診断し、承認された最小変更を行う。広いgrantを一律に避けたり、拒否ログをそのままallowへ変換したりしない。

対話wrapper・Hermes gateway・dashboardの3経路は `--allow-profile-writes` を指定する。独自の管理wrapper/policy編集denyの撤廃とは別に、Safehouse標準のappend profile保護を省く設定であり、ごみ箱の deny や `.safehouse` の保護は解除しない。承認された変更は `config/` の正本へ行い、次回起動で反映する。現在のsandboxで拒否された場合は無断で外側へ回さない。

IPCの広域許可とSimulatorの `system-fsctl` は `compatibility.sb` にまとめ、ごみ箱保護と `/bin/rm` 実行拒否は後段の `local-overrides.sb` に置く。すでに許可されたMach/network/signalの個別allowを重複追加しない。

## 配布

```bash
# dist/safehouse.sh — ランタイム＋ポリシーモジュールを埋め込んだ自己完結スクリプト
./scripts/generate-dist.sh
```

## 対応エージェント

13種類のエージェントがテスト済み。Safehouse 本体の設定で解決できない、エージェント固有のファイルアクセスパターンや認証情報管理の問題を調べるときだけ `references/agent-investigations.md` を参照する。

| エージェント | 種別 | 内蔵サンドボックス |
|-------------|------|-------------------|
| Claude Code | CLI/TUI (Node.js) | Bash のみ（Read/Write/Edit は対象外） |
| Codex | CLI (TypeScript+Rust) | あり（Seatbelt/bubblewrap/Landlock） |
| Gemini CLI | CLI/TUI (TypeScript) | あり（Seatbelt 6段階プロファイル） |
| Cursor Agent | IDE (Electron) | なし（アプリレベル制限のみ） |
| Copilot CLI | CLI (Node.js) | なし（アドバイザリー権限のみ） |
| Aider | CLI (Python) | なし |
| Goose | CLI (Rust) | なし |
| Cline | VS Code 拡張 | なし |
| Kilo Code | VS Code 拡張 | なし |
| OpenCode | CLI/TUI (Go) | なし（禁止コマンドリストのみ） |
| Auggie | CLI (Node.js) | なし |
| Droid | CLI (Bun) | なし（アプリレベル権限のみ） |
| Pi | CLI (TypeScript) | オプション（sandbox-runtime） |

## リファレンスファイル

詳細が必要な場合は以下を参照：

- `references/policy-and-customization.md` — ポリシーアーキテクチャ詳細、パスマッチャー、カスタマイズ、配布
- `references/debugging-and-testing.md` — デバッグ手法、テストフレームワーク、E2E テスト
- `references/agent-investigations.md` — 全13エージェントの詳細セキュリティ分析
- `references/llm-profile-generator.md` — LLM を使ったカスタムプロファイル生成ガイド

## 参考リソース

- [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime) — Anthropic の公式サンドボックス実装
- [neko-kai/claude-code-sandbox](https://github.com/neko-kai/claude-code-sandbox) — 制限的な読み取りポリシー実験
- [n8henrie/trace.sh](https://github.com/n8henrie/trace.sh) — deny-to-allow プロファイル自動生成
