# サブエージェント用モデル一覧と更新手順

`use-t3-code` でサブエージェントへ委譲するときに参照するモデル表（可変層）。委譲の判断・ティア選定・プロバイダ固有制約は [delegation.md](delegation.md) を参照する。

## モデル表

実行時の `providerInstanceId`、`model`、option 名は `orchestrator_capabilities` の出力を正とする。親になり得るモデルも掲載し、親自身のティア判定に使う。根拠欄の数値は採用時の決定記録であり、更新時の直接比較には使わない。

| `providerInstanceId` | `model` | 系統 | ティア | effort option | 既定 / 引き上げ / 打ち止め | 根拠（決定記録） | 確認日 |
|---|---|---|---|---|---|---|---|
| `codex` | `gpt-6.1-terra` | GPT | 軽量 | `reasoningEffort` | `low` / `medium` / `—` | 軽量下限を満たし最速（Terminal-Bench 15・FrontierCode 24・GDP.pdf 26、48 秒/task） | 2026-10-31 |
| `codex` | `gpt-6.2-sol` | GPT | 標準 | `reasoningEffort` | `medium` / `high` / `—` | Codex 評価で low→medium が +8 点、medium→high は最大 +5 点（FrontierCode 36・Terminal-Bench 49） | 2026-11-18 |
| `codex` | `gpt-6.2-astra` | GPT | 最上位 | `reasoningEffort` | `high` / `xhigh` / `max` | Codex 評価で medium→high が Terminal-Bench +6 点（FrontierCode 42・Terminal-Bench 60） | 2026-11-18 |
| `claudeAgent` | `claude-sonnet-5-5` | Claude | 標準 | `effort` | `high` / `xhigh` / `—` | GPT 系親に対する別系統の標準候補（Terminal-Bench 44・FrontierCode 26） | 2026-10-31 |
| `claudeAgent` | `claude-fable-5-2` | Claude | 最上位 | `effort` | `high` / `—` / `high` | Claude Code 評価で medium→high が FrontierCode +13 点（49・Terminal-Bench 64）。xhigh は high と同点 | 2026-11-18 |
| `antigravity` | `gemini-4-neon` | Gemini | 標準 | `thought_level` | `medium` / `high` / `xhigh` | 親・文章スロットの標準主力（Terminal-Bench 54.5・FrontierCode 36.9・GDP.pdf 32.8） | 2026-11-25 |
| `antigravity` | `gemini-4-hydrogen` | Gemini | 軽量 | `thought_level` | `low` / `medium` / `—` | 文章スロットの軽量候補（GDP.pdf 28.2、85 秒/task） | 2026-11-25 |

### `delegate_task` の指定例

通常・難所委譲の例:

```json
{ "providerInstanceId": "codex", "model": "gpt-6.2-sol", "options": { "reasoningEffort": "medium" } }
```

```json
{ "providerInstanceId": "claudeAgent", "model": "claude-fable-5-2", "options": { "effort": "high" } }
```

読者向け文章を別プロバイダから委譲する例:

```json
{
  "task": "以下の仕様と対象箇所を参照して文言案を作成し、対象箇所と文言案だけを返してください。ファイル編集とシェルコマンド実行は行わず、反映は親が担当します。",
  "runtimeMode": "approval-required",
  "target": {
    "providerInstanceId": "antigravity",
    "model": "gemini-4-neon",
    "options": { "thought_level": "medium" }
  }
}
```

- 速度系 option（`serviceTier`、`fastMode`）はユーザーの指示がある場合だけ指定する。
- 表にない思考レベル（Codex の `ultra`、Claude の `ultracode` / `ultrathink` など）は根拠がないため、ユーザーの指示がある場合だけ指定する。

## 文章スロット

