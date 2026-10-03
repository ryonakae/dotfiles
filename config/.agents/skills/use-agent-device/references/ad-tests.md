# agent-device の `.ad` テスト運用

iOS Simulator の UI 動作検証には agent-device を使い、繰り返す検証は `.ad` として対象アプリのリポジトリに残す。
基本操作は公式の `agent-device` スキルを参照し、この文書ではテストの保存・執筆・実行・引き継ぎを定める。
既存のプロジェクト規約があれば優先する。

> `.ad` の記法は2026-10-02に CLI 0.21.19 のヘルプと公式資料で確認。操作例は Simulator で未実行。
> 導入・診断・Node の選択と公式資料を読む条件は [SKILL.md](../SKILL.md) を参照する。

## 保存先

プロジェクトに規約がなければ、次を既定とする。agent-device が要求する配置ではない。

```text
<app-repository>/
├── e2e/agent-device/
│   ├── README.md
│   └── ios/
│       ├── create-item.ad
│       └── validation-error.ad
└── .artifacts/agent-device/
```

- `.ad` と実行手順は Git 管理する。機能・期待結果が分かる kebab-case 名にし、1 ファイルで 1 シナリオを検証する。主要導線と重要な異常系に絞る。
- 記録の既定保存先や個人の HOME だけに置いて完了にしない。既存テストをこの配置に合わせて移動しない。
- 証跡は `.artifacts/agent-device/` を既定とし、対象アプリの `.gitignore` に追加する。既定の `.agent-device/test-artifacts/` を使う場合も Git 管理外にする。
- Bundle ID、ビルド・インストール、初期状態準備、実行方法は `e2e/agent-device/README.md` に残し、アプリの既存指示書から参照する。dotfiles にアプリ固有の `.ad` は置かない。

## 初期状態と期待結果

1. 対象アプリの指示書と既存テストを読む。コードから確認できる前提は調べ、不明な認証・テストデータ・端末用途だけ質問する。
2. プロジェクトの既存手順でアプリをビルド・インストールする。`.ad` の実行がビルドも行うとは扱わない。
3. シナリオ開始時の画面、データ、認証、権限を用意する。各テストを単独でも実行できる状態にし、実行順や直前の手操作に依存させない。
4. 仕様から期待結果を決める。「タップが完了した」だけで合格にせず、保存結果やエラー表示などを `is` で確認する。見た目はスクリーンショットで別に確認する。

`open --relaunch` は再起動であり、データ初期化ではない。
リトライやセッション終了もアプリデータの初期化を保証しない。
アプリデータ削除・再インストール・権限変更はテスト専用 Simulator と承認された準備手順の範囲で行う。
共有・用途不明の端末は初期化しない。
iOS のアプリ状態消去後も Keychain の認証情報が残り得るため、ログアウトや専用テストアカウントの準備を明記する。
Simulator 全体の Keychain 消去は通常テストの準備に含めない。

## 記録から作る

ローカルの daemon を使い、アプリのリポジトリルートで保存先とセッションを指定する。
`com.example.app` は対象アプリの Bundle ID に置き換える。

```fish
npx --yes agent-device open com.example.app --platform ios --session author \
  --save-script ./e2e/agent-device/ios/create-item.ad
```

以後の操作・期待結果の確認には同じ `--session author` を付ける。
公式スキルどおり、最新の出力の ref で操作し、`--settle` の差分を利用する。
対象が差分にないときだけ `snapshot -i` で再観察する。
例えば、その時点の出力に `@e12` があるなら `npx --yes agent-device press @e12 --settle --session author` と操作する。例の ref を観察せずコピーしない。

```fish
npx --yes agent-device close --session author
```

`close` 時に `.ad` が保存される。
`--save-script` にパスを指定しない場合は `~/.agent-device/sessions/<session>-<timestamp>.ad` に保存される。
親ディレクトリは自動作成される。
記録したフローの操作対象、アサーション、不要な探索操作、終了処理をレビューしてから初期状態で再実行する。
記録が成功したことだけでテスト完成とは扱わない。

## 手書きの `.ad`

`.ad` はシェルスクリプトや YAML ではなく、1 行ごとの agent-device コマンドである。
各行に `agent-device` の接頭辞を付けない。
`context` と `env` は最初の操作より前に置く。

次は、対象アプリに `create_item`、`item_name`、`save_item`、`item_created` の accessibility ID があり、最後の要素に保存した名前が表示される場合の例。
ID と期待結果は実際の画面を観察して置き換える。例をそのまま実行可能なテストとは扱わない。

```text
# 前提: ログイン済みの一覧画面。テスト用アイテムは未作成。
context platform=ios timeout=60000 retries=0
env APP_ID=com.example.app

open ${APP_ID} --relaunch
wait 'id="create_item"' 5000
press 'id="create_item"'
wait 'id="item_name"' 5000
fill 'id="item_name"' "検証用アイテム"
press 'id="save_item"'
wait 'id="item_created"' 5000
is visible 'id="item_created"'
is text 'id="item_created"' "検証用アイテム"
close
```

