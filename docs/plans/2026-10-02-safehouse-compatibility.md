# Safehouseの互換性緩和・gomi・dotenvx導入 Implementation Plan

参照: [dig log](../dig/2026-10-02-safehouse-compatibility.md)。Q12の全体方針への回答「ok」と、その後のQ13:A（XDG方式・コピーへのフォールバック無効化）の説明への回答「ok」を含めて計画化する。dig logの最終確認待ちという記載は会話で解決済み。計画作成時点では計画ファイルだけを変更し、設定変更・インストール・テスト実行・commit・pushは行っていない。その後の`/implement`で実装を承認され、gomiは`brew install gomi`での導入を明示された。

## Requirements

- Safehouseを継続し、Claude Code、pi、Codex、OpenCode、Antigravity CLI（既存の`gemini`関数）、Hermes対話CLIとgateway/dashboardに共通方針を適用する。
- 互換性を優先し、環境変数を全継承する。ホストプロセス操作・IPC・Macサービス・GUI連携を許可する。HOME配下は原則読み書き可能とし、作業リポジトリ中心へ許可を絞らない。HOME外の書き込みまで全面開放する変更ではない。
- HOMEの許可を広げても、機密・私的ファイルの直接の読み書き保護を残す。SSH agent、エージェント用ブラウザ、vendor内fixture、既存の`~/.hermes`信頼境界などの意図した例外は維持する。外部アプリ・MCP・Docker・Keychain・許可したホストプロセスまで含む完全な隔離は保証しない。
- 普段のfishターミナル、エージェント、そのPATHを継承する子シェル、Hermesサービスの通常の`rm`をgomiへ転送する。`/bin/rm`の改変はしない。絶対パスのrm、独自にPATHを設定するプロセス、Python/Nodeの直接削除、Gitの破壊的操作、上書き・切り詰めは保護外。
- gomiはXDG方式を選び、`core.trash.home_fallback: false`で、直接移動に失敗した際のコピー＋元データ削除を無効にする。同じボリューム内のごみ箱が利用できなければ元データを残してエラーにする。標準の保存先は`~/.local/share/Trash`で、Finderのごみ箱とは別。復元にはgomiを使う。
- ごみ箱の自動掃除・永久削除の自動化は導入しない。通常のrm転送からgomiのprune等の永久削除機能を呼べないようにする。手動の復元・ごみ箱掃除は通常のrmと分ける。
- 共通ツール用の秘密はdotenvxで暗号化し、`~/.config/.env`からエージェントとHermesサービスの起動時に自動注入する。ツール別には分割せず、AIへの特別なコマンド指示にも依存しない。注入した値がエージェントと子プロセスから利用できることは許容する。
- Git管理するのは秘密を含まない`config/.config/.env.example`。実体の`config/.config/.env`は既存の`.gitignore`の`.env`で除外し、`~/.config/.env`へsymlinkする。プロジェクト用秘密はこの共通ファイルに混ぜず、必要なアプリ・テスト・デプロイのコマンド単位で注入する。
- 復号鍵はmacOS Keychainに保存する。launchd経由の非対話起動から取得できることを受入条件とする。取得できなければ相談し、鍵ファイル方式へ無断で切り替えない。初期の実秘密移行・実鍵登録・バックアップはユーザーが行い、エージェントは既存の秘密の値を読まない。
- 既存のTMPDIR補正、HISTFILE、Git rootのworkdir、各CLIの起動引数、mise/venv、Hermesの待受設定・正規シャットダウンを維持する。gateway/dashboardに既存の非対話用途を理由とするfeature差分があることも尊重する。
- 開始時に存在する`config/.claude/settings.json`と`config/.pi/agent/settings.json`の他者変更を保持する。Hermesの認証・config.yaml・実行中の自己改善データは変更対象にしない。

## Implementation Decisions

### Safehouseの許可と保護の順序

