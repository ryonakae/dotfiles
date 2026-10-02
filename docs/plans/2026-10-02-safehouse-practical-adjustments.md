# Safehouseの実用優先への調整 Implementation Plan

[元計画](2026-10-02-safehouse-compatibility.md)と[dig log](../dig/2026-10-02-safehouse-compatibility.md)の続き。元計画の実装・検証履歴は残し、矛盾する受入条件は本計画で置き換える。本計画は方針への「じゃあそれで」を受けて保存し、計画提示後の「ok」で実装を承認された。

## Requirements

- 目的は完全な隔離ではなく、普段の開発・テスト・ツール利用を妨げにくくし、重要ファイルの直接アクセスと通常rmの誤削除に備えること。使い勝手と管理の簡単さを優先する。
- 実装済みのHOME読み書き許可、環境変数全継承、ホストプロセス操作、IPC・Macサービス連携を維持する。Documents、Music/Musics、Movies、Downloads、Picturesは許可のままとする。HOME外への全面書き込み許可は追加しない。
- 追加のファイル許可は、`.secrets`のメタデータ・追跡用`.gitkeep`と、`~/.android/debug.keystore`の2点だけ。その他の実.env、秘密鍵、本番署名鍵、実config.fish、人間用ブラウザ・Mail/Messages等の保護と、既存のvendor/Hermes例外は維持する。
- OpenHandsは未使用なので例外を追加せず、アンインストールもしない。原因未確定のnice/cwdエラー、テスト用.env領域の新設、OS権限/TCC変更を今回へ追加しない。
- 通常rmは普段のfish、子shell、エージェント、Hermesサービスでgomiへ転送する。OSのrmは改変せず、実rmへのfallback、コピー＋元データ削除、永久削除の自動化は行わない。絶対パスrm、言語API、Git、上書きによるデータ損失まで保証しない。
- dotenvxの共通注入を維持する。共通キーにTYPESAFE_API_KEYを含め、Git管理するテンプレートは空値のみ。実秘密の移行・暗号化・実鍵の登録・バックアップはユーザー操作とする。復号済みの値はエージェントと子プロセスから利用できることを許容する。
- 既存TMPDIR補正、HISTFILE、workdir、各CLI引数、mise/venv、Hermes待受設定と正規停止、サービス間の意図したfeature差分を保持する。他者の変更・既存実ファイルは上書きしない。

## Implementation Decisions

### 2か所のファイル許可

`config/.config/agent-safehouse/local-overrides.sb`の該当denyに狭い例外を加える。

- `.secrets`はディレクトリ一覧と配下のメタデータ確認を許可し、直下の`.gitkeep`だけはGitのstatus/diff/add/checkoutやworktree展開に必要な読み書きを許可する。それ以外のファイルの内容読み取り・変更・削除は引き続き拒否する。ファイル名と属性は見えるという保護範囲にする。`secrets`という名前全般へ例外を広げない。
- `~/.android/debug.keystore`だけを読み書き可能にする。親`.android`は既存のHOME許可を使う。他の`.keystore`、release用署名鍵には例外を広げない。
- profile順序は既存どおり。symlinkで別の保護対象を指した場合まで、これらの例外によって内容が開放されないことをダミーで確認する。

直近7日間の保存ログ調査では、Claudeの`.secrets/.gitkeep`拒否が231結果・21 session、Lefthookの全ファイル列挙失敗が1結果あり、piでも反復した。Androidではdebug keystore生成失敗を確認した。件数は警告・ログ再読を含み、独立した停止回数ではない。調査の全出典はローカル一時レポート `/tmp/safehouse-session-audit.eFEMFp/summary.md` にあり、この計画の実施に一時ファイルの永続性は要求しない。

### rm/gomiの簡素化

- `config/.local/bin/rm`は引数検査、必要な依存/設定確認、共有ロック、gomiへの逐次転送、失敗通知に絞る。既存のuv scriptとPython標準機能を使い、新しい依存・外部ヘルパーは追加しない。
- よく使う`-f/-r/-R/-v/--`を維持する。既存の`-i`の対象単位確認と`-d`の空directory判定は小さな処理として残し、rmの完全互換を目指した機能追加はしない。未対応/gomi専用optionは全対象の操作前に拒否し、ファイル名はgomiの`--`以降に渡す。
- `check_protected_path`の外部trash発見・祖先探索を廃止する。標準/指定XDGの保存先とロックを巻き込む通常の操作に対する、小さな固定対象のガードは残す。未知のmount・移動済みのごみ箱まで追跡しない。
- 同時rmの保存競合を防ぐ共有ロックと、各operandの逐次転送は残す。通常のCtrl-C/SIGTERMで次のoperandへ進まず、子の処理中に別rmが同時保存しないことを守る。子へのロックFD継承は既存の標準機能を再利用し、過剰なグローバル状態・signal分岐を整理する。特殊なkillタイミング全般を新たな保証対象にしない。
- `config/.config/gomi/config.yaml`はXDG/no-fallback、復元確認、永久削除無効、保存先自身・システム主要パスの禁止を中心にする。未使用legacy項目、配色/レイアウトの複製、空フィルター、debugログ設定は削除候補。gomi 1.6.5は省略値を全面的に既定補完しないため、転送・一覧・TUI復元に必要な項目だけ実動作に基づいて残す。
- 移動失敗や壊れたsymlinkは元の対象を保持して非zero。独自の移動/コピーfallbackは追加しない。複数対象の途中失敗は部分成功として報告し、rollbackを作らない。

