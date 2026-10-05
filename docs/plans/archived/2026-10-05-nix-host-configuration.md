# ホスト設定を標準 Nix module に集約する Implementation Plan

## Requirements

[dig log](../../dig/2026-10-05-nix-host-configuration.md) と会話に基づく。Q1 は A（非秘密のホスト定義を Git 管理）、Q2 も A（既存の安全確認付き操作入口を残して簡素化）で承認済み。dig log に Q2 承認と実装状況を反映した。

- 独自の host.json を廃止し、ユーザー名・ホームを通常の nix-darwin module に定義する。非秘密のホスト定義は Git 管理し、clone 後にローカル JSON を用意しなくても build できるようにする。
- 現在の `darwinConfigurations.mac` と適用先 `ryo.nakae` / `/Users/ryo.nakae` を維持する。macOS のコンピューター名、ユーザー名、HOME を変更・作成する移行ではない。
- 独自 machine 引数、JSON 検証、一時 host snapshot、host input の差し替えを削除する。汎用ホストレジストリ、独自 option、将来用の factory は作らない。
- `scripts/dotfiles.sh` の build／switch／update 入口は維持する。固定 lock、Git 外ファイルの非取込、適用先と実行ユーザーの一致、root・非対話・Safehouse 内 switch 拒否、対話承認、既存の Hermes 停止確認を維持する。サービスの自動停止・再開は追加しない。
- 秘密・認証情報は Git／Nix store の対象外。AGENTS.md のマシン固有値に関する規約は、非秘密の Nix ホスト定義だけを例外にする。
- 既存の settings 3ファイルの変更を保持する。ツール・アプリ・preferences の値や Home Manager の配置方式は変えない。
- 実機 switch は別承認。今回の完了条件はテスト・評価・build・独立レビューまでで、サービス再起動や実機への適用を検証に使わない。

## Implementation Decisions

### Nix のユーザー定義を正本にする

- `config/nix/hosts/mac.nix` を追加し、`system.primaryUser = "ryo.nakae"` と `users.users."ryo.nakae".home = "/Users/ryo.nakae"` を定義する。現在の `darwinConfigurations.mac.modules` に加える。
- `config/nix/darwin/default.nix` から machine 由来のユーザー定義と host.json 用 assertion を除く。ユーザー名等はホスト module の標準 option に任せる。
- `homebrew.nix` の nix-homebrew.user は `config.system.primaryUser`、`preferences.nix` の HOME 配下パスは `config.users.users.${config.system.primaryUser}.home` を参照する。
- flake の Home Manager 統合を `config` を受け取る通常の module にし、`home-manager.users.${config.system.primaryUser}` を設定する。`inputs` の受け渡しは維持し、machine だけを廃止する。
- `config/nix/home/default.nix` の独自 home.username／home.homeDirectory 設定を除く。固定版 Home Manager の `nixos/common.nix` が OS の `users.users.<name>.name/home` を渡すことを確認済み。各モジュールで同じユーザー値を再定義しない。
- `config/nix/hosts/host.json.example` と Flake の host input を削除する。Git 外の既存 host.json があっても移動・削除しない。読込・fallback・互換経路は残さない。

### 操作入口は構成名を選ぶだけにする

- `build`／`switch` は既定の構成名 `mac` を使う。別のホストは `--configuration NAME` で `darwinConfigurations.NAME` を選ぶ。存在しない名前は Nix 評価エラーとして失敗し、mac に fallback しない。
- 旧 `--host DIRECTORY` は廃止して argparse で拒否する。意味を変えて同じ引数を再利用しない。`update [input|all]` はホストに依存しないので `--configuration` の指定を拒否する。
- build・適用先検査・switch は同じ構成名と Git 由来の固定 source snapshot を使う。属性名は文字列として安全に扱い、ドット等を別の属性経路や式として誤解釈しない。
- `locked_source` は Git Flake の `metadata --no-update-lock-file` から store source を解決するだけにする。JSON の読取・一時コピー・host override・host を除外した lock 比較と不要な import を取り除く。
- eval／check／build／switch に必要な lock 保護を維持する。単なる `--no-write-lock-file`（更新した lock を保存しないだけ）に依存せず、通常操作では `--no-update-lock-file` を使い、不整合は明示 update までエラーにする。
- `update all` の host 除外処理は不要になる。明示 update 以外で公開 input の revision を動かさない。

