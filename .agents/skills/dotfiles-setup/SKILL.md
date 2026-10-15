---
name: dotfiles-setup
description: >-
  ryonakae/dotfiles の macOS 環境を導入・更新・復元するための運用スキル。
  この dotfiles の Homebrew / Brewfile / mise 設定変更、パッケージ追加、外部スキル・plugin の取得と配置、
  setup、直接リンク、ツールのバージョン差・更新相談、別 Mac への復元、適用失敗、Nix からの引渡し・撤去で使う。
  一般的な Nix の質問や、別プロジェクトの環境構築には使わない。
---

# dotfiles-setup

このスキルはエージェント向け。ユーザーへの操作案内には `docs/` の該当手順を使い、内部制約をまとめて読ませない。

## 着手時

1. `~/dotfiles` の `AGENTS.md` と Git 差分を確認する。他者の変更を保持し、ホーム側ではなく `config/` の正本を編集する。
2. `APP_SANDBOX_CONTAINER_ID` と `HERDR_ENV` を個別に確認する。環境変数・設定・秘密を全量出力しない。
3. 初回導入・日常更新・移行・復旧のどれかを判断し、下表と[運用条件](references/setup.md)の該当節を読む。
4. 編集、検証、実機適用、認証・権限変更の承認を分ける。スキル起動・計画承認を実操作の承認とみなさない。

## ユーザーへ案内する手順

| 目的 | 正本 |
|---|---|
| 新しい Mac の導入 | [初回セットアップ](../../../docs/setup.md) |
| 設定・アプリ・runtime・macOS の更新 | [日常操作](../../../docs/usage.md) |
| 共通 API キーの準備・追加・更新 | [秘密の管理](../../../docs/secrets.md) |
| 失敗の対処・配置の再開 | [トラブル対応](../../../docs/troubleshooting.md) |
| 旧 HM・nix-homebrew の引渡しと Nix 撤去 | [既存環境の移行](../../../docs/migration.md) |
| Hermes・Herdr・個別アプリ | [アプリ別設定](../../../docs/apps.md) |

## 変更と検証

- 本文は直接リンクで即時反映。配置・外部 repos・macOS defaults は構成別 mise 宣言、アプリ一覧は構成別 Brewfile、共通 runtime は既存 mise 設定を使う。別管理方式を重ねない。
- 構成は全件明示し、default を自動追加しない。ルート `mise.toml` に共通リソースを置かない。全体 setup と標準ツールの部分操作を分け、旧 Nix build/switch/update の恒久互換層は追加しない。
- runtime の exact 版を維持する。Hermes は指定 fork の ryonakae ブランチを未導入時だけ入れ、更新は別の明示操作。追加依存・全機能確認は移行ゲートにしない。
- 外部スキル・fish/Yazi plugin はブランチ追従を許容し、スキルは選択済みだけ配置する。自作の2 glob・共通優先関係は[運用条件](references/setup.md#外部自作スキル)を確認する。
- 最新版の相談では解決先・使用版・管理元の提供版を分ける。更新済みと希望版の取得・動作成功を区別する。
- 構文・差分・関連テストを確認する。検証のために実 HOME apply、サービス再起動、installer、GC を実行しない。

## 実機適用と復旧

- setup は対象ユーザーの通常対話端末から Safehouse 外で行う。全体を sudo で起動せず、秘密・Keychain 登録はユーザーへ引き継ぐ。
- Hermes は既存管理関数で操作する。適用入口へ自動停止・再開・状態保存・rollback を追加しない。
- 旧 HM の所有解除前に実 HOME の配置 dry-run を60秒の制限付きで完了確認する。既知の旧 HM 衝突以外の問題・未知の実体・timeout では停止する。
- 既存 Nix 管理 Homebrew は通常 setup で置換しない。一時 HM 引渡し・Homebrew 本体移管・nix-darwin・Nix 本体撤去は別工程で再承認する。
- 未知の実体を force や一括退避で置換しない。対象だけ保全し、既存 backup、認証・session・DB・管理外の兄弟を保持する。
- 失敗時は終了コードと変更済み段階を確認する。自動再試行せず、成功済み段階を繰り返さず標準コマンドで再開する。

## 完了報告

変更した宣言・文書、実行した検証、実際の適用、未検証範囲を分けて伝える。ビルド成功を実機成功として報告しない。commit / push は呼び出し元の承認範囲に従う。
