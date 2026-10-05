# dig log: ホスト設定を Nix に集約する

## 目的・前提・制約
- ユーザーは独自の host.json の役割を確認した後、「nixに寄せて」と依頼した。単に拡張子を変えるのでなく、独自の入力処理を減らす方向で検討する。
- 現在は flake.nix が host input 内の JSON を読み、machine を Darwin と Home Manager へ渡す。scripts/dotfiles.py が JSON の検証・一時 snapshot・host input の override を実装し、標準配置の host.json がないと通常 build が失敗する。
- AGENTS.md は「マシン固有値・秘密は Git 管理外の実ファイルへ置き、管理するのは値を含まない *.example」と定める。非秘密のホスト定義を Git 管理する変更には方針変更の承認が必要。
- 秘密は引き続き Git／Nix store の対象外。既存の無関係な settings 3ファイルの変更は保持する。調査・要件確認段階では実装・適用しない。

## 決定事項
- ユーザー名・ホームディレクトリ等の非秘密のホスト定義を Nix ファイルとして Git 管理する。AGENTS.md のマシン固有値を管理外とする規約に、この例外を設ける（Q1: A）。秘密・認証情報は引き続き対象外。
  - 出典: ユーザーの「a」。
- 独自 host.json 方式を見直し、Nix の設定へ寄せる。
  - 出典: ユーザーの「nixに寄せて」。

## 未決・保留
- Q2 は A で承認済み。続いて `docs/plans/2026-10-05-nix-host-configuration.md` の実装も「ok」で承認された。合意した範囲は以下。
  - ホスト定義は通常の Nix module とし、system.primaryUser と users.users.<name>.home を正本にする。現在の darwinConfigurations.mac は維持する。
  - 独自 machine 引数の受け渡しは標準 config 参照に置き換える。Home Manager の標準 Darwin 統合からユーザー名・HOME を設定できる経路を使う。
  - JSON input／example／検証／一時 snapshot／host override を廃止する。ホストの選択は darwinConfigurations の名前を基準にする。
  - scripts/dotfiles.py の build／switch／update 入口は安全確認のために残して簡素化する。対象ユーザー確認・固定 lock・Git外ファイル非取込・Safehouse 内 switch 拒否・対話確認・既存サービス停止確認を維持する。
  - 現在の JSON schema に依存するテストは Nix 定義のテストに置換し、lock 更新拒否・明示更新・管理外ファイルの非取込は維持する。
- 実装・15件のテストが完了。全体 build は Safehouse 拒否後、今回の変更について追加承認を得た Herdr 通常ペインで成功。移行前と同一の system store path を生成した。詳細は計画に記録。実機 switch は別承認とする。