- インストール済みSafehouse 0.12.0の`--env`と`--add-dirs="$HOME"`を使い、個別の`--env-pass`とHOME内top-level許可の列挙を置き換える。現在のworkdir検出とHOME外に必要な標準ランタイム許可は維持する。
- `process-control`と`launch-services`を明示的に有効化する。IPC・Machサービス・Unix socket通信は、ファイルアクセスと切り離した互換性オーバーレイ`config/.config/agent-safehouse/compatibility.sb`で緩める。具体的なoperationは0.12.0の定義・コンパイラで確認する。`allow default`でファイル制限ごと解除しない。
- 読み込み順は標準profile/HOME許可 → `compatibility.sb` → `local-overrides.sb`とする。Safehouse標準の末尾のprofile書き込み保護と`.safehouse`書き込み保護を維持し、`--allow-profile-writes`等は通常起動に追加しない。
- `local-overrides.sb`には、HOME許可で再開放される保護を明示する。対象は現行の.env/credentials/秘密鍵等のパターン、fish実設定と実体、GnuPG/AWS/netrc/Git/Kubernetes credential、SSH秘密鍵、Mail/Messages/人間用ブラウザデータ等。`~/Library`全体を拒否してGUIやキャッシュを壊す構成にはしない。SSHのconfig/known_hosts/socketと`~/.config/agent-browser/profile`は必要な例外を残す。
- symlinkの実体側にも保護が効くことを確認する。保護ディレクトリやその親のrenameで保護が外れる経路も確認し、必要な親ディレクトリ自体の移動・削除を止める場合も、その配下の通常ファイルの書き込みは広く許可する。
- 通常のrmラッパー・gomi設定・起動時の秘密注入処理がエージェントから書き換えられないよう、管理ファイルと実体の書き込みを保護する。人間のsandbox外での編集は妨げない。共通.envはsandboxの外でdotenvxに読み込ませるため、そのファイルをsandbox内から読む許可は追加しない。
- rm転送のtrash祖先検出はHOME/指定XDGと、operandの祖先/直下に存在する既知の外部trashまでとする。深いmountを含む任意のdirectoryの網羅は対象外（実装中にユーザーがAを承認）。既知の外部XDG形式の内容保護は対象外にしない。
- 人間が捨てた機密ファイルが共有のごみ箱へ移って保護対象外になる点にも対処する。XDGごみ箱のpayloadにはsandbox内からの内容読み取りを許可せず、gomiのPutに必要なmetadataアクセス・書き込みと`.trashinfo`の処理を維持できるか検証する。復元・内容確認は人間がsandbox外で行う。

### 通常rmの転送

- OSのrmやHomebrewの実体には手を加えず、`config/.local/bin/rm`にユーザー用の実行ファイルを置く。`config/.config/fish/conf.d/gomi.fish`で非対話も含めてPATHに反映し、`config/.config/fish/functions/rm.fish`はこの実行ファイルへ転送する。関数だけを安全策とせず、bash/shの子プロセスとサービスでも同じ実行ファイルを使う。
- 引数の解析・プロセス間の排他に必要な標準機能を利用する。既存のuvとPython標準ライブラリ（`fcntl.flock`、`subprocess`等）で実行する小さなラッパーを候補とし、新しいCLI依存や独自のロック基盤を追加しない。uvはプロジェクトを変更しないscript実行を使う。採用する起動方法は実装前に公式仕様で確認し、初回のPython準備は導入手順へ含める。
- 一つの共有ロックの下で、対象を一つずつgomiへ渡す。gomi自身が複数対象を並列にPutすることと、複数プロセスによる同名の保存先選択・metadata更新の競合を避ける。中断時も生きているgomi子プロセスの処理と次の処理が重ならないよう、ロックの保持とsignal処理を確認する。
- rm用の引数として解釈してから、ファイル名をgomiの`--`以降へ渡す。`--prune`、`--config`、restore等のgomi専用引数を通常rmから渡さない。`-- --prune=1d`のようなオプション風のファイル名は通常の対象として扱う。
- よく使う`-f/-r/-R/-v/--`を維持する。gomiでは`-i/-r/-R/-d`の一部がdummyのため、rmとしての確認やディレクトリ判定を黙って省略しない。`-i`は対象を丸ごとごみ箱へ移すことを明示した確認を行い、非対話で確認不能なら削除せず失敗させる。`-f`との優先順位、`-f`かつ対象なし/不存在、ディレクトリへの`-r/-R/-d`の扱いを既存rmの仕様と照合する。サポートできないオプションは操作前に明示的なエラーとし、黙って読み替えない。
- gomi/uv/管理設定の欠落、不正な設定、移動失敗では非zeroにし、実rmへfallbackしない。gomi 1.6.5が移動できない壊れたsymlinkも、リンクを残して非zeroにする（実装中にユーザー承認済み）。設定不存在時にgomiがデフォルト設定を生成するため、ラッパーで管理設定の存在を先に確認する。ごみ箱とその親など、ごみ箱自体を巻き込む削除も拒否する。
- 正常時に余計なstdoutを出さず、`-v`やエラー時だけ必要な出力をする。複数対象の途中失敗については部分成功があり得るため、失敗対象と終了コードを報告し、全体がatomicとは表示しない。
- 既存のHOME全体のrm alias/function/PATHを勝手に上書きしない。対象名に既存のユーザー実体があれば配置を止めて確認する。独立して起動した別シェルやPATHを再構築するツールまで強制適用するためのシステム設定変更はしない。

