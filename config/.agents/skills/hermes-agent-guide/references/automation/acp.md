# ACP / IDE 統合

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/acp

## VS Code

```bash
hermes acp start --vscode
```

VS Code 拡張 `hermes-agent.hermes-acp` をインストール後、設定:

```json
{
  "hermes.acp.url": "http://localhost:3000",
  "hermes.acp.autoConnect": true
}
```

## Zed

```bash
hermes acp start --zed
```

Zed の `settings.json` に追加:

```json
{
  "language_servers": {
    "hermes-acp": {
      "url": "http://localhost:3000"
    }
  }
}
```

## JetBrains (IntelliJ / PyCharm / WebStorm 等)

```bash
hermes acp start --jetbrains
```

プラグイン「Hermes Agent」をインストールし、Settings → Tools → Hermes Agent で URL を設定。
