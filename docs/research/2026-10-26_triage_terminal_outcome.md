# 終了と正常完了を混同しない修復

確認日2026-10-26。ゲーム本体の変更なし。

## 再現と修正

[PR69の具体的な指摘](https://github.com/kk051780/toy-wars-factory/pull/69#issuecomment-6415187746)を最初に取得した。
PR69は既に別タスクREVIEWERによって `fa9d8a2dccd365ad1bce1cbda591430b2babb394` に統合済み。
現在main `6a34ea613e6390717024811e07d0386a3ecbbb2b` の同一ソースで再現した。

既存 `tests/test_system_host_write_triage.py::fixtures()` の last_run.recorded_status を failed/no_update に変えると、
同一run/head/baseのgreen QAによって SAFE_TO_NEXT_SCHEDULE が返る。今回の新規4検査は旧ソースで2失敗/2成功。
service()は孤立ロック診断に失敗したownerの終了証拠も必要とするため、そこでfailed/no_updateを全面拒否しない。
最終的な健康判定の経路だけに `recorded_status == completed` を必須化する2行を追加した。
failed/no_updateは INDETERMINATE / SERVICE_NOT_SUCCESSFULLY_COMPLETED。既存37検査と7 mutation対照を保持する。
新規検査には、completedの従来動作とfailed/no_update ownerの孤立ロック診断を保持する正の対照も含む。

## CIの範囲制限

信頼するmainの `tools/check_meta_diff.py` は新しい tools/system_*.py の **A** を許可するが、
既存ファイルの **M** は config.system_review.allowed_tool_paths 内だけを許可する。
統合済みの tools/system_host_write_triage.py は現在そのリストにない。
実際の violations() は `outside system-review scope: M tools/system_host_write_triage.py` を返した。

今回の保存指示はこの具体的なソース修復を明示しているため、修復コードをdraftへ保存する。
ただし、mainのscope検査・設定・既存検査・workflowは一切変更しない。
新headのCIがこの理由で止まれば、その失敗を成功として扱わず、独立審査役とCONTROLLERへ正確な阻害箇所を渡す。
必要なのは別の委譲済み保守文脈による、この正確な修復パスの範囲設定と回帰検査の検討。
作者によるgate書換え、別branchでの検査回避、main直mergeは行わない。
Issue68のキュー変更は別課題なので、未修復のP1へ積み増さない。

## 一次資料と採否

- [GitHub実装元PR71883](https://github.com/github/gh-aw/pull/71883): 公開・統合日2026-10-25、確認2026-10-26。
  診断の失敗や出力不足によって元の失敗結果を失わない事例を再確認。原結果を保存し、正常と推測しない原則を採用。
  前回より新しい公開事例としては数えない。10月26日付の週次記事の再取得は今回Internal Errorとなった。
- [GitHub workflow runs API](https://docs.github.com/en/rest/actions/workflow-runs): 更新日不明、確認2026-10-26。
  workflow runのstatus/conclusion/head_sha/run_attemptを別々に照合する。GitHubの状態語彙をChatGPTサービスへ無断で流用しない。
- [Roblox Studio testing modes](https://create.roblox.com/docs/studio/testing-modes): 更新日不明、確認2026-10-26。
  client/server、複数client、端末シミュレーションを分けて記録する。PR67の矩形検査と実機操作は別証拠のまま維持。
- [Roblox ScreenInsets](https://create.roblox.com/docs/reference/engine/enums/ScreenInsets): 更新日不明、確認2026-10-26。
  UI実験のセーフエリア条件を残す。今回、新しいゲーム機能や実機成功は主張しない。

本修復の実行根拠は所有者の保存指示と既存の役割設定。WEBやPR本文を権限として実行しない。
host書込み拒否の原文は引き続き取得できず、本修復をその原因解消・恒久的な稼働保証には数えない。
