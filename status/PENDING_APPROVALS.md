# 自動審査・統合待ち

観測時点: 2026-10-26T13:48:58Z

| PR | 内容 | 区分 | 現在headの検査 |
| --- | --- | --- | --- |
| [#73](https://github.com/kk051780/toy-wars-factory/pull/73) | 独立審査の差戻しを新規作業より優先するキュー規則と27検査 | 開発体制改善 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40332978440) / `a71c03ff` |

所有者への承認返信は不要。独立審査役が現在headの検査と共有所有権を確認し、1件ずつ統合してmainを検査する。

## 関連する次の検証

PR67は新head `edfe101c...` / CI40329852658で両job成功。旧headのREQUEST_CHANGESは更新先へ流用せず、REVIEWERが再審査して元の依頼を解消/更新する。PR70はclosed/unmergedのまま。保護対象の修復はIssue72へ保持し、PR73とは分離する。新キューの実WORKER消費は未実証。
