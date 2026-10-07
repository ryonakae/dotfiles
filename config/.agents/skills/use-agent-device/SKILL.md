---
name: use-agent-device
description: >-
  この dotfiles 環境で agent-device を使うための共通運用スキル。
  iOS Simulator での実装後の動作確認、不具合再現、.ad テストの作成・記録・replay・test、
  npx による agent-device CLI の実行や Node バージョンの問題を扱うときに使う。
  公式 agent-device スキルも読み込み、プロジェクトの既存規約を尊重して再実行可能な検証を残す。
compatibility: Requires a compatible Node.js and npm/npx, the official agent-device skill, and Xcode for iOS Simulator automation.
---

# Use agent-device

公式スキルに、この環境の実行方法と `.ad` テストの運用を補う。
基本操作や CLI の仕様は公式スキルと導入版のヘルプに従い、このスキルで再定義しない。

## 公式スキルを読む

最初に `~/.agents/skills/agent-device/SKILL.md` を読む。
未導入なら操作を止め、dotfiles の `dotfiles-setup` スキルに同梱された `references/setup.md` の「外部スキル」の手順で導入するよう案内する。
公式スキルは外部スキルなので、追加ルールを書き込まない。公式スキル中の `agent-device …` は、下記の `npx` 起動方法へ読み替える。

仕様や手順の質問だけなら、必要な資料を読んで回答する。確認のために Simulator を操作したり、CLI を更新したりしない。

## 必要な公式ドキュメントを読む

基本操作と、導入版で確認済みの既存テストの実行は、公式スキル・プロジェクトの手順・このスキルの reference で進める。セッションが変わったことだけを理由に公式ページを読み直さない。
公式ページは、初めて使う機能、手元の手順では判断できない点、未解決の問題、更新で挙動が変わった箇所がある場合に限り、下表から選んで読む。同じセッションで確認済みの内容は再取得しない。

