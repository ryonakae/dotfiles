---
name: ask-codex
description: OpenAI Codex CLI に外部視点の調査、設計相談、コードレビュー、セカンドオピニオンを依頼する。ユーザーが Codex の調査・レビュー・意見を明示的に求めた場合や、別の AI によるダブルチェックを求めた場合に使う。単純な実装、追加意見が不要な作業、機密情報を外部へ送る必要がある依頼には使わない。
---

# Codex セカンドオピニオン

## 方針

OpenAI Codex CLI の非対話モードで外部視点を得る。

- 調査、設計相談、一般的なセカンドオピニオン: `codex exec`
- リポジトリの差分やコミットのレビュー: `codex exec review`
- 単発の依頼: `--ephemeral` を付ける
- 最新の外部情報が必要な調査: `--search` を付ける
- モデル: 設定済みの既定モデルを使い、ユーザーが指定した場合だけ `-m <MODEL>` で上書きする

## 実行手順

1. 利用可能なファイル閲覧・検索ツールで、質問に必要なコンテキストを集める。
2. 現在の会話は Codex に引き継がれないため、前提、論点、制約、期待する回答をプロンプトに含める。
3. 実行環境を判定し、次のサンドボックス指定を使う。
   - 通常環境: `-a never -s read-only`
   - `APP_SANDBOX_CONTAINER_ID=agent-safehouse`: `--dangerously-bypass-approvals-and-sandbox`
4. 依頼に合う `exec` または `exec review` を実行する。
5. Codex の回答を現在の分析やプロジェクト固有の事情と照合して報告する。

## 調査・設計相談

```bash
codex -a never -s read-only exec --ephemeral "質問内容"
```

プロジェクトを参照させる場合は、作業ルートを指定する。

```bash
codex -a never -s read-only exec --ephemeral -C /path/to/project "質問内容"
```

stdin からコンテキストを追加することもできる。

```bash
cat path/to/file | codex -a never -s read-only exec --ephemeral "質問内容"
```

最新情報の調査では `--search` を `exec` より前に置く。ローカル情報だけで答えられる依頼には付けない。

```bash
codex --search -a never -s read-only exec --ephemeral "最新情報を調査して"
```

モデルを明示する必要がある場合だけ `-m` を使う。

```bash
codex -a never -s read-only exec --ephemeral -m <MODEL> "質問内容"
```

## コードレビュー

レビュー対象が分かる場合は専用セレクターを使う。

```bash
# staged、unstaged、untracked の変更
codex -a never -s read-only exec --ephemeral review --uncommitted

# 指定ブランチとの差分
codex -a never -s read-only exec --ephemeral review --base main

# 指定コミットが導入した変更
codex -a never -s read-only exec --ephemeral review --commit <SHA>
```

対象より観点の指定を優先する場合は、独自プロンプトを渡す。

```bash
codex -a never -s read-only exec --ephemeral review "認証まわりの回帰を重点的に確認して"
```

`--uncommitted`、`--base`、`--commit`、独自プロンプトは相互排他なので、同時に指定しない。

## Agent Safehouse 内での実行

`APP_SANDBOX_CONTAINER_ID=agent-safehouse` の場合は、各コマンドの `-a never -s read-only` を `--dangerously-bypass-approvals-and-sandbox` に置き換える。

```bash
codex --dangerously-bypass-approvals-and-sandbox exec --ephemeral "質問内容"
```

外側の Agent Safehouse がセキュリティ境界になるため、このフラグは Safehouse の外では使わない。実行ファイルの場所は固定せず、Bash から `PATH` 上の `codex` を直接呼び出す。fish の `codex` wrapper は Safehouse を追加で起動するため、既に Safehouse 内にいる場合は使わない。

`-s read-only` とのネストで `sandbox_apply: Operation not permitted` が発生した場合や、外側の Safehouse がアクセスを拒否した場合は、回避策を試さずユーザーへ報告する。

## 報告

依頼の規模に合わせて簡潔にまとめる。固定の見出しは不要だが、判断に必要な次の内容を含める。

- Codex に何を質問したか
- 回答の要点
- 現在の分析と一致した点、異なる点
- Codex の回答を踏まえて採用する判断や次のアクション

Codex の回答は参考情報として扱い、プロジェクトのコンテキストに基づいて最終判断する。

## 注意事項

- APIキー、パスワード、個人情報、非公開情報など、外部へ送信すべきでない情報をプロンプトに含めない
- `--ephemeral` を付けた実行は再開できない。継続的な対話には通常の Codex セッションを使う
- 通常テキスト出力では進行状況が標準エラー、最終回答が標準出力へ出る
- 一時的な通信エラーを再実行する前に、課金や重複実行の影響を考慮する
