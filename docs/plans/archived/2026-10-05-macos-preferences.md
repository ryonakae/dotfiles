# macOS 設定の Nix 管理拡張 Implementation Plan

## Requirements

[dig log](../../dig/2026-10-05-macos-preferences.md) と会話の Q3: A に基づく。ただし、その後の「無理に複雑にしすぎない。nix標準機能で管理できるものだけにする」を優先し、管理範囲を以下へ縮小する。本計画が最新の方針であり、標準ショートカット・電源を管理する旧決定は本計画の対象外規定で置き換える。dig log にも変更後の決定を記録した。

- 現在の使い勝手を変えず、nix-darwin の標準オプションだけで表現できる設定を管理する。全分野を埋めるための独自処理は作らない。
- `system.defaults` の専用オプションを優先する。標準機能の `CustomUserPreferences` は、確認済みの単純なスカラー設定に限って利用可とする。辞書全置換や ByHost の特殊な扱いが必要な設定には使わない。
- Dock 高速化は `autohide-delay = 0.0`、`autohide-time-modifier = 0.15` を宣言する。旧 README の手順は `ab60631` で削除され、Nix 移行から漏れたが、実機には現在も残る。
- 現在値・意味が確認できない項目は推測で追加せず、保留として報告する。標準対応のために現在値を別の値へ変更しない。
- 既存の他者差分と lock を保持する。実装・build と実機適用を分け、switch・必要な再ログインは別途承認を得る。

### 対象外

- 独自 activation、defaults／pmset／hidutil の追加スクリプト、辞書マージ処理、常駐処理、独自 module option、host schema 拡張、新しいテスト基盤。
- **macOS 標準ショートカット**: 専用オプションがなく、CustomUserPreferences で AppleSymbolicHotKeys を部分指定すると辞書全体を置換する。安全な部分更新の独自処理は追加せず、現在の設定をそのまま残す。
- **電源設定**: 現在のディスプレイスリープはバッテリー2分／AC10分、本体スリープは1分／無効。標準 power.sleep は電源種別を分けられないため、今回の追加対象から外す。共通値に揃えず、現状を維持する。
- **デバイス別キー割り当て**: 標準 system.keyboard のグローバルマップへの置換はしない。現在の hidutil UserKeyMapping は `(null)` なので、新しい共通マップも追加しない。
- **Control Center の Bluetooth／NowPlaying**: 現在の整数値2／8を標準オプションの18／24へ変更しない。個別の ByHost 書き込みは追加しない。
- アプリ別メニューショートカット、Apple ID、指紋登録、TCC、認証・秘密・Keychain、sudo 認証、フォント、ネットワーク・ファイアウォール、サービス運用、アプリ導入方式の変更。

## Implementation Decisions

### 変更は既存 preferences に集約

`config/nix/darwin/preferences.nix` を拡張する。keyboard.nix／power.nix や独自スクリプトは追加しない。標準 module が生成する activation のみ利用する。

固定 lock の nix-darwin は `4cff07de74b50e64bdd68cd4e722ab5b6b35ee48`。実装時はこの固定 input のオプションと型を確認し、対応のために input を更新しない。

2026-10-05 に個別キーを読んで確認した追加候補は次のとおり。既存宣言は維持する。

| 分野 | 確認済みの現在値／追加方針 |
|---|---|
| 入力補正 | WebAutomaticSpellingCorrectionEnabled=false。標準 CustomUserPreferences の NSGlobalDomain で補完 |
| 外観 | AppleInterfaceStyleSwitchesAutomatically=true。読取時の Dark は固定の好みと誤認せず、自動切替を維持 |
| 操作 | AppleShowScrollBars=WhenScrolling、AppleKeyboardUIMode=2、com.apple.keyboard.fnState=true、_HIHideMenuBar=false |
| スクショ | show-thumbnail=true |
| Dock | 高速化2項目、expose-group-apps=true。四隅の corner は左上2・右上12・左下3・右下4。modifier も確認し、標準オプションで組として維持できるものだけ追加 |
| Finder | NewWindowTarget=PfHm。内蔵／外付けディスクのデスクトップ表示false、リムーバブルメディア表示true、_FXSortFoldersFirst=true |
| 時計 | ShowDate=0、ShowDayOfWeek=true |
| Control Center | BatteryShowPercentage=true、Sound=18。対応する標準オプションの出力値が一致するものだけ追加 |
| Window Manager | GloballyEnabled=false（Stage Manager 無効） |

