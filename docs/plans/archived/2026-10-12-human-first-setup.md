# ユーザー向け初回セットアップの整理 Implementation Plan

## Requirements

- README と setup.md を、コーディングエージェントがまだ使えない新規 Mac で、ユーザーが順に進められる構成にする。
- 完了範囲はツール・設定・ランタイムを揃えてエージェントを起動できるところまで。認証、API キー登録、秘密の復元方法は初回手順に含めず、ユーザーに任せる。
- 今回実機で確認した /etc/bashrc・/etc/zshrc の衝突と com.apple.universalaccess 書き込み失敗への対処を、適切な時点に置く。フルディスクアクセス付与後に進んだことと、switch 全体の成功は区別する。
- 初回の通常経路は switch 一回とする。既存スクリプトが check → build → 対話確認 → 適用を実装しており、別途 build は不要。適用なしの検証用 build は残す。
- switch 前に App Store を開いてサインインし、Xcode を先にインストールする。Xcode を起動してライセンスに同意し、初期設定を完了してから switch へ進む。エージェントの認証手順とは区別する。
- ユーザー実機では、mas が App Store を開くまで進まず、購入時のパスワード要求によりアプリごとの入力が必要だった。「メディアと購入」の要求頻度を見直す任意の選択肢を説明する。認証を弱める設定を必須化・自動適用せず、OS・アカウントによる選択肢の差を確認する。
- ユーザー実機では Homebrew のインストールが Xcode ライセンス未同意で失敗した。Command Line Tools の導入と Xcode のライセンス同意は区別し、ユーザーによる事前確認を案内する。
- `bashrc`・`zshrc` の初回衝突対応を switch スクリプトへ追加する。内容・退避先の表示後に別途承認を求め、既存退避の保全、管理済みリンクの維持、異常時の適用中止を守る。CLI 入口と一時ファイルによるテストを含め、ユーザー承認済み。
- `default`・`private` の両構成で Nix 版 fish をログインシェルとして利用可能にする。設定配置と fish の起動確認後、ユーザーが標準の `chsh` で切り替える手順を記載する。実行中の zsh は維持し、設定配置が完了するまで初回作業用の端末を閉じない。ユーザー承認済み。
- TCC 権限の自動変更、自動再試行、実機適用、適用順序の変更、commit / push は対象外。

議論: [dig log](../../dig/2026-10-12-human-first-setup.md)。

## Implementation Decisions

- ユーザー向け手順の正本は既存の `.agents/skills/dotfiles-setup/references/setup.md` のまま。README は入口と用途別リンクに絞り、詳細手順を重複させない。
- setup.md の先頭を新規 Mac の時系列手順にする。既存 Mac の所有権移行、日常更新、管理方式、任意の機能別設定は後段へ分離する。既存の認証・秘密に関する参照資料は削除せず、初回導線の外に置く。
- 初期段階は標準 Terminal / zsh で実行できるコマンドを使い、fish 導入後の切替地点を明記する。導入前の mise / Homebrew / エージェントを前提にしない。
- 初回手順は、App Store・Xcode の導入とライセンス同意・CLT・Terminal 権限、clone・ホスト確認、Nix 導入、switch 内の shell 退避確認と適用、完了確認、設定配置、fish の起動確認と chsh、runtime、エージェント起動確認の順で構成する。家用 private と default の選び方をコマンド実行前に示す。
- フルディスクアクセスは実行元アプリに対する広い権限であることを明記し、ユーザーが設定する。shell ファイルの退避は switch 内で内容・種別・既存退避先を確認し、ユーザーが承認した場合だけ行う。独自設定の引継ぎが未確認なら承認せず停止する。手動 mv を通常の初回手順にしない。
- `nix/darwin/default.nix` で `environment.shells = [ pkgs.fish ]` を宣言し、`/etc/shells` へ安定パスを登録する。設定配置後にユーザーが `chsh -s /run/current-system/sw/bin/fish` を実行する。固定版 nix-darwin では管理外の既存ユーザーの UserShell は変更されないため、ユーザーの shell 属性は追加しない。管理者ユーザーを `users.knownUsers` へ追加せず、switch からの `chsh` も行わない。
- エラーごとに再開地点と停止条件を示す。失敗時に bootstrap や退避操作を繰り返さず、成功した工程をやり直さない。profile の存在だけで適用成功としない。
- `safe.fish` → `run-with-agent-env.sh` は dotenvx の strict モードで `~/.config/.env` を読み込む。秘密環境の準備はユーザーが済ませる前提とだけ記し、未準備でも起動できるとは案内しない。各サービスのログイン方法は追加しない。

