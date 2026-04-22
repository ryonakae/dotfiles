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
