# dig log: Nix を中心とした Mac 環境の再構築

## 目的・前提・制約
- Mac の新規購入・クリーンインストール時に、ツール・アプリ・ユーザー設定・macOS 設定をリポジトリから再構築しやすくする。日常の変更・更新の扱いやすさも重視する。
- 本ログは、初回の要件整理と実装中に必要になった追加判断を記録する。過去の調査記録は当時の状態であり、現在の実装・検証状況は [実装計画](../plans/2026-10-03-nix-migration.md) を参照する。
- 現在の Homebrew、mise、config/ と HOME の対応構造、自作 symlink 配布、*.example のコピー等は、維持必須の要件ではない。
- 秘密の保護、rm 転送による誤削除防止、Hermes の安全な停止など、既存実装が守る要件は維持する。実現手段は見直せる。
- 初回の要件整理時点では Nix のインストール・ビルド・実機への適用を行っていなかった。過去の調査は当時の Git 管理ファイルと公開資料が対象で、実秘密や Git 管理外の実設定は読んでいない。
- 要件合意後に plan で実装計画を保存し、その承認後に implement で実装する。要件整理中は実環境を切り替えない。
- 2026-10-03 開始時点の既存変更は config/.pi/agent/extensions/pi-gpt-fast-mode/config.json と config/.pi/agent/settings.json。上書きしない。

## 標準管理の補完調査（当時の候補・採否は決定事項と実装計画を参照）

