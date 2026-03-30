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

## 経路 A: サブエージェント実行（最優先）

実行環境が以下を両方サポートする場合のみ使う。

- 独立コンテキストでのサブエージェント実行
- その結果の親ワークスペースへの確実な反映

注意:
- モデル名の固定指定は避け、「軽量かつ高速なモデルを優先する」と伝える

## 経路 B: 別 skill としての明示呼び出し

経路 A が未対応、利用不可、親ワークスペースへ反映不可、または失敗した場合のフォールバック。

実行環境が `doc-updater` を別 skill として明示呼び出しできる場合に使う。

## 経路 C: inline 実行

経路 A・B がともに使えない場合のフォールバック。

`doc-updater` を実行できる仕組みがあればそれを使う。無ければ [`../doc-updater/SKILL.md`](../doc-updater/SKILL.md) を読んで同じ手順を inline で実行する。
