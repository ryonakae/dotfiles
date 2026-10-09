# dotfiles

macOS の開発環境と AI エージェントの設定を、新しい Mac に引き継ぐための個人用 dotfiles。
Nix で macOS と基盤、Homebrew で普段使うアプリ、mise で共通ランタイムと設定の直接リンクを管理する。

## Install

Git が未導入なら、先に `xcode-select --install` で Command Line Tools を導入する。
新規 Mac では、sandbox 外の通常端末で実行する。

```fish
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash scripts/bootstrap-nix.sh --install
```

導入済みの Mac で bootstrap をやり直さない。続きは `dotfiles-setup` スキル同梱の[セットアップ手順](.agents/skills/dotfiles-setup/references/setup.md)。Nix のホスト定義、秘密・認証、既存設定との衝突を必要な範囲で確認する。Homebrew の別途 bootstrap や Fisher による導入は併用しない。

## 日常の変更

通常設定と自作スキルの本文は `config/` の正本を編集する。HOME からの直接リンクに即時反映されるため、本文変更だけなら再適用は不要。アプリ・設定ディレクトリ単位の Git manifest で配置する。既存 manifest 内の追跡ファイル増減は apply で反映し、個別リンクや管理ディレクトリの追加はルートの `mise.toml` も更新する。削除・改名は宣言を消す前に対象を unapply する。

```fish
mise -C ~/dotfiles dot apply
```

- **CLI / GUI:** Homebrew で更新する。導入一覧は Nix 宣言に保ち、追加・削除は一覧と対象の install / uninstall を整合させる。
- **共通ランタイム:** mise の Git 正本で版を指定し、install / upgrade を使い分ける。個別プロジェクトの版指定は維持する。
- **Nix 基盤・外部スキル:** 宣言・lock を確認して `bash scripts/dotfiles.sh build`、適用承認後に通常の対話端末で `bash scripts/dotfiles.sh switch` を使う。

既定では共通の `default` 構成を使う。家用Macでは build／switch の両方に `--configuration private` を指定する。
自作スキルの glob 配置と削除前の unapply、依存更新・初回切替の事前確認・復元・失敗時の扱いは[セットアップ手順](.agents/skills/dotfiles-setup/references/setup.md)を参照。外部スキルの Source registry 更新は、システムの Flake input 更新とは別操作。

エージェントに作業を任せる場合は [dotfiles-setup](.agents/skills/dotfiles-setup/SKILL.md) を使う。リポジトリ共通の編集・検証上の制約は [AGENTS.md](AGENTS.md) を参照する。

## 手動設定・運用

- **秘密・認証・サービス初期設定:** [同梱の手順](.agents/skills/dotfiles-setup/references/setup.md)に従い、人間が sandbox 外で行う。
- **削除と復元:** 人間の通常端末では `rm` は直接削除し、Safehouse 内では gtrash でごみ箱へ移す。復元・掃除は人間が sandbox 外で[復元手順](.agents/skills/dotfiles-setup/references/setup.md#削除したファイルの復元)に従って行う。
- **mosh:** Homebrew で更新するたびに `bash scripts/allow-mosh-firewall.sh` を実行し、署名とファイアウォール登録をやり直す。
- **iOS Simulator の検証:** [use-agent-device](config/.agents/skills/use-agent-device/SKILL.md) を参照する。

エージェントは fish の起動関数から Safehouse 内で使う。HOME への広いアクセスを許可する互換性重視の構成で、完全隔離は保証しない。
