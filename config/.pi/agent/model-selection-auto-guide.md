## モデル × thinkingの選択

Jevによる自動選択が有効。委譲の要否、type、タスクの内容は引き続き親が判断する。

- 新規の`Agent`では通常`model`と`thinking`を省略する。agent定義と呼び出しの両方で未指定の項目だけを、Jevがタスクに応じて選ぶ。
- `SubagentWorkflow`内の新規`agent()`も、通常`model`と`effort`を省略する。Workflowの引数名は`thinking`ではなく`effort`。
- ユーザーによる指定、異なるモデルによる独立評価など、特定の組み合わせが必要な場合だけ明示指定する。片方を固定した場合、Jevはその条件を満たす候補から残りだけを選ぶ。
- `Agent`とWorkflowのどちらも、agent定義の固定値を最優先する。呼び出し指定・自動選択・親による選定で上書きしない。
- Jevの失敗・タイムアウト・棄権・低信頼度・候補不足では、子を起動せず親へ選定を求める。親のmodel・thinkingをそのまま継承せず、タスクに合う組み合わせを親が判断する。予備候補を毎回先に計算する必要はない。
- `Agent`が`model_selection_required`を返したら、要求された未指定項目をすべて決め、元の委譲内容を維持して`model`・`thinking`を指定し直す。初回には子が起動していないため、`resume`は使わない。
- Workflowの選定要求を受けたら、`SubagentWorkflow({action:"route", runId, decisions:[{agentId, model, effort}]})`で未指定項目を返す。要求に含まれるrun/agent IDを使い、同じ実行を続行する。選定待ちを解決するためにスクリプトや`resumeFromRunId`を再実行しない。
- 固定値が無効な場合は、別の値へ黙って置き換えない。設定上の問題として報告する。中断された依頼も選定・起動を続行しない。
- 再開は既存セッションのmodel・thinkingを維持するため指定しない。切替が必要なら新規起動とし、文脈を失う負担も考慮する。
- 手動選定が必要なら、同じagent設定ディレクトリの`model-selection-guide.md`と`subagents.json`の`jev.candidates`・`jev.benchmark`を参照する。モデル名や比較データを別の一覧として保守しない。

Jevは選択を補助するだけであり、期待品質の保証ではない。親は実際の差分・テスト・出典を検証する。
