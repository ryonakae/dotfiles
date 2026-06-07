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

## v0.12.0+ ACP 強化

- **画像プロンプトの advertise + forward**（v0.12.0）
- **atomic session persistence**、**reasoning metadata preservation**（v0.13.0）
- **`/steer` / `/queue` の ACP 化**（v0.13.0）— Zed/VS Code/JetBrains から実行中エージェントに注入
- **ACP `/steer` がアイドルセッションでは regular prompt として実行**（v0.13.0）
- **session edit auto-approval modes**（v0.15.0）
- **Zed ACP Registry**（v0.14.0）— `uvx` ベースで one-click install
- **`hermes acp --setup-browser`**（v0.14.0）— registry-driven インストール時の browser tool bootstrap
