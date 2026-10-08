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

1. **カスタム `.sb` オーバーレイ**: `--append-profile` で読み込み。認証情報 deny 等を追加
2. **`profiles/20-network.sb`**: ネットワーク動作の調整
3. **`profiles/40-shared/`**: クロスエージェント共有ルールの変更
4. **`profiles/60-agents/`**: 新しいエージェントプロファイルの追加
5. **`profiles/65-apps/`**: デスクトップアプリプロファイルの追加
6. **`profiles/30-toolchains/`**: ツールチェーンプロファイルの追加

### 安全ガイドライン

- このdotfiles環境では開発の互換性を優先し、HOME RW、`wide-read`、全環境継承、既存の `process-control` と広域IPC許可を維持する。`allow default` や `/` のRWには変更しない
- 標準機能と生成policyの最終順序を確認し、必要性と保護への影響を説明して、ユーザー承認後に最小修正する
- 機密・個人データの独自denyは設けない。ごみ箱payloadと `/bin/rm` 実行は後段のprofileで拒否する。OS重要領域は標準のdeny-first構成で書き込み許可を広げず、最終policyで範囲を確認する。拒否された操作や機密へのprobeを無断で外側に回さない
- worktree が安定した親ディレクトリ配下にある場合、`--add-dirs-ro` で親を指定してクロス worktree 読み取りアクセスを許可
- 検証は変更範囲に合わせる。dotfilesの文書修正にフルsuiteやSandbox外実行を一律に要求しない
- Safehouse本体のプロファイルやランタイムロジックを変更する場合は、必要に応じて `./scripts/generate-dist.sh` で配布アーティファクトを再生成する。dotfilesの追加profileだけの変更では不要

### ローカルオーバーライド

マシン固有の例外プロファイルを以下に配置：

```
~/.config/agent-safehouse/local-overrides.sb
```

この環境は `compatibility.sb` → `local-overrides.sb` の順で追加する。広域IPCとSimulatorの `system-fsctl` は前者、ごみ箱保護と `/bin/rm` 実行拒否は後者にまとめる。既存の広域allowと重複する個別Mach/network/signalルールは追加しない。

機密・個人データの独自denyと、それだけのためのvendor・Hermes等のallow例外は撤廃済み。ごみ箱payloadの直接読み取り・上書き・削除の拒否は維持し、metadataとrenameによる投入は許可する。Hermes配下もごみ箱保護の対象とし、アプリ固有の例外は設けない。親・ごみ箱ルートのrenameに関する限界は残り、完全な削除防止ではない。通常rmのgtrash転送は失敗しても直接削除へ戻らず、復元・掃除は人間がsandbox外で行う。

Safehouse標準のappend profile書き込み保護は独自denyとは別で、3起動経路の `--allow-profile-writes` で省く。これは書き込みgrantを追加せず、`.safehouse` の標準保護も解除しない。承認後に `config/` の正本を編集し、次回起動で反映する。実行中のsandboxは変更できず、現在の拒否を無断で迂回しない。

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