- Hermes: [公式 Flake](https://github.com/NousResearch/hermes-agent/blob/main/flake.nix) は aarch64-darwin を対象に含み、パッケージとサービスモジュールを分離している。パッケージのみを公式定義から採用し、root lock で入力を固定する案。独自 package 定義・updater は作らず、サービス起動は別扱い。実ビルドは未実施。
- agent-device: [0.21.19 の helper 実装](https://unpkg.com/agent-device@0.21.19/dist/src/helper.js) はパッケージの `apple/macos-helper` 内で `swift build -c release --package-path` を行い、`.build/release` から HOME 内の cache へコピーする。単純な store 配置はこのビルド先が読み取り専用になるため、[mise の標準 npm backend](https://mise.jdx.dev/dev-tools/backends/npm.html) を残す案。npm の版固定と全推移依存の固定は区別し、Node 要件も導入時に確認する。helper の実ビルド・署名・権限変更は未実施。
- 可変設定: 採用中の Home Manager では Zed に `mutableUserSettings` があり、Pi のモジュールは設定を store にリンクする。汎用 `lib.hm.generators.mkImpureConfigMerger` は experimental と明記されている。通常ファイル配置とは分けて採用方法を判断し、独自 merge 基盤は作らない。

## 決定事項
- Hermes の追加承認: fork の `default` から `voice` だけを標準 `override` で除外する。ローカル音声認識・マイク入力用の依存は同梱せず、Hindsight・メッセージング・TTS など他の追加グループは残す。fork 本体の改変や依存パッケージのテスト無効化は行わない。
  - 理由: Apple Silicon 用の CTranslate2 を nixpkgs から供給する経路で、検証用依存の PyTorch がソースビルドされていた。候補の実依存グラフを比較し、`voice` だけの除外でこの依存を避けられることを確認した。
  - 出典: 調査結果の「default から voice だけ除外」案に対する「じゃあそれで」。初回の所要時間と、既に構築済みの依存を再利用した所要時間は区別する。
- 最新の Hermes 合意: 本体は `ryonakae/hermes-agent` fork、起動・停止・再起動は既存の fish 管理関数から fork 標準処理を利用する。dotfiles の適用入口は起動状態を保持せず、自動停止・再開もしない。配置上必要な読み取り専用の確認に失敗したら中止する。
  - 出典: ユーザーが fork URL と既存スクリプトの利用を指定し、「dotfiles が起動状態を管理する必要はない」と指示。修正計画への `ok` に続き、「タイムアウト時の挙動も fork に任せる」ことへの `ok` を取得した。自動強制終了を禁じる旧 Q18 はこの点で置換された。
  - 専用 controller・独自の子プロセス管理は撤去する。fork の標準停止が強制終了へ進むことは受け入れるが、実サービス操作を今行う承認ではない。DB バックアップの整合性は別に確認する。
- Q17: A を採用。Hermes の plist の生成・配置は Nix / Home Manager が担当し、起動・停止は既存の管理関数で行い、最新合意により切替入口は確認だけに限定する。Hermes に標準 launchd activation を使わず、必要最小限の配置処理と停止確認を追加する。
  - 理由: 固定 HM は同一設定でも未ロードなら bootstrap するため、停止状態を維持する要件と両立しない。変更・削除時の bootout も Hermes の正規停止を経由しない。
  - この Mac でサービスを起動しないこと、実操作直前の承認、別 Mac の既存データ保持は維持する。通常の適用で停止済みサービスを再開しない。
  - 出典: Q17 への「a」。標準 launchd の自動再ロードを許容する B 案は不採用。
- 実装中の追加合意: Hermes は公式 Flake のパッケージのみ採用し、サービスは別に扱う。agent-device はグローバル mise 管理をやめ、版を固定しない `npx --yes agent-device` を使う。独自の版固定・自動更新制限は追加しない。Shepherd は復元対象から外し、Zerdr は Homebrew 版、cua-driver は公式 skill の固定復元を採用する。実アンインストールやサービス起動の承認とは区別する。
- 実装中の追加合意: 通常の設定は immutable とし、Pi の書き込みが確認された JSON だけ標準 `mkImpureConfigMerger` を使う。自作・外部スキルは個別配置し、認証・session・自己更新データや管理外の兄弟ディレクトリを置き換えない。
- 設定の分離に関する追加指示: fish 以外も通常の設定本文は元の形式で管理し、Nix は導入・連携・配置の指定に薄くする。Nix 固有のパス解決や OS 宣言は Nix に残す。
- 最新の追加指示: 「可能な限り標準管理に統一。どうしてもそれが難しいというものだけは相談」。AI を含む本体は共通 nixpkgs の標準定義、設定の配置は Home Manager に分ける。現行版維持・個別更新のための独自パッケージや専用 updater は不要。標準管理が難しい対象だけ理由・代案を示して採用前に相談する。Q3 / Q10 の個別・AI グループ更新の決定は撤回した。
- 検証方針の追加指示: 本移行では回帰テストの追加・再実行を行わず、構文・差分・Nix 評価とビルドで進める。
- Q16: A で要件整理を終了し、実装計画の作成を承認。その後、保存した計画への「ok」で実装を承認された。
- 追加確認（訂正）: この Mac では Hermes を使用しておらず、ディレクトリもない。別の Mac では稼働中。この Mac は新規導入対象として停止・既存データ移行を不要とし、自動起動しない。共通構成は別の Mac の既存データ保持と稼働中の安全な切替にも対応する。別の Mac への適用・停止・再起動は、その Mac での作業時に確認する。
- Nix 実装は標準の upstream Nix を採用し、導入後の本体・daemon・設定は nix-darwin で管理する（Q15: A）。Determinate Nix に本体管理を分離する構成は採らない。
  - macOS の multi-user daemon 構成を前提に、macOS 26.2 対応の具体的な installer と初期導入手順を計画時に確認する。今回の回答はインストールやサービス変更の即時実行承認ではない。
  - 理由: Mac 全体の構成と Nix 本体の管理主体を nix-darwin へ揃えるため。
  - 出典: Q15 への「a」。
- 移行対象は管理済みの宣言例だけでなく現在の実機を基準にする（Q14: A）。意図的に導入されたツール・アプリは宣言例にないものも含め、不要と確認したものだけ除外する。
  - 依存ライブラリは直接の導入対象と区別し、Nix / Homebrew の依存解決に任せる。名称変更・別系列を単純な追加・削除と扱わず、実機一覧を無条件に直接依存へ変換しない。
  - 理由: 今の作業環境を落とさず、今回まとめて Nix 中心の構成へ切り替えるため。
  - 出典: Q14 への「a」。
- 普段使う外部拡張・プラグイン・スキルも、取得元と版を固定して再構築する対象に含める（Q13: A）。追加・更新は管理設定に記録して適用する。
  - エージェントが実行中に生成・自己更新するデータとは区別し、書き込みが必要なものは個別に扱う。Hermes 等の既存の可変状態を一律に読み取り専用化する承認ではない。
  - すべてを個別の Flake input にするのではなく、取得元・固定方法・配布方法を調査して適切にまとめる。
  - 理由: 本体だけでなく、普段の作業に必要な拡張とスキルを含めて環境を再構築するため。
  - 出典: Q13 への「a」。
- 設定変更はリポジトリの編集後に適用する方式を基本とする（Q12: A）。Nix の宣言的管理を優先し、現在の即時反映方式を維持するためだけの store 外リンクは設けない。
  - Home Manager モジュールは導入・連携・配置に利用し、通常の設定・スクリプト本文は元の形式のファイルを正本にする。Nix 側にはファイル参照と Nix 固有の指定だけを残す。
  - 秘密・認証・履歴・セッション・DB・キャッシュは設定から分離して store 外で扱う。アプリが設定を書き換える場合は所有権を確認し、実際に書き込みが必要な箇所だけ例外として設計する。
  - 理由: 既存構成の維持ではなく、適用済み構成の把握と新規 Mac での再構築を優先する。
  - 出典: Nix のベストプラクティスについての説明後、Q12 確認への「a」。公式資料: https://github.com/nix-community/home-manager/blob/master/docs/manual/usage/dotfiles.md 。
- Homebrew / App Store 経由で残る一般の GUI アプリは自動更新を許容する（Q11: A）。Nix 側で導入一覧を管理し、厳密な版固定が必要なアプリだけ例外扱いにする。
  - flake.lock による同一版への固定・復元保証の対象外。Nix 管理するエージェント本体の自己更新とは区別する。
  - 理由: セキュリティ更新と普段の使い勝手を優先し、アプリごとの更新抑止・例外管理を増やさない。
  - 出典: Q11 への「a」。
- Q10 の旧決定（撤回済み）: エージェント本体と周辺ツールの独立更新を選んだが、最新の標準管理優先へ変更した。ツール別に版・hash を持つ要件は残さない。サービス操作の直前承認は維持する。
- 共通ツール用の秘密管理は dotenvx + Keychain + Safehouse を継続する（Q9: A）。機密ファイルへの直接アクセスを防ぐ目的を優先し、Nix 移行を理由に sops-nix / agenix へ置き換えない。
  - Nix はツール・秘密を含まない起動処理・保護設定の再構築を担当する。実秘密と復号鍵は store に入れず、実秘密の移行・鍵登録・バックアップは人間が sandbox 外で行う。
  - 既存合意どおり、共通ツール用の値は sandbox 外で復号して起動時に注入し、エージェント・子プロセスが利用できることを許容する。プロジェクト用の秘密は共通ファイルへ混ぜず、必要なコマンド単位で扱う。完全な秘密隔離を新たな要件にしない。
  - 理由: 復号ファイルの宣言的配置より、機密ファイルの直接アクセス拒否と平文・鍵ファイルを増やさない既存方式が目的に合う。
  - 出典: 保護目的の補足と、推奨説明後の「じゃあaで」。過去の Safehouse dig・元計画・実用優先への補足計画を参照。
- Mac 共通の Node / Python / Ruby / Bun 等のランタイムは基本的に Nix へ移す（Q8: A）。mise は既存プロジェクトが必要とする用途に限って残し、プロジェクト自体の設定は無断で変更しない。
  - Hermes 専用ランタイムは、本体・更新処理との互換性を確認して具体方式を決める。
  - 出典: Q8 への「a」。
- macOS 設定は現在の使い勝手を再現することを基準にする（Q7: A）。再構築に必要な項目を選び、一時的な状態や不要な設定まで丸ごとコピーしない。判断が必要な項目だけ確認する。
  - 具体値は対象を絞った非機密の調査で確認し、preferences 全体を無差別に取得・保存しない。
  - 出典: Q7 への「a」。
- 切替時は作業を中断できる（Q6: A）。必要なターミナル・エージェント・アプリ・Hermes 等の停止と再起動、必要に応じたログアウト／Mac 再起動を許容する。
  - 停止・再起動は実行直前に確認する。現在のセッションで即時実行する承認ではない。
  - 出典: Q6 への「a」。
- 現在の Mac を今回の作業で、なるべく早く Nix 中心の管理へ完全に切り替える（Q5）。長期間の段階移行・新旧管理の併用を目標にしない。
  - 事前の棚卸し・ビルド確認・復旧準備を行い、切替作業は可能な限りまとめる。検証や必要な安全手順を省く意味ではない。
  - 完全切替は、合意済みの Nix 中心の管理方式への切替を意味する。補完としての Homebrew と、store 外の秘密・実行時状態は引き続き区別する。
  - 出典: Q5 への「aというか、段階的にというか、なるべく速く完全に切り替える」。実操作は承認済み計画と操作ごとの承認範囲に従う。
- 対応対象は現在と今後の Apple Silicon Mac（aarch64-darwin）に絞る（Q4: A）。共通設定とマシン固有設定を分離する。
  - 出典: Q4 への「a」。
- Q3 の旧決定（撤回済み）: AI 系のみ独立した取得元・更新入口を用意する案を選んだが、現在は標準パッケージ群を nixpkgs 単位で更新する。設定ファイルの分割・配置のために本体を独自化する必要はない。
- Nixpkgs はローリング更新系列を基本とする（Q2: A）。明示的な更新時に新しい版を取り込み、通常の適用では lock に固定した依存を使う。
  - 出典: Q2 への「A」。
- 設定の適用と依存更新を分離する（Q1: A）。通常の適用・新規 Mac の構築は固定済みの依存を使い、最新版を取り込むときだけ明示的に更新する。
  - 日常の全体更新は brew update && brew upgrade に相当する一連の操作としてまとめられる。個別更新の粒度は Nixpkgs・独立した Flake input 等の構成による。
  - Nix 管理部分の依存元を flake.lock で固定し、その変更を Git に記録する。Homebrew 経由のアプリは同じ版固定・復元保証の対象外であり、アプリ自身の自動更新も別途扱う。
  - 理由: ユーザーは、従来に近い一括更新の操作性を保ちつつバージョンも管理できる点を評価した。
  - 出典: Q1 の具体的運用・一括更新の説明後の「バージョンも管理できるってことですかね。ならAかな」。
- Nix / Flakes を構成管理の中心とし、nix-darwin に Home Manager を組み込む方向で設計する。
  - 理由: パッケージ、ユーザー設定、macOS 設定を一つのリポジトリと適用操作にまとめるため。
  - 出典: macOS 設定の管理範囲を説明した後の「良いと思います。この方針で進めよう」。
- ツール・アプリは原則 Nix 管理とする。Nix で導入できない、または保守負担が大きいものは Homebrew を補完手段として使い、導入一覧の正本は Nix 側へ集約する。
  - 出典: 「基本は nix管理にして、nixで無理なやつはbrewで入れる、でも設定ファイルはnix」「それがいいな」と、その後の方針合意。
- 設定ファイルとスクリプトは原則 Home Manager で管理する。本文は既存形式のファイルを優先し、Nix 固有の値や連携部分だけを生成する。
  - 出典: config 等の管理についての説明と、その後の方針合意。
- 移行範囲に macOS 本体の設定を含める。現在の dotfiles に記録されていない GUI 設定も洗い出す。
  - 出典: 「macの設定とか他も管理できるの？」への説明に対する最終の方針合意。
- 現在の構成は大幅に変更してよい。既存運用の温存ではなく、新しい Mac での再構築と日常運用を判断基準にする。
  - 理由: 現在の手段はその時点で扱いやすかったため選んだもので、ベストと考えて固定しているわけではない。
  - 出典: 「今の構成はガラッと変えても良い」と、それを受けた提案への「その方針でいいと思う」。
- 秘密情報は Nix store の外で扱い、実行時状態・個人データの復元と、環境構成の再構築を区別する。
  - 出典: 秘密と実行時状態を分離する方針への合意。

## 対象外
- 今回の Intel Mac / Linux / WSL 対応。必要になった時点で追加を検討する（Q4: A）。
- Nix による macOS 自体の再インストールや、Mac 全体の完全なスナップショット復元。
- 実秘密の読み取り・移行や Keychain 操作を、通常の設定移行と一緒に無承認で行うこと。

## 未決・保留
- T9 の適用・復旧準備は継続するが、Q19 の選択は撤回。最新合意により switch は Hermes を運用せず、必要な停止確認・衝突確認・適用確認だけを行う。
  - 調査: 固定 nix-darwin の標準 `switch` は profile 登録後に activation を実行し、失敗時の自動復旧はない。固定ソース・host snapshot を渡せば、標準の世代登録を維持して同じ入力を再評価できる。`activate` のみでは profile 世代が登録されないため、その代用にはしない。
  - 読み取り専用確認には標準 `check` / `--dry-run` を使わない。固定版では `checkActivation` を export して activation を実行する一方、生成 activation の shebang は `env -i` で環境を消去する。実行ではなくソースと既存生成物で確認した。根拠: nix-darwin 固定 source `pkgs/nix-tools/darwin-rebuild.sh:192–261`、`modules/system/activation-scripts.nix`、生成物 `/nix/store/vxvdvlvffr0lf9kaiy2lvb1w6sxg5izy-darwin-system-26.11.4cff07d/activate`。
- fork と既存スクリプトの実サービス動作、別 Mac の旧定義からの移行は未検証。調査・ビルド結果だけで実機の停止や DB 保全を検証済みとしない。
- Q17 の管理方式は確定済み。T7 の配置処理・停止確認の準備範囲は実装計画を参照。切替入口との接続・実機確認は T9・T10 に残る。HM 実装は plist にユーザー所有の実ファイルを使っており、単純な store symlink への置換は前提にしない。
  - 調査根拠: [固定 HM の activation](https://github.com/nix-community/home-manager/blob/acd21c5a3420a9d5fd0ed06299b10828267ef9ba/modules/launchd/default.nix#L275-L620)。コードの読み取りのみで、実サービス操作による検証ではない。

### 初回調査時の保留事項（進捗・解決状況は実装計画を参照）
- 標準パッケージに未収録・非対応の対象を調べ、必要な例外の導入方法を相談する。GUI アプリの自動更新方針は Q11 で確定済み。
- ホスト別設定と具体的な切替・復旧手順。停止対象・切替タイミングは実行前に確認する。
  - 読み取り専用のホスト確認: macOS 26.2 (25C56)、arm64。現在の PATH では nix が見つからない。インストール済み環境全体の存在確認や Nix ビルドは行っていない。
- 全パッケージの棚卸し: 共通 nixpkgs の標準定義で macOS / CPU に対応しているか確認する。難しい対象だけ公式 Flake・Homebrew 等の補完案を相談し、独自定義を既定の選択肢にしない。
  - 読み取り専用の brew list では formula 116件（依存を含む）、cask 59件。Brewfile.example は formula 38件、cask 51件で一致しない。インストール済みをすべて直接依存として宣言せず、導入意図・依存関係・名称変更を区別する。
  - 宣言例にない実機 cask: 1password-cli、cmd-eikana、cursor、discord、figma-beta、google-japanese-ime@dev、obs、sheltie、tailscale-app、unity-hub、via、visual-studio-code@insiders。一方、宣言例の google-japanese-ime、figma@beta、ogdesign-eagle、zoom は同名で見つからない。名称変更や別系列の可能性があるため単純な追加・削除一覧とは扱わない。
  - 移行対象の基準は Q14: A で確定。実機の意図的な導入対象と依存ライブラリの区別、Homebrew 以外の導入経路との照合、名称変更・別系列の整理は引き続き必要。
  - 主要候補の公開定義を調査。Herdr は上流 Flake に aarch64-darwin があり、Agent Safehouse は nixpkgs に Darwin 定義がある。親も両定義を確認。Safehouse は調査時点で実機版との差があったが、後のユーザー指示により標準定義を採用済み。Herdr も共通 nixpkgs の標準定義を採用し、上流 Flake は使わない。
  - サブエージェント調査では Claude Code / Codex / OpenCode / Pi に Nix 定義があるが、Darwin 向け patch・配布物・依存 hash を含めた固定が必要。agent-device は Apple helper の署名・XCUITest・TCC と store 配置の互換性が未検証。Ghostty 等の GUI、Xcode / SDK / 権限承認は Homebrew / 手動操作の補完候補。パッケージ名の存在だけでは macOS 対応やビルド成功としない。
  - 出典: https://github.com/herdrdev/herdr/blob/master/flake.nix 、https://github.com/NixOS/nixpkgs/blob/master/pkgs/by-name/ag/agent-safehouse/package.nix 、https://github.com/NixOS/nixpkgs/tree/master/pkgs/by-name 、https://oss.callstack.com/agent-device/docs/installation 。Nix 評価・ビルド・実動作確認は未実施。
- ランタイムの具体的な版と PATH の分担、mise が必要な用途の確認。config/.config/mise/config.toml で共通ランタイムと npm:agent-device、config/.hermes/mise.toml で Hermes 専用 Node / Python の指定を確認済み。Hermes 専用ランタイムは本体・更新方式との互換性を確認する。
- エージェント本体・拡張・外部スキルの具体的な取得元と版の固定方法、自己更新との競合、書き込みが必要な設定の所有権。普段使う外部拡張・プラグイン・スキルを固定対象に含める方針は Q13 で確定済み。
  - `config/skills-lock.json` は取得元・skillPath・computedHash を記録するが、復元用コミットを記録していない。`docs/setup.md` も experimental_install を最新版の再取得と明記している。この運用の単純移植では Q13 を満たさない。取得可能な revision と hash の固定を設計する。
  - Pi の管理済み settings.json は版なし npm パッケージと Git master を含む。ローカル Pi 1.0.0 の `docs/packages.md` では npm の版、Git の tag/commit、ローカルパッケージ参照に対応。トップレベルの版指定だけで依存全体の再現性まで保証せず、Nix での依存解決・配布方法を確認する。`docs/configuration.md` は /settings による設定変更を案内しており、設定ファイルの一律 read-only 化との競合を避ける。既存の他者変更は保持している。
  - Herdr は `docs/setup.md` に3つの取得元と Zerdr 提供のローカルプラグインを記載するが、復元用 lock がない。外部プラグインの取得 revision を追加で固定し、アプリ提供プラグインは提供元との整合を確認する。
- Q12 に基づく設定と可変状態の具体的な分離、アプリからの設定書き換えとの競合確認。既存 symlink 方式の維持は前提にしない。
- macOS 設定の具体値と対象一覧を調査し、専用オプション・preferences・独自処理・手動設定に分類する。
- Hermes 等のサービス定義と更新・停止手順。plist の二重管理を避け、既存の安全要件を満たす方法。
  - 上流 `flake.nix` は aarch64-darwin を対象に含み、Python 依存と Node 等を組み込む構成を提供する。標準定義に未収録の場合の補完候補であり、採用は相談後に決める。実ビルド・既存機能の互換性は未検証。`nix/packages.nix` では messaging 等の追加依存をビルド時に選び、Matrix は Linux 限定としている。実利用する追加機能との照合が必要。
  - 上流 Home Manager モジュールに Darwin の launchd agents と gateway / backend の定義がある。ただし現行 Safehouse / dotenvx 起動経路をそのまま提供するものではない。パッケージのみ利用する構成と、モジュールを必要な範囲で調整する構成を比較する。
  - Home Manager の launchd 適用処理は変更された job を bootout / bootstrap する。既存の停止・待機を飛ばして採用しない。現行 `__hermes_gateway_wait_pid_die.fish` はタイムアウトでも成功扱いで続行するため、移行では実装の複製でなく「停止を確認してから切り替える」という安全要件を基準にする。今回の調査では既存 wrapper を変更していない。
  - 上流モジュールは設定の deep merge と managed marker を使う。設定コマンドの制限や、宣言から削除したキーが実ファイルに残る可能性を考慮し、設定の所有権と削除・復旧時の意味を確認する。秘密の実ファイルを Nix の path 型へ渡さない。既存の認証・DB・memory・cron 等を移行時に上書きしない。
  - 出典: https://github.com/NousResearch/hermes-agent/blob/main/flake.nix 、https://github.com/NousResearch/hermes-agent/blob/main/nix/packages.nix 、https://github.com/NousResearch/hermes-agent/blob/main/nix/homeManagerModules.nix 、https://github.com/NousResearch/hermes-agent/blob/main/nix/moduleCommon.nix 、https://github.com/NousResearch/hermes-agent/blob/main/website/docs/getting-started/nix-setup.md 、https://github.com/nix-community/home-manager/blob/master/modules/launchd/default.nix 。調査時点の main/master であり、採用 revision は未決。
- Q15 で採用した upstream Nix の具体的なインストーラ、nixpkgs / Home Manager / nix-darwin の系列、初期導入手順。
  - upstream Nix の multi-user daemon を nix-darwin に管理させる構成と、Determinate Nix に本体管理を任せる構成を区別する。nix-darwin の公式チェックを親も確認し、Determinate Nix 併用時は nix.enable = false が必要で、nix-darwin の nix.* による管理の一部が利用できなくなることを確認した。両者が併用不能という意味ではない。
  - upstream Nix の採用は Q15: A で確定。macOS 26.2 対応の具体的な installer / bootstrap 手順は未完了。
  - 出典: https://github.com/nix-darwin/nix-darwin/blob/master/modules/system/checks.nix 、https://docs.determinate.systems/guides/nix-darwin/ 。
- 秘密の新規 Mac 向け復元手順と、Nix 管理の起動経路でも既存の直接アクセス保護・注入が成立することの確認。方式は Q9 で確定済み。OAuth 等のアプリ固有認証状態とは区別する。
- 新規 Mac で残るログイン・権限承認・データ復元手順、検証方法、切替・復旧手順。
- 参考資料は設計材料として使い、例にある Homebrew 自動削除や GID 固定等を無条件に流用しない。
- 要件の見直しが必要な調査結果は無断で例外化せず確認する。具体的な実装・検証・切替の進捗は承認済みの [実装計画](../plans/2026-10-03-nix-migration.md) に記録する。

## 撤回・置換済み
- Hermes の本流パッケージ採用、旧 Q18 の「標準 stop を使わず強制終了を禁じる」方式、専用 controller による PID / 子プロセス管理、switch による利用状態保存・停止・再開は最新の fork / 既存スクリプト利用方針へ置換した。旧 Q18 は本流の停止実装を根拠に承認されたが、対象本体と運用境界の認識が誤っていた。旧実装のレビュー・ビルド記録は実装計画に履歴として残す。
- Q9 の比較で復元の利便性を重視しすぎた説明を修正。sops-nix / agenix の nix-darwin 対応は確認したが、宣言的な秘密配置自体はエージェントの読み取り制限ではない。保護目的への適合を理由に現行方式を継続する。
  - 比較資料: https://nix.dev/manual/nix/2.34/store/secrets 、https://github.com/Mic92/sops-nix 、https://github.com/ryantm/agenix/blob/main/flake.nix 。
- Q5 で提案した段階的切替を、ユーザーの希望により「事前準備後、なるべく早く完全切替」へ変更した。長期間の新旧併用は前提にしない。
- 当初の「既存構成をなるべく残して Home Manager 単体から移す」という提案を、ユーザーの意図に合わせ「Mac 環境全体の再構築を目標に設計し直す」方針へ置換した。
- Homebrew・mise・自作 symlink 配布・Hermes 運用をそのまま残すことは必須ではない。移行コストだけでなく、再構築性と日常の保守負担を比較して決める。
