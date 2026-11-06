# Linked environment での別マシン作業

ユーザーが別マシンでの調査・操作・同期を頼んだら、そのマシンの Linked environment を使う。ツールの引数と接続手順は T3 Code が注入する指示・ツール説明に従う。

## 接続先を選ぶ

- `t3_environment_links` でマシンの `label`、`environmentId`、`status`、`access` を確認する。名前だけで一意に決まらない場合は、操作前に対象を確認する。
- 未登録・期限切れなら `t3_environment_link` を使う。`hint` はユーザーが呼んだマシン名から取り、既知の `environmentId` があれば渡す。URL はユーザーが提示したものだけを使い、ペアリングコードをチャットで求めない。
- 接続要求が `pending` なら、結果の通知を待つ。接続状態のポーリングや、確認のための再 link はしない。
- 登録済みでも `unreachable` なら `lastError` を確認し、接続できないことを報告する。勝手に再登録したり、SSH に切り替えたりしない。
- 接続できることを作業全体の承認とみなさない。依頼範囲と接続先の権限を守り、権限不足を別の接続手段で回避しない。

## 接続先の環境で操作する

T3 のツールで別マシンを操作するときは `environmentId` を指定する。project・thread・device の ID とパスは接続先で確認し、ローカルの値を流用しない。プロジェクトの選択が必要なら、接続先の `t3_project_list` で repository と `workspaceRoot` を確認する。

別マシンでシェル・ファイル作業をする場合は、`delegate_task` の `target.environmentId` に接続先を指定する。プロジェクトを指定するなら `target.projectId` も接続先の ID にする。ローカルのシェル実行は、接続先の名前や ID を書くだけでは遠隔実行にならない。

サブエージェントへの委譲に使う provider・モデル・思考レベルは[既存の選定方針](../SKILL.md#サブエージェントの既定モデル思考レベル)と `orchestrator_capabilities` に従う。通常の委譲のために `t3_thread_launch` などで新しいトップレベルスレッドを作らない。

## サブエージェントへ渡す内容

接続先のサブエージェントは親の会話履歴を持たない。[依頼と結果の確認](delegation.md#依頼と結果の確認)に加え、次を明記する。

- 対象マシン、作業の目的、対象 repository・branch・commit
- 調査・変更してよい範囲、禁止する操作、保持する未コミット変更
- 接続先で確認すべきパス・ツール・前提条件
- 完了条件、必要な検証、報告する HEAD・ファイル一致・残作業

checkout、未コミット変更、絶対パス、インストール済みツールはマシン間で共有されない。`isolation: "shared"` もマシン間のファイル共有を意味しない。必要な変更は commit・push など、依頼で認められた方法で接続先へ渡す。秘密は依頼文に含めない。

## 完了を確認する

- 戻り値の `taskId` と `remoteChild` を保持する。`childThreadId` が `null` でも、`remoteChild` に接続先の情報があれば、その値を使う。
- 実行中は戻り値の `next` に従う。待機のタイムアウトは完了ではない。完了通知に任せ、`task_status`・sleep・ループでポーリングしない。不要になったタスクは `task_cancel` で止める。
- 結果のスレッドを読むときは `t3_thread_read` に `remoteChild.environmentId` と `remoteChild.threadId` を渡す。ユーザーへスレッドを示すときは返された `link` をそのまま使う。
- 子の実行終了だけで成功とせず、依頼の完了条件と報告を照合する。ローカルでの push 成功と、接続先での取り込み・適用成功を区別する。

## 例：dotfiles のスキル本文を別 Mac へ同期する

既存スキルの本文だけを更新した場合は、次の範囲で同期する。配置宣言の変更や別プロジェクトの運用に、そのまま適用しない。

1. 元のマシンで対象変更を commit し、push の成功を確認する。同期先へ目標 commit を渡す。
2. 接続先で repository の origin・branch・HEAD と未コミット変更を確認する。
3. fetch 後、目標 commit が現在の HEAD に含まれていれば更新しない。対象 branch 上で現在の HEAD が目標 commit の祖先なら、`git merge --ff-only <目標commit>` で取り込む。
4. 未コミット変更との衝突、履歴の分岐、別 branch では止まり、状態を報告する。自動 stash・reset・clean・force は行わず、無関係な変更は保持する。
5. 対象ファイルが目標 commit と一致し、HOME 側の既存スキル参照からも同じ内容が読めることを確認する。パスやリンク先は接続先で調べ、想定と違う実体・リンクを勝手に置換しない。

本文だけなら既存リンクを通じて反映されるため、通常は setup・mise apply は不要。パッケージや外部 repository の更新、installer、サービス再起動を同期に混ぜない。
