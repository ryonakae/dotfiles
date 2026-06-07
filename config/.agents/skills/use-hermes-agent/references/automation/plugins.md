# プラグインシステム

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins

## ディレクトリ構造

現行実装（v0.11.0 / `hermes_cli/plugins.py`）では、directory plugin は **`plugin.yaml` と `__init__.py` の `register(ctx)` 関数**で検出・ロードされる。

```
~/.hermes/plugins/
└── my_plugin/
    ├── plugin.yaml             # manifest。name/version/description/provides_hooks など
    ├── __init__.py             # エントリポイント。register(ctx) を定義
    ├── requirements.txt        # Python 依存関係（オプション）
    └── config.yaml             # プラグイン設定（オプション）
```

## register パターン

```python
# ~/.hermes/plugins/my_plugin/__init__.py

def register(ctx):
    ctx.register_hook("pre_llm_call", inject_context)


def inject_context(session_id: str, user_message: str, is_first_turn: bool, **kwargs):
    return {"context": "追加コンテクスト"}
```

`plugin.yaml` 例:

```yaml
name: my_plugin
version: 1.0.0
description: プラグインの説明
provides_hooks:
  - pre_llm_call
```

ユーザーインストール plugin は opt-in。`config.yaml` の `plugins.enabled` に plugin key/name を入れるか、`hermes plugins enable <name>` で有効化する。`plugins.disabled` にある name/key は常にロードされない。

## プラグイン検出パス

1. bundled plugins: `<repo>/plugins/<name>/`（一部 category backend を含む）
2. user plugins: `~/.hermes/plugins/<name>/`
3. project plugins: `./.hermes/plugins/<name>/`（`HERMES_ENABLE_PROJECT_PLUGINS` が true の場合のみ）
4. pip entry point: `hermes_agent.plugins`

## CLI コマンド

```bash
hermes plugins list              # インストール済みプラグイン一覧
hermes plugins install <path>    # プラグインインストール
hermes plugins remove <name>     # プラグイン削除
hermes plugins enable <name>     # 有効化
hermes plugins disable <name>    # 無効化
```

## Plugin Surface

プラグインから利用できる API。Python プラグインで実装する。

| API | 用途 | 導入 |
|-----|------|------|
| `register_command(name, handler)` | スラッシュコマンドを動的に追加（gateway 上のメッセージング全プラットフォームに自動公開） | v0.11.0 |
| `dispatch_tool(name, args)` | プラグインコードから既存ツールを直接呼び出す | v0.11.0 |
| `pre_tool_call` フックで veto | ツール呼び出しを実行前にブロック可能 | v0.11.0 |
| `transform_tool_result(name, result)` | ツール結果を汎用的に書き換える | v0.11.0 |
| `transform_terminal_output(output)` | terminal ツール出力を加工する | v0.11.0 |
| `transform_llm_output(text)` | LLM 出力を会話前に変換・フィルタ | v0.13.0 |
| `pre_gateway_dispatch` | dispatch 前の interceptor | v0.12.0 |
| `pre_approval_request` / `post_approval_response` | 承認フローへの介入 | v0.12.0 |
| `ctx.llm(...)` | プラグインから LLM 呼び出し | v0.14.0 |
| `tool_override(name, impl)` | 組込みツール差し替え | v0.14.0 |
| `register_tts_provider(name, impl)` | TTS provider 登録 | v0.15.0 |
| `register_transcription_provider(name, impl)` | STT provider 登録 | v0.15.0 |
| `register_auxiliary_task(name, impl)` | 補助タスク（aux LLM）登録 | v0.15.0 |
| `standalone_sender_fn` | out-of-process cron delivery（no_agent モード） | v0.14.0 |
| `env_enablement_fn` / `cron_deliver_env_var` | プラットフォームプラグインフック（IRC, Teams, Google Chat 等） | v0.13.0 |
| `embedder` environment-hint hook | embedder への env hint | v0.16.0 |
| `image_gen` バックエンド登録 | 独自画像生成プロバイダーを差し込める | v0.11.0 |
| ダッシュボードカスタムタブ | Web ダッシュボードに独自タブを追加 | v0.11.0 |
| 名前空間化スキル登録 | プラグインがバンドルしたスキルを独自名前空間で登録 | v0.11.0 |
| Shell hooks | Python なしで shell スクリプトをライフサイクルフックとして登録 | v0.11.0 |

## ProviderProfile ABC（v0.13.0）

Providers 自体がプラグインに移行。`plugins/model-providers/` に各 provider を実装。

```python
# plugins/model-providers/my-provider/__init__.py
from hermes.plugin import ProviderProfile

class MyProvider(ProviderProfile):
    name = "my-provider"
    transport = "chat_completions"

    def resolve_credentials(self): ...
    def list_models(self): ...
```

### 組み込み参考プラグイン

`disk-cleanup` プラグインがバンドル済み（opt-in、デフォルト無効）。プラグイン記述のリファレンス実装として参照可能。

### bundled プラグイン（v0.12.0+）

- **Langfuse** — 観測性（v0.12.0、v0.15.1 で修正）
- **hermes-achievements** — 実績システム（v0.12.0）
- **Discord** / **Mattermost** — v0.15.0 から bundled plugin に移行
- **ntfy** — v0.15.0
- **security-guidance** — v0.15.0
- **Google Meet** — v0.12.0

### Project-local プラグイン

`HERMES_ENABLE_PROJECT_PLUGINS=1` でプロジェクト内 `./hermes-plugins/` を読み込める。

### デバッグ

`HERMES_PLUGINS_DEBUG=1`（v0.14.0）でプラグインロードログを詳細出力。
