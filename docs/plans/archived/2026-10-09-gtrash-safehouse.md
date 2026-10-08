# gtrashによるrm転送とSafehouse緩和 Implementation Plan

## Requirements

参照: [設計記録](../../dig/2026-10-02-safehouse-compatibility.md)の「2026-10-09 再開」と本セッションの後続合意。Q14の確認待ちは、ユーザーの「じゃあgtrashでいいか」「お願いします」で解決。今回確定した構成は次のとおり。

- 普段のターミナル、PATHを継承する子shell、エージェント、Hermes gateway/dashboardの通常rmをgtrash putへ転送する。OSの/bin/rm実体は変更せず、Safehouse内ではその実行を拒否する。
- Safehouseのdeny-first、HOME RW、wide-read、全環境継承、既存feature/IPC許可は維持する。機密・個人データの独自denyを撤廃し、それだけのための例外を整理する。allow defaultや/全体のRWは追加しない。
- ごみ箱payloadへの直接の読み取り・書き換え・削除の既存保護は維持する。投入に必要なmetadata・rename・復元情報の保存を妨げない。復元・内容確認・掃除は人間がsandbox外で行う。エージェントによる復元は不要。
- gtrashはHomebrew公式formulaで管理する。別volumeからHOMEへのコピーfallbackは有効にしない。永久削除・ごみ箱の自動掃除は通常rmに組み込まない。
- gomi本体・設定・既存ごみ箱データは保持し、今回削除・移行しない。他者変更config/.claude/settings.jsonを保持する。
- 追加承認（既存衝突についてユーザー「ついでに直して」）: Claude専用スキルを明示宣言したときの親ディレクトリとの配置衝突も修正する。共通globと専用の明示宣言による優先順位は変えない。
- Python/Node等の削除API、別rm実装、Git、上書き、許可済みIPC等による操作まで封じる完全な削除防止・隔離は対象外。既存のごみ箱保護が持つ親renameやHermes例外等の保証限界を無断で再設計しない。

## Implementation Decisions

- `config/.local/bin/rm`を小さなPOSIX shell wrapperとして追加し、信頼するHomebrewのgtrashへ引数を保持してexecする。rmオプションの独自実装・共有ロック・独自移動処理は追加せず、gtrashのputに委ねる。gtrash欠落/失敗時に実rmへfallbackしない。
- `mise.toml`に当該wrapperの個別symlinkを宣言する。HOME一括配置や独自配置スクリプトは追加しない。配置先の既存実体を確認し、未知の衝突をforce置換しない。
- 共通runtime `run-with-agent-env.sh`とfishの`shell-init.fish`は既に.local/binを優先する。追加のPATH設定・イベント機構は不要だった。既存PATH/プロジェクトruntime選択を変えず、mise activate後の新規fishと子shellでもwrapperが先に解決されることを確認する。
- HOMEへのコピーfallbackの無効化は、全経路が通るrm wrapperの環境指定へ集約する。fish/runtimeへ同じ指定を重複追加しない。`GTRASH_ONLY_HOME_TRASH`と`GTRASH_HOME_TRASH_FALLBACK_COPY`をfalseにし、前者をtrueにしてコピーが有効になることも避ける。検証に限って格納先を専用ダミー領域に指定する。
- `local-overrides.sb`は機密・個人データdenyと不要例外を削除し、ごみ箱保護および `(deny process-exec (literal "/bin/rm"))` を残す。`compatibility.sb`、追加profile順、欠落時の起動拒否、サービスの意図したfeature差分を維持する。
- policy本文は正本編集で次回起動から変わる。一方、サービスwrapperはNixで生成されるため、内容変更が必要ならビルドまで行い、実サービスのswitch/restartは別途承認とする。検証目的だけのサービス再起動やNix activationは行わない。

## Tasks

Review base: `675d1815ec2b01919bf40be266c0dd33534495dd`。開始時は `origin/master` と一致し、staged差分なし。既存の設計記録と計画は本セッションの成果物、`config/.claude/settings.json`は他者変更として除外する。

導入・policy・配置・運用記述は同じ切替に必要なため、検証済みの一つの成果物としてまとめてcommitする。

- [x] **導入・rm実行経路**: `nix/darwin/homebrew.nix`へgtrashを追加し、wrapper、miseの個別リンク、fish/runtimeのPATHと必要な環境指定を整合させる。
  - `scripts/tests/`の既存unittest基盤とtddスキルで、引数（空白・空文字・--）、終了コード、欠落時非fallback、fish/子shell/サービスruntimeからの解決を守る。上流gtrashの全rm互換仕様を自作テストで再実装しない。