### 旧受入条件の置換

- ごみ箱payloadへの通常の直接アクセスを拒否する既存の簡単なpolicyは残すが、祖先をHermes例外へ移すなど特殊な迂回の完全封鎖は完了条件から外す。既知の残存経路を「修正済み」とは記録しない。これを理由にHermesの信頼領域を狭めたり、新しい探索/監視を作ったりしない。
- dotenvx経由のCtrl-Cで外側がexit 1になる観測は許容する。通常終了の数値code、TTY、キャンセル後の子停止、Hermesの正規停止を確認するが、signal終了状態やPIDの完全一致のための独自注入処理は追加しない。
- SwiftPM/Flutterの二重sandboxは別対応。内側sandboxの無効化が可能な起動経路を確認し、できない経路だけ承認済みの外側ビルドを使う方針だが、今回のdotfiles変更で各プロジェクトのbuild設定を変更しない。未解決の互換性制約として残し、本計画の完了条件から分離する。

## Tasks

実装開始時: `master`、upstream `origin/master`、ahead/behind 3/0、stagedなし。補足のreview baseは`93001c5e8d0efe638deed9d3cb0485d3a80d497f`、全体のreview baseは元計画の`38b8996b957ed7f63fd461e9503cfbe147955265`。先行3 commitは同テーマの承認済み成果物。他者のREADME 2 hunk、共通AGENTS、Claude/Pi/mise設定、skills-lockとuse-agent-deviceを保持し、対象外とする。

- [x] **狭い例外の追加**: `local-overrides.sb`と`scripts/tests/check_safehouse_runtime.py`に2例外と隣接する保護対象の回帰確認を加える。既存profileに必要以上の整理・許可を追加しない。
  - `f9defb5`でcommit済み。Red: `.secrets` stat拒否、debug.keystore作成拒否をそれぞれnative再現。Green: `PRACTICAL_POLICY_FINAL=0`、73 checks通過。Gitのstatus/add/diff/checkout-index、隣接秘密のread/write/unlink拒否、通常keystoreと.envを指すalias拒否、既存例外・trash Putを確認。初回のregex候補はescapeの誤りで不一致だったため、既存のSBPL記法に修正した。
- [x] **rm/gomiの簡素化**: `config/.local/bin/rm`、`config/.config/gomi/config.yaml`、`scripts/tests/test_rm_trash.py`、必要なら`check_gomi_runtime.py`を上記の契約に合わせる。既存のfish→PATH転送は維持する。廃止した探索・過剰保証だけを検証するテストは整理し、保存・失敗・並行実行のテストを残す。
  - `0113a7f`でcommit済み。rmは167→157行、gomi設定は75→27行。外部trash探索、legacy/UI配色/空フィルター/debug設定を削除し、signal状態を子実行中のローカルhandlerへ整理。SIGHUPの追加保証テストを除き、INT/TERM・子FD継承・frRvid/--は維持。全20 tests（rm14/runtime5/TMPDIR1）が24.032秒で通過。`PRACTICAL_GOMI_DONE=0`でproduction policy内Put、隔離TUIの一覧/確認/復元、4並列同名保存を確認。
- [x] **運用文書と注入確認**: `README.md`とルート`AGENTS.md`の今回の箇所だけ更新し、旧計画へ本補足計画の優先を明記する。`config/.config/.env.example`には追加済みの`TYPESAFE_API_KEY=`を含める。共通loaderをキー名ごとに改修せず、任意キーの継承を既存runtimeテストで確認する。
  - `39207c2`までにcommit済み。READMEは他者のNode/npm・agent-device 2 hunkを保持。旧計画に補足計画の優先を記し、通常rmの範囲とCtrl-Cのexit 1許容を文書化。TYPESAFE_API_KEYは空値1件、テンプレート内全値が空であることを確認。READMEは既存部分込み646行のためdoc-updaterの300行超警告に該当するが、全体整理は対象外。
- [ ] **配布と実動作確認**: 不足する`compatibility.sb`、共通loader、rm等を含む配置を揃え、新規起動で確認する。既存の`~/.config/gomi/config.yaml`は実ファイルなので、設定内容・用途の確認と退避の承認後に置き換える。実秘密の移行前に既存CLI/サービスを壊す中途半端な配布・再起動をしない。

## Final Validation

既存の21 unit tests、ダミーpolicy、実gomi復元・並列保存、ダミーKeychain/launchdの成功は旧実装の結果。変更した契約・コードに近い項目を再検証し、無関係なKeychain検証を反復しない。実装は既存のTDD手順を使う。

