# iOS Simulator

- リポジトリごとに `{機種名} ({リポジトリ名})`（例: `iPhone 17 (dotfiles)`）の専用端末を使う。なければ `xcrun simctl create` で作り、他リポジトリの端末は操作しない。
- 端末は `device_open` で開く。専用端末の ID が分からなければ先に `device_list` で確認する。
- 操作は `device_open` が返す `quickStart` に従う。`agentDevice.targetArgs` が空でなければ毎回付ける。実行パスとセッションは開くたびに変わるので、文書やスクリプトに固定しない。
- zsh では変数に入れた引数列が単語分割されず 1 引数になる。`targetArgs` 付きの呼び出しを繰り返すなら shell 関数で包む。
- UI 動作検証や `.ad` テストの配置・初期状態・実行方法は、対象アプリの既存規約を優先する。
