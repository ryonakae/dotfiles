# プラグインシステム

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins

## ディレクトリ構造

```
~/.hermes/plugins/
└── my_plugin/
    ├── plugin.py               # エントリポイント（HermesPlugin 継承クラス）
    ├── requirements.txt        # Python 依存関係（オプション）
    └── config.yaml             # プラグイン設定（オプション）
```

## register パターン

```python
from hermes.plugin import HermesPlugin, register

@register
class MyPlugin(HermesPlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "プラグインの説明"
```

## プラグイン検出パス

1. `~/.hermes/plugins/`
2. `config.yaml` の `plugins.paths` で指定されたディレクトリ
3. pip インストール済みの `hermes-plugin-*` パッケージ

## CLI コマンド

```bash
hermes plugins list              # インストール済みプラグイン一覧
hermes plugins install <path>    # プラグインインストール
hermes plugins remove <name>     # プラグイン削除
hermes plugins enable <name>     # 有効化
hermes plugins disable <name>    # 無効化
```

## v0.11.0 で大幅拡張された Plugin Surface

プラグインから利用できる API が大幅に増えた。Python プラグインで実装する。

| API | 用途 |
|-----|------|
| `register_command(name, handler)` | スラッシュコマンドを動的に追加（gateway 上のメッセージング全プラットフォームに自動公開） |
| `dispatch_tool(name, args)` | プラグインコードから既存ツールを直接呼び出す |
| `pre_tool_call` フックで veto | ツール呼び出しを実行前にブロック可能 |
| `transform_tool_result(name, result)` | ツール結果を汎用的に書き換える |
| `transform_terminal_output(output)` | terminal ツール出力を加工する |
| `image_gen` バックエンド登録 | 独自画像生成プロバイダーを差し込める（OpenAI Codex 経由 gpt-image-2 など） |
| ダッシュボードカスタムタブ | Web ダッシュボードに独自タブを追加 |
| 名前空間化スキル登録 | プラグインがバンドルしたスキルを独自名前空間で登録 |
| Shell hooks | Python なしで shell スクリプトをライフサイクルフックとして登録 |

### 組み込み参考プラグイン

`disk-cleanup` プラグインがバンドル済み（opt-in、デフォルト無効）。プラグイン記述のリファレンス実装として参照可能。

### Project-local プラグイン

`HERMES_ENABLE_PROJECT_PLUGINS=1` でプロジェクト内 `./hermes-plugins/` を読み込める。
