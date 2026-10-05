---
name: dotfiles-setup
description: >-
  ryonakae/dotfiles の macOS 環境を導入・更新・復元するための運用スキル。
  この dotfiles の Nix / Home Manager 設定変更、パッケージ追加、外部スキルの
  Source registry 管理、build / switch、別 Mac への復元、適用失敗の調査で使う。
  一般的な Nix の質問や、別プロジェクトの環境構築には使わない。
---

# dotfiles-setup

このスキルは操作の承認を代替しない。依頼に応じた範囲だけを進め、更新・ビルド・適用・サービス操作を分ける。

## 作業前

1. checkout は `~/dotfiles`。その `AGENTS.md` と Git 差分を確認し、他者の変更を保持する。設定は `config/` の正本を編集する。
2. [セットアップ手順](references/setup.md) の該当節を読む。初回導入、日常更新、復元、適用失敗を区別する。以前の移行計画や一時ディレクトリを現在の実機状態とみなさない。
3. `APP_SANDBOX_CONTAINER_ID` と `HERDR_ENV` を、セッション内で未確認なら個別に確認する。環境変数を一括出力しない。
4. 新規 Mac では Nix / Command Line Tools と非秘密の host 入力を準備する。導入済みの環境へ bootstrap を再実行しない。現在の作業ディレクトリが別リポジトリなら、そちらの設定を書き換えない。

以降のコマンドは dotfiles のルートから実行する。スキルの配置先ディレクトリで実行しない。

## 変更と更新を選ぶ

| 依頼 | 編集・操作 |
|---|---|
| 通常設定・HOME 配布用の自作スキルの本文編集 | `config/` の正本。既存 live link の本文変更だけなら再適用不要 |
| このリポジトリ専用のスキル編集 | `.agents/skills/` の正本。`.claude/skills/` は相対 symlink。Nix 適用は不要 |
| パッケージや HOME 配置対象の追加・削除 | 既存の Nix 定義を変更し、build 後に適用。HOME 配布用の自作スキルの新規追加も配置変更に含む |
| システム・管理ライブラリの更新 | `bash scripts/dotfiles.sh update <公開input名>`。名前は root `flake.lock` / `flake.nix` で確認 |
| 外部スキルの追加・選択変更 | `config/nix/skill-sources/` の取得元・探索範囲と `config/nix/home/skills.nix` の選択を確認 |
| 外部スキル取得元の更新 | `nix run .#skills-sources-lock`。標準の全取得元更新で、単体更新引数はない |
| 固定版からの復元・管理方式だけの移行 | 更新しない。root と registry の両 lock の revision を維持 |

`update all` は root Flake input 全体が対象で、外部スキルの専用 lock は更新しない。registry の宣言変更後の lock 再生成は既存取得元も更新するため、その範囲が依頼に含まれるか確認する。手書きの新しい updater やスキル取得用 root input は追加しない。

外部スキルは必要な集合だけを選ぶ。自作優先・Claude 専用同名優先・隠しディレクトリ除外・Antigravity CLI の共通参照を維持する。自作本文を store に固定しない。

## ビルドと適用

1. 必要な更新だけを行い、宣言・lock の差分を確認する。秘密やマシン固有の実ファイルを Git / store に含めない。
2. 新規ファイルを Git ソースへ含める場合は、対象を確認してパスを明示して追加する。他者差分を一括 stage しない。`path:.` で未追跡ファイルをまとめて取り込まない。
3. `bash scripts/dotfiles.sh build` を実行する。必要なら依頼に対応する `--host DIRECTORY` を指定する。build は適用せず、lock も更新しない。変更に関係する生成物と構文・テストを確認する。
4. 適用範囲の承認後に、対象ユーザーの通常の対話端末で `bash scripts/dotfiles.sh switch` を実行する。build と同じ host 入力を使い、スクリプト全体を sudo で起動しない。
5. 終了コードと現在の system、変更したリンク・ツールを確認する。スキル配置を変えた場合は選択集合・自作参照・管理外の兄弟項目も確認する。ビルド成功を適用成功と報告しない。

Safehouse 内から switch しない。既存の制限を回避せず、Herdr の利用が依頼・承認されていて `HERDR_ENV=1` なら、そのスキルに従って通常ペインへ渡す。それ以外は人間の通常端末へコマンドを案内する。sudo パスワードは人間が端末へ直接入力する。

一律のアプリ停止・全件棚卸し・全設定の退避を前提にしない。実際の衝突や書き込み競合がある対象についてだけ、必要な停止・保全と承認を確認する。Hermes が稼働する Mac では管理関数による停止が必要で、適用入口が自動停止・再開するわけではない。組織管理アプリは宣言から勝手に除かず、セットアップ手順のローカル skip を使う。

## 失敗・復旧

- エラー時は自動再試行せず、失敗段階・profile・既に変更された範囲を確認する。activation は非原子的で、失敗しても profile や一部設定が変わっている場合がある。
- 通常設定の未知の実体を force や一括削除で通さない。外部スキルの標準 HM link 置換と、通常設定の衝突は区別する。親ディレクトリ全体や Claude の `synced` を移動・削除しない。
- 世代の切替だけでは live link の本文、Homebrew アプリ、preferences、DB は戻らない。復旧範囲と操作を個別に確認する。検証目的の activation / dry-run、サービス再起動、GC は行わない。
- 秘密・Keychain・認証・バックアップ復元・権限変更は人間へ引き継ぐ。値を読み出したりログへ出したりしない。初回移行の履歴は参考資料であり、そこにある全操作を再実行しない。

## 完了時

変更した宣言・lock・文書、ビルドと実適用の結果、未検証事項を分けて報告する。commit / push は利用者の依頼または呼び出し元ワークフローの承認範囲に従う。
