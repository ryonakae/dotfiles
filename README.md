# dotfiles

macOS の開発環境と AI エージェントの設定を、新しい Mac に引き継ぐための個人用 dotfiles。
Nix / nix-darwin / Home Manager でツールの導入と設定のリンク配置を管理する。

この Mac の初回適用は完了し、拡張の機能確認と旧管理の整理を進めている。新規 Mac の導入は [セットアップ手順](docs/setup.md#nix-の初回導入)、適用前の注意と復旧は [適用と復旧準備](docs/setup.md#nix-の適用と復旧準備)を参照。

## Install

既存の設定をバックアップし、sandbox 外のターミナルで実行する。
Git が未導入なら、先に `xcode-select --install` で Command Line Tools を導入する。

```fish
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash scripts/bootstrap-nix.sh --install
```

完了後は新しいターミナルで Nix を確認し、[host 入力の準備と事前ビルド](docs/setup.md#nix-の事前ビルド)へ進む。既存の設定を使う Mac は、初回の退避・適用範囲を確認してから切り替える。
Homebrew 本体とアプリ、fish プラグイン、共通ランタイムも Nix 構成で管理する。Homebrew の別途 bootstrap や Fisher による導入は併用しない。

## Quickstart

Nix と host 入力を準備した後、構成を適用せずビルドする。

```fish
cd ~/dotfiles
bash scripts/dotfiles.sh build
```

適用する場合は、[適用と復旧準備](docs/setup.md#nix-の適用と復旧準備)を確認し、承認した範囲で Safehouse 外の対話端末から実行する。

```fish
bash scripts/dotfiles.sh switch
```

組織管理アプリをこの Mac だけ導入対象から除外する場合は、[Homebrew のローカル設定](docs/setup.md#組織管理アプリをこの-mac-だけスキップする)を使う。
AI エージェントの起動前に、[共通ツール用の秘密](docs/setup.md#共通ツール用の秘密)を設定する。日常の依存更新は [update の手順](docs/setup.md#nix-の事前ビルド)を使う。

## 外部スキル

自作スキルはこのリポジトリへの live link、外部スキルは Source registry の専用 lock で固定した store へのリンクとして Home Manager で配布する。外部スキルの更新はシステムの Flake input 更新と分ける。
追加・更新・復元と配布先の制約は[外部スキルの手順](docs/setup.md#外部スキル)を参照する。
iOS Simulator の検証は [use-agent-device](config/.agents/skills/use-agent-device/SKILL.md) を参照する。

## 運用

- **エージェント:** fish の起動関数から Safehouse 内で使う。HOME への広いアクセスを許可する互換性重視の構成で、完全隔離は保証しない。
- **削除と復元:** Nix 環境の `rm` は通常どおり直接削除する。ごみ箱へ移す場合は `gomi` を明示して使う。既存のごみ箱データは保持し、[復元手順](docs/setup.md#削除したファイルの復元)を参照。
- **常駐サービス:** [Hermes のセットアップ](docs/setup.md#hermes-agent)と [Herdr の復元](docs/setup.md#herdr)は、dotfiles の配布とは別に行う。
- **mosh:** Homebrew で更新するたびに `bash scripts/allow-mosh-firewall.sh` を実行し、署名とファイアウォール登録をやり直す。

Pi の導入拡張は [settings.json](config/.pi/agent/settings.json) を参照する。
設定や拡張を更新した後は Pi を起動し直す。
このリポジトリを編集するときの制約は [AGENTS.md](AGENTS.md) に記載する。
