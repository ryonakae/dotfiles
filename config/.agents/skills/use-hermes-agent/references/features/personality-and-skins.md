# パーソナリティ・スキン

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/personality / skins

## パーソナリティ

エージェントの口調・スタイルを切り替える機能。`SOUL.md` の上にレイヤーされる軽量なプリセット。

### CLI

```bash
hermes personality list             # 利用可能なパーソナリティ一覧
hermes personality use <name>       # デフォルト設定
/personality <name>                 # セッション内で切替
```

### 組み込みパーソナリティの例

| 名前 | 性質 |
|------|------|
| `default` | 中立・実務 |
| `kawaii` | 親しみやすい敬体 |
| `tsundere` | ユーモア・ロール強め |
| `professional` | フォーマル・簡潔 |
| `terse` | 短文応答 |

### カスタムパーソナリティ

`~/.hermes/personalities/<name>.md` を作成して内容を書く。`personality.md` 内で SOUL.md を参照する場合は `{soul}` プレースホルダーが使える。

```markdown
# tsundere
あなたはツンデレなアシスタント。要点は伝えるが、敬語と素っ気ない態度を交互に出す。
{soul}
```

### config.yaml

```yaml
display:
  personality: "kawaii"             # デフォルトパーソナリティ
```

## スキン

ターミナル表示の配色・装飾セット。表示エンジン（プロンプトトークン色、ツール出力枠、reasoning ブロック背景など）を一括変更できる。

### CLI

```bash
hermes skins list
hermes skins use <name>
/skin <name>                       # セッション内切替
```

### 組み込みスキンの例

| 名前 | 性質 |
|------|------|
| `default` | デフォルト配色 |
| `light` | 明色背景向け |
| `dark` | 暗色背景向け |
| `solarized` | Solarized 互換 |
| `mono` | 単色（Accessibility 向け） |

### カスタムスキン

`~/.hermes/skins/<name>.yaml` を作成。

```yaml
name: my-skin
prompt:
  user: "#88c0d0"
  agent: "#a3be8c"
tool:
  border: "dim white"
  output: "white"
reasoning:
  background: "#3b4252"
```

### config.yaml

```yaml
display:
  skin: default
```

## TUI ライブテーマ切替 (v0.11.0)

新型 Ink TUI と Web ダッシュボードでは、テーマを再起動なしでホットスワップ可能。色・フォント・レイアウト・密度を一括制御するテーマシステムが入った。