| 確認が必要になった作業 | 読むページ・確認事項 |
|---|---|
| 記録・suite を初めて導入する、未確認の replay 機能や再開条件を使う、失敗を調べる | [Replay & E2E Testing](https://oss.callstack.com/agent-device/docs/replay-e2e)。記録と再実行の区別、`REPLAY_DIVERGENCE` の診断、`--keep-session` と再開条件を確認する |
| 不具合の原因調査、ログ・通信・性能・クラッシュの証拠収集 | [Debugging & Profiling](https://oss.callstack.com/agent-device/docs/debugging-profiling)。調査対象に応じて logs / network / perf / debug symbols を選ぶ。React Native の内部状態は react-devtools、JS ヒープは CDP の節も読む |
| CLI の導入・更新、実行環境の不備 | [Installation](https://oss.callstack.com/agent-device/docs/installation)。Node・Xcode の要件、PATH、環境診断を確認する |
| 要素が見つからない、画面とツリーが一致しない、セレクターを選ぶ | [Snapshots](https://oss.callstack.com/agent-device/docs/snapshots) と [Selectors](https://oss.callstack.com/agent-device/docs/selectors)。ref の有効性、画面外の要素、sparse / recovered の区別、探索範囲、属性による対象指定を確認する |
| 自動化だけで検証できるか判断する、OS 固有の挙動に遭遇する | [Known Limitations](https://oss.callstack.com/agent-device/docs/known-limitations)。XCUITest で抑制される貼り付け許可ダイアログなど、手動確認が必要な制約を確認する |
| 複数 worktree・端末・エージェントでの実行構成を初めて組む、セッションが競合する | [Sessions](https://oss.callstack.com/agent-device/docs/sessions)。暗黙セッションの分離、明示名による共有、端末の所有者、変更操作の直列化、終了対象と証跡の場所を確認する |
| `agent-device.json` や永続的な既定値を変更する、設定の優先順位を調べる | [Configuration](https://oss.callstack.com/agent-device/docs/configuration)。ユーザー設定・プロジェクト設定・環境変数・CLI の優先順位と、リポジトリに置けない接続・認証設定を確認する。CLI パッケージの取得方法とは区別する |
| 証跡の種類・保存先・共有先を新設・変更する、機密性が不明、権限や接続の信頼境界を変更する | [Security & Trust](https://oss.callstack.com/agent-device/docs/security-trust)。画像・ログ・録画・replay・レポートに含まれる秘密や私的データ、共有先と必要な権限を確認する |
| batch を初めて使う、未確認の input を組む、部分実行の失敗を調べる | [Batching](https://oss.callstack.com/agent-device/docs/batching)。構造化 input、操作後の待機、失敗時の部分実行結果を確認する。未知の画面を探索するために長い batch を組まない |
| 更新後に既存 `.ad` の swipe / gesture が引数エラーになる | [Migrating Gestures](https://oss.callstack.com/agent-device/docs/migrating-gestures)。廃止された duration / velocity と代替操作を確認し、元の操作意図を保って修正する |

上記にない連携・対象で確認が必要なら [公式ドキュメント索引](https://oss.callstack.com/agent-device/llms.txt) から該当ページを選ぶ。索引や見出しだけで仕様を判断せず、使用する機能の本文を読む。全ページや `llms-full.txt` を毎回読み込まない。

実行するコマンドの記法や対応範囲が不明なら、`npx --yes agent-device help <topic>` で照合する。
公式ページと導入版に差がある場合は導入版の契約に合わせ、不明点を推測して実行しない。
診断は再現に必要な時間帯・対象に絞り、詳細な成果物はファイルに保存して要点を報告する。公式ページを再読しない場合も、成果物の共有・コミット前には秘密や私的データの混入を確認する。
公式ドキュメントを取得できなければ、その旨を示して導入版のヘルプを参照する。

## 実行環境を選ぶ

- CLI は `npx --yes agent-device …` で実行する。mise やグローバル npm の管理対象には追加せず、独自 wrapper も作らない。スキルの導入と CLI の取得は別に扱う。
- パッケージは必要に応じて npm から取得され、npm キャッシュに保存される。
- npx は Node 自体を選ばない。通常操作は Node 22.12 以上、Web 操作は24以上を要求する。実行 shell の Node が要件を満たさなければ、そのプロジェクトの手順で対応 Node を選んでから実行する。
- cwd は対象アプリのリポジトリに保つ。HOME に移ると、相対パスと worktree 単位のセッションが変わる。

導入・更新後、または環境不備の調査が必要なときに、以下の該当コマンドを使う。通常のテスト実行のたびにインストールや診断を繰り返さない。

```fish
node --version
npx --yes agent-device --version
npx --yes agent-device doctor --platform ios
```

`doctor` はデーモンのバージョン不一致を検出すると置き換える場合があるため、他セッションが同じデーモンを使用中なら更新のタイミングを調整する。更新後は関連テストも再実行する。

## 検証を進める

1. 対象アプリの指示書と既存テストを読み、Bundle ID、ビルド・インストール手順、Simulator、初期状態、期待結果を確認する。既存の配置や手順があれば優先する。
2. `.ad` を初めて扱うときや手順の確認が必要なときは [references/ad-tests.md](references/ad-tests.md) を読む。配置が未定なら `e2e/agent-device/ios/` にテスト、`e2e/agent-device/README.md` に準備・実行手順を残す。既存テストをこの既定へ移動しない。
3. 通常の画面操作は公式スキルの観察・操作・確認ループに従う。繰り返す検証は `.ad` に残し、操作の成功だけでなく仕様に基づく期待結果をアサーションで確認する。
4. 新規・変更したフローは初期状態から再実行する。失敗したら画面・ログと前提を確認し、通すためだけに期待結果を弱めない。レイアウトの確認にはスクリーンショットも使う。
5. アプリ固有のビルド・初期化・認証・テストデータ・実行方法は、そのアプリの文書へ残す。dotfiles にアプリ固有のテストを置かない。

アプリデータや Keychain の削除、再インストールは承認されたテスト環境・手順の範囲に限る。
他セッションの端末を横取りせず、Sandbox 拒否は共通指示書の委譲・承認ルールに従う。

## 完了報告

実行したコマンドとフロー、合否、証跡のパス、未検証項目を必要な分だけ報告する。
CLI の取得・実行や Simulator 接続ができなければ、その理由を明記する。
文書・構文の確認だけでアプリの動作検証済みとは扱わない。