### lock と運用

- root flake.lock は host node と root の host 参照だけを除去する。Nix の lock 再生成を使う場合も公開 input の revision／narHash が一切変わらないことを機械的に比較する。公開 input の update は今回の範囲外。
- README、AGENTS.md、dotfiles-setup スキルと setup 手順を現行方式へ揃える。ホストを追加する場合は新しい Nix module と darwinConfigurations エントリを定義し、構成名で選択する。現時点で架空の2台目の本番設定は作らない。
- 過去の archived plan は当時の記録として維持する。現行手順や新しい dig log の状態だけを更新する。

## Tasks

Review base: `ae16a31957a46e02d37a5e76e285e66f5430e4b6`。開始時は master と origin/master が一致。既存の無関係な settings 3ファイルは保持する。Nix／CLI／規約・手順の切替は不可分なので、一つの成果物として検証・commit する。

- [x] **ホスト定義・CLI・テストを一体で移行**: `flake.nix`、`flake.lock`、`config/nix/hosts/`、`config/nix/darwin/{default,homebrew,preferences}.nix`、`config/nix/home/default.nix`、`scripts/dotfiles.py`、`scripts/tests/test_dotfiles_cli.py` を変更する。
  - この切替は一つの成果物として扱う。Nix 側だけ／CLI 側だけを先に運用できる互換層は設けない。
  - `tdd` に従い、既存 CLI 統合テストで「Git 管理の Nix 定義を読み、ローカル host ファイル不要で build できる」を先に表現する。既存の JSON fixture とそのためだけの検証は置き換える。
  - fixture に2つの構成を持たせ、既定 mac と明示構成の選択、不明な構成の失敗、build と switch 対象の一致を検証する。fixture は本番のホスト定義を増やさない。
  - lock 不整合拒否・明示 update・Git 外ファイルの非取込は継続する契約としてテストを維持する。switch の安全確認は副作用境界を stub／mock し、実際の sudo・activation・サービス処理を呼ばずに確認する。
- [x] **現行手順・規約を更新**: `AGENTS.md`、`README.md`、`.agents/skills/dotfiles-setup/SKILL.md`、同 `references/setup.md` を更新する。
  - host.json 作成手順と `--host DIRECTORY` をホスト module／構成名へ置き換える。秘密の管理外規約と標準の適用前確認は維持する。
  - dig log に Q2 承認と実装結果を反映する。README／AGENTS に設定値やファイル一覧を重複転記しない。

## 実装状況・再開条件

- 2026-10-05: Nix ホスト定義、標準 config 参照、CLI の JSON／snapshot／override 廃止、構成名選択、規約と手順の更新を実装。旧 host.json.example を削除し、Git 外の実ファイルには触れていない。
- 固定版 darwin-rebuild はフラグメントに引用符を許さず、ドットを属性経路として扱う。そのため構成名を `[A-Za-z_][A-Za-z0-9_-]*` に限定し、曖昧な属性経路・引用符等を引数処理時に拒否する。通常名 `mac`／`work-mac` は対応する。複雑な名前用の wrapper は追加しない。
- TDD: JSON 不在で旧 build が失敗する Red を確認し、JSON 処理削除後に既存4テストが成功。構成選択の未対応 Red を確認後に選択機能を追加。最終的に実 Nix の統合8件と、副作用を mock した switch 安全性7件、計15件が成功（skip なし）。
- nixfmt を変更した6つの Nix ファイルへ適用。`bash -n scripts/dotfiles.sh`、`git diff --check` が成功。lock は変更前の host node と参照だけを除いた辞書と完全一致し、公開 input は不変。
- 新規 `config/nix/hosts/mac.nix` のみを Git ソースへ明示追加して通常の `bash scripts/dotfiles.sh build` を実行。ローカル JSON や host override なしで flake check が成功。
- system build は既存の fish 依存評価で `getting status of "/nix/store/1562h92r7sppvrahcm4l89vlmfg5wb9i-source/.envrc": Operation not permitted`。固定 source は `/nix/store/b3jj2q9ckph46c200bis29ip4q4pykgy-source`。Safehouse 拒否を回避せず停止した。
- ユーザーの追加承認後、Herdr 通常ペインで同じ固定 source の非適用 build が終了コード0で成功。出力は `/nix/store/c4mnqzv56k8sr9bsxaasj7mlw8nbbbvr-darwin-system-26.11.4cff07d` で、移行前のビルド成果物と同一。activation・配置・preferences に差分はない。
- Nix 評価で primaryUser／Home Manager username／nix-homebrew.user が ryo.nakae、OS／Home Manager home が /Users/ryo.nakae と確認。変更した Nix 入力・lock・CLI 実装の8ファイルがビルド snapshot と一致することを比較した。
- nixfmt --check、shell 構文、差分検査が成功。最後のテスト変更は bytecode 生成抑制のみで switch 安全性7件を再実行して成功、統合8件の成功結果は再利用。テストが作った pycache は除去し、以降は生成しない。
- 現行コードに JSON input／machine 引数／--host が残らないことを確認。setup 手順の host.json 言及は「不要・旧実体は読まない」という移行説明のみ。文書更新は今回の差分に限定し、README／AGENTS とスキルの整合を確認済み。
- 実機 switch は未実施で別承認。独立レビュー結果は下記の gate summary に記録した。