### 共通の秘密注入と非対話起動

- `config/.config/agent-safehouse/run-with-agent-env.sh`を一つの実装としてfishの`safe`、Hermes対話CLI、gateway/dashboardから利用する。dotenvxの引数や共通ファイルのパスを呼び出し元へ重複実装しない。
- 実行は`dotenvx run --quiet --strict --no-armor -f "$HOME/.config/.env" -- <command> ...`を基本とし、復号はSafehouseの外で行う。平文を一時ファイルに書いたり、`get`の出力をeval/sourceしたりしない。特定のキーをフィルタせず、標準どおり既存の環境変数を優先する。
- `--strict`により共通.envの欠落・復号失敗時に起動を止め、秘密注入なしで黙って続行しない。鍵を取得できない場合の`.env.keys`生成やKeychainのアクセス設定変更は自動化しない。Armor等の外部秘密管理サービスは今回導入しない。
- 共通起動処理でrmラッパーのPATHを再度優先する。Hermesサービスでは`mise exec`の環境適用後にこの処理を通し、miseのshimやlaunchdの限定PATHでrmが実体へ戻らないようにする。必要なHomebrew/uv/dotenvx/gomiのPATHは非対話の環境でも解決させる。
- `exec`の連鎖を保ち、dotenvxの子プロセス起動による終了コード・signal・PIDの扱いを確認する。CLIのTTYとキャンセル、gateway/dashboardの正規停止を実機で検証する。
- CLIから管理対象profileを書き換える検証は通常のsandbox内では行わない。現在の外側sandboxが禁止する.env作成、Keychain操作、sandboxの重ね掛けによる偽の失敗は回避せず、ユーザー承認のあるsandbox外の実行に分ける。実鍵操作と既存サービスの変更はユーザーと実施時点を合わせる。

## Tasks

実装preflight: reviewのbaseは`38b8996b957ed7f63fd461e9503cfbe147955265`。current branchは`master`、upstreamは`origin/master`、開始時点のahead/behindは0/0、staged変更なし。既存の`config/.claude/settings.json`と`config/.pi/agent/settings.json`の変更は今回の対象外。dig logとPlanはこの会話で作成した未追跡ファイルとして保持。現在はSafehouse内（`APP_SANDBOX_CONTAINER_ID=agent-safehouse`、`HERDR_ENV=1`）で、Homebrewへの書き込みと使用中profileの編集が制限される。Herdrのsandbox外ペインを使う確認へユーザーが「ok」と回答し、今回作成した`w3T:p2`で導入とダミー検証を実行。実秘密・実鍵の移行は引き続きユーザー操作とする。

Keychain検証: `scripts/tests/check_dotenvx_runtime.py`の初版はOS Keychain操作にもダミーHOMEを渡し、`failed to save private key to macOS Keychain`と「キーチェーンが見つかりません」のダイアログで失敗した。実HOMEを維持しenvファイルだけ一時領域に置くfixtureへ修正。ユーザーの「ダイアログ出てないですよ」を受け再開し、CLI復号・実launchdの非対話復号・env欠落時の子起動阻止・新規ダミーKeychain項目/jobのcleanupを通過（`HOST_KEYCHAIN_RETRY=0`）。既存Keychainのdefault、アクセス設定、実鍵は変更していない。

