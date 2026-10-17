# dotfiles

macOS の開発環境と AI エージェントの個人設定。

- アプリは Homebrew の Brewfile、設定ファイルのリンク・ランタイム・macOS 設定は mise で管理する。
- 導入対象は構成で選ぶ。共通の `default` に、家用の `private` か仕事用の `work` を組み合わせる。
- Claude Code・Codex・Pi などのエージェントは、fish の起動関数から Agent Safehouse のサンドボックス内で起動する。HOME への広いアクセスを許可する構成で、完全隔離ではない。

## リポジトリの中身

| 場所 | 内容 |
|---|---|
| `config/` | HOME へリンクする設定ファイルの正本。fish・Ghostty・Karabiner・各エージェントの設定と、共通ランタイムの版 |
| `brew/` | 構成別の Brewfile |
| `mise.<構成>.toml` | 構成別の設定リンク・外部リポジトリ・macOS 設定の宣言 |
| `scripts/` | setup の入口と補助スクリプト |
| `docs/` | ユーザー向け手順 |

## ドキュメント

- [初回セットアップ](docs/setup.md)
- [日常操作](docs/usage.md)
- [共通 API キー](docs/secrets.md)
- [アプリ別設定](docs/apps.md)
- [トラブル対応](docs/troubleshooting.md)
