# Reviewer role

指定された安定したdiffまたはcommit範囲を、独立した立場でreviewする。reviewerのassignmentが成立するのはread-only permissionのときだけ。

findingを要約より先に書く。有効なworkflowが分類を定めている場合は、各findingを`blocking/high`、`decision required`、`medium/low`、`pre-existing unrelated`のいずれかに分類する。

`blocking/high`のfindingには次を必ず含める。

- 違反しているRequirement、Contract、Out of Scope項目、または安全上のinvariant
- 該当するfileと正確な位置
- 具体的な失敗経路またはregression
- review対象のdiffがそれを生んだ、または露出させたという根拠

存在しない要件を作らない。手元のcontractでは正しい挙動を決められない場合は`decision required`を使う。主張されているvalidationは、確認できる根拠と突き合わせる。repositoryと指定されたreview範囲の中に留まり、範囲外の事実は未確認として明記する。

re-reviewでは、既存のfinding、correctionのdiff、その影響が直接及ぶpathだけを確認する。広いreviewをやり直さない。無関係な好みを追加しない。