現在の停止条件: read-only事前検査 `a440770a-2f95-423` は `Changes Required`。high 2件はtrashルートのrenameによるpayload保護迂回と、外部XDGの`.Trash-<uid>/files`・`.Trash/<uid>/files`の拒否漏れ。親も一時HOMEだけでnative再現し、3ケースとも読めてしまうことを確認した（`/tmp/dotfiles-trash-gap.py`、`HOST_TRASH_GAP=0`は再現プログラム自体の正常終了であり保護通過ではない）。high 2件は修正済み。trashルート/標準share親のrename拒否を追加し、既知の外部XDG形式へpayloadのread/write/unlink拒否を拡張。Redは`TRASH_RENAME_RED=1`（ルートrenameが成功して失敗）と`EXTERNAL_TRASH_RED=1`（外部payloadを読めて失敗）。Greenは`TRASH_RENAME_GREEN=0`と`EXTERNAL_TRASH_GREEN=0`で、標準・custom XDG・`.Trash-<uid>`・`.Trash/<uid>`のpayload読み書き拒否、trashルートrename拒否、metadata読み取り、rename Put、既存SSH/vendor/Hermes例外を確認した。再レビューはまだ実施していない。壊れたsymlinkをエラーで残す受入仕様はユーザーの「ok」で確定。独自の削除/移動やコピーfallbackは追加せず、実gomiでリンク保持と非zero終了を回帰確認する。外部trash祖先の保証範囲はユーザーの「a」でAに確定。HOME/指定XDGと、operandの祖先/直下で検出できる既知の外部trashを保護し、深いmountを含む任意のdirectoryの網羅は対象外。既知の外部XDG形式のpayload拒否とtrashルートのrename迂回は修正する。decision requiredは解決。実gomiのbroken symlink保持/非zeroを回帰テストに追加し、rmの15テストを通過。`README.md`に別作業のagent-device節とNode/npm環境の変更が混在していたため停止し、他者変更を残して今回の箇所だけ編集/部分stageする扱いをユーザーの「ok」で承認された。別作業のhunkはstageせず残す。正式な独立レビューは成果物commit・residue整理・必須検証後に同じreview contextへ再依頼する。全体実装・HOME配布・実秘密移行・既存サービス確認・archive/pushは未完了。別操作で追加された`config/.agents/AGENTS.md`、`config/skills-lock.json`、`config/.agents/agent-device-tests.md`も今回の対象外として保持する。新たな`config/.config/mise/config.toml`、`config/.pi/agent/extensions/pi-gpt-fast-mode/config.json`、`config/.agents/skills/use-agent-device/`も対象外。他者変更の増減は引き続き確認し、勝手にstageしない。

- [x] **導入と初期設定のひな形**: `brew/Brewfile.example`に`gomi`と`dotenvx/brew/dotenvx`を追加し、`config/.config/.env.example`を追加。`config/.config/fish/config.fish.example`のContext7/Homebrew token exportをひな形へ移し、README/AGENTSにユーザー側の初期移行手順を記載。
  - `brew install gomi`と`brew install dotenvx/brew/dotenvx`はsandbox外でexit 0。導入版はgomi 1.6.5、dotenvx 2.32.4。実Brewfile/実config.fish/実.envは読まず変更していない。gomiの初回起動は管理設定を要するため、保存方式と実動作は次のタスクで検証する。
  - `ruby -c brew/Brewfile.example`、`fish --no-execute config/.config/fish/config.fish.example`、`git diff --check`、実.envのGit除外とテンプレートの空値を確認。READMEは既存部分を含め541行（300行超の警告、全体整理は範囲外）。ユーザー承認済みの新規ダミー鍵で暗号化・native up・`run --strict -fk /dev/null`の非対話復号に成功し、鍵ファイル生成なし、ダミーKeychain項目の削除もexit 0。
  - 例ファイルは空の値のみ。既存のcopy/symlinkスクリプトと`.gitignore`を再利用。実.envはユーザーが設定・暗号化を終えてからエージェントを再起動する。
