# dotfiles

macOS の開発環境と AI エージェントの設定を、新しい Mac に引き継ぐための個人用 dotfiles。
Nix で macOS と基盤、Homebrew でアプリ、mise で共通ランタイムと設定のリンクを管理する。

## 新しい Mac に導入する

**[セットアップ手順](.agents/skills/dotfiles-setup/references/setup.md#新しい-mac-のセットアップ)を上から順に進める。**

標準の「ターミナル」と zsh から始め、エージェントを起動できるところまで案内する。
Xcode・App Store・端末の権限を準備してから Nix を導入し、`setup` でビルド・適用・設定配置まで進める。その後、fish への切替とランタイム導入を行う。エージェントの認証方法の解説は含めない。

家用は `private`、共通設定だけなら `default` を選ぶ。導入中に止まったら、最初からやり直さず[該当する対処](.agents/skills/dotfiles-setup/references/setup.md#初回導入で止まったとき)を確認する。

## 導入後に使う手順

| 目的 | 参照先 |
|---|---|
| 設定・アプリ・ランタイムを更新する | [日常の変更と更新](.agents/skills/dotfiles-setup/references/setup.md#日常の変更と更新) |
| 設定ファイルの配置を変える | [管理の分担と通常配置](.agents/skills/dotfiles-setup/references/setup.md#管理の分担と通常配置) |
| 既存の Home Manager 配置から移行する | [既存 Mac の切替](.agents/skills/dotfiles-setup/references/setup.md#既存-mac-の切替) |
| 任意のアプリ・サービスを設定する | [機能別リファレンス](.agents/skills/dotfiles-setup/references/setup.md#機能別リファレンス) |
| エージェントに dotfiles の操作を任せる | [dotfiles-setup スキル](.agents/skills/dotfiles-setup/SKILL.md) |
| iOS Simulator で検証する | [use-agent-device](config/.agents/skills/use-agent-device/SKILL.md) |

mosh を Homebrew で更新した後は、`bash scripts/allow-mosh-firewall.sh` で署名とファイアウォール登録をやり直す。
リポジトリの編集・検証ルールは [AGENTS.md](AGENTS.md) を参照する。

エージェントは fish の起動関数から Safehouse 内で使う。HOME への広いアクセスを許可する互換性重視の構成で、完全隔離は保証しない。

## 削除したファイルの復元

Safehouse 内の `rm` は gtrash でごみ箱へ移す。ユーザーの通常端末では直接削除となり、ごみ箱からは復元できない。通常端末でもごみ箱へ移したい場合は `gtrash put` を使う。

保存先は Finder のごみ箱とは別で、HOME volume では既定で `~/.local/share/Trash`（`XDG_DATA_HOME` 指定時はその配下）。別 volume ではその volume のごみ箱を使い、利用できなければ失敗する。

削除操作が終わってから、ユーザーが Safehouse 外の通常端末で復元する。

```fish
gtrash restore
```

TUI の `?` で操作方法を確認する。復元先に別のデータがある場合は、必要に応じて `--restore-to` で別の場所へ戻す。復元・掃除中は削除操作を並行実行せず、永久削除は復元・バックアップを確認してから行う。

既存の gomi データを復元する場合：

```fish
gomi --config "$HOME/.config/gomi/config.yaml" --restore
```
