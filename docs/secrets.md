# 環境変数の管理

[README](../README.md) / [日常操作](usage.md) / 環境変数の管理

API キーなどの秘密は Git に入れない。値の控えは 1Password に置き、使う場所ごとに次へ登録する。

| 使う場所 | 置き場所 |
|---|---|
| T3 Code から起動するエージェント | T3 Code の provider ごとの Environment variables |
| Hermes の CLI・gateway | `~/.hermes/.env` |
| 各プロジェクト | プロジェクト直下の `.env`（Git 管理外）と、値のない `.env.example` |

各エージェントの OAuth 認証は、ここでは扱わない。

## T3 Code のエージェントに渡す

T3 Code はログインシェルの環境変数を一部しか引き継がないので、fish で export してもエージェントには届かない。provider ごとに登録する。

1. T3 Code の **Settings → Providers** で対象の provider（Claude、Codex、Pi など）を開く。
2. **Environment variables** に変数名と値を入力し、**Sensitive** をオンにして保存する。

Sensitive の値は `~/.t3/userdata/secrets/` に保存され、dotfiles で管理する `settings.json` には値の入っていない項目だけが書かれる。保存後に次を実行し、登録した変数の `value` が空で `valueRedacted` が `true` になっていることを確認する。

```sh
jq '.providerInstances | map_values(.environment)' ~/.t3/userdata/settings.json
```

現在使う変数と登録先：

| 変数 | 登録する provider | 用途 |
|---|---|---|
| `CONTEXT7_API_KEY` | Claude、Codex、Pi、OpenCode | Context7 によるドキュメント参照 |
| `OMLX_API_KEY` | OpenCode | oMLX のローカル API への認証 |
| `GIT_OPTIONAL_LOCKS` | Pi | 値は `0`。秘密ではないので Sensitive は不要。Git の任意ロックを止め、並行する Git 操作との競合を避ける |

エージェントが `env` などで環境変数を表示すると、その出力は T3 Code の会話履歴に平文で残る。値を出力させない。

値を変えたら、その provider の新しいスレッドから反映される。ターミナルから直接起動したエージェントには渡らないので、API キーが必要な作業は T3 Code から行う。

## Hermes に渡す

Hermes は `~/.hermes/.env` を起動時に読み込む。Git 管理外の実ファイルとして作り、他のユーザーから読めないようにする。

```sh
touch "$HOME/.hermes/.env"
chmod 600 "$HOME/.hermes/.env"
```

`KEY=value` の形式で値を書く。変更後は gateway を再起動する。

```fish
hermes gateway restart
```

## プロジェクトで使う

プロジェクト直下の `.env` に値を置き、`.gitignore` に `.env` を加える。必要な変数名は、値を空にした `.env.example` で管理する。