- [x] **共通のrm転送とgomi設定**:
  - 担当実装を受領。5ファイルを変更し、rmの15テスト（実gomiのダミーpayload/metadata、stdin確認、並列実行とsignal、設定/保存失敗、fish→sh/bash）を通過と報告。親はコードとテストを確認し、全体の21テストも再実行。実gomiの復元TUIも後述のhost検証で通過。成果物は`d74495a`としてlocal commit済み。実HOMEへの配布と正式な独立レビューはFinal Validationのゲートとして残る。
  - gomi 1.6.5の上流制限: 壊れたsymlinkはリンク先のdevice判定に失敗し、exit 1でリンクを残す。通常のsymlinkの移動は成功する。独自の移動/コピーfallbackは追加していない。外部volumeのtrash親の検出は既知の規約名とoperandの祖先/直下に限定され、深い位置のmount/trashを網羅していない。壊れたsymlinkはリンク保持/エラー、外部trash祖先はAの検出範囲とすることでユーザー承認済み。
  - 親のhost検証 `scripts/tests/check_gomi_runtime.py`はproduction policy内のreal gomi Put、XDG metadata、隔離PTYでの復元確認・元パス/内容/有効symlink、4並列の同名保存のdata/metadata保全を通過（`HOST_GOMI_CONFIRM_FIX=0`）。harness初版のpath比較は`/var`入力を`/private/var`へ期待変換してしまい失敗、絶対入力パスを保持する期待へ修正。TUI確認promptは実際の`OK to restore?`に合わせた。productのfallback変更はしていない。
  - 計画対象: `config/.local/bin/rm`、`config/.config/fish/functions/rm.fish`、`config/.config/fish/conf.d/gomi.fish`、`config/.config/gomi/config.yaml`を追加し、通常rmの引数処理・排他・失敗時のデータ保全を実現する。
  - gomi設定は公式の完全な設定を基に必要箇所を変更し、最小YAMLによって`forbidden_paths`などが失われないようにする。`strategy: xdg`、`home_fallback: false`、TUIの`permanent_delete.enable: false`を指定する。復元一覧の期間・サイズ・除外フィルターで古い/大きいデータが見えなくならないよう設定を確認する。
  - 手動のgomi復元と通常rmが同時にmetadataを操作する場合の扱いを確認し、直接gomiを起動する際は通常rmの排他対象外であることと、復元中の注意をREADMEへ記す。
- [x] **Safehouseの互換性許可と保護の再適用**:
  - `compatibility.sb`・HOME許可/全環境継承/順序を各起動経路へ実装。protected path・SSH・browser・vendor/Hermes例外とtrashの修正をnativeダミーで検証済み。修正profileで実gomi転送/復元/4並列も再通過（`CORRECTED_POLICY_GOMI=0`）。成果物をlocal commitする。正式なreviewと実HOME/GUI/サービスの最終ゲートはまだ残る。
  - 計画対象: `__safehouse_args.fish`、`local-overrides.sb`を変更し、`compatibility.sb`を追加する。gateway/dashboardの引数も同じ方針へ揃える。
  - 現行の特定Mach service・Simulator/fsctl・vendor例外・Hermes信頼境界を失わない。HOMEの追加許可より後の拒否、SSH/socket例外、profile自身の保護まで含む生成profileを確認する。
- [x] **dotenvxによるCLI・サービスの自動注入**:
  - loaderへ共通PATHとstrict/native/no-armor/`-fk /dev/null`を集約し、CLIとmise後のサービスから呼ぶ。21 tests（runtime 5、TMPDIR 1、rm 15）通過。ダミーの実Keychain/launchd復号は前述のとおり通過。成果物をlocal commitする。本番秘密初期移行・実サービス確認は未実施。
  - 計画対象: `run-with-agent-env.sh`を追加し、`safe.fish`、`hermes.fish`、`safe-hermes-gateway.sh`、`safe-hermes-dashboard.sh`を変更する。各CLI関数の個別オプションは維持し、コマンド引数・終了コード・signalを透過する。
  - 初期のKeychain検証を実鍵で行わない。ユーザー承認を得たダミー鍵で非対話動作を確認する。既存の鍵やKeychainのアクセス制御を変更・削除しない。
