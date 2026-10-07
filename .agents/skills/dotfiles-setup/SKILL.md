---
name: dotfiles-setup
description: >-
  ryonakae/dotfiles の macOS 環境を導入・更新・復元するための運用スキル。
  この dotfiles の Nix / Homebrew / mise 設定変更、パッケージ追加、外部スキルの
  Source registry 管理、build / switch、直接リンクの配置、ツールのバージョン差・更新相談、別 Mac への復元、適用失敗の調査で使う。
  一般的な Nix の質問や、別プロジェクトの環境構築には使わない。
---

# dotfiles-setup

このスキルは操作の承認を代替しない。依頼に応じた範囲だけを進め、更新・ビルド・適用・サービス操作を分ける。

## 作業前

1. checkout は `~/dotfiles`。その `AGENTS.md` と Git 差分を確認し、他者の変更を保持する。設定は `config/` の正本を編集する。
2. [セットアップ手順](references/setup.md) の該当節を読む。初回導入、日常更新、復元、適用失敗を区別する。以前の移行計画や一時ディレクトリを現在の実機状態とみなさない。
3. `APP_SANDBOX_CONTAINER_ID` と `HERDR_ENV` を、セッション内で未確認なら個別に確認する。環境変数を一括出力しない。
4. 新規 Mac では Nix / Command Line Tools と適用先に合う Nix ホスト定義を準備する。導入済みの環境へ bootstrap を再実行しない。現在の作業ディレクトリが別リポジトリなら、そちらの設定を書き換えない。

以降のコマンドは dotfiles のルートから実行する。スキルの配置先ディレクトリで実行しない。

## 変更と更新を選ぶ

| 依頼 | 編集・操作 |
|---|---|
| 通常設定・HOME 配布用の自作スキルの本文編集 | `config/` の正本。直接リンクの本文変更だけなら再適用不要 |
| 既存 Git manifest 内の追跡ファイル増減 | 対象を確認して `mise -C ~/dotfiles dot apply` |
| 個別リンク・管理ディレクトリの追加・削除 | ルート `mise.toml` を更新する。削除・改名は宣言を消す前に標準 unapply。詳細は同梱手順に従う |
| このリポジトリ専用のスキル編集 | `.agents/skills/` の正本。`.claude/skills/` は相対 symlink。HOME 配布とは別 |
| 通常 CLI / GUI の追加・削除 | `nix/darwin/homebrew.nix` の一覧を整合させ、対象限定の `brew install` / `brew uninstall`。Nix build / switch は必須でない |
| 通常 CLI / GUI の更新 | Homebrew。cask の自己更新・`auto_updates` / `latest` の扱いを確認し、無条件に全件 greedy 更新しない |
| 共通ランタイムの導入・更新 | `config/.config/mise/config.base.toml` の版指定と mise install / upgrade。個別プロジェクトは変更しない |
| OS・Nix・Homebrew 本体・Bash / fish / mise と補完依存・管理ライブラリの更新 | `bash scripts/dotfiles.sh update <公開input名>` → build → 承認後に switch。名前は root `flake.lock` / `flake.nix` で確認 |
| 外部スキルの追加・選択変更 | `nix/skill-sources/` の取得元・探索範囲と `nix/home/skills.nix` の選択を確認 |
| 外部スキル取得元の更新 | `nix run .#skills-sources-lock`。標準の全取得元更新で、単体更新引数はない |
| 固定版からの復元・管理方式だけの移行 | 更新しない。root と registry の両 lock の revision を維持 |

`update all` は root Flake input 全体が対象で、外部スキルの専用 lock は更新しない。registry の宣言変更後の lock 再生成は既存取得元も更新するため、その範囲が依頼に含まれるか確認する。手書きの新しい updater やスキル取得用 root input は追加しない。

