---
name: dotfiles-setup
description: >-
  ryonakae/dotfiles の macOS 環境を導入・更新・復元するための運用スキル。
  この dotfiles の Nix / Homebrew / mise 設定変更、パッケージ追加、外部スキルの Source registry 管理、
  build / switch / setup、直接リンクの配置、ツールのバージョン差・更新相談、別 Mac への復元、適用失敗の調査で使う。
  一般的な Nix の質問や、別プロジェクトの環境構築には使わない。
---

# dotfiles-setup

このスキルはエージェント向け。ユーザーへの操作案内には `docs/` の該当手順を使い、内部の制約をまとめて読ませない。

## 着手時

1. `~/dotfiles` の `AGENTS.md` と Git 差分を確認する。他者の変更を保持し、ホーム側ではなく `config/` の正本を編集する。
2. `APP_SANDBOX_CONTAINER_ID` と `HERDR_ENV` を個別に確認する。環境変数・設定・秘密を全量出力しない。
3. 依頼が初回導入・日常更新・移行・復旧のどれかを判断し、下表の資料と[運用条件](references/setup.md)の該当節を読む。
4. 編集、検証、実機適用、認証・権限変更の承認を分ける。このスキルの起動を実操作の承認とみなさない。

## ユーザーへ案内する手順

| 目的 | 正本 |
|---|---|
| 新しい Mac の導入 | [初回セットアップ](../../../docs/setup.md) |
| 設定・アプリ・runtime・Nix の更新 | [日常操作](../../../docs/usage.md) |
| 共通 API キーの準備・追加・更新 | [秘密の管理](../../../docs/secrets.md) |
| 失敗の対処・設定配置の再開 | [トラブル対応](../../../docs/troubleshooting.md) |
| 旧 HM 所有リンク・既存 Homebrew の移行 | [既存環境の移行](../../../docs/migration.md) |
| Hermes・Herdr・個別アプリ | [アプリ別設定](../../../docs/apps.md) |

## 変更と検証

- 通常設定の本文は直接リンクで即時反映。配置変更は mise、アプリ一覧は Nix 宣言、通常アプリの導入・更新は Homebrew、共通 runtime は mise を使う。別の管理方式を重ねない。
- build は検査・ビルド、switch は明示した成果物の適用、setup は両者と確認付き配置・HOME からの runtime install。chsh は別操作。Git 管理外のファイルを Nix store に取り込まない。
- 外部スキルは Source registry と専用 lock、自作は mise の2 glob。取得元の追加・選択・配布優先順位は[運用条件](references/setup.md#外部自作スキル)を確認する。
- 最新版の相談では、解決先・使用版・管理元の提供版を調べる。更新済みと希望版の取得・動作成功を区別する。固定版からの復元に更新を混ぜない。
- 変更ファイルの構文・差分・関連テストを検証する。Nix 変更は対象構成を build する。検証のために activation、サービス再起動、GC を実行しない。

## 実機適用と復旧

- setup / switch は対象ユーザーの通常対話端末から、Safehouse 外で行う。全体を sudo で起動せず、秘密・Keychain 登録はユーザーへ引き継ぐ。
- Hermes は既存管理関数で停止・再開する。適用入口へ自動停止・状態保存・rollback を追加しない。
- 旧 HM からの移行では所有解除前に、実 HOME の mise dry-run を時間制限付きで完了確認する。既知の旧 HM 衝突以外の問題・未知の実体・timeout があれば停止する。
- 未知のファイル・リンクを force や一括退避で置換しない。競合する対象だけ保全し、既存 backup、管理外の兄弟、認証・session・DB を保持する。
- 失敗時は終了コード、profile / current-system、変更済み範囲を確認する。自動再試行しない。設定配置だけ失敗した場合は、成功済み switch を繰り返さない。

## 完了報告

変更した宣言・lock・文書、実行した検証、実際に適用した操作、未検証の範囲を分けて伝える。ビルド成功を実機適用成功として報告しない。commit / push は依頼または呼び出し元の承認範囲に従う。