- [x] **継続的な回帰検証と運用手順**:
  - `test_agent_runtime.py`、`test_rm_trash.py`、TMPDIR fixture、明示的なhost check 3本を追加/更新。READMEにrm/gomiの復元/手動掃除/制限/uv初回準備・戻し方を記載し、古いtoken export案内を修正。root AGENTSも新方針へ更新。READMEの別作業hunkは残して部分stageする（ユーザー承認済み）。READMEは300行超の警告、全体整理は範囲外。
  - 計画対象: 既存の`unittest`を使い、`scripts/tests/test_hermes_tmpdir.py`を新しい起動連鎖に合わせて更新する。新しい振る舞いは`test_agent_runtime.py`と`test_rm_trash.py`など同じディレクトリに最小限追加する。既存のテストがあるため実装は`tdd`スキルで行う。
  - fake dotenvx/safehouse/mise/gomiとダミーHOMEで検証し、実秘密・実Keychain・実サービスを自動テストに使わない。実.env fixtureを現在のsandboxで無理に作らず、注入処理の単体テストはstubで成立させる。
  - `README.md`とroot `AGENTS.md`のallowlist/個別env-passに関する記述を実装に合わせる。AGENTS/CLAUDEの正本・symlinkを確認し、二重編集しない。手順に導入、rmの適用範囲、gomiでの復元/手動掃除、Finderとの違い、ユーザーによる秘密移行・Keychain登録・バックアップ、Hermesの再起動・復旧を含める。

## Final Validation

この計画作成時点では以下は未実行。シェルコマンドの提示はfish構文にする。

- [x] **継続的なテスト**: `uv run python -m unittest discover -s scripts/tests -p 'test_*.py'` → 通過。起動処理のargv境界、空白を含むパス、全環境継承、共通ファイルの明示パス、rm優先PATH、CLI引数/終了コード、既存TMPDIR補正が保たれる。stubの復号失敗・依存欠落では後続コマンドを起動せず、ログにsentinelの秘密値を出さない。
- [x] **rmの通常動作と失敗経路**: 単体テストで`-rf/-R/-v/--`、`-i`確認、`-f`と不存在/対象なし、オプション風ファイル名、空のdirectory/non-recursive directory、symlink、不正オプションを確認する。fake gomiの移動失敗・設定/実行ファイル不存在で実rmへfallbackしない。複数対象/同名の並列呼び出しは一つずつ処理され、signal後も排他が破れない。
- [ ] **シェルと配布の確認**: 変更対象のfishに`fish --no-execute`、bash/shに構文チェック、Pythonに構文チェック、差分に`git diff --check`を行う。`.env.example`を一時的な配置先へコピー・symlinkし、Git管理外の実体と参照先が正しく対応することを確認する。ユーザーの既存実体は上書きしない。
- [ ] **実際のrm解決**: 配布後の新しいfish、そこから起動したbash/sh、エージェント、miseを通るサービスで`command -v rm`とダミー対象の削除を確認する → 共通ラッパーを使う。人間の実config.fishによるPATH上書きがあれば、秘密を読まずユーザーに調整を依頼する。
- [ ] **gomiでのデータ保全・復元**: 空白・オプション風の名前、directory、symlink、同名の複数対象を含むダミーだけを実gomiでごみ箱化し、人間の復元操作で元のパス・内容が戻る。並列呼び出しでも全データとmetadataを保持する。移動先が使えない場合やコピーが必要な場合はエラーで元データを保持し、永久削除経路へ進まない。異なるvolumeの確認はユーザーが許可したダミーvolumeだけで行い、実データやpruneを使わない。
- [ ] **Safehouseの実効保護**: 全起動経路の生成profileを確認し、sandbox外で用意したダミーHOME/ダミーの保護対象をsandbox内から操作する。通常のHOME内別リポジトリやDownloads等は読み書きでき、保護対象は読めず書けない。symlink、保護ディレクトリ/親の移動、trash payload経由でも保護が外れない。SSH非機密metadata/socket、vendor fixture、Hermes例外は意図どおり利用できる。実秘密・人間のブラウザデータは検証で読まない。
- [ ] **互換性のスモーク確認**: 合成した非機密環境変数と空白を含む値の継承、子プロセス、IPC/Unix socket、ダミーの別プロセスへのsignal、Macサービス/GUI、agent-browserの既存のno-sandbox起動、利用するSimulator経路を確認する → ファイル以外の緩和が成立し、ファイル拒否は残る。無関係なホストプロセスへsignalを送らない。OSのTCC/SIPやChromiumのsandboxネストまで解決済みとは扱わない。
- [ ] **dotenvx/Keychainの実効確認**: ユーザー承認を得たダミーの暗号化ファイルとKeychain登録でCLIとlaunchd相当の限定環境から復号する → 子がsentinelを受け取り、元シェルへexportされず、平文一時ファイル/恒久鍵ファイル/値を含む起動ログを作らない。共通.envの欠落・鍵の取得失敗・復号失敗は起動を止める。検証用鍵だけを承認済み手順で片付ける。実鍵の初期移行とバックアップはユーザー操作として完了状況のみ確認する。
- [ ] **全CLIと実Hermesサービス**: 人間の秘密移行が完了してから各CLIで通常のツール起動を確認する。Hermesは既存の`hermes-gateway`/`hermes-dashboard`管理関数で正規再起動し、gatewayの`http://localhost:8642/health`とdashboardの`http://127.0.0.1:9120/api/status`、PATH/注入/停止を確認する。launchdのbootout/bootstrapは直接実行しない。Keychainで対話要求・ハング・起動失敗があれば適用を完了扱いせず相談する。
- [ ] **差分とロールバック手順**: 他者変更の保持、実秘密・実鍵がGitへ入っていないこと、CLIとサービスの意図したfeature差分を確認する。ユーザーの既存設定・既存鍵・ごみ箱の内容を削除しない戻し方をREADMEに記す。必須のsandbox外検証が実行できなければ未検証範囲を報告し、代替方式を無断採用しない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま`docs/plans/archived/`へ移す。

