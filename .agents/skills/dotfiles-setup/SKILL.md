---
name: dotfiles-setup
description: >-
  ryonakae/dotfiles の macOS 環境を導入・更新・復元するための運用スキル。
  この dotfiles の Homebrew / Brewfile / mise 設定変更、パッケージ追加、外部スキル・plugin の取得と配置、
  setup、直接リンク、ツールのバージョン差・更新相談、別 Mac への復元、適用失敗で使う。
  別プロジェクトの環境構築には使わない。
---

# dotfiles-setup

ユーザーへの操作案内には `docs/` の該当手順を使う。

## 着手時

1. `~/dotfiles` の `AGENTS.md` と Git 差分を確認する。
2. `APP_SANDBOX_CONTAINER_ID` を確認する。環境変数・設定・秘密を全量出力しない。
3. 初回導入・日常更新・復旧のどれかを判断し、下表と[運用条件](references/setup.md)の該当節を読む。
4. スキル起動・計画承認を実操作の承認とみなさない。

## ユーザーへ案内する手順

| 目的 | 正本 |
|---|---|
| 新しい Mac の導入 | [初回セットアップ](../../../docs/setup.md) |
| 設定・アプリ・runtime・macOS の更新 | [日常操作](../../../docs/usage.md) |
| 環境変数の準備・追加・更新 | [環境変数の管理](../../../docs/secrets.md) |
| 失敗の対処・配置の再開 | [トラブル対応](../../../docs/troubleshooting.md) |
| Hermes・Herdr・個別アプリ | [アプリ別設定](../../../docs/apps.md) |

## 変更・適用・復旧

編集と検証は `AGENTS.md`、管理元ごとの判断基準・実機操作の承認・失敗時の扱いは[運用条件](references/setup.md)に従う。

## 完了報告

変更した宣言・文書、実行した検証、実際の適用、未検証範囲を分けて伝える。