- [x] **2例外と機密保護**: sandbox外で作った一時HOME/一時Git repoを使い、`check_safehouse_runtime.py`で`.secrets`のmetadataと`.gitkeep`を扱えること、Gitのstatus/diff/addと新worktree相当のcheckoutで当該警告が出ないことを確認する。隣接する秘密ファイルは読めず変更・削除できない。debug.keystoreは読み書きでき、別名keystore・実.envへのsymlinkは保護される。実際の秘密・署名鍵を使わない。
- [x] **通常rmと失敗時の保全**: `env PYTHONDONTWRITEBYTECODE=1 uv run python -m unittest discover -s scripts/tests -p 'test_*.py'` → 対応option、空白/option風の名前、directory/symlink、複数対象、依存/保存失敗、並列実行、通常キャンセル、fishと子shellの転送が通る。実rmへのfallbackはなく、保存失敗時は元データが残る。
- [x] **短縮設定の実gomi**: sandbox外から `uv run --no-project scripts/tests/check_gomi_runtime.py` → production policy内でPut、metadata作成、並列同名保存、外側の隔離TUIで一覧・復元が成功する。過去の実ごみ箱に触れず、新規ダミーだけを使う。
- [ ] **起動と互換性**: 新しい設定で起動した環境から、非機密env値、ps、Unix socketのlisten/connectとテスト、HOME内のWrangler/Kotlin/agent-device相当のダミー保存先を確認する。TTYとCtrl-Cで子が止まることを確認し、exit 1をsignal透過失敗として再び停止理由にしない。実際の各CLI・利用ツールでも主要導線を確認し、未確認のツールを解消済みと表示しない。
- [ ] **配布・秘密移行・Hermes**: ユーザーによる共通秘密の暗号化/鍵登録/バックアップと既存gomi設定の扱いを確認してから配置し、新しいfish/子shell/エージェントのrm解決を確認する。既存の`hermes-gateway`/`hermes-dashboard`管理関数で再起動・health/status・正規停止を確認する。実秘密は読まず、鍵取得の対話要求やハングは未解決として報告する。
- [x] **構文・差分・独立レビュー**: 変更したfishの`fish --no-execute`、shellの構文、Pythonの構文と`git diff --check`を確認する。独立レビューは本計画の直接アクセス保護・データ保全・承認範囲に照らして行い、完全な迂回防止や終了状態一致を追加要求しない。他者のREADME hunk・設定・スキルを保持し、実秘密をstageしない。

## 実装・配布時の境界

- 現在のSafehouse制限を迂回しない。使用中policyの編集やnative dummy検証は、既存の承認範囲内でsandbox外のHerdrペインを使う。実秘密・既存設定の退避・既存サービス操作はそれぞれ必要な確認を行う。
- 元計画で承認済みの成果物単位local commitと、全gate通過後のcurrent branchへの通常push 1回の手順を引き継ぐ。force push/amend等はしない。配布やユーザー側の移行が未完了なら、コード完了と運用適用完了を分けて報告し、全体完了・archive・pushへ進めない。
- 互換性の追加確認で、`process-control`を有効にしたダミーHOMEの新しいsandboxでも`/bin/ps`のexecがEPERMになった。`/tmp/dotfiles-practical-compatibility.log`に記録。process-controlで解消済みとは扱わず、許可の追加や受入条件の変更前に確認する。`/bin/ps`はsetuid実行ファイルだが、それだけで原因確定とはしない。
- `ps`以外の確認は`PRACTICAL_COMPAT_OTHER_DONE=0`。所有するダミーhostプロセスへのsignal、Wrangler/Kotlin/agent-device相当の保存先、AF_UNIX listen/connect、共通loaderのenv注入・TTY・Ctrl-Cによる子停止を確認した。外側のexit 1は合意どおり許容する。実ツール全体や既存サービスの動作まで確認した結果ではない。
- ステージング時に既存`.git/index.lock`で失敗。mtimeは2026-10-02 15:45:30（作業確認時17:14）、サイズ0、`lsof -t .git/index.lock`は所有processを出さずexit 1。ユーザーの「削除でいいです」で承認を得て、所有process不在・通常の空ファイル・inode/mtimeの不変を再確認して削除した。index自体は変更していない。psの受入判断は未解決。独立したread-onlyレビューは`39207c2`に対してApproved。コード修正を要するblocking/high・medium/lowはなし。`93001c5..39207c2`を中心に全体baseからの変更、関連起動経路と配布契約も確認し、commit版のPython AST・shell/fish構文・差分検査を通過。unit/native/host結果は親報告であり、reviewerによる独立再実行ではない。psと本番配布の残ゲートは解消しておらず、全体完了とはしない。
- HOME配布、既存gomi設定の退避、本番秘密移行、全CLIと既存Hermesサービスの確認は未実施。他者の変更を保持し、archive/pushはしない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、本計画と元計画をそれぞれ同名のまま `docs/plans/archived/` へ移す。