- [x] **policyと契約の更新**: `local-overrides.sb`、`scripts/tests/check_safehouse_runtime.py`、必要なら`test_agent_runtime.py`を新しい許可/拒否に整合させる。消滅した機密保護仕様専用のテストは削除し、ごみ箱・/bin/rm保護の振る舞いを残す。
- [x] **運用記述**: `.agents/skills/dotfiles-setup/references/setup.md`の復元手順、`config/.agents/skills/use-agent-safehouse/`の該当説明、ルート`AGENTS.md`の標準rm前提、設計記録の現在地を更新する。古い計画の履歴は書き換えず、READMEへの設定値・一覧の重複記載は避ける。
- [x] **最終構成の隔離検証と配置**: 最終policy＋実gtrashのダミー検証を先に完了し、その後対象限定のHomebrew導入・標準mise applyで配置する。未知の衝突・拒否・タイムアウトは停止して報告する。
  - sandbox内からのnested sandboxはOperation not permitted。承認済みのHerdr外側ペインでダミー検証を実行する。導入・配置の制限操作は同じく承認範囲を確認し、無断で迂回しない。

## Final Validation

- [x] **wrapperと起動契約**: `uv run --no-project python -m unittest discover -s scripts/tests -p 'test_agent_runtime.py'`と追加したrm転送の関連testを実行し、引数/失敗/PATHの契約を通過する。追加testの正確な実行コマンドは実装時にここへ記録する。`test_dotfiles_links.py`・`test_hermes_tmpdir.py`は関連する配置/環境変更がある場合に実行する。
- [x] **構文・差分**: 変更fishを`fish --no-execute`、POSIX shellを`sh -n`、Bashを`bash -n`、Pythonを一時bytecode先で構文確認する。Nixの変更はdotfiles-setupに従い`bash scripts/dotfiles.sh build`で確認する。`git diff --check`、参照パス、変更範囲を確認する。
- [x] **実policy**: sandbox外で`uv run --no-project python scripts/tests/check_safehouse_runtime.py`を更新済みのダミーHOMEで実行。旧保護対象を模したダミー.env/鍵/個人データの読み書きは成功し、/bin/rm実行、ごみ箱payloadの読み取り・書き換え・unlinkは失敗する。既存Trash/XDG形式とHermes例外の意図した差分を明示して確認する。実秘密をprobeしない。
- [x] **gtrash投入と人間の復元**: 実gtrash＋最終policy＋専用ごみ箱で、ファイル・directory・broken symlink、1コマンドの同名対象、16プロセス同名投入の内容/metadata保全、移動拒否時の非zeroと元保持を確認する。sandbox内からのpayload操作は拒否され、sandbox外でダミーだけを元パスへ復元できる。投入後の復元で内容確認を行い、検証のためにごみ箱保護を解除しない。
- [x] **終了処理**: 転送PATHと最終policyの実Safehouseで、mktemp/EXIT trap、起動・終了が0で、内容が専用ごみ箱へ保存される。gtrashの実行先、version、検証結果とログパスを記録する。以前の許可追加済み13項目は最終構成の合格として流用しない。
- [x] **実配置**: 導入前に対象の`type -a`と配置先の実体/管理状況を確認する。`brew install gtrash`は対象限定、mise配置はdotfiles-setupの標準手順・時間制限付きdry-runを用い、既存データを上書きしない。新規fishと子shellで通常rmがwrapper、gtrashがHomebrew版に解決されることを確認する。実ごみ箱には検証データを投入しない。稼働Hermesの再起動・認証通信は未実施範囲として報告する。

### 実施記録

- rm wrapperの初回テストは未実装で失敗し、実装後に引数・終了コード・環境指定・欠落時非fallback・fish/子shellの3 testが通過。共通runtimeのrm解決も追加し、`test_agent_runtime.py`の10 testが通過した。
- `check_safehouse_runtime.py`は旧policyのダミー.env読み取りで失敗し、新policyでは全項目通過。ごみ箱5形式のpayload read/write/unlink拒否、4形式へのrename投入、Hermes例外、機密・個人データ相当ダミーのread/write、/bin/rm実行拒否を確認。
- `check_gtrash_runtime.py`を追加。公式配布版とHomebrew版のgtrash 0.0.6で全項目通過。通常投入、16並列の同名file/directory、単一コマンド同名投入、外側での復元、payload保護、移動失敗時の元保持、Safehouse/EXIT trap終了処理を確認。ダミーHOMEだけを使い、実ごみ箱には投入していない。
- `brew install gtrash`成功。依存追加なし。標準の自動updateがtapメタデータを更新したが、他のformula/caskのupgradeは行っていない。
- 実HOMEのrm宛先・旧fish rm/gomiリンクが存在しないことを確認。標準miseの対象限定dry-runが2.5秒で完了し、同じ宛先をapply。`~/.local/bin/rm`は正本へのsymlinkとなり、新規fishと子shellで先に解決される。
- 初回dry-run起動は未導入のgtimeoutで実行前に失敗。Python subprocessの30秒timeoutを使って標準miseを実行した。mise自体の拒否・衝突・timeoutはない。
- 親プロセスのPATHには旧Homebrew mise 2026.6.14が残っているが、新規fishはNix管理の2026.9.18を使う。今回の配置・配置テストはNix版を明示して実行し、既存のPATHや旧実体は変更していない。
- ログ: `/tmp/gtrash-implementation.xw5rsy/`（一時成果物）。`policy-red.log` / `policy-green.log`、`gtrash.log` / `gtrash-homebrew.log`、`brew.log`、`mise-dry-run.log` / `mise-apply.log`。
- サービスwrapper本体は変更不要。Nix switch、Hermes再起動、認証通信、別volume実機投入、実データ復元・掃除は未実施。
- `test_rm_trash.py` 3件、`test_agent_runtime.py` 10件、`test_hermes_tmpdir.py` 1件が成功（skipなし）。`sh -n`、変更PythonのAST構文確認、Markdownローカルリンク確認、`git diff --check`も成功。fish/runtime本文は変更していない。
- `bash scripts/dotfiles.sh build`成功。出力: `/nix/store/9ciqxkwq7kb1h3wy0ay4d0sv6k30nfwh-darwin-system-26.11.4cff07d`。flake checks成功、activation未実施。`nix-build.log`に保存。