スマートダッシュ／クォート、スクショの保存先・形式・影、ナチュラルスクロールなどは明示値が未設定だった。必要な範囲で UI 等の実効値を確認し、標準オプションで確実に再現できるものだけ追加する。全項目の網羅調査や未設定キーへの一律デフォルト値の書き込みはしない。保留項目は完了報告で区別する。

### Dock の固定項目

標準 `dock.persistent-apps` / `persistent-others` を使う。2026-10-05 の対象キー抽出で以下を確認済み。GUID・bookmark・履歴は宣言しない。

- アプリ順: Spark Desktop、1Password、CleanArchiver、Google Chrome、Slack、Notion Calendar、Bear、CotEditor、Figma、Figma Beta、Ghostty、Zed、X、Bluesky、Spotify、LINE。
- X／Bluesky は `${machine.homeDirectory}/Applications/Chrome Apps.localized/` 配下。それ以外は `/Applications` 配下。現在の項目パスを確認し、HOME をハードコードしない。
- フォルダ順: `/Applications`（名前順・フォルダ表示・自動表示）、`${machine.homeDirectory}/Downloads`（追加日順・フォルダ表示・ファン表示）。標準オプションで表現できることを確認済み。
- Chrome アプリの作成・認証は手動復元のまま。未導入アプリを解決する仕組みを追加しない。別 Mac ではアプリ本体の復元が別途必要なことを手順に記す。

## Tasks

Review base: `f3c95049f6f3b47c456087957e3c8e67613d7335`（master、開始時 origin/master と一致）。実装と運用手順は同じ管理範囲を定義するため、一つの成果物として検証・commit する。

- [x] **標準 preferences の追加**: `config/nix/darwin/preferences.nix` に上記の標準対応項目を追加する。
  - 対象キーの現在値・型と固定 input のオプションを照合する。未対応なら無理に補完せず保留する。
  - Dock の高速化・並び・フォルダ表示を含める。外観の自動切替を固定 Dark にしない。
  - 既存 `machine.homeDirectory` を使い、追加 module や汎用の設定機構を作らない。
- [x] **復元手順の整合**: `.agents/skills/dotfiles-setup/references/setup.md` の macOS 節を必要な範囲だけ更新する。
  - Dock の並びを一律に手動復元扱いする旧記述を改める。標準ショートカット・電源・デバイス別リマップは手動のままと明記する。
  - GUI で変えた管理対象値は次回 switch で宣言値に戻ること、アプリ本体の復元は別であることを説明する。設定値一覧は重複転記しない。

## 実装状況・ブロッカー

