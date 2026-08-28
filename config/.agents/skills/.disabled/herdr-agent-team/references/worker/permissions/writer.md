# Writer permission

task briefが指定するpathと成果物について、単一のwriter leaseを持つ。

- 編集を始める前に、briefが自分を現在のwriter ownerとして指名していることを確認する。
- 担当範囲だけを編集し、その外にあるbaselineの変更は保持する。
- writer所有権を他へ渡さない、共有しない、指定より広い範囲を持っていると仮定しない。
- branchやworktreeを作らない。repositoryの設定を変更しない。履歴を書き換えない。
- 編集後はfocused validationを実行し、生成されたdiffを確認する。
- 担当範囲と重なる新しい変更が現れたら、上書きせずに止まる。

commitはbriefまたは有効なworkflowが求める場合だけ行う。`/implement`のもとでは、担当するPlan Taskを更新し、Taskの成果物とそのPlan更新を含むcommit-onlyのatomic commitを一つ作る。pushはしない。`/implement`の外では、ユーザーの明示的な承認がbriefに記録されている場合を除いてcommitしない。

作業が完了またはblockedになったら編集を止める。Main Piがdiffを確認し、writer所有権を安全に移せるようにするため。
