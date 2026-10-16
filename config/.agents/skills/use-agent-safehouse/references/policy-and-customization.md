# ポリシーアーキテクチャ・カスタマイズ・配布 詳細リファレンス

## ポリシー組み立てレイヤー

Safehouse はモジュール式のプロファイルを特定の順序でレイヤリングし、`sandbox-exec` 配下でコマンドを実行する。

### レイヤー詳細

1. **00-base.sb**: デフォルト deny、ヘルパー関数、HOME 置換トークン (`__SAFEHOUSE_REPLACE_ME_WITH_ABSOLUTE_HOME_DIR__`)
2. **10-system-runtime.sb**: macOS ランタイムバイナリ、一時ディレクトリ、IPC
3. **20-network.sb**: ネットワークポリシー設定
4. **30-toolchains/*.sb**: ツールチェーン別サポート
   - Apple Toolchain, Node.js, Python, Go, Rust, Bun, Java, PHP, Perl, Ruby
5. **40-shared/*.sb**: クロスエージェント共有モジュール（`agent-common.sb` 等）
6. **50-integrations-core/*.sb**: コア統合（Git, SSH agent, worktree 等）
7. **55-integrations-optional/*.sb**: `--enable=...` でオプトイン可能な統合
8. **60-agents/*.sb**: コマンドのベースネームでエージェント別プロファイルを自動選択
9. **65-apps/*.sb**: アプリバンドル別プロファイル
10. 設定/環境変数/CLI グラント
11. `--append-profile` で追加されたプロファイル
12. appendしたprofileの標準書き込み保護と、最後のterminal deny（workdirの `.safehouse` の保護）。それぞれ対応するopt-outで省略可能

### 重要な設計原則

- **後のルールが優先**: 予期しない動作はまず順序を確認する
- **広い late グラント**: 後から追加された広いグラントは、先の deny を再度開放できる
- **追加プロファイル**: パス deny の最終オーバーライドレイヤーとして機能

### パスマッチャー

| タイプ | 説明 | 例 |
|--------|------|-----|
| `literal` | 完全一致 | `(literal "/path/to/file")` |
| `subpath` | 配下全体 | `(subpath "/path/to/dir")` |
| `prefix` | プレフィックス一致 | `(prefix "/path/to/")` |
| `regex` | 正規表現 | `(regex #"^/path/.*\.txt$"#)` |

### シンボリックリンク解決

組み込みプロファイルはシンボリックリンクターゲットを自動解決し、互換性を維持する。

### HOME プレースホルダ

プロファイル内で `__SAFEHOUSE_REPLACE_ME_WITH_ABSOLUTE_HOME_DIR__` トークンが使用され、組み立て時に実際の `$HOME` パスに置換される。

### メタデータオンリートラバーサル

再帰的読み取りを許可せずに `stat` 操作のみ許可する。`/`、`$HOME` へのパス、`$HOME` 自体にはこのモードが適用される。

## カスタマイズ

### 6つの拡張ポイント

1. **カスタム `.sb` オーバーレイ**: `--append-profile` で追加
2. **`profiles/20-network.sb`**: ネットワーク動作の調整
3. **`profiles/40-shared/`**: クロスエージェント共有ルールの変更
4. **`profiles/60-agents/`**: 新しいエージェントプロファイルの追加
5. **`profiles/65-apps/`**: デスクトップアプリプロファイルの追加
6. **`profiles/30-toolchains/`**: ツールチェーンプロファイルの追加

### 安全ガイドライン

- このdotfiles環境の前提と変更方針は SKILL.md の「設計哲学」「ポリシーとカスタマイズ」に従う
- HOME 外の worktree の参照で読み取り許可が不足する場合は、必要な範囲を `--add-dirs-ro` で指定する
- 検証は変更範囲に合わせる。dotfilesの文書修正にフルsuiteやSandbox外実行を一律に要求しない
- Safehouse本体のプロファイルやランタイムロジックを変更する場合は、必要に応じて `./scripts/generate-dist.sh` で配布アーティファクトを再生成する。dotfilesの追加profileだけの変更では不要

### ローカルオーバーライド

マシン固有の例外プロファイルを以下に配置：

```
~/.config/agent-safehouse/local-overrides.sb
```

この環境での追加順と `--allow-profile-writes` の扱いは SKILL.md の「ポリシーとカスタマイズ」を参照する。

### ワーキングディレクトリ設定ファイル

プロジェクトルートに `.safehouse` を配置：

```
add-dirs-ro=/path/to/shared/libs
add-dirs=/path/to/output
```

`--trust-workdir-config` で読み込む。

### グラントの優先順位

パスグラントは以下の順序でマージされる：
1. 信頼された設定ファイル（`.safehouse`）
2. 環境変数（`SAFEHOUSE_ADD_DIRS_RO`, `SAFEHOUSE_ADD_DIRS`, `SAFEHOUSE_WORKDIR`）
3. CLI フラグ

## 配布

### 単一ファイル配布

```bash
./scripts/generate-dist.sh
```

`dist/safehouse.sh` が生成される。ランタイムとポリシーモジュールをプレーンテキストとして埋め込んだ自己完結スクリプト。開発版と同等の CLI パリティを維持。

### ランタイムポリシーレンダリング

配布スクリプトは以下を実行時に処理：
- HOME 置換
- workdir/グラントの出力
- 組み込み絶対パスのシンボリックリンク解決

### Homebrew 配布

安定版リリースは Homebrew で公開：

```bash
brew install eugene1g/safehouse/agent-safehouse
```

### Electron アプリ

Safehouse 内でネストされたサンドボックスの初期化を防ぐため `--no-sandbox` フラグを維持。