### 配置テスト失敗と追加承認

- `test_dotfiles_links.py`は初回9 test中、新規rmリンクのtestだけ通過。多くは未追跡wrapperがテスト用checkoutへコピーされないため失敗した。正本`config/.local/bin/rm`を明示的にstageし、追跡対象に追加した（この時点では未commit）。
- 追跡後の全配置test再実行は120秒の実行制限で中断。途中にClaude専用スキルの衝突があり、全件成功とは扱わない。ログ: `test_dotfiles_links-tracked.log`。
- `test_claude_specific_skill_entry_overrides_shared_glob`は、開始時HEADの`mise.toml`とtest本体を隔離した一時Git checkoutへ取り出しても再現。`~/.claude`と`~/.claude/skills/ask-codex`のsymlink-each宣言が衝突する。今回のrm宣言がない状態でも同じ失敗で、所要2.55秒。ログ: `base-claude-conflict.log`。
- この時点では既存失敗を自動修正・対象外扱いせず停止した。新規rmリンクの実配置と単独test、Safehouse/gtrashの隔離検証、Nix buildは成功していたが、必須配置suiteの成功が未確定だった。
- ユーザーが既存衝突の修正を追加承認。`mise.toml`の`~/.claude`親宣言に`exclude = ["skills"]`を追加し、共通glob・専用明示宣言との二重所有を解消する。現在`config/.claude/skills/`に追跡ファイルはないため、実配置の解除・移行は不要。仕様と配置手順は既に専用明示宣言を前提としており、手順変更はない。
- 変更前HEADでの失敗をRedとして使用し、既存回帰testを含む配置suiteを600秒上限で再実行した。mise.tomlはNixのスキル選択からも参照されるためNix buildも再確認した。
- 修正後の配置suiteは9件すべて成功（166.8秒、skipなし）。ログ: `test_dotfiles_links-fixed.log`。修正後Nix buildも成功し、出力は前回と同一。ログ: `nix-build-fixed.log`。必須validationの未解決失敗はない。
- 検証済みunit/integration testは合計23件（rm 3、runtime 10、配置 9、Hermes tmpdir 1）。配置以外の成功結果は入力・挙動が変わっていないため再利用する。
- 再実行コマンド: `uv run --no-project python -m unittest discover -s scripts/tests -p 'test_dotfiles_links.py'`（他3 suiteはpatternを対応するファイル名へ変更）、sandbox外で `uv run --no-project python scripts/tests/check_gtrash_runtime.py` と `uv run --no-project python scripts/tests/check_safehouse_runtime.py`。Nix管理miseをPATHで優先する。
- 本文の既存長文は今回の変更に必要な箇所だけ更新し、文書全体の分割は対象外。Markdownローカルリンクと変更範囲を確認済み。
- 他者変更`config/.claude/settings.json`は未変更・未stage。

## Gate summary

- 実装commit・レビュー対象HEAD: `c03d0e443887c926a7cfb7eee72a9bfcfb85f95b`。base `675d1815ec2b01919bf40be266c0dd33534495dd`からの1 commit・18ファイルをread-onlyの独立reviewerが確認した。
- blocking/high、decision required、medium/lowはいずれもなし。採用finding・correction commitなし。既存のClaude配置衝突も追加承認の範囲内として確認済み。
- 必須の23 test、実policyとgtrashの隔離検証、Nix build、構文・リンク・差分チェックは成功。review後に実行コードを変更していないため、成功結果を再利用する。独立reviewerもshell/Python/TOML構文、実行権限、起動経路を確認した。
- 未実施の範囲はNix switch、稼働Hermes再起動・認証通信・実サービス全経路、別volume実機投入、実秘密・既存ごみ箱の操作。実配置とHomebrew版の検証は親が確認し、reviewerはリポジトリ外を調査していない。
- 未解決blockerなし。計画archiveのcommit後、開始時と同じ`origin/master`へ通常pushする。force pushや履歴書換えは行わない。

ごみ箱保護下でgtrashの投入・並列保存・終了処理が成立しない場合は、保護を緩めて通さず停止して相談する。実秘密移行、既存ごみ箱削除、復元元の不明なデータ整理は行わない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
