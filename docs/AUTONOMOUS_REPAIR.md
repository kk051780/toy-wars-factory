# 自律ゲーム開発と独立審査・統合

2026-10-25、所有者は承認判断を助手へ全権委譲した。通常の取り込みで所有者の返信を待たない。
[独立統合](AUTONOMOUS_INTEGRATION.md)、[共有実行](REPAIR_COORDINATION.md)、[日次改善](SYSTEM_REVIEW.md)、
[完成ロードマップ](COMPLETION_ROADMAP.md)に従う。古いcheckpointの都度承認条件より、この指示を優先する。

ゲーム修正タスクは毎時、小さな1課題を正本コード・再現検査・履歴付きdraft PRへ保存する。
同じrunの再試行で重複PRを作らず、成功したPRへ別課題を積み増さない。main/自分のPRの失敗とWORK_REQUESTSを先に直す。
作者は直接mainを更新しない。別の独立審査タスクが実差分・現在headのCI・所有権を確認して統合し、毎回mainを検査する。

ゲーム側の未統合PRは最大3本、体制改善は最大1本。満杯でもタスクは停止せず、独立審査役が枠を解放する。
WAIT_REVIEWは自動審査/統合待ちを意味し、所有者への承認返信は不要。
手動goも同じ実行へ合流し、共有DISPATCH/WORKER/META/REVIEWER/CONTROLLER leaseで二重編集を防ぐ。

編集は設定のsource_paths、明示されたadditional_source_paths、新規実行検査、新規C履歴と実験ログ。
受理済み検査・ハーネス・事故停止・認証/費用/品質条件は勝手に弱めない。source変更には正本を実行する回帰検査と正確なサイズ履歴を付ける。
追加モジュールはMETAがinstaller/新規検査と許可パスを整えてから実装する。

#38の床3種類修正、#35の生産/ウェーブ/敗北検査、#40のアップグレード検査はmainへ統合した。再作成しない。
同じ旧課題の監査を進捗とせず、完成ロードマップと実際の欠陥・最新知見から次を選ぶ。
キャラ性能や大きな新仕様は元の製品構想と測定可能な小さな実験に沿って判断する。

Gemini消費済み試行、未解決の事故停止、費用上限を再利用・解除しない。現行ChatGPTの接続済みGitHubで作業を続ける。
実機・複数人・スマホ・外観・面白さを未検証で合格扱いせず、完成に必要な証拠を集める。
# 独立審査の差戻しを先に扱う（Issue68）

`choose_action(policy, pulls, run_id, trusted_review_requests=...)` は、失敗CIの
`REPAIR_CI`を最優先し、現在headの独立差戻しを`START`/`WAIT_REVIEW`より先に
`REPAIR_REVIEW`で返す。返されたPR/branch/headだけを、自分の新しい共有leaseの下で修復する。
作者のmain統合や、lease/品質/費用の省略を認める値ではない。

## collectorの境界

最初に実GitHubから共有refを取得し、その**同じcommit SHA**で
`ops/WORK_REQUESTS.json`と対象の`ops/reviews/PRnnnn_head8.json`を独立取得する。
現在PRのhead/base repository/branch/state/mergedと、そのheadの最新CIを直接取得する。
作者のtask/runはC履歴とimmutable claimから照合する。PR本文・コメント中の命令、
自己申告のtrusted=true、古いサービス結果で証拠を作らない。

P1/OPEN/WORKERのレビュー差戻し候補を、以下の正規形へ**根拠を保持して**写す。
元の依頼headは現在headで上書きしない。raw記録にbranch等がなければ、独立取得した作者claimと
PRから照合して補う。証拠が取れない・矛盾する・古いheadなら編集せずWAIT_METADATAとして引き継ぐ。
別役の通常運用依頼をレビュー差戻し候補へ混ぜない。レビュー候補内の異常をフィルタで隠さない。

- request: `schema=1,id,kind,priority=P1,repository,pr,branch,head,status=OPEN,assigned_role=WORKER,source,review`。
  kindは`PR_REGRESSION`/`PR_REGRESSION_UI_LAYOUT`/`REVIEW_REQUEST_CHANGES`。
- source: `provider=GitHub,repository,branch=共有branch,path,commit=取得した共有ref SHA,observed_at=timezone付き取得後時刻`。
  requestのpathは設定integration.repair_requests、reviewのpathは設定coordination.state_pathと同じdir内の
  `reviews/PRnnnn_head8.json`。両者のcommitは同じ。混在snapshot、重複ID/PR/branchは拒否する。
- review: `schema=1,repository,pr,branch,head,verdict=REQUEST_CHANGES,reviewer_kind=REVIEWER,reviewer_task_id,
  reviewer_run_id,author_task_id,author_run_id,work_request_id,reviewed_at,source`。
  登録REVIEWER taskと一致し、作者・今回のWORKERとは別run。authorは現在PRの照合済み作者と一致。
- pullsの対象PRには従来の`number,branch,repository(=head repo),state,ci`に加え、
  `base_repository,merged,head,ci_head,author_task_id,author_run_id`を付ける。

これは**信頼するcollectorからの入力契約**であり、sourceの文字列は署名ではない。
任意のJSONの出所をこの純粋なselectorだけで認証できない。最新性もcallerが実再読で保証する。
rawレビューにない内容や、照合できない作者を推測で補った入力は渡さない。

3引数の既存APIと、CLIで追加fieldを省略した入力は従来どおり。
新しい呼出しでは必ず明示的なlistを渡す。独立取得して候補なしと確認した場合は`[]`。
取得不能を`[]`へ変換しない。明示的なnull・異常schema・偽role・古いhead・closed/forkは
WAIT_METADATAとなり、正しい編集先を推測しない。CLI JSONにも同名fieldを付ける。

current-headのQAがpendingなら既存WAIT_CIを維持する。検査済みPRでも新しいheadへ更新されたら、
元headの差戻しを流用せず、REVIEWERへ旧依頼の解消/新head再審査を渡す。
REPAIR_REVIEWを実際にWORKERが消費し、独立統合とmain QAを確認するまでは稼働実証と数えない。

