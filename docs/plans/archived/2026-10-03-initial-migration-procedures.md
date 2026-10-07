# 初回 Nix 移行時の退避・復旧手順（検討履歴）

この文書は、2026-10-03 の Nix 初回移行で検討した資料を旧 `docs/setup.md` から保存したもの。以下の手順を全部実施済みという意味ではない。実際の適用では、全件台帳・一括事前バックアップではなく、実際に報告された衝突を個別に対処する方針へ変更した。

**現行の必須手順ではなく、この資料だけを根拠に実行しない。** 必要になった対象について現在の実機状態・候補生成物・操作範囲・復旧方法を確認し、個別の承認を得る。現行の初期設定・運用は [dotfiles-setup の同梱資料](../../../.agents/skills/dotfiles-setup/references/setup.md)を参照する。

以下は当時の原文。リンクだけを移動先に合わせて修正した。当時の「この Mac」や未実施事項の記述は現在の状態を示さず、実施結果は [移行計画](2026-10-03-nix-migration.md)に記録されている。

### 初回の退避台帳と停止前の引継ぎ

以下は初回移行用の手順であり、退避・復旧の実行承認ではない。実行直前に候補の生成物と実機を照合し、[移行計画の T9](2026-10-03-nix-migration.md) に残る確認を終える。古い `/tmp` の調査結果だけを使って移動しない。

退避先は Git / store 外に、今回専用の未使用ディレクトリを用意する。HOME 用は `~/.local/state/dotfiles-backups/<移行ID>/`（本人所有・0700）、system 用は `/var/root/dotfiles-backups/<移行ID>/`（root 所有・0700）とする。system 側の作成・保全は人間が sandbox 外で行う。親経路に予期しないリンクがないことを確認し、既存バックアップへ上書きしない。

| 保存先（各退避ルートからの相対パス） | 保存内容 |
|---|---|
| `before/home/<HOME相対パス>` または `before/system/<ルート相対パス>` | 元のリンク・通常ファイル・ディレクトリ。リンクは参照先を辿らずリンク自体を保存し、所有者・mode・必要な ACL / 拡張属性も保持する |
| HOME 側の `before/pi-content/<HOME相対パス>` | Pi の旧リンクを動かす前に保存した設定内容。リンクの保存と分離する |
| `after/` | 復旧する直前の、新構成のファイル・リンク・適用後の変更。`before/` を使い回さない |
| `manifest`・`operations`・`resume` | 対象ごとの元パス、種別（未作成も含む）、リンク先、metadata、退避先、移動の要否、実行済み操作、失敗箇所と再開手順。設定内容や秘密は書かない |

台帳の通常配置対象は、完成ビルドに対応する Home Manager の `home-files` の各末端ファイル・リンクとする。store 側でディレクトリへのリンクになっているスキル・plugin は、そのリンクを1対象として扱い、リンク先の中を展開して列挙しない。下表の activation の追加配置先・旧 fish ファイルも台帳へ加える。Pi 設定3件は通常配置に含める。非秘密のリンク先正本も切替時点の内容を保全し、旧リンクの復元を Git の巻き戻しに依存させない。

Pi や端末を止める前に、`resume` へリポジトリと host 入力の場所、候補 system / HM の store path、旧 profile または「なし」、両退避ルート、未完了の行を記録する。人間がこの文書と台帳を開ける別の通常端末を残す。停止後に自動でエージェントを起動する手順にはしない。

### HOME の退避と Pi 設定の準備

初回のリンク退避時は、書き込み元の Pi・Claude・設定対象のアプリと、旧 shell 状態を整理する場合の fish を停止してから保全する。必要な停止対象とタイミングは直前に確認する。この停止は退避時の競合回避であり、日常の内容編集で全アプリを止める運用にはしない。認証・session・DB や未管理の兄弟を移動せず、共有正本へのリンクを理由にリポジトリ側の実体を移動しない。

