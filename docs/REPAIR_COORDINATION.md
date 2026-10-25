# 手動go・ゲーム修正・体制改善の共通排他

同じゲームへ書く経路を一本化する。手動の「go」「進めて」は、別のゲーム修正作業を並列に始める命令ではない。
手動要求は既存のゲーム修正タスクへ渡す。すでに動いていればその実行を確認し、追加起動しない。
別チャットも最初に本書とGitHubの共有状態を読み、チャット内のフラグで排他したつもりにならない。

## 正本

- 共有branch: `twf-repair-coordinator`。mainへマージしない調整用の追記履歴。
- 共有state: `ops/REPAIR_COORDINATOR.json`。
- 最新承認一覧: `status/PENDING_APPROVALS.md`（同branch）。
- 日次体制調査: `ops/SYSTEM_REVIEW_LATEST.json`。ゲーム実験候補: `ops/GAME_IMPROVEMENT_BACKLOG.json`。
- 計画・所有権・承認文: `tools/repair_control.py`。計画を作っただけではロック取得ではない。

## ロックの取得と解放

1. `branches/twf-repair-coordinator`から現在head/tree、同じrefのstateを読む。
2. サービスpeekで自分のrun UUIDを確認し、WORKERまたはMETAの取得計画を作る。
   新規/CI修理の対象branchも`work_branch`へ記録する。CONTROLLERは手動の保守/承認済み統合用。
3. 読んだtreeをbaseにstateだけを変更し、読んだheadそのものをparentにして新commitを作る。
4. `update_ref(branch_name=twf-repair-coordinator, expected_sha=読んだhead, sha=新commit, force=false)`。
   **成功したrefを再読して所有者・epochを確認したときだけ取得成功。** 取得commitのSHAを保存する。
   同じparentからの競合候補はfast-forwardできず、古いexpected_shaでも拒否される。forceや別parentは禁止。
5. 取得後にmain/PR/現在headのCIと枠数を再読する。確認前の古いキュー判断で編集しない。
6. 毎回の書込み直前に共有headと所有者・epoch・期限を確認する。所有権を失ったら編集を終了する。
   30分以内の小さな作業に区切る。期限切れは編集を許可しない。
7. ゲーム/体制PRの新規C履歴へ`coordination`のbranch、claim_commit、owner_run_id、epochを保存する。
   同じbranchのCI修理を後の別runが扱うときも、そのrunの新しい取得証拠を追加する。
8. 取得した所有者とepochのまま、共有refに対して同じexpected_sha/force=false方式で解放する。
   承認表/調査結果を更新する場合も、最新treeの他のデータを保つ。例外時も可能なら解放する。

他のWORKER/META/CONTROLLERが保持していれば編集しない。期限切れだけで奪わない。
`recover_finished_worker`は、**同じowner runが終了したサービス証拠**がある場合だけ使える。
別runの完了や「しばらく動いていない」は復旧根拠にならない。不明ならowner/run/期限と復旧の不足を報告する。
コーディネータ更新失敗を単なるリトライで上書きせず、新headを読んで判断し直す。

## 手動go

1. main方針、ゲームタスクの実行状態、共有ロック、PR/CIを読む。
2. 実行中/ロック保持中は既存作業へ合流して状態を報告し、別のゲーム編集とrun_nowを始めない。
3. CI待ちならその現在headの状況、承認待ちなら**対象PRの完全な一覧**を回答する。
4. 空きがあり実行可能な場合だけ、DISPATCHチケットを共有refで先に取得する。
   チケットは120秒。別の手動goは同じチケットへ合流し、二重にrun_nowを呼ばない。
5. もう一度ゲームタスクのpeekと共有refを読む。先に自動実行が始まっていれば、
   自分がまだ持つDISPATCHだけを解放して合流する。作業者が採用済みのチケットは消さない。
6. それ以外は所有者が求めた即時実行として既存タスクのrun_nowを一回呼ぶ。
   run_nowを呼べるのは新しいACQUIREが共有refへ成功したときのみ。RESUME/既存チケットは再送しない。
   次のWORKERがチケットを原子的に採用する。時刻実行と重なっても、取得した一方だけが編集する。
   起動要求の成功を作業完了と呼ばず、実行ID/PR/CIを別に確認する。

main統合や手動の保守もCONTROLLERロックを取る。所有者が明示した取り込み対象・head・CIを確認し、
許可されたものだけ統合する。普通の「go」からmain取り込み承認やRoblox公開承認を推定しない。

## 承認待ちの再発防止

「承認待ち」だけでは不十分。PR番号、何を変えるか、ゲーム修正/検査/体制改善の区分、
現在headの合格CIリンク、必要な承認範囲、コピーして返信できる承認文を出す。
手動status/goの回答では毎回一覧を出す。定期実行で同じ一覧を省略できるのは、
一度完全な依頼を記録した後のみ。head・対象・CIが変われば新しい一覧を作る。
通知の記録と配達成功は区別する。main取り込みの承認にRoblox公開は含めない。

CIは信頼するbaseから検査コードを読み、新しい自動PRの取得commitが共有branchの祖先であり、
登録task/run・epoch・対象branchが一致することを確認する。
導入前の#35/#38/#40は**指定されたbranchとheadが一致する場合だけ**例外とし、内容変更へ流用しない。
この排他は本書に従う経路のもの。直接GitHub上で行う外部の編集や、指示に従わないツール利用まで
物理的に禁止する権限プロキシではない。違反はCIと実行監査で検出し、日次点検で再評価する。
