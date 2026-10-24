# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: f5088816ba5c8247016f9fecf8f025270471448f
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 自律AI開発: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- PvE: PROTOTYPE_OFFLINE_ONLY
- PvP: NOT_IMPLEMENTED
- 協力: NOT_IMPLEMENTED

## サイズゲート（初回基準との差分）
- ソース: 4 ファイル / 678 行 / 26753 bytes
- 基準差分: files 0, lines 15, bytes 1027
- サイズ増加は品質の証明ではない。合理的削減は問題ない。機能・テストの欠損は別途監査。

## キャラクター（見た目の実機検査ではない）
- ポン: 突破・設計図運搬 / antenna_round / prototype
- ガードン: 護衛・前線維持 / big_shield / prototype
- タンクル: 遠距離・拠点攻撃 / long_cannon / prototype

## 品質の実測範囲
- Studio: NOT_RUN
- マルチクライアント: NOT_RUN
- スマホ表示: NOT_RUN
- 記録済GitHub QA: PASS_OFFLINE_URL:https://github.com/kk051780/toy-wars-factory/actions/runs/40106001876（最新Actionsを別途確認すること）

## 次の開発優先事項
- PR #32 is merged at 83465372f6701e20cd92ec7f9e8bd48f945c8da4 and main QA/handoff passed. PR #30/#31 are also complete. Do not request the same integration approvals again.
- Read C00016 and docs/AUTOMATION_READINESS.md. Current main source is four Lua files / 678 lines / 26,753 bytes; tracked_metrics retains the original baseline.
- Prioritize a reviewable offline design for bounded AI development and independent review, using new evidence or a different bounded path. Current model, 10-AIC cap and all holds remain unchanged.
- A calendar completion date is not established while the complete request bound/shared enforcement remain unproved. The proposed 24-48 hour observation allowance applies only after an approved bounded trial succeeds; no monitoring or recurring activation has started.
- Keep original source proposals #13/#17/#20/#25/#28/#29 intact. Their reviewed gameplay changes are already integrated through #30/#32; do not merge them again to apply the same source.
- Keep consumed trial approval, inactive recurring AI, no future automatic merge and Roblox release HOLD. Real Studio, multiplayer, mobile, visuals and player feedback remain unverified.

## 最新の再開地点（観測時点の記録）
- 記録: C00016 / 2026-10-25
- 照合したmain: 83465372f6701e20cd92ec7f9e8bd48f945c8da4
- 証拠: history/C00016_approved_hud_merge.json
- 完了: Owner explicitly approved the concrete PR #32 integration with 進めて。; approval of PR #30 was not reused.
- 完了: Recheck unchanged head e2cdbb8ddf6efc084031e4900ce754e73f336cbf, clean mergeability, all nine reviewed file blobs and successful pre-merge CI 40103243365.
- 完了: Merge PR #32 at 83465372f6701e20cd92ec7f9e8bd48f945c8da4 using the reviewed head lease; merged tree 5f8fa106da6cc3b495df718bcde66614e1b8e192 equals review.
- 完了: Verify post-merge main QA 40106001876 and handoff 40106001904 both pass on the merge SHA.
- 完了: Verify whole-HUD fixtures: original current-price case passes and exactly five varied-price cases fail; canonical fixed HUD passes all six. All 27 server fixtures, 53 Python tests, balance/stress, compiler, installer and handoff checks also pass.
- 完了: Record actual main source: four Lua files / 678 lines / 26,753 bytes; PR #32 adds 194 bytes and two lines only in HUD, preserving original baseline and all prior history.
- 完了: Read actual audit/handoff and candidate AI workflow sources. Existing schedules perform audits/handoff, while Gemini activation and reviewer remain held; no successful autonomous coding trial or recurring AI is established.
- 完了: Record automation readiness and the unresolved ETA without presenting gameplay fixes as resolution of the financial bound. A proposed 24-48 hour observation period is conditional on a future approved successful bounded trial, not a completion date or scheduled activation.
- 完了: Preserve the original PR #13 and other source proposals, and record the completed merge so future chats do not repeat its approval.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: PR #32 is already merged and post-merge QA/handoff passed; do not ask for its merge approval again. The automation timing question is not authorization to call a provider, change model/cap/billing, enable recurring AI, automatically merge future code or publish Roblox.
- 再開する作業: Prioritize an offline automation design review that can establish the approved financial bound for both developer and independent reviewer. Produce a concrete reviewable proposal using new attributable evidence or a different bounded execution path; do not repeat the same pinned SDK inspection as progress. PR #32/#30 and their factual integrations are complete. Keep all inference and recurring execution held pending established bounds and fresh scoped owner authorization.
- 未確認・制限: HUD fixtures validate text and callbacks in native Lua, not rendering, touch, replication, Studio, real multiplayer or mobile behavior. Runtime balance hot-reloading is not implemented.
- 未確認・制限: Gemini complete input/framing bounds and shared live financial enforcement remain unproved; developer and independent reviewer are blocked, and the consumed trial must not be rerun.
- 未確認・制限: An offline QA/handoff schedule does not establish unattended AI development. Continuous AI operation has not begun.
- 未確認・制限: The 24-48 hour observation allowance is a planning suggestion after prerequisites, not a started test, completion commitment or change to release policy.
- 未確認・制限: Automatic merge and Roblox publication are not authorized; Studio, multiplayer, mobile visuals and player feedback remain unverified.

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
