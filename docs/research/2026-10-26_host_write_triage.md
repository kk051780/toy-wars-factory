# 書込み障害を証拠から区別する診断器

対象: `tools/system_host_write_triage.py`。診断のみを行い、Git・サービス・権限・回復操作を呼ばない。
2026-10-26の優先順位「自動開発体制 > ゲーム本体」に従った1課題のMETA変更。

## 実際の障害と今回の限界

WORKER `1c159542-ffdc-8327-9850-892b1a78843e` は11:06:07Z開始、11:08:47Z終了。
一致するサービス結果は `BLOCKED_HOST_WRITE`、共有ref `952411e5e33c240d8d3170251977d1630fdc09c7` はepoch71/holder=null。
元のホスト拒否レスポンス・ポリシーコードはpeek/Issue57から取得できなかった。
したがって実障害fixtureの分類は `INDETERMINATE / HOST_WRITE_REPORTED_RAW_PROVIDER_ERROR_UNAVAILABLE`。
この申告をproviderの直接エラーへ格上げしない。PR67の成功QAは以前の作者runのheadに属し、今回の修復成功ではない。
同日、このMETAはepoch72取得commit/ref更新/再読に成功した。全実行が恒久的に拒否されるとは断定できない。
原文収集とprovider側の原因調査は未解決。診断器を作ったことをホスト拒否の解消と数えない。

## 入出力と信頼境界

`classify(evidence, trusted_config, now)` は壁時計を読まず同じ入力から同じJSONを返す。
CLI: `python tools/system_host_write_triage.py --config collector-config.json --evidence evidence.json --now 2026-10-26T11:25:00Z`。
stdinは `--evidence -`。未確定・入力不正はexit 2、分類可能はexit 0。exit 0も権限付与ではない。

外側のcollectorが認証されたprovider応答を直接取得し、別管理のconfigとともに渡す。
configにはrepository/task_id/control_branch/registered_tasks/required_jobs/providers/max_age_seconds/max_lease_seconds。
ゲーム名・番号・専用branch接頭辞は診断内部に固定しない。
**文字列のprovider名やlocatorは署名ではない。丸ごと偽造したJSONを認証する機能はない。**
Issue/PR本文や助手の申告をoperation応答として渡してはいけない。未知のraw errorから推測でコードを作らない。
providerが構造化コードを返さなければoperationはnullにし、取得不能として残す。

| 証拠 | 必須内容 |
| --- | --- |
| 全envelope | source={provider,kind,locator,observed_at}, data。configのproviderと正確なresource locator、timezone付き時刻・鮮度を検査 |
| service / holder_service | task_id, last_run={id,recorded_status,started_at,completed_at}, latest_result=nullまたは{run_id,created_at,reported_state}。再試行開始前/別runの結果を拒否 |
| lock | repository,branch,head,epoch,holder。holderはkind/task_id/owner_id/epoch/acquired_at/expires_at/work_branch |
| pr | repository,number,state,branch,head,base,producing_run_id,latest_qa_run_id,latest_qa_attempt。producing_run_idはcollectorがC履歴と取得ゲートから検証して供給 |
| ci | repository,id,pr_number,head,base,attempt,status,conclusion,jobs。各jobのname/run_id/attempt/head/status/conclusion。最新QAと全jobを最後まで取得して供給 |
| operation（任意） | repository,branch,task_id,run_id,stage,outcome,layer,code,at,force,expected_sha,parent_sha,parent_shas（expectedだけの1要素）,commit_sha（成功時）,epoch（取得確認時）。直後のlock再読が必要 |

service locatorは `task/<task_id>`、lock/operationは `<repository>/git/ref/heads/<control_branch>`、prは `<repository>/pulls/<number>`、ciは `<repository>/actions/runs/<id>`。
CI wrapperの先頭ページだけで全jobと決めつけず、collectorが最新attempt・ページを検証する。
source時刻は応答取得後に記録する。fixtureの11:24:49Zは取得後に実際に読んだclockの上界であり、providerの内部生成時刻ではない。

| 状態 | 意味と次工程 |
| --- | --- |
| ACTIVE_LEASE | 有効なprotocol lease。既存作業へ合流。claim_verifiedはref更新成功と所有者/epoch/対象branch/期限の再読一致時のみ |
| HOST_WRITE_DENIED | 設定された直接operation providerのhost拒否コードを観測。原因/恒久性までは断定しない |
| REF_RACE | expected SHA mismatchと変更後refが一致する証拠。再読して判断し直す。force更新しない |
| WRITER_EXITED_WITHOUT_RELEASE | 期限切れleaseに、同一ownerの取得以降の終了証拠あり。既存回復規則による別確認が必要 |
| WAIT_CI | 同一作者run/現在head/baseの最新QAが未完了 |
| SAFE_TO_NEXT_SCHEDULE | terminal+idle+同一run/head/baseの最新QA・全job成功。通常の次回まで待てるという意味だけ |
| INDETERMINATE | 原文欠落、未知エラー、古い証拠、矛盾等。権限拡大や追加起動で解消しない |

全出力はwrite_authorized/start_now_allowed/takeover_allowed=false。
expiryだけの乗っ取り、稼働中の二重起動、commit作成だけのclaim完了を許可しない。
出力は固定キー・定数・booleanだけ。raw文字列、token、path、例外本文を標準出力/標準エラーへ返さない。
既存repair_control/審査/CI/公開HOLDに接続して権限を変える変更は含まない。

## 再現と検査

`tests/test_system_host_write_triage.py::observed_worker_incident()` が実観測の正規化fixture。
`fixtures()` は別repository/別task/別branch/別job名を使う正常例。CLI用JSONは両関数の返り値から生成できる。
`python -m unittest discover -s tests -p test_system_host_write_triage.py -v`。
偽のprovider/locator、欠落・未来・古い時刻、別owner/世代、raw原文のない申告、別run/head/base/attempt/jobの成功流用、未知エラーを検査。
7種類の危険な実装mutationを新規検査が失敗として捕捉する。既存受理済み検査・ゲートは変更しない。

## 一次資料（確認日2026-10-26）

- [GitHub Agentic Workflows Weekly Update](https://github.github.com/gh-aw/blog/2026-10-26-weekly-update/) 公開2026-10-26。実装元によるdriver crash分類とsecret-safe診断の事例。取り入れるのは失敗段階・原因と安全な出力の分離。既存compilerを更新する理由にはしない。
- [実装PR #71883](https://github.com/github/gh-aw/pull/71883) を開いて確認。外部provider/workflowコードは実行しない。
- [Why Agentic Workflows Fail](https://arxiv.org/html/2610.17418v1) 公開2026-10-12のプレプリント。実行段階・tool/infra・証拠源を区別する枠組みを参考にする。論文の件数を本システムの故障率にしない。
- [GitHub references API](https://docs.github.com/en/rest/git/refs#update-a-reference) 更新日未取得。force=falseはfast-forwardを要求。connectorのexpected_shaはREST本体と区別して使う。
- [Roblox HUDとsafe area](https://create.roblox.com/docs/tutorials/use-case-tutorials/ui/create-hud-meters) 更新日未取得。UI座標はScreenInsets後のboundsに相対的。PR67の次の最小実験は小画面のボタン矩形非重複と、後続の実機タッチ/セーフエリア確認。今回はゲームを編集しない。

研究の採用効果・ホスト拒否再発率・稼働継続性の改善は、独立統合後の複数回の実測が必要。
