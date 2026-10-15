# dotfiles

macOS の開発環境と AI エージェントの個人設定。
Homebrew の Brewfile でアプリ、mise でランタイム・設定リンク・macOS の設定を管理する。

## 使い方

**新しい Mac では、[初回セットアップ](docs/setup.md)を上から進める。** 標準のターミナルと zsh から始められる。

導入済みなら、必要な手順だけ読む。

| やりたいこと | 手順 |
|---|---|
| 設定・アプリ・ランタイムを更新する | [日常操作](docs/usage.md) |
| `.env` に API キーを追加・更新する | [共通 API キー](docs/secrets.md#値を追加更新する) |
| インストールや配置のエラーを解決する | [トラブル対応](docs/troubleshooting.md) |
| Hermes・Herdr などを設定する | [アプリ別設定](docs/apps.md) |
| Nix / Home Manager 管理から切り替える | [既存環境の移行](docs/migration.md) |
| 削除したファイルを戻す | [ごみ箱から復元](docs/troubleshooting.md#削除したファイルを復元する) |
| iOS Simulator で検証する | [use-agent-device](config/.agents/skills/use-agent-device/SKILL.md) |

エージェントは fish の起動関数から Safehouse 内で使う。HOME への広いアクセスを許可する構成で、完全隔離ではない。

## エージェントに変更を任せる

編集・検証のルールは [AGENTS.md](AGENTS.md)、導入・更新・復旧の判断基準は [dotfiles-setup](.agents/skills/dotfiles-setup/SKILL.md) を参照する。