| 対象 | 退避・適用前の扱い |
|---|---|
| 通常配置の旧リンク | 元のリンク文字列を台帳へ記録し、リンク自体を `before/home/` の同じ相対パスへ移す。元パスを空ける |
| 外部スキル・Yazi plugin の実ディレクトリ、Herdr hook の実ファイル | 対象単位で保全してから同じ相対パスへ退避する。`.agents/skills` や `.claude/skills` 全体、`synced` は動かさない |
| `.gemini/antigravity-cli/skills` | 共通スキル置き場への参照を記録。配置対象のリンク自体だけを扱い、共通置き場は動かさない |
| `.config/fish/config.fish` | 秘密を含み得るため人間が保全・退避する。内容を Git・会話・検証ログへ出さない |
| 旧 fzf / bobthefish | 候補 plugin source と照合した既存ファイルだけを個別退避する。旧 `conf.d/fzf.fish` と9関数、bobthefish の9関数が対象。差分のある旧関数も保存し、`fish_frozen_*`・由来不明の `fish_logo` を一括退避しない |
| 旧 Unity CLI 初期化・既知の Zellij リンク | `conf.d/unity-cli.fish`、`functions/zl.fish`、Zellij の `config.kdl` は個別に記録。Unity 本体・PATH の整理は[Unity CLI](../../../.agents/skills/dotfiles-setup/references/setup.md#unity-cli)と T9 の別作業で、ここでは本体や Hub データを削除しない |
| 新規配置 | 元が未作成と記録し、退避物を作らない。通常配置以外に Hermes plist 2件、`~/Applications/Home Manager Apps`、`~/Library/Fonts/HomeManager` を含む。アプリ・フォント配置は rsync の削除を伴うため、直前に既存実体が見つかったら保全方針を確認して止まる |

Pi は次の3ファイルを、1件ずつこの順に処理する。

- `.pi/agent/settings.json`
- `.pi/agent/extensions/pi-footer.json`
- `.pi/agent/extensions/pi-gpt-fast-mode/config.json`

1. Pi の終了後、親経路とリンク先を再確認する。リンクを動かす前に内容を `before/pi-content/` へ保存し、有効な JSON であることを確認する。
2. 旧リンク自体を `before/home/` へ退避する。退避先へ移した相対リンクを辿って内容を読み直さない。
3. 元パスを空けた状態で Home Manager の標準配置へ引き渡し、`~/dotfiles/config/` の追跡済み正本への live link を配置する。通常ファイル化・merger・旧正本への手動取り込みは行わない。必要な非秘密内容は保全したまま保持する。
4. 適用・リンク先の確認を終えるまで Pi を再起動しない。未知の実体や内容差分を強制上書きしない。

`fish_variables` はこの準備で変更しない。後続の PATH 整理では対象キーの旧値を別に控える。履歴・認証を含み得る状態ファイル全体を Nix の入力へ加えない。

### system の保全と適用前の確認

初回は旧 nix-darwin 世代がない。人間が次を system 側台帳へ記録し、必要な旧ファイルを保全する。`/etc` 配置だけで初回復旧を完了した扱いにしない。

- 候補 system の `etc` 配置先と同名の `.before-nix-darwin` の有無。既存の `/etc/bashrc`・`/etc/zshrc`・`/etc/zprofile`・`/etc/nix/nix.conf` は私有バックアップにも保存する。既知 hash と一致するファイルも適用で置き換わる。未知内容の bashrc / zshrc を標準退避名へ移すのは、保全と直前承認の後に限る。既存の退避名へ上書きしない。
- `/Library/LaunchDaemons/org.nixos.nix-daemon.plist` の実ファイルと metadata、実行先、launchd の登録・disabled 状態。installer の `/nix/var/nix/profiles/default` から root profile・旧 store environment までのリンク鎖を記録して保持する。旧 daemon の実配置と未比較の store 内 plist を復旧用コピーの代わりにしない。
- `org.nixos.activate-system.plist`、system profile、`/run/current-system`、current-system GC root、`/etc/static` の元の有無と参照先。HOME 側も home-manager profile と `current-home` GC root の有無・リンク先を記録する。既存のユーザー Nix profile を HM profile と混同しない。
- `/etc/synthetic.conf` の内容・mode、`/run` の元の状態、PAM の `/etc/pam.d/sudo`、必要な Nix custom config。SSH host key の有無と保全は人間が扱い、秘密鍵をエージェントやログへ渡さない。`hosts.before-nix-darwin` 等の既存退避がある場合は、候補の復元処理と衝突しないか確認する。
- `/Applications/Nix Apps`・`/Library/Fonts/Nix Fonts` と `/var/lib/linux-builder` の有無。前二者は同期で削除が起こり、後者は候補 activation の冒頭で削除される。既存実体があれば適用を止め、保全と扱いを確認する。
- Nix build users / group、PAM、SSH、TCC について、候補が変更する条件と実機の状態を照合する。変更が必要ならその範囲と戻し方を承認する。ログイン shell・権限・秘密の変更を、通常のファイル退避へ紛れ込ませない。preferences は[対象キーだけを控える](../../../.agents/skills/dotfiles-setup/references/setup.md#macos-と手動復元)。

旧 daemon の復元元・登録し直す操作、system 固有の変更条件の確認が終わるまでは `switch` へ進まない。実機を変えずに読み取った生成物だけでは、復旧時の daemon 起動や権限の復元を検証したことにならない。復旧が終わるまで Nix GC・旧 profile の更新・バックアップ削除をしない。

### 失敗段階ごとの復旧と再開

自動再試行せず、台帳と出力から変更済みの対象を確認する。標準 `switch` 起動前に止まった場合も、手動で退避済みの HOME・`/etc` はそのままなので、再開するか下記の方法で戻すか決める。標準 `switch` 起動後は、エラーが早い段階でも profile や一部変更が残り得る。

system を戻す場合は、人間が管理操作可能な端末を維持し、次の順で行う。各 service・権限・秘密・削除操作は直前承認の対象であり、未登録のサービスを推測で停止しない。

1. 今回登録された `org.nixos.activate-system` があれば登録を解除し、今回配置した plist を保全して元の状態へ戻す。このサービスは system profile から `/etc` と current-system を再設定するため、先に止める。
2. daemon を置換済みなら新 daemon の登録を解除する。今回の `/etc/static` への管理リンクだけを外して保存した旧設定を戻し、必要な PAM の変更も戻す。各リンクの参照先と切替後の変更を確認してから処理し、最後に `/etc/static` を元の状態へ戻す。
3. 保全した旧 daemon plist を元の所有者・mode で戻し、確認済みの installer profile を使って登録・起動し直す。daemon 接続を確認する。Nix 自体を再インストールしたり、build users を一括削除したりしない。
4. HOME・HM の状態と preferences を対象別に戻す。system / current-system / GC root の今回の有効な参照を元の状態へ戻すが、候補世代・store 成果物は復旧資料として残す。
5. `synthetic.conf` の今回の変更だけを戻す。installer の Nix mount 設定は保持し、`/run` を先に外さない。APFS の反映や再起動が必要なら別途確認する。Homebrew の導入物、SSH 鍵・build users・TCC 等の変更は、このファイル復旧だけでは戻らないので個別に扱う。

HOME は書き込み元を止めたまま、台帳の対象ごとに次の順で戻す。

1. 現在のパスと親経路を確認する。新構成のリンク・ファイルと適用後の変更を `after/` へ保存・退避し、復旧先を空ける。未知の実体や、台帳と異なる参照先を force overwrite しない。
2. `before/home/` から元のパスへ、元の種別・metadata で戻す。スキルの実ディレクトリなどの参照先を先に戻し、その後で参照リンクを戻す。旧リンクが指す正本に後続変更があれば、勝手に巻き戻さず確認する。
3. Pi は適用後のリンクと必要な非秘密内容を保全してから旧リンクを戻す。`before/pi-content/` は切替直前の内容として保持し、正本への後続変更を無断で巻き戻さない。旧正本への手動取り込みを移行手順にはしない。
4. 元が未作成だった対象は、今回の生成物であることと後からのデータがないことを確認して `after/` へ退避する。親ディレクトリを再帰削除しない。Hermes はこの Mac で起動せず、別 Mac では管理関数による停止を確認してから plist を扱う。
5. HM の profile / `current-home` 参照も元の有無・リンク先へ戻す。世代や store 成果物は消さない。旧 shell の PATH と削除コマンドの実行先・挙動を確認してからアプリを再開する。現行構成の `rm` は直接削除するため、ごみ箱を使う場合は `gomi` を明示する。

廃止した配布スクリプトによる復旧は行わない。標準 `darwin-uninstaller` も初回復旧の既定手段にしない。今回以外の `.before-nix-darwin` や shell・`run` 設定も変更し、途中失敗では旧 daemon の復元条件が成立しない場合があるため、必要なら固定版の処理と失敗状態を確認して別途承認する。

以前の nix-darwin 世代がある場合は標準の `--list-generations` / `--switch-generation` による復旧を検討できるが、実行は別途承認する。世代の切替は管理リンクを戻す操作であり、live link 先の本文は戻らない。本文は Git で別に戻す。Homebrew アプリ・preferences・DB も世代の切替だけで戻るとは扱わない。中断後は `resume` と `operations` の最後の完了行から状態を再確認し、bootstrap・`switch`・退避操作を最初から繰り返さない。