## 追加確認事項

- ローカルで確認した nix-darwin の `modules/system/activation-scripts.nix` は defaults / userDefaults → homebrew の順。リポジトリには順序変更の宣言がない。今回この順序は変更しない。
- Xcode は masApps の宣言にも残すが、新規 Mac ではその導入を switch に任せず、事前に手動でインストール・ライセンス同意を済ませる。
- 現在の `nix/darwin/preferences.nix` は App Store のパスワード要求頻度を管理していない。macOS 設定を先に適用すれば購入設定も変更されるとは案内せず、ユーザーの事前準備として扱う。

## shell 設定の退避仕様（承認済み）

- `scripts/dotfiles.py` の switch に、候補が管理する `/etc/bashrc`・`/etc/zshrc` だけを対象とした退避処理を追加する。build は読み取り・ビルドのみのまま維持する。
- 通常ファイルはローカル端末で内容と退避先を示し、switch の確認とは別に明示的な退避承認を受ける。既存バックアップ、未知のリンク、ディレクトリ、確認後の変更があれば停止する。
- nix-darwin 管理のリンクは触らない。退避済みで元ファイルがない場合は通常の switch を続行する。既存バックアップを上書きしない。
- サービス停止検査と適用承認が成功した後に退避し、退避失敗なら activation を実行しない。途中まで退避して失敗した場合は成功済み対象を報告し、自動 rollback・再試行は行わない。
- macOS の `renamex_np(RENAME_EXCL)` で排他的に移動し、退避先を承認時の内容・メタデータと照合する。不一致なら移動済みデータを残して停止する。API 非対応や操作失敗時に上書き可能な方法へフォールバックしない。
- テスト境界は既存の `scripts/tests/test_dotfiles_cli.py` の CLI `main()` とする。ファイルは一時ディレクトリ、sudo / activation は代替処理で確認し、実 `/etc` は変更しない。承認・拒否・既存退避保全・リンクの扱い・失敗時の適用中止を確認する。macOS 実権限下の動作は、このテストでは検証しない。

## Tasks

レビュー基点: `4f2bd3ba4d29617919568fb6f29c437e4ff0b104`。以前の用語統一による差分と、ユーザーの Claude / Pi 設定差分は保持する。今回の対象外ファイルを検証・レビューの変更範囲へ含めない。

- [x] 初回 shell 設定の引継ぎ: `scripts/dotfiles.py` と `scripts/tests/test_dotfiles_cli.py` を TDD で変更し、ドキュメントの手動 mv をスクリプトの確認手順へ置き換える。
  - 結果: CLI 入口の red → green を確認し、確認付き退避を実装。独立レビューで検出した最終検査後の競合を再現し、排他的原子移動へ修正。最終CLI全体33テスト成功、skip 0。限定再レビューで解消を確認。
- [x] ログインシェル: `nix/darwin/default.nix` で fish を利用可能なログインシェルに登録し、`default`・`private` の両構成を検証する。初回手順へ `chsh` と新しい端末での確認を記載する。
  - 結果: 両構成の `/etc/shells` 登録を red → green で確認。両buildの生成物で登録行と実行可能な fish を確認。ユーザーによる chsh と新規端末の確認手順を記載し、独立レビューで文書との整合を確認。
- [x] ユーザー向け導線: `README.md` と `.agents/skills/dotfiles-setup/references/setup.md` を上記構成へ整理する。
  - 結果: README を入口と用途別リンクに整理。setup.md は初回の8手順、停止時の対処、日常運用、既存 Mac の移行、任意リファレンスへ再構成。相対リンク・掲載コマンド構文・独立レビューを確認済み。
  - 必要な安全条件を該当手順の近くに置き、抽象的な管理説明や既存環境の移行条件を新規導入の必須作業に混ぜない。
  - 手順の各段階で使用可能なコマンド、成功の確認方法、次の工程を明確にする。
