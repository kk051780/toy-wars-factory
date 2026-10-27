# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: ca6d1662092d71e81e959fc30a5dea306ee7f60e
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 既存GitHub AIワークフロー: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- ChatGPT定期ゲーム修正: ENABLED_AUTHOR_FIRST_INDEPENDENT_MERGE_AND_MAIN_QA_VERIFIED
- PvE: PROTOTYPE_OFFLINE_ONLY
- PvP: NOT_IMPLEMENTED
- 協力: NOT_IMPLEMENTED

## サイズゲート（初回基準との差分）
- ソース: 4 ファイル / 763 行 / 30428 bytes
- 基準差分: files 0, lines 100, bytes 4702
- サイズ増加は品質の証明ではない。合理的削減は問題ない。機能・テストの欠損は別途監査。

## キャラクター（見た目の実機検査ではない）
- ポン: 突破・設計図運搬 / antenna_round / prototype
- ガードン: 護衛・前線維持 / big_shield / prototype
- タンクル: 遠距離・拠点攻撃 / long_cannon / prototype

## 品質の実測範囲
- Studio: NOT_RUN
- マルチクライアント: NOT_RUN
- スマホ表示: NOT_RUN
- 記録済GitHub QA: PASS_OFFLINE_URL:https://github.com/kk051780/toy-wars-factory/actions/runs/40157791404（最新Actionsを別途確認すること）

## 次の開発優先事項
- First independent game PR #45 has merged with post-merge QA; record A08 and G07 progress as completed, keep A09/A13 pending until end-to-end recovery and repeated-cycle proof.
- Approval decisions are delegated to the assistant. Do not ask the owner to approve #35/#38/#40 again; all three are integrated with passing post-merge QA.
- Keep author, daily system review and independent integration tasks enabled. Authors create small tested drafts; the separate reviewer validates current head/base, CI, shared ownership and actual diffs, then integrates one at a time and checks main.
- Use docs/COMPLETION_ROADMAP.md and WORK_REQUESTS. Repair failing main/PRs first, then the smallest implementation advancing playable PvE and real-engine/mobile evidence.
- Daily review checks observed failures/effectiveness against current primary-web cases, proposes tested system improvements and concrete game experiments. Do not freeze the architecture or mistake tests/research for game fixes.
- Verify bootstrap and regular reviewer outcomes from service result/head/CI, not registration. Preserve objective engine/multiplayer/mobile/visual/fun and release evidence requirements.
- Use the explicit additional-module/installer/regression path when needed. Preserve accepted tests, initial source provenance, incident holds and financial caps.

## 委譲された承認判断
- 通常のゲーム/体制開発・main統合は助手が判断する。所有者への承認返信は不要。
- 作者と別タスクの審査役が現在headのCIと実差分を確認し、1件ずつ統合してmainを検査する。
- 完成ロードマップと日次の実測/最新WEB一次資料から次を選ぶ。客観的な品質条件・費用上限は免除しない。

## 手動goと自動実行の競合防止
- 手動goは既存ゲームタスクへ統一。実行中は追加起動せず確認へ合流する。
- 共通ロック: twf-repair-coordinator / ops/REPAIR_COORDINATOR.json。expected_sha・force=false・epochを必須にする。
- ゲーム修正・日次体制改善・独立審査・手動統合が同じロックを使う。docs/REPAIR_COORDINATION.mdを読む。

## 体制とゲームの日次改善
- タスク: 6add445e4138819197d9cf2b1a02534d / 毎朝（Asia/Tokyo）
- 実測の欠陥と最新WEB一次資料から、体制の最小修正・回帰検査・draft PR、ゲームの根拠付き実験候補を進める。
- 現在の方式を最適と固定せず、前後の結果と未解決点を記録する。docs/SYSTEM_REVIEW.mdを読む。

## 最新の再開地点（観測時点の記録）
- 記録: C00029 / 2026-10-25
- 照合したmain: c396e4aa28908a024c70cf54a572ed5db18f04dc
- 証拠: history/C00029_delegated_autonomous_integration.json
- 完了: Record explicit owner delegation of ordinary development/system/integration decisions; completion is prioritized over routine owner replies.
- 完了: Independently inspect actual diffs and exact-head CI, integrate #38 then #35 then #40 under the shared controller, and match each actual merged tree to its predicted tree.
- 完了: Verify post-merge QA/handoff for each candidate: #38 QA 40146924040, #35 QA 40147170649, #40 QA 40147278940. Any later current-main changes were proven generated status snapshots.
- 完了: Main now includes the three floor properties and the new accepted regressions: 4 Lua source files / 681 lines / 26,913 bytes. Preserve initial 25,726-byte baseline; #35/#40 are test-only, not two more source bug fixes.
- 完了: Register separate reviewer 6add4ea80d3881919da4ea2c1d5def88; update all saved/live prompts to delegate integration without owner replies. Authors retain draft-only source writes.
- 完了: Add delegated integration decisions and regressions for ownership/independent identity/current head and base/CI/scope/claim evidence/main failure/verified status-only descendants. All 128 Python tests pass.
- 完了: Add a revisable completion roadmap and guarded additional-module/installer/regression extension. Retain mandatory daily primary-web and effectiveness review.
- 完了: Separate read-only bootstrap run 8e81a8de-c59c-8332-83e0-d5f0c57f15c8 rejected the initial proposed head with two reproduced identity-validation gaps. Fix both and add two regressions; all 127 Python tests pass. Re-review the new head before deployment.
- 完了: Check the analogous main/QA SHA input boundary: reject missing or malformed identities, with a new regression. Current full suite: 128 tests.
- 新規推論承認: False
- 定期AI承認: True
- 自動マージ承認: True
- Roblox公開承認: False
- 再実行の前提: Standing assistant authority replaces per-PR owner replies. Require independent task/run review, exact-head CI, shared ownership and successful main QA. Objective quality and cost/incident controls remain.
- 再開する作業: Verify the separate read-only bootstrap review and deploy the quality-gated integration loop. Continue completion work without routine owner approval replies.
- 未確認・制限: Separate reviewer is registered; bootstrap and regular runtime require actual result evidence.
- 未確認・制限: Roblox engine/physics, multiplayer, mobile, character visuals and player experience remain unverified; release HOLD is evidence-based.
- 未確認・制限: Source bytes/PR/test counts are not a completion percentage; incident and cost controls remain.