読者向けの文章の新規作成・構成整理・推敲では Gemini 系を優先する。適用対象と Antigravity 権限モードの制約は [delegation.md の読者向けの文章の優先方針](delegation.md#読者向けの文章の優先方針) に従う。

| 用途 | `providerInstanceId` | `model` | `thought_level` |
|---|---|---|---|
| 構成・論旨の判断を伴う新規作成、長文 | `antigravity` | `gemini-4-neon` | `medium`（難度に応じて `high`） |
| 短い UI 文言、局所的な推敲 | `antigravity` | `gemini-4-hydrogen` | `low`〜`medium` |

- **自動更新禁止**: このスロットはベンチマーク指標ではなくユーザーによる文章品質の評価に基づく。モデル更新時に指標の点数だけを理由に別系統へ置換せず、ユーザー判断でのみ変更する。

## 更新手順

モデル表の更新時だけ参照する。通常タスクの実行時には読まない。

### 更新契機

- ユーザーからモデル表の更新を依頼されたとき。
- `orchestrator_capabilities` の結果で、表に記載した `model` ID が利用不能になった、または表にない新モデルが出現したとき（その委譲では無断切替せず親が対応または確認し、更新を提案する）。

### 比較ルールと参照元

- **同日再取得の必須**: 指標の版（例: Terminal-Bench 4.0 → 4.1）が変わるため、表の根拠欄の保存値と新モデルの値を直接比較しない。更新時は**現行の代表モデルも同日に同じ比較ページから再取得**し、同一条件で比較する。未掲載値の補間や他世代からの流用はしない。
- **参照元**: [Artificial Analysis](https://artificialanalysis.ai/)（[評価方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking)、[Claude Code と Codex の比較](https://artificialanalysis.ai/agents/coding-agents/comparisons/claude-code-vs-codex)）。
- **effort 別比較ページの URL 規則**: リリースページ URL の末尾を `<m>`（例: `gpt-6-1-terra`、`claude-fable-5-2`、`gemini-4-neon`）とする。
  - Codex・Claude: `https://artificialanalysis.ai/models/comparisons/<m>-low-vs-<m>-medium`（low・medium）、`<m>-high-vs-<m>-xhigh`（high・xhigh）、`<m>-vs-<m>-low`（max）。
  - Gemini 4 系: `<m>-low-vs-<m>-medium`（low・medium）、`<m>-high-vs-<m>`（high・xhigh、Neon・Hydrogen）、`<m>-vs-<m>-medium`（high・medium、Argon・Carbon）。
  - 比較ページの列は URL の順序ではなく見出しの順に並ぶ点に注意する。

### 選定基準

- **作業種別と重視指標**:
  - リポジトリの変更: **FrontierCode**（Codex・Claude Code でのハーネス評価があれば優先確認）
  - ターミナル・環境操作そのものが難所の作業: **Terminal-Bench**
  - 揃った資料の読解・統合: **GDP.pdf**
  - 補助指標: **AutomationBench**（外部 SaaS・API 操作）、**AA-Briefcase**（大量資料の探索・統合）。Intelligence・Omniscience は主指標に使わない。
- **計測条件の注意**:
  - Codex・Claude Code ハーネス評価とモデル単体評価は計測条件が異なるため混同しない。
  - Gemini 4 系は Google モデル単体の値であり、Antigravity 経由の実測ではない。
  - USD/task は provider ごとに使用量枠が異なるため provider をまたいで比較せず、同一 provider 内の価格比にのみ使う。
- **ぶれ幅**: 評価ページに信頼区間がないため、問題数 $N$ を独立標本数とみなし、得点率 50% の二項分布 95% 区間の半幅（$1.96 \times 50 / \sqrt{N}$）で概算する。ぶれ幅未満の点差は同等とみなす。
- **ティア境界**: 各モデルの medium の USD/task を、比較対象のうち同一 provider で最も高いモデルの値で割った価格比で分類する。
  - 軽量: `0.12 未満`（ぶれ幅を超える下限を満たす候補から秒/task が最小のものを採用）
  - 標準: `0.12 以上 0.3 未満`
  - 最上位: `0.3 以上`
- **effort 選定**: 開始レベル（軽量＝`low`、標準＝`medium`、最上位＝`high`）から 1 段上でぶれ幅を超える伸びがあれば 1 段上を既定にし、伸びが頭打ちになる水準を「打ち止め」列へ記録する。
