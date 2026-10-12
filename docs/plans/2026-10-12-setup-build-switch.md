# setup の追加と build / switch の分離 Implementation Plan

## Requirements

- `setup` を、初回・既存 Mac 共通の「ビルド → 適用 → 設定配置」の入口にする。現行 setup.md の手順5〜6を一度のコマンド起動で進め、必要な対話確認は残す。ユーザー承認済み。
- `build` は検査・ビルドのみ、`switch` は明示されたビルド済み成果物の適用のみとする。`switch` から system の再評価・再ビルドを行わず、最新成果物や現在の checkout を暗黙に選ばない。ユーザー承認済み。
- 対象ユーザー・HOME、通常の対話端末、Safehouse 外、Hermes 停止、shell 設定退避の既存条件を維持する。スクリプト全体を sudo で動かさない。
- 設定配置は標準の mise trust / dot apply を利用する。対象の確認と承認、60秒の dry-run 制限、失敗時の停止を維持する。force・一括退避・独自配置処理・自動 rollback は追加しない。
- 追加依頼として `nix/darwin/homebrew.nix` から `cmd-eikana` の cask 宣言を削除する。Karabiner の設定は変更しない。
- sudo の再入力を減らすため、適用直前に標準の `sudo -v` で認証し、適用中だけ `sudo -n -v` で認証キャッシュを維持する。パスワードをスクリプトで取得・保持・転送せず、expect や sudoers の変更は使わない。ユーザー承認済み。
- `chsh`、runtime install、Xcode・App Store・FDA の準備、上記 sudo 認証以外の秘密・認証の操作、サービスの自動停止・再開、実機適用・アプリのアンインストールは対象外。`update` の既存契約は維持する。

背景: [前回の初回セットアップの議論](../dig/2026-10-12-human-first-setup.md)。同ログの「switch がビルドを含み、過去成果物を受け渡さない」という以前の方針は今回の会話で置き換えられた。それ以外の安全条件と初回準備は継続する。今回の公開 CLI の具体的な構文・実装方針は以下の計画承認対象とする。

## Implementation Decisions

### CLI と成果物の契約

| コマンド | 振る舞い |
|---|---|
| `bash scripts/dotfiles.sh build [--configuration NAME]` | Git 追跡ソースの snapshot に対する check / build。stdout は system store path 1行とし、適用・mise trust・設定配置を行わない |
| `bash scripts/dotfiles.sh switch SYSTEM_PATH` | 既存の system store path を明示して適用。`--configuration` は受け取らず、成果物内の設定名を使う |
| `bash scripts/dotfiles.sh setup [--configuration NAME]` | 同じ build 処理の成果物を switch 処理へ渡し、成功後に現在の checkout の設定を配置する |
| `bash scripts/dotfiles.sh update [INPUT]` | 従来どおり lock 更新だけを行う |

- 設定名の既定値 `default` と `private` の選択、未知の設定名の拒否、lock を暗黙に更新しない契約は維持する。旧 `switch --configuration NAME` はエラーにして新しい手順を案内し、暗黙 build の互換経路は残さない。
- `switch` の引数なし、存在しない・GC 済み・system ではない成果物は変更前に拒否する。受け取ったパスは store 内の system に正規化し、`systemConfig` の自己参照、必要ファイルと実行可能性を確認する。再取得・再ビルド・別候補へのフォールバックはしない。
- `flake.nix` と `nix/darwin/` の小さな module で、成果物の `etc/dotfiles/build.json` に設定名、source snapshot、username、homeDirectory、Hermes 停止検査と Nix 版 mise の store path を生成する。秘密や checkout の絶対パスを追加しない。同じ設定から生成し、可変な外部 JSON や適用時の checkout 評価に依存しない。
- メタデータなしの旧成果物はこの CLI では拒否し、新しい build を案内する。旧世代復旧は既存の nix-darwin 標準手順を別途承認下で行う。独自の履歴・最新成果物管理・GC root 管理は追加しない。build のみの成果物は GC で消え得ることを明記する。
- メタデータは安全確認に必要な対応情報であり、未知の Nix 成果物を安全と認定する仕組みではない。自分が確認してビルドした成果物を指定する。

### ビルドなしの適用

固定版 nix-darwin `4cff07de74b50e64bdd68cd4e722ab5b6b35ee48` の `pkgs/nix-tools/darwin-rebuild.sh` では `switch --flake` は再度 build を呼ぶ。一方、`activate` は起動パスから system を特定して既存成果物を適用するが、profile は更新しない。したがって次の標準操作を組み合わせる。