## 確認した一次資料

- Safehouse 0.12.0: `/opt/homebrew/Cellar/agent-safehouse/0.12.0/bin/safehouse`のprofile/render実装、[公式usage](https://agent-safehouse.dev/docs/usage)。HOME/wide-readのlate grant、SSH例外、process-control/launch-services、append-profileの最終書き込み保護を確認。
- gomi 1.6.5（commit `8b689e8cee60db051619b176094bfbc620c3a586`）: [CLI](https://github.com/babarot/gomi/blob/8b689e8cee60db051619b176094bfbc620c3a586/internal/cli/cli.go)、[XDG storage](https://github.com/babarot/gomi/blob/8b689e8cee60db051619b176094bfbc620c3a586/internal/trash/xdg/storage.go)、[Move](https://github.com/babarot/gomi/blob/8b689e8cee60db051619b176094bfbc620c3a586/internal/utils/fs/atomic.go)、[default config](https://github.com/babarot/gomi/blob/8b689e8cee60db051619b176094bfbc620c3a586/internal/config/defaults.go)。dummyのrmフラグ、設定の非strictロード、legacy選択、コピー失敗経路、保存先とmetadata競合をソースで確認。競合は未実測。
- dotenvx 2.32.4: [公式Homebrew formula](https://github.com/dotenvx/homebrew-brew/blob/main/Formula/dotenvx.rb)、[CLI options](https://github.com/dotenvx/dotenvx/blob/v2.32.4/src/cli/dotenvx.js)、[run action](https://github.com/dotenvx/dotenvx/blob/v2.32.4/src/cli/actions/run.js)、[Keychain enrollment](https://github.com/dotenvx/dotenvx/blob/v2.32.4/src/lib/services/keychainUp.js)、[公式の鍵保管説明](https://dotenvx.com/)。strict失敗時の停止、quiet/native/Armorの設定、明示的な.env指定を確認。macOS/launchdでの実動作は未検証。
