# doc-updater 委譲の詳細

`commit-push` はこのファイルを読んで、`doc-updater` の実行経路を選ぶ。

## 共通の渡し方

どの経路でも以下を `doc-updater` に渡す。

- 対象は `git diff --cached` だけに限定する
- staged file list（`git diff --cached --name-only --diff-filter=ACMRD` の出力）を渡す
- rename/delete context（`git diff --cached --diff-filter=R --name-status` と `git diff --cached --diff-filter=D --name-only` の出力）を渡す
- 呼び出し元に学びや補足文脈があれば反映を依頼する
- commit / push は行わず、更新ファイルと変更要約だけを返すように伝える
- [`../doc-updater/SKILL.md`](../doc-updater/SKILL.md) を source of truth として読むように伝える

## モデル選択

全経路共通: doc-updater の起動時にモデル指定が可能なら、実行環境で利用可能な最も軽量かつ高速なモデルを選ぶ。モデル名は固定指定しない。

## 経路 A: サブエージェント実行

実行環境が以下を両方サポートする場合のみ使う。

- 独立コンテキストでのサブエージェント実行
- その結果の親ワークスペースへの確実な反映

### プロンプトテンプレート

以下をサブエージェントに渡すプロンプトとして使う。プレースホルダは実行前に実際の値で埋めること。

```
あなたは doc-updater スキルを実行する。

## 指示ファイル
以下のファイルを読んで、そこに書かれた手順に従うこと:
{SKILL_MD_PATH}

## 対象の staged 変更
### staged file list
{STAGED_FILE_LIST}

### rename context
{RENAME_CONTEXT}

### delete context
{DELETE_CONTEXT}

## 制約
- commit / push は行わない
- ドキュメントを更新したら git add でステージングに追加する
- 更新不要と判断した場合は「ドキュメント更新は不要」とだけ返す
- 完了したら、更新したファイル名・変更概要・スキップ理由を簡潔に返す

## 呼び出し元からの補足
{CALLER_CONTEXT}
```

| プレースホルダ | 値の取得方法 |
|---|---|
| `{SKILL_MD_PATH}` | `../doc-updater/SKILL.md` の絶対パス |
| `{STAGED_FILE_LIST}` | `git diff --cached --name-only --diff-filter=ACMRD` の出力 |
| `{RENAME_CONTEXT}` | `git diff --cached --diff-filter=R --name-status` の出力。なければ「なし」 |
| `{DELETE_CONTEXT}` | `git diff --cached --diff-filter=D --name-only` の出力。なければ「なし」 |
| `{CALLER_CONTEXT}` | セッション中の学びや補足。なければ「なし」 |

## 経路 B: 別 skill としての明示呼び出し

経路 A が未対応、利用不可、親ワークスペースへ反映不可、または失敗した場合のフォールバック。

実行環境が `doc-updater` を別 skill として明示呼び出しできる場合に使う。

## 経路 C: inline 実行

経路 A・B がともに使えない場合のフォールバック。

`doc-updater` を実行できる仕組みがあればそれを使う。無ければ [`../doc-updater/SKILL.md`](../doc-updater/SKILL.md) を読んで同じ手順を inline で実行する。