## Final Validation

計画作成時は実行しない。実装時は次を確認する。

- [x] **CLI の契約と安全性**: `uv run --no-project python scripts/tests/test_dotfiles_cli.py` を実 Nix で実行し、skip ではなく成功すること。上記の build／構成選択／lock／非取込／switch の安全確認を検証する。拒否経路では sudo や activation に到達しないこと。
- [x] **構文・差分**: 固定 input の nixfmt で変更 Nix を確認、`bash -n scripts/dotfiles.sh`、`git diff --check`。削除した JSON input／machine 引数／--host の現行コード・手順への参照が残らないことは検索で一度だけ確認し、専用テストは作らない。
- [x] **lock 保全**: 変更前後を比較し、host node／参照の除去以外に差分がなく、全公開 input の固定値が一致すること。
- [x] **標準設定の伝播**: Nix 評価で primaryUser、users.users の home、Home Manager の username／homeDirectory、nix-homebrew.user が現在と一致すること。既存の live link と Dock の HOME 配下パスも変わらないこと。
- [x] **ローカル入力なしの通常 build**: 必要な新規 Nix ファイルだけ明示して Git ソースに追加し、`bash scripts/dotfiles.sh build` を実行する。host.json や --override-input host を用いず、lock を変更せず成功すること。生成 activation／配置を比較し、適用ユーザー・HOME と管理内容に意図しない差がないこと。ビルド成果物自体は実行しない。
- [x] **文書と移行**: 新規 clone からの手順にローカル host ファイルが不要で、別構成の指定、適用時のユーザー照合、秘密の除外が説明されていること。Git 外の実ファイルを変更・削除していないこと。

このセッションでは Safehouse 内で既存 fish 依存の `.envrc` が拒否され、前の作業は承認済みの Herdr 通常ペインで build を検証した。今回も拒否されたら回避せず報告し、この変更に対する sandbox 外の非適用テスト／build の承認を得て実行する。前回の別変更の承認を実機 switch や任意の外部操作へ広げない。

## Gate summary

- 実装 commit: `d9c2e82`。review base: `ae16a31957a46e02d37a5e76e285e66f5430e4b6`。
- 独立 read-only reviewer が base..d9c2e82 を確認し、blocking/high・decision required・medium/low の指摘なし。修正 cycle なし。
- 実 Nix 統合8件・switch 安全性7件、固定 lock 比較、Nix formatter、shell 構文、設定伝播、同一 system 出力の build の成功結果を再利用。レビュー後はこの記録・アーカイブと参照更新だけを行い、実装は変えていない。
- doc-updater の確認範囲は本変更の16ファイル。README／AGENTS／スキル／setup の必要な更新は実装と同じ commit に含む。追加の文書変更は不要。
- 実装の受入条件に未解決事項なし。実機 switch は今回の受入条件ではなく、別承認のまま。既存の無関係な settings 3ファイルは保持する。
- 本アーカイブ commit と実装 commit をまとめて通常 push する。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