- 2026-10-05: `preferences.nix` に確認済みの標準対応項目を追加。Finder は `NewWindowTarget = "Home"` を使い、Other 専用の NewWindowTargetPath は設定しない。四隅の modifier は個別読取で全て整数0を確認し、単純な CustomUserPreferences 値として宣言した。
- `setup.md` に管理範囲・GUI 変更と switch の関係・Dock アプリ本体の手動復元を反映。未設定項目は実効値を推測せず保留。独自処理は追加していない。
- 固定 nixfmt 1.5.0 の `--check config/nix/darwin/preferences.nix` は成功。
- 通常 build は `~/.config/dotfiles/host/host.json` 不在で失敗。現在ユーザーの username / homeDirectory だけを一時ディレクトリに生成し、`bash scripts/dotfiles.sh build --host <temporary-directory>` を実行した。永続 host 設定は作っていない。
- 一時入力では flake check が成功したが、system build は既存の `config/nix/home/fish.nix` の依存評価で停止: `getting status of "/nix/store/1562h92r7sppvrahcm4l89vlmfg5wb9i-source/.envrc": Operation not permitted`。入力 source は `/nix/store/b41haa1hqbifm908whlzwcyk3mla4j74-source`、一時 host snapshot は `/nix/store/6snq49j2m7agdrl80vh5g2m55css20ma-dotfiles-host`。
- ユーザーの追加承認後、Herdr の通常ペインで同じ固定 source／host snapshot の非適用 build を実行し、終了コード0で成功。system は `/nix/store/c4mnqzv56k8sr9bsxaasj7mlw8nbbbvr-darwin-system-26.11.4cff07d`。永続 host 設定の不在は未解消なので、将来の通常 switch 前にセットアップ手順に従って用意する。
- 生成 activation の48個の defaults plist を parse し、全 scalar を現在値と照合。Dock の16アプリ／2フォルダは順序・パス・表示形式が一致（GUID 等は比較対象外）。対象外の AppleSymbolicHotKeys／Bluetooth／NowPlaying／固定 AppleInterfaceStyle、および pmset／hidutil／systemsetup 書き込みがないことを確認。指定された Nix Bash 5.3 による `-n` も成功。
- 一度きりの照合コードは当初、標準生成物にない tile-type の必須扱い、設定件数の誤算、括弧の構文誤りで失敗した。検証コードを修正した最終実行は成功し、この過程で実装の変更はない。
- build source 内と作業ツリーの preferences.nix は cmp で一致。文書リンク・`git diff --check` を確認。doc-updater は今回の4ファイルを対象とし、運用手順の更新済みを確認。README／AGENTS の追加変更は不要。
- 実機適用・UI 動作確認は未実施で、今回の承認範囲外。独立レビューの結果は以下の gate summary に記録した。

## Final Validation

計画修正時にはテスト・build・activation を実行しない。実装時の確認は以下に絞る。

- [x] **構文・ビルド**: 固定 input の formatter で変更 Nix を確認し、`git diff --check`、`bash scripts/dotfiles.sh build` を実行する。lock が変わらず成功すること。独自ロジックを追加しないため、そのためのテストやテスト基盤は作らない。
- [x] **生成物**: 追加した defaults のキー・型・値、Dock の順序・フォルダ表示・HOME 展開を確認する。対象外のショートカット・電源・Bluetooth／NowPlaying・機器別リマップを書き換える新規処理がないこと。生成 activation を検証目的で実行しない。
- [x] **文書**: 管理対象／手動復元の説明と参照リンクが実装に一致すること。
- [ ] **承認後の実機適用**: 対象キーだけの旧値・型・未設定状態を Git 外へ控え、通常の対話端末から `bash scripts/dotfiles.sh switch`。Safehouse 内から適用しない。標準 Dock 再起動の UI 影響を事前に伝える。
- [ ] **実機確認**: 追加した設定に限り、Dock の出現速度・並び・フォルダ表示、Finder、スクショ、メニューバー、外観の自動切替設定等を確認する。build 成功だけでは動作確認済みとしない。

preferences は宣言削除・Nix 世代 rollback だけでは戻らない場合がある。復旧時は対象キーの旧値を戻し、元が未設定なら対象キーだけを削除する。復旧操作は必要時に承認を得る。実機適用が未承認なら、その検証は未完了として実装・build の結果と分けて報告する。

## Gate summary

- 実装・運用手順・決定記録の commit: `244ec72`。review base は `f3c95049f6f3b47c456087957e3c8e67613d7335`。
- 独立 read-only reviewer が base..244ec72 と計画を照合し、blocking/high・decision required・medium/low の指摘なし。修正 cycle は不要。
- build・生成物照合・構文・差分検査の有効な結果を再利用。レビュー後の変更はこの記録と計画のアーカイブ／参照整理のみで、実装は変更していない。
- 現在値が未設定で実効値未確認の追加候補は保留。承認済みの縮小方針に従い、独自処理で補完しない。
- 実装の受入条件に未解決事項なし。実機適用・UI確認は別承認のため上記チェックを未完了のまま残す。通常switchには永続 host 入力の準備が必要。
- 既存の無関係な settings 3ファイルはコミット対象外として保持。実装 commit と本アーカイブ commit をまとめて通常 push する。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
