# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 398da14631c9f1540cc5f8ab6778c2fb83002e69
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
- 記録済GitHub QA: PENDING_HUD_CANDIDATE_CI; current main PASS https://github.com/kk051780/toy-wars-factory/actions/runs/40102403182（最新Actionsを別途確認すること）

## 次の開発優先事項
- Read C00015 and the main-based HUD pricing candidate. PR #30/#31 integration and C00014 are already complete; do not repeat their merge approval.
- Require the exact old-HUD negative control (one current-price pass and five expected varied-price failures), all six fixed-HUD fixtures and all existing offline QA to pass.
- Review the concrete candidate against current main and ask the owner for its own merge approval; main retains the original HUD until then. Original PR #13 remains preserved.
- Keep source proposals #17/#20/#25/#28/#29 intact; their gameplay changes are already integrated through #30.
- Keep Studio, multiplayer, mobile visuals and player feedback unverified, and release on HOLD. These HUD fixtures are native substitutes, not UI screenshots or engine evidence.
- Keep Gemini held, the 10-AIC cap and independent review requirements unchanged; no recurring AI, automatic merge or Roblox publication.

## 最新の再開地点（観測時点の記録）
- 記録: C00015 / 2026-10-24
- 照合したmain: b4e6901f5880102eb55bd20490eab8c049f2cbc6
- 証拠: history/C00015_hud_shared_pricing.json
- 完了: Read C00014, confirm current main b4e6901f5880102eb55bd20490eab8c049f2cbc6 and successful main QA 40102403182 / handoff 40102403217; PR #30/#31 remain merged.
- 完了: Review existing PR #13 at 87ff9b2f4b5403632ea126b0b691ee31b2c36a62. Current 10/28/48 labels match balance but duplicate its purchase costs.
- 完了: Execute the complete original HUD against the real balance.buy function with varied in-memory costs: current-price fixture passes and exactly five price-change fixtures fail.
- 完了: Reuse the exact PR #13 HUD blob 0dcd1f1f16991b3f02b970361eea9f026d1e8688 on current main; all six native HUD price fixtures pass.
- 完了: Confirm all three selectable IDs and one-argument remote selection payloads survive each fixture; no client price is sent.
- 完了: Extend exact history byte accounting from server-only changes to all four original Lua files without changing their initial baseline or old history.
- 完了: Require exact immutable old-HUD failure evidence and successful canonical HUD fixtures in existing offline CI, retaining all prior gates and Gemini stops.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: PR #30 approval covered its completed gameplay integration and factual C00014 record. This separate HUD candidate needs explicit owner merge approval after its concrete diff and CI are reviewable. No inference, recurring AI, billing or Roblox publication approval is implied.
- 再開する作業: Verify the main-based HUD candidate CI and exact before/after fixture evidence, then request explicit owner approval for this concrete candidate to enter main. PR #30/#31 are already merged and must not need approval again. Keep the original #13 and other source drafts intact, Gemini held and Roblox release on HOLD.
- 未確認・制限: Main still has the original HUD until this separate candidate is approved; current main game source is 26,559 bytes, candidate source is 26,753 bytes.
- 未確認・制限: Current literal HUD prices already match current balance; the reproduced defect is stale labels after a balance edit.
- 未確認・制限: Native Lua UI/value/signal substitutes do not verify Roblox rendering, touch, replication, Studio, multiplayer or mobile layout.
- 未確認・制限: Prices are read at HUD initialization; runtime balance hot-reloading is not implemented.
- 未確認・制限: Gemini input/framing bounds and a hard financial cap remain unproved; the consumed trial must not be rerun.

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