- 一括実行では `context platform=ios` を各フローに入れる。`test --platform ios` は対象を上書きする指定ではなくフィルターであり、platform のないファイルはスキップされる。
- `context session=...` や `context device=...` を書かない。セッションと端末は実行 CLI 側で指定する。
- 手書きで恒久保存する対象は `id="..."` を優先し、必要なら `role="button" label="..."` で絞る。ID を付ける場合はアプリの既存方針に従う。
- 探索時の `@e12` はスナップショットに依存する。手書きで固定しない。記録由来の ref・対象注釈は必要性を確認して残し、生成された注釈を不用意に削らない。
- 待機には要素の出現条件を使う。固定時間の `wait 500` を増やして失敗を隠さない。`wait '<selector>' 5000` の時間はミリ秒。
- アサーションは `is visible '<selector>'`、`is text '<selector>' "期待値"` などを使う。`is absent` は読み取り可能なツリーで一致がないことを確認するため、単なる画面外・非表示とは区別する。
- セレクターや空白を含む値を引用する。変数は `${VAR}` または `${VAR:-default}`。CLI の `-e KEY=VALUE` が `AD_VAR_KEY` 環境変数、ファイルの `env KEY=VALUE` より優先する。
- 個人の UDID・絶対パスや秘密を共有フローに固定しない。記録・証跡の入力値にも私的データを使わない。
- 通常フローは末尾を `close` にする。途中からの再開を成功した回帰テストとは数えない。

## 実行方法

[SKILL.md の実行環境](../SKILL.md#実行環境を選ぶ) と初期状態の準備を済ませ、アプリのリポジトリルートから実行する。
以下は npx で実行する例。対応 Node を選び、`.ad` 本文には npx の接頭辞を加えない。

```fish
# 単体
npx --yes agent-device replay ./e2e/agent-device/ios/create-item.ad --session verify

# 一括。ディレクトリ配下の .ad を再帰探索して直列実行する
npx --yes agent-device test ./e2e/agent-device/ios --platform ios \
  --retries 0 --artifacts-dir ./.artifacts/agent-device

# glob は fish に展開させず、引用して渡す
npx --yes agent-device test './e2e/agent-device/ios/**/*.ad' --platform ios \
  --retries 0 --artifacts-dir ./.artifacts/agent-device

# Bundle ID を実行時に変更する場合
npx --yes agent-device replay ./e2e/agent-device/ios/create-item.ad \
  -e APP_ID=com.example.app.debug --session verify
```

複数 Simulator がある場合は実行 CLI に `--device "$DEVICE"` を追加し、対象を明示する。
`DEVICE` はプロジェクトの手順で選んだ Simulator の識別子を fish の `set DEVICE ...` で設定する。
他セッションが使っている端末を横取りしない。

JUnit が必要な場合は `--reporter default --reporter junit:./.artifacts/agent-device/junit.xml` を `test` に追加する。
明示的な reporter 指定は既定 reporter を置き換えるため、端末表示も必要なら `default` を併記する。
CLI の timeout / retries は `context` の値より優先する。通常検証はリトライなしで行い、再試行で合格した場合は不安定さも報告する。
`--dry-run` や `--plan` があると仮定しない。構文の確認だけで動作検証済みとは報告しない。

## 検証と失敗時の扱い

- 新規・変更したフローは初期状態を作り直して再実行し、直前の操作に依存しないことを確認する。
- 新規アサーションは Git 管理外の一時コピーで期待結果を意図的に変え、失敗を確認する。共有フローの期待値を変更したままにしない。
- 失敗したステップ、画面、ログを確認し、仕様違反・対象の不一致・初期状態不足・環境不備を切り分ける。通すためだけにアサーションを削除・弱体化しない。
- `REPLAY_DIVERGENCE` の候補は確認してから手動編集し、初期状態から全体を再実行する。現行の `--update` / `-u` は自動修復を行わない。
- 各 attempt の `replay.ad`、`result.txt`、`replay-timing.ndjson` や保持された証跡を確認する。ログ・画像・記録には入力値が残り得るため、コミットや外部共有の前に確認する。
- CLI の取得・実行失敗、ビルド失敗、接続不可、Sandbox 拒否などで実行できなければ、原因と未検証範囲を報告する。
- Sandbox の拒否は回避せず、共通指示書の委譲・承認ルールに従う。

## 各アプリに残す実行手順

`e2e/agent-device/README.md` に次を記載する。既存の関連文書があればそこに追記する。

- 導入 CLI バージョン、Bundle ID、ビルド・インストールの具体的なコマンド。
- Simulator の選び方、認証・権限・テストデータの準備と復元の具体的な手順。
- フローが保証する仕様、シナリオごとの初期状態。再実行前のクリーンアップや初期化に承認が必要ならその条件。
- リポジトリルートからの単体・一括実行コマンド、証跡の保存先。
- Simulator で検証できない機能と、別途必要な実機・目視確認。

作業報告には、実行コマンド、フロー名、合否、証跡のパス、未検証項目を必要な分だけ含める。

## 公式資料

- [agent-device スキル](https://github.com/callstack/agent-device/blob/main/skills/agent-device/SKILL.md)
- [Replay & E2E Testing](https://oss.callstack.com/agent-device/docs/replay-e2e)
- [Commands](https://oss.callstack.com/agent-device/docs/commands)
