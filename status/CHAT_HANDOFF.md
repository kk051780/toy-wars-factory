# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 5de8c39ebfc95e67e649ba4b418b9b8dad29d39e
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 自律AI開発: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- PvE: PROTOTYPE_OFFLINE_ONLY
- PvP: NOT_IMPLEMENTED
- 協力: NOT_IMPLEMENTED

## サイズゲート（初回基準との差分）
- ソース: 4 ファイル / 676 行 / 26559 bytes
- 基準差分: files 0, lines 13, bytes 833
- サイズ増加は品質の証明ではない。合理的削減は問題ない。機能・テストの欠損は別途監査。

## キャラクター（見た目の実機検査ではない）
- ポン: 突破・設計図運搬 / antenna_round / prototype
- ガードン: 護衛・前線維持 / big_shield / prototype
- タンクル: 遠距離・拠点攻撃 / long_cannon / prototype

## 品質の実測範囲
- Studio: NOT_RUN
- マルチクライアント: NOT_RUN
- スマホ表示: NOT_RUN
- 記録済GitHub QA: PASS_OFFLINE_URL:https://github.com/kk051780/toy-wars-factory/actions/runs/40102033728（最新Actionsを別途確認すること）

## 次の開発優先事項
- PR #30 is merged at 1e29505f62192597de6019f97a8b87447b1998e8 and post-merge main QA/handoff passed. Do not ask again to merge it. PR #26/#27 stop integration is also complete.
- Read C00014 and resolve current main/Actions. Current game source is four Lua files / 676 lines / 26,559 bytes; tracked_metrics retains the original baseline.
- Review the separate HUD pricing proposal #13 against the integrated main and canonical balance. Any new implementation must have offline evidence and a reviewable branch; no unrelated merge is approved.
- Keep source proposals #17/#20/#25/#28/#29 open as historical review branches; their gameplay changes are already integrated through #30, so do not merge them again to apply the same changes.
- Roblox Studio, multiplayer, mobile, visuals and player feedback remain required before release; native event fixtures do not supply those results.
- Keep Gemini held, the 10-AIC cap and independent review requirements unchanged. Revisit missing input/framing proof only with changed sources or new attributable evidence; no recurring AI, automatic merge or Roblox publication.

## 最新の再開地点（観測時点の記録）
- 記録: C00014 / 2026-10-24
- 照合したmain: 1e29505f62192597de6019f97a8b87447b1998e8
- 証拠: history/C00014_approved_game_merge.json
- 完了: Owner explicitly approved the concrete PR #30 main integration with 進めて; the previous PR #26 stop approval was not reused.
- 完了: Recheck unchanged head 4366658aa9c71ec30e49476897fbd41f84b1d47c, clean mergeability, all 15 reviewed file blobs and successful pre-merge CI 40099984529.
- 完了: Merge PR #30 at 1e29505f62192597de6019f97a8b87447b1998e8 using the reviewed head SHA lease; merged tree c79c1e149ad68a8a21604c9aa3c8151e64427937 equals the reviewed tree.
- 完了: Verify post-merge main QA 40102033728 and handoff 40102033772 both pass on the merge SHA, including 27 event fixtures, 53 Python tests, exact compiler and installer checks.
- 完了: Verify the immutable pre-fix server passes 25 fixtures and fails exactly the two NaN fixtures; the canonical fixed server passes all 27. These are native mocks, not Roblox engine evidence.
- 完了: Record the actual integrated game metrics: four Lua files, 676 lines and 26,559 bytes; +13 lines/+833 bytes against the original main game source. Original baseline and C00011-C00013 remain unchanged.
- 完了: Preserve literal-false Gemini activation, removed reviewer provider transport, consumed one-shot approval, inactive recurring AI and Roblox release hold; no provider calls or credential reads.
- 完了: Record completion in canonical project state and regenerated handoff so the next chat resumes after the merged work instead of requesting the same approval.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: PR #30 is already merged and post-merge QA/handoff passed. Do not request its merge approval again. This specific approval does not authorize future unrelated merges, inference, recurring AI, billing or Roblox publication.
- 再開する作業: PR #30 integration is complete. Read C00014, resolve current main and check Actions before new work. Review the separate HUD pricing proposal #13 against the integrated server and current balance, with offline evidence and a reviewable draft if changes are needed. Preserve source drafts and all operational/quality guards; no further merge or provider inference approval is implied.
- 未確認・制限: Native service/event/coroutine substitutes test callback logic only; Roblox Studio, physics, replication, real multiplayer, mobile visuals and player fun remain unverified.
- 未確認・制限: NaN was a synthetic invalid-coordinate fixture; no real client injection exploit was demonstrated.
- 未確認・制限: Complete Gemini input/framing bounds and a hard financial cap remain unproved; provider inference stays blocked and the consumed trial must not be rerun.
- 未確認・制限: Related source PRs #17/#20/#25/#28/#29 remain open as preserved proposals; their reviewed gameplay changes are integrated via PR #30. Experimental budget/runtime proposals remain unmerged.

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