HOME 全体を `symlink-each` の配置先にせず、アプリ・設定ディレクトリ単位の Git manifest で配置する。管理記録がない初回には各配置先全体を走査する。`exclude` はこの走査を止めないため、実 HOME の dry-run 完了を確認する。配布対象は Git 追跡ファイルとし、除外は追跡済みの配布不要物と別宣言の対象に絞る。[PR #11549](https://github.com/jdx/mise/pull/11549) の改善後も記録欠落・不正時の走査は残る。

外部スキルは必要な集合だけを選ぶ。自作優先・Claude 専用同名優先・隠しディレクトリ除外・Antigravity CLI の共通参照を維持する。自作本文を store に固定しない。自作スキルの共通・Claude 向け2 glob を維持し、通常の追加は Git 追跡と mise apply で行い、名前を列挙しない。外部との優先関係が変わる場合だけ Nix 側も適用する。

## ツールの版が古い・最新版を導入したい場合

まず現在の解決先と管理主体を確認する。通常 CLI / GUI は Homebrew、共通ランタイムは mise、Nix に残した本体・依存だけを Flake input 更新へ案内する。上流のリリース、管理元の提供版、手元の使用版を区別し、未確認の版を最新版と断定しない。

- Homebrew は `brew update && brew upgrade` が日常の更新入口。本体は nix-homebrew で更新する。cask と自己更新抑止の確認は[同梱手順](references/setup.md#homebrew-本体とアプリの管理)に従う。
- mise の exact pin は自動で進まない。Git 正本の指定変更と install / upgrade を区別し、復元には更新を混ぜない。
- Nix 管理なら公開 input を必要な範囲だけ更新する。同じ input の他の依存への影響、lock 差分、収録版を確認する。標準更新でも希望版に届かないと確認できてから代案を相談する。
- 相談だけなら操作せず、更新成功を希望版の取得や実機適用成功と同一視しない。確認方法は[同梱手順](references/setup.md#ツールのバージョン差を確認する)を参照する。

## Nix のビルドと適用

1. 必要な更新だけを行い、宣言・lock の差分を確認する。非秘密の Nix ホスト定義以外の、Git 管理外のマシン固有ファイルや秘密を Git / store に含めない。
2. 新規ファイルを Git ソースへ含める場合は、対象を確認してパスを明示して追加する。他者差分を一括 stage しない。`path:.` で未追跡ファイルをまとめて取り込まない。
3. `bash scripts/dotfiles.sh build` を実行する。既定の `mac` 以外を使う場合は、定義済みの構成名を `--configuration NAME` で指定する。build は適用せず、lock も更新しない。変更に関係する生成物と構文・テストを確認する。
4. 適用範囲の承認後に、対象ユーザーの通常の対話端末で `bash scripts/dotfiles.sh switch` を実行する。build と同じ構成名を使う。switch はその呼び出しで snapshot / check / build を行い、過去 build の出力を受け渡す方式ではない。スクリプト全体を sudo で起動しない。
5. 終了コードと現在の system、変更したリンク・ツールを確認する。スキル配置を変えた場合は選択集合・自作参照・管理外の兄弟項目も確認する。ビルド成功を適用成功と報告しない。

Safehouse 内から switch しない。既存の制限を回避せず、Herdr の利用が依頼・承認されていて `HERDR_ENV=1` なら、そのスキルに従って通常ペインへ渡す。それ以外は人間の通常端末へコマンドを案内する。sudo パスワードは人間が端末へ直接入力する。

一律のアプリ停止・全件棚卸し・全設定の退避を前提にしない。実際の衝突や書き込み競合がある対象についてだけ、必要な停止・保全と承認を確認する。Hermes が稼働する Mac では管理関数による停止が必要で、適用入口が自動停止・再開するわけではない。組織管理アプリは宣言から勝手に除かず、セットアップ手順のローカル skip を使う。

## 失敗・復旧

- エラー時は自動再試行せず、失敗段階・profile・既に変更された範囲を確認する。activation は非原子的で、失敗しても profile や一部設定が変わっている場合がある。
- 通常設定の未知の実体を force や一括削除で通さない。mise apply 前に対象の実体とリンク先を確認し、未知の symlink を自動拒否すると仮定しない。外部スキルの標準 HM link 置換とは区別する。親ディレクトリ全体や Claude の `synced` を移動・削除しない。
- 初回の所有権移行・Herdr integration は[同梱手順](references/setup.md#初回の配置と既存-mac-の切替)に従い、実機操作を別途承認する。Nix 所有解除前に実 HOME の mise dry-run を時間制限付きで完了確認し、既知の旧 HM リンクによる衝突以外の問題やタイムアウトがあれば switch しない。dry-run 成功だけで後続成功を保証しない。切替中の新規アプリ起動を避け、失敗時は現状を確認して、所有リンクの引渡し・旧世代復旧を承認下で行う。自動 rollback や独自配置ツールは追加しない。Hermes の installer 禁止とサービス運用は変えない。
- Nix 世代の切替だけでは mise 所有リンク、正本の本文、Homebrew アプリ、mise runtime、preferences、DB は戻らない。所有権の引渡しと内容の復旧を分ける。検証目的の Nix activation / dry-run、サービス再起動、GC は行わない。
- 秘密・Keychain・認証・バックアップ復元・権限変更は人間へ引き継ぐ。値を読み出したりログへ出したりしない。初回移行の履歴は参考資料であり、そこにある全操作を再実行しない。

## 完了時

変更した宣言・lock・文書、実行した Homebrew / mise 操作、Nix のビルドと実適用の結果、未検証事項を分けて報告する。commit / push は利用者の依頼または呼び出し元ワークフローの承認範囲に従う。