1. root・Safehouse・非対話の実行を拒否する。成果物とメタデータを検証し、対象 username・passwd の home・環境の HOME が一致することを確認する。
2. source、設定名、候補、既存 profile、対象ユーザー、変更範囲と非原子的な適用であることを表示し、適用承認を得る。
3. 候補に固定された Hermes 停止検査と、既存の確認付き bashrc / zshrc 退避を実行する。排他的原子移動・移動後照合・途中失敗時の保全を変更しない。
4. 候補の `sw/bin/nix-env -p /nix/var/nix/profiles/system --set SYSTEM_PATH` を sudo で実行し、成功した場合だけ候補の `sw/bin/darwin-rebuild activate` を sudo で実行する。順序は通常 switch と同じ。後者の symlink は実体へ解決して呼び出してはいけない。起動パスが system 選択に必要なため。
5. subprocess の失敗を保持し、成功時も system profile と `/run/current-system` が候補を指すことを確認する。失敗時は profile と current-system、完了済み段階を表示し、setup の配置段階へ進まない。

activation 内の Nix による世代登録や Homebrew のアプリ取得まで禁止する意味ではなく、system の再評価・再ビルドを禁止する。profile 更新後の activation 失敗では部分適用が残り得る。復旧は自動化しない。

上流確認: [darwin-rebuild.sh](https://github.com/nix-darwin/nix-darwin/blob/4cff07de74b50e64bdd68cd4e722ab5b6b35ee48/pkgs/nix-tools/darwin-rebuild.sh) の build / activate 分岐と profile 登録。固定成果物の activation では非ゼロの `brew bundle` は後続の Home Manager を停止させる。ただし brew 不在時は上流が表示だけで続行するため、setup は終了コードとリンクだけで全アプリ導入を保証せず、適用後の Homebrew・mise の存在を確認してから配置へ進む。

### sudo 認証キャッシュの維持

- `setup` と単独の `switch` に共通の適用スコープを設ける。ビルド・適用承認・Hermes 停止検査を終え、shell 退避が必要ならその承認も終えてから、最初の昇格直前に `/usr/bin/sudo -v` を実行する。ユーザーは sudo 自身の端末プロンプトへ入力し、Python がパスワードを読むことはない。認証拒否・失敗時は退避・profile 更新・activation を行わない。
- 認証成功後、同じ制御端末を使って `/usr/bin/sudo -n -v` を定期実行する。各更新には有限の timeout を設け、入力を求めず、パスワードの自動再送も行わない。独立した常駐サービス・detached process にせず、適用を実行する親が寿命を管理する。
- 維持する範囲は shell 退避・profile 更新・activation とその結果確認まで。正常終了・例外・ユーザー中断・通常の終了シグナルで、更新処理と実行中の更新 subprocess を終了・回収する。mise trust / dry-run / apply に入る前に必ず終了する。`build`・`update` や確認待ちのために維持を開始しない。
- 更新の失敗・timeout は記録・通知し、更新側が勝手に対話認証・無限再試行しない。実行中の activation をキャッシュ更新失敗だけで強制終了して部分適用を増やさず、終了結果を回収して、次の変更段階には進まず非ゼロで停止する。完了済み操作と再認証が必要な状態を報告し、自動で適用し直さない。
- 更新停止はキャッシュの即時失効とは異なる。既存セッションのキャッシュを巻き込む `sudo -k` / `sudo -K` は自動実行せず、通常の有効期限に戻す。維持中は同じ端末の別 sudo 操作も再認証なしになる場合があることを文書に記載する。
- 会社のポリシーや端末・プロセス構成によってキャッシュの共有・更新が効かない場合があり、認証1回を保証しない。上流 activation 内の認証や App Store の Apple Account 認証を自動応答する仕組みにはしない。

根拠: [sudo 公式マニュアル](https://www.sudo.ws/docs/man/sudo.man/) とローカル `/usr/share/man/man8/sudo.8` の `-v` / `-n` および端末単位の認証キャッシュの説明。実 sudo は sandbox に拒否されたため動作未検証。検証のために制限を回避したり認証・sudoers を変更したりしない。

### setup と設定配置

- `setup` も root・Safehouse・非対話の実行をビルド前に拒否する。現在の checkout を一度 snapshot 化し、対象ユーザー確認と build に共用する。内部の build / switch 関数を共用し、CLI を再帰実行しない。
- Nix の適用対象は immutable な build 成果物、設定の配置元はコマンドの作業ディレクトリではなく `scripts/dotfiles.py` が属する checkout の `mise.toml` と `config/`。store のコピーへ通常設定をリンクしない。配置前にこの違いと実際の配置元を表示する。
- Nix 成果物をビルドした後に checkout の `mise.toml` が変更されていたら停止する。確認済み宣言と異なる配置を黙って進めない。個別設定の本文は従来どおり可変な Git 正本であり、システム全体の snapshot 適用とは説明しない。
- 成果物で選ばれた Nix 版 mise の絶対パスを利用し、親 shell の PATH を変更させない。起動時 PATH にある旧 mise や他プロジェクトの runtime に依存しない。手元の PATH の mise 2026.6.14 は `dot` に未対応だったため、検証でも候補版を明示する。
- 対象 `mise.toml` のパスと内容を表示し、承認後にそのファイルだけを trust する。`trust --all` や自動の広域 trust は使わない。次に checkout を明示して `dot apply --dry-run` を60秒制限付きで実行し、出力を表示する。
- dry-run が失敗・timeout なら apply しない。配置予定を確認する別の承認を得てから、標準の `dot apply` を実行する。未知の実体・リンクや引継ぎ未確認の対象があればユーザーは承認せず停止する。mise が未知の symlink を必ず拒否するとは保証しない。独自の manifest 展開・配置エンジンは作らない。
- apply の終了コードと代表的な直接リンク（fish と mise）が checkout 内の正本を指すことを確認する。拒否・失敗・timeout は非ゼロ終了とし、完了済み段階と残った操作を表示する。mise 段階だけ失敗した場合は、既存の標準 mise 手順で再開できるよう案内し、成功した switch を自動でやり直さない。新しい resume 状態ファイルや再開専用 CLI は追加しない。
- 既存 Mac の通常更新にも使えるが、旧 HM からの所有権移行を自動化する入口にはしない。所有解除前の時間制限付き dry-run・保全・承認という既存の移行前提は維持し、未完了の移行には分離した build / switch / mise 手順を使う。setup を移行前提の代替として案内しない。

mise 参照: [dotfiles](https://github.com/jdx/mise/blob/main/docs/dotfiles.md)、[trust](https://github.com/jdx/mise/blob/main/docs/cli/trust.md)。実装時に候補版の help と一時 HOME テストで構文・結果を確認し、実 HOME の trust / dry-run / apply を検証目的で実行しない。

## Tasks

レビュー基点: `7736860e78bcb4910d4067d35a1570029ca7c602`。開始時点は `master` と `origin/master` が一致、既存 staged なし。アプリ一覧の既存差分はこの会話で承認・変更済みの対象として引き継ぐ。CLI 分離・sudo 認証・setup・対応文書は共有契約のため1つの成果物としてまとめ、アプリ一覧は独立した commit にする。ユーザー側の Claude / Pi 差分4件は保持して除外する。

- [ ] 成果物と適用 CLI: `flake.nix`、`nix/darwin/default.nix` と必要な小さな metadata module、`scripts/dotfiles.py`、`scripts/tests/test_dotfiles_cli.py` を変更する。TDD で build の独立性と成果物の明示選択を守り、メタデータと対象チェックを成果物に固定し、標準 profile 更新と activate を使って switch を分離する。
- [ ] sudo 認証: `scripts/dotfiles.py` と `scripts/tests/test_dotfiles_cli.py` に、初回認証と適用中だけのキャッシュ更新・終了処理を追加する。共通の switch 処理にまとめ、setup と単独 switch で同じ契約を守る。実 sudo を使わない代替 subprocess と制御可能な待機で TDD を行う。
- [ ] 一括 setup: 同 CLI とテストに build → switch → trust → dry-run → apply → 配置確認を追加する。既存の `/usr/bin/python3` を用いる shell 入口は維持し、実機を操作しない fixture と一時 HOME で段階別停止を確認する。配置の契約に必要な統合ケースだけ `scripts/tests/test_dotfiles_links.py` の既存基盤へ追加する。
- [x] アプリ一覧: `nix/darwin/homebrew.nix` の `cmd-eikana` 宣言を削除する。既に承認・変更済みの Pages / Numbers / Keynote ID 更新、Transmit の cask 化、Okta 宣言削除を保持する。cleanup は `none` のままとし、実アプリの削除を行わない。
  - 検証: 対象 module を fixture の primaryUser で Nix 評価し、3 ID・Transmit cask・cmd-eikana / Okta / Transmit mas の除去・cleanup=none を確認。直接 import は pure 評価で拒否されたため、読取対象をこの非秘密 module に限定して `--impure` で評価した。実インストール・アンインストールなし。両構成の生成物確認と独立レビューは最終ゲートで行う。
- [ ] 運用文書: `README.md`、`AGENTS.md`、`.agents/skills/dotfiles-setup/SKILL.md` と `references/setup.md` を新 CLI に合わせる。初回手順5〜6は setup にまとめ、既存 Mac の通常更新と移行・失敗後の再開を区別する。適用だけの例では build 出力パスを明示する。手順番号とリンクも整合させる。履歴文書を一括書換えせず、前回 dig log には置換された決定と本計画への参照だけを追記する。

## Final Validation

- [ ] `uv run --no-project python scripts/tests/test_dotfiles_cli.py`：実 Nix 必須の統合テストを skip せず通す。Git snapshot・lock 非更新・未追跡ファイル非混入・default/private 選択を維持する。switch が metadata / eval / check / build を呼ばず指定成果物だけを適用し、checkout の変更でも候補が変わらないことを確認する。
- [ ] 同 CLI テストで引数不足・旧構文・不正/消失/metadata 欠落の成果物、ユーザー/HOME 不一致、root・Safehouse・非対話、承認拒否、Hermes 検査失敗、profile 登録失敗、activation 失敗、適用結果の不一致を確認する。いずれも該当段階より後の処理を実行しない。既存の shell 退避の競合・途中失敗の回帰テストを新入口に合わせて維持する。
- [ ] sudo 認証のテストで、適用承認・必要な退避承認・停止検査より前には認証しないこと、認証失敗時は変更しないこと、非対話更新・有限 timeout、更新失敗時の後続停止と実行中適用の結果回収を確認する。正常終了・例外・中断・通常の終了シグナルで更新が終了・回収され、mise 段階と build / update では更新しないことを確認する。モックだけで寿命を確認できない箇所は、隔離した代替実行ファイルで検証する。パスワード保持・expect・sudoers 変更・キャッシュの一括失効を追加しない。
- [ ] setup のテストで build は一度、同じ成果物を適用、既存 PATH の mise を使わない、対象ファイルだけの trust、dry-run の60秒制限、拒否・timeout・各 subprocess 失敗・宣言変更時の停止、代表リンクの不一致と完了済み段階の報告を確認する。実 sudo・profile・`/etc`・実 HOME は触らない。
- [ ] 候補 Nix 版 mise の bin ディレクトリを PATH の先頭に置いて `uv run --no-project python scripts/tests/test_dotfiles_links.py` を実行し、既存の直接リンク・未追跡ファイル除外・衝突保全を確認する。setup の trust / dry-run / apply 連携は隔離された一時 HOME と state/cache/config ディレクトリでも確認し、親環境の広域 trust や CI 自動承認に依存しない。
- [ ] `bash scripts/dotfiles.sh build` と `bash scripts/dotfiles.sh build --configuration private`：両方成功し、生成 metadata が各成果物の設定名・ユーザー・HOME・Hermes check・mise に対応することを確認する。生成 Brewfile の iWork ID と Transmit cask を確認し、cmd-eikana・Okta・旧 Transmit mas 指定の除去は一度きりの成果物確認で済ませる。新規 Nix module を使う場合はそのパスだけを Git に追加してから build し、Git 外の設定を取り込まない。
- [ ] 変更 Python の構文、`bash -n scripts/dotfiles.sh`、文書リンク・掲載コマンド構文、`git diff --check` を確認する。README とエージェント指示の両方で旧 switch 例が運用手順に残っていないかを対象限定検索で確認する。
- [ ] 実装側の独立レビューで、成果物選択と昇格の境界、非原子的な適用、確認・競合・失敗時の保全を確認する。実 sudo / profile 更新 / activation / App Store / アプリ導入 / chsh / 実 HOME 配置は未検証範囲として明記し、検証目的で実行しない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。

## 作業開始時点

- `nix/darwin/homebrew.nix` の iWork ID・Transmit・Okta の変更は未コミット。直前に両構成 build と生成 Brewfile を確認済みだが、本計画の Nix 変更後はその検証で代用しない。cmd-eikana 削除は未実施。
- Claude / Pi のユーザー側の変更4件と、他テーマの計画 `2026-10-10-pi-subagent-completion-delivery.md` は変更対象外。
- 本計画の作成では read-only の調査のみ行い、実装・テスト実行・実機適用・commit・push は行っていない。
