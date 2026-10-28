# OWNER原案とWeb研究の共通ストック（読み取り専用・導入候補）

2026-10-29、登録METAの新規実runとepoch222から作成。手動PR110の最新head b74cace762f671dff268d2109b0dfd47b22d8184 を参照し、修復済みグラフ検査・仮評価を出典付きで移した。C00118/C00120は原作者の記録であり移植しない。元24検査を先に再実行し、未受理のfixtureを新scope/要求された状態遷移へ適合させ、追加回帰を作成した。受理済み253ファイルは変更しない。

## 原文を別の解釈で上書きしない

OWNER-20261028-DUAL-EVOLUTIONはIssue109 comment6480372522から独立取得した。元会話URLはNOT_AVAILABLE、GitHub取得先と原文全文はC00121.stock_checkpointへ保存。短いキャラ原案は今回のユーザー指示を別IDでそのまま保存した。テストのWORDSは合成fixtureとして扱い、認証済み原案と混同しない。

Web事実はURL/公開日/取得日時/種別/限界を持つ。公開日不明はNOT_AVAILABLE、日付しか分からない場合は時刻を創作しない。派生案は親ID・変種・重複を持つ別レコード。scopeはproject/repository/WORKER・META・REVIEWER、domainはGAME/SYSTEM。別ゲーム間のrepo/task再利用や同一projectのscope変更を拒否する。

merge_registry(existing, incoming)は、独立取得した基準ストックの原文・起源・scope・観測・参照を変えず、イベントの追記だけを認める。再ハッシュした別の原文でも置換を拒否し、既存レコードを削除しない。新しい研究や解釈は新IDへ保存する。基準ストックの独立取得とfenced CAS保存は呼出側の責任であり、ハッシュ/roleラベルは本人証明ではない。

## 実験と実績の境界

共通計画状態はCAPTURED→RESEARCHED→COMPARED→EXPERIMENT_DESIGNED。失敗/保留/拒否/撤回は理由を残す終端状態。後段PROTOTYPE_PR→OFFLINE_VERIFIED→INDEPENDENT_APPROVED→MERGED_MAIN_QA→ENGINE_VERIFIED→PLAYER_MEASUREDは表示するが、呼出者JSONからの昇格は拒否する。後段の実績取得・自動チャット取り込みは未実装。今回を両輪の全自動完成とは呼ばない。

C00121へ原案2・Web案3・派生4、GAME/SYSTEMそれぞれ2案＋変更なし案を実モジュールに通した記録を保存。各案に仮説/検査/反証条件/工数・QA・性能リスクを付け、指標はNOT_MEASURED、engineはNOT_RUN。スコアは仮の設計点で、市場勝率や人時ではない。実main採用0、実機0、プレイヤー計測0。

GAME：支援役を段階導入し収集目標を見せる案と、既存3体の初回製造/180秒の導線を先に改善する案を比較。PR98キュアボは未統合、Issue102クルリンは依存候補。新キャラは保護導入後のWORKER範囲。大きなハート/工具袋等の独自輪郭を32/64pxで識別する。通常18/大型24パーツは本作の仮予算であり、20体/陣営×4工場の実機負荷を測る計画。競合素材は複製しない。現在は未実施。

SYSTEM：コードによるscope/原文保持と、Issueだけの手動構造化を比較。今回の選択は前者の最小コアだが、原文喪失/混同件数と記録負荷を実サイクルの分母・期間付きで確認するまで効果は未測定。

## 調査台帳（確認日2026-10-29 JST）

- Roblox公式 https://create.roblox.com/docs/discovery （公開/更新日不明）：初回離脱と再訪日数を区別し、流入元を揃えて比較する。自作の効果は示さない。
- Roblox公式 https://create.roblox.com/docs/production/experiments （日付不明）：対照・標本・検出可能効果の限界を踏まえる。実験は起動しない。
- Roblox公式 https://create.roblox.com/docs/production/analytics/retention （日付不明）：初回来訪cohortのD1/D7と集計play-daysは異なる指標。
- 開発者一次例 https://www.biggames.io/post/pet-simulator-99-update-99 （2026-10-24公開）：図鑑と進行報酬を紹介。人気や継続率への因果証明ではない。
- 開発体制一次例 https://opensource.microsoft.com/blog/2026/10/19/introducing-scope-open-source-evaluation-for-ai-coding-agents/ （2026-10-19公開）：代表課題/設定/繰返し/失敗経路を記録する方針を採用。SDK事例の効果を本作へ転用しない。
- コミュニティ候補 https://devforum.roblox.com/t/50-of-players-leave-within-2-minutes/4946893 （検索上2026-10-20）：本文はJS検証画面。NOT_VERIFIEDとして統計/反応は採用せず、検索断片を実読と偽らない。

## 実行と検査

`python -m unittest tests.test_system_idea_pipeline tests.test_system_idea_vault`

`python tools/system_idea_pipeline.py` はstdinのproject_id/ideas/proposalsから仮比較JSONを返す。C00121.stock_checkpoint.recordsとproposals.GAMEまたはSYSTEMを入力例にできる。重複JSONキー/異常値/権限の混入を拒否し、エラー入力本文は出さない。ネットワーク・書込み・dispatch・merge・公開・支出は行わない。

元候補がscope欠落を受理する負対照は1失敗、原文保持の行を隔離変異すると2失敗（いずれもerrors0）。既存の履歴祖先検査は、Git履歴のないローカルsnapshotでは失敗する。既存検査を変更/skipせず、正確な新headのGitHub offline/compile_holdを要求する。実行件数と結果はC00121と共有報告へ保存する。

別登録REVIEWERへ渡し、PR111の修復/審査を優先してから、新PRの取得証拠・原作者帰属・差分・CIを検査する。作者は自己統合しない。統合後main QA/handoffまでは未採用。Gemini・公開・費用HOLDを保持する。
