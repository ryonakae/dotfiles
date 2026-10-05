# dotfiles

macOS の開発環境と AI エージェントの設定を、新しい Mac に引き継ぐための個人用 dotfiles。
Nix / nix-darwin / Home Manager でツールの導入と設定のリンク配置を管理する。

## Install

Git が未導入なら、先に `xcode-select --install` で Command Line Tools を導入する。
新規 Mac では、sandbox 外の通常端末で実行する。

```fish
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash scripts/bootstrap-nix.sh --install
```

導入済みの Mac で bootstrap をやり直さない。続きは `dotfiles-setup` スキル同梱の[セットアップ手順](.agents/skills/dotfiles-setup/references/setup.md)。host 入力、秘密・認証、既存設定との衝突を必要な範囲で確認する。Homebrew の別途 bootstrap や Fisher による導入は併用しない。

## 日常の変更

通常設定と自作スキルの本文は `config/` の正本を編集する。既存の live link を通じて反映されるため、本文変更だけなら Nix 再適用は不要。
パッケージや配置対象を変更した場合は、まずビルドする。

```fish
cd ~/dotfiles
bash scripts/dotfiles.sh build
```

生成物と適用範囲を確認し、通常の対話端末で `bash scripts/dotfiles.sh switch` を実行する。
依存更新・復元・失敗時の扱いは[セットアップ手順](.agents/skills/dotfiles-setup/references/setup.md)を参照。外部スキルの Source registry 更新は、システムの Flake input 更新とは別操作。

エージェントに作業を任せる場合は [dotfiles-setup](.agents/skills/dotfiles-setup/SKILL.md) を使う。リポジトリ共通の編集・検証上の制約は [AGENTS.md](AGENTS.md) を参照する。

## 手動設定・運用

- **秘密・認証・サービス初期設定:** [同梱の手順](.agents/skills/dotfiles-setup/references/setup.md)に従い、人間が sandbox 外で行う。
- **削除と復元:** `rm` は直接削除する。ごみ箱へ移す場合は `gomi` を明示し、[復元手順](.agents/skills/dotfiles-setup/references/setup.md#削除したファイルの復元)を使う。
- **mosh:** Homebrew で更新するたびに `bash scripts/allow-mosh-firewall.sh` を実行し、署名とファイアウォール登録をやり直す。
- **iOS Simulator の検証:** [use-agent-device](config/.agents/skills/use-agent-device/SKILL.md) を参照する。

エージェントは fish の起動関数から Safehouse 内で使う。HOME への広いアクセスを許可する互換性重視の構成で、完全隔離は保証しない。