- [x] 参照の整合: `.agents/skills/dotfiles-setup/SKILL.md` の初回手順と build / switch の説明を整合させる。影響を受ける文書のリンクも修正する。
  - エージェントによる事前検証とユーザーによる実適用の分離、既存 Mac の移行条件は維持する。
  - dig log の決定事項・未決事項を最終合意に合わせる。

## Final Validation

- [x] CLI の退避・キャンセル・既存バックアップ保全・管理済み／未知のリンク・確認後の変更・退避失敗時の適用中止・build の非変更性を `uv run --no-project python scripts/tests/test_dotfiles_cli.py` で確認する。sudo と実 `/etc` はテストで使わない。実 Nix 必須のテストが skip の場合は成功扱いにしない。
- [x] fish の登録を `default`・`private` の Nix 評価テストで確認し、`bash scripts/dotfiles.sh build` と `bash scripts/dotfiles.sh build --configuration private` で生成された `/etc/shells` と fish 実行パスを確認する。switch / chsh は実行しない。
  - 結果: 最終の両buildは終了0。default `/nix/store/1c3qymb8slxvhy01d1p7bn1r67xpiz79-darwin-system-26.11.4cff07d`、private `/nix/store/dhzy80rybxq0xa64cfg9xxhkjrplfwrg-darwin-system-26.11.4cff07d`。各 `etc/shells` と `sw/bin/fish` を確認済み。
- [x] 変更した Python と shell 入口の構文、独立した読み取り専用レビューで退避の安全性・文書の初回導線を確認する。
- [x] 記載するコマンドを `scripts/dotfiles.py`、bootstrap、mise 宣言、fish と起動 wrapper に照合する。追加オプションは実装または help で確認する。
- [x] 標準 zsh の新規 Mac を想定して先頭から読み、未導入ツールの先行使用、エージェントの認証操作の要求、別途 build の必須化がなく、switch 前に Xcode のインストールとライセンス同意があることを確認する。
- [x] 今回の2つの停止について、予防・確認・対処・再開地点が分かり、未知内容の上書きや既存退避の破壊へ誘導しないことを確認する。
- [x] 変更文書の相対リンク・見出しアンカーと、リポジトリ内から変更見出しへの参照を確認する。
- [x] `git diff --check` と差分レビューで、他者の未コミット変更を保持し、依頼外の運用変更がないことを確認する。bootstrap / switch / サービス操作は実行しない。build は承認された Nix 設定変更の検証としてのみ実行する。

## 検証・レビュー結果

- CLI 全体33テスト成功、skip 0。ログ: `/tmp/dotfiles-setup-validation.1jr2c8/cli-reviewed.log`。
- 両build成功。ログ: 同ディレクトリの `build-default-final.log`、`build-private-final.log`。既存の dirty tree と skills-sources-lock の meta 未指定警告は残る。
- 相対リンク53件、setup.md への既存の見出し参照、shell コード40ブロック、Python 2ファイル、昇格後の退避プログラム、shell 入口の構文を確認。`git diff --check` 成功。
- 独立レビュー: 基点 `4f2bd3b` からの対象6ファイルの作業ツリー差分を確認。退避の最終検査と unlink の間の置換競合を high として採用し、1回の修正サイクルで排他的原子移動と移動後照合へ変更。再レビューで解消、新しい blocking/high・decision required なし。
- レビューで残った非blockingの指摘: 移動後に元パスが再出現する停止分岐の直接テストは未追加。移動直前の元パス置換、退避先作成、途中失敗はテスト済み。
- 未検証: 新規 Mac での一連の実操作、実 `/etc` と sudo 権限下の退避、FDA・App Store・Xcode の画面操作、chsh 後のログインとエージェント起動。これらはユーザー側で確認する。
- commit / push / 実機適用は依頼範囲外のため未実施。ユーザーの Claude / Pi 設定差分と、前の用語統一差分は保持した。