## 未マージの提案（現在のPR状態はGitHubで再確認）
- PR #29: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Guard deferred workshop teleport against disconnect/respawn race / https://github.com/kk051780/toy-wars-factory/pull/29
  - QA: PASS_OFFLINE_CI; prior gameplay checks are mostly static. Studio, multiplayer and mobile NOT_RUN. https://github.com/kk051780/toy-wars-factory/actions/runs/40096885886
- PR #28: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Main-based offline integration QA: selector authority + workshop backfill (no merge) / https://github.com/kk051780/toy-wars-factory/pull/28
  - QA: PASS_OFFLINE_CI; prior gameplay checks are mostly static. Studio, multiplayer and mobile NOT_RUN. https://github.com/kk051780/toy-wars-factory/actions/runs/40088574401
- PR #25: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Integration QA: selector authority plus workshop backfill (no merge) / https://github.com/kk051780/toy-wars-factory/pull/25
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40076928524
- PR #24: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Hold Gemini activation and remove the unreserved reviewer transport / https://github.com/kk051780/toy-wars-factory/pull/24
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40075974239
- PR #23: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Tighten request output reservations and record the unresolved input proof / https://github.com/kk051780/toy-wars-factory/pull/23
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40074151010
- PR #22: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Connect offline Gemini price bounds to a persistent shared budget runtime / https://github.com/kk051780/toy-wars-factory/pull/22
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40072355807
- PR #21: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Reject unpriced native Gemini requests and test reserved call budgets / https://github.com/kk051780/toy-wars-factory/pull/21
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40069599840
- PR #20: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Admit waiting players when a workshop plot becomes free / https://github.com/kk051780/toy-wars-factory/pull/20
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40069151903
- PR #19: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Fix shallow-history handoff churn and retain Gemini failure provenance / https://github.com/kk051780/toy-wars-factory/pull/19
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40067722798
- PR #17: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Reject spoofed distant toy-selector prompt activation on server / https://github.com/kk051780/toy-wars-factory/pull/17
  - QA: PASS_OFFLINE_CI; inspect linked run for exact scope. No Roblox engine or new live inference evidence. https://github.com/kk051780/toy-wars-factory/actions/runs/40061153081
- PR #13: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Keep toy HUD prices in sync with canonical balance costs / https://github.com/kk051780/toy-wars-factory/pull/13
- PR #12: DRAFT_UNMERGED / PROPOSAL / Cut idle QA runner usage ~94% while preserving every-change checks / https://github.com/kk051780/toy-wars-factory/pull/12
- PR #6: DRAFT_UNMERGED / PROPOSAL / Prepare audited 20-minute AI coding runner — authentication approval required / https://github.com/kk051780/toy-wars-factory/pull/6
- mainの実装と未マージPRの提案を合算しない。Geminiの成果と別の修正を区別する。

## 新しいチャットでAIが必ず行う引き継ぎ手順
1. GitHubコネクタでこのファイルと status/LATEST_STATE.json、PROJECT_STATE.json、AGENTS.md、config/quality_policy.json を読み込む。
2. 最新 main、Actions実行結果、PR、Issuesを直接確認し、生成ファイルのsource_revisionと整合させる。
3. 正本はGitHub。毎回コード変更と品質証拠、サイズ差分、キャラクター監査、再発防止を積み上げる。
4. 無人AIコード生成・Studio試験・面白さの実測を根拠なしに合格扱いしない。
5. プレイヤー向け公開・課金・権限拡張・品質基準緩和にはユーザー承認が必要。

## ユーザー操作
同じChatGPTプロジェクトの新しいチャットで『TOY WARS再開』と送れば、AIはGitHubへアクセスして続きから着手する。
ただし別チャットへの無条件の自動コンテキスト注入はプラットフォーム上保証されない。
無人作業はGitHub側の認証済みエージェント・ワークフローが実際に稼働してから可能。
