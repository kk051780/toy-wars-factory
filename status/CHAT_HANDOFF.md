# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 47770033da4e78b55a43b8e5fa7a3977e134ca68
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 自律AI開発: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- PvE: PROTOTYPE_OFFLINE_ONLY
- PvP: NOT_IMPLEMENTED
- 協力: NOT_IMPLEMENTED

## サイズゲート（初回基準との差分）
- ソース: 4 ファイル / 663 行 / 25726 bytes
- 基準差分: files 0, lines 0, bytes 0
- サイズ増加は品質の証明ではない。合理的削減は問題ない。機能・テストの欠損は別途監査。

## キャラクター（見た目の実機検査ではない）
- ポン: 突破・設計図運搬 / antenna_round / prototype
- ガードン: 護衛・前線維持 / big_shield / prototype
- タンクル: 遠距離・拠点攻撃 / long_cannon / prototype

## 品質の実測範囲
- Studio: NOT_RUN
- マルチクライアント: NOT_RUN
- スマホ表示: NOT_RUN
- 記録済GitHub QA: PASS_OFFLINE_URL:https://github.com/kk051780/toy-wars-factory/actions/runs/40064857413（最新Actionsを別途確認すること）

## 次の開発優先事項
- Read docs/GEMINI_REQUEST_BOUND_RESULT.md and C00007: request-specific output bound is implemented; a smaller complete input bound remains unproved.
- Do not declare live readiness from passing offline/container tests. Current 2048-output reservation remains 79.4112 modeled AIC using the full model input ceiling.
- A fresh 10-AIC budget would require input independently bounded to <=123093 tokens for 2048 charged output tokens; the diagnostic does not certify this input count.
- Require attributable provider input/framing bounds or an independently validated exact path before revisiting inference. The inspected official SDK 2.33.0 lacks a Gemini 3.8 local lookup.
- Keep estimates, tokenizer aliases, character/byte ratios and arbitrary margins out of admission decisions; do not change the cap or model automatically.
- Fresh owner inference approval and verified quota/pricing are still required after technical prerequisites hold. Keep recurring AI, automatic merge and Roblox publication inactive.

## 最新の再開地点（観測時点の記録）
- 記録: C00007 / 2026-10-24
- 照合したmain: e62bddc469e5edfbc97c2ccd67e9ae05ff8e5904
- 証拠: history/C00007_request_bound_proof.json
- 完了: Read canonical main, current drafts and completed QA before continuing from PR #22.
- 完了: Verify native GenerateContent output cutoff includes thinking; reserve only the explicit request output limit.
- 完了: Inspect exact official Python SDK 2.33.0 model lookup without importing SDK dependencies, downloading vocabularies or calling a provider.
- 完了: Confirm the checked SDK cannot map Gemini 3.8 Flash to a local tokenizer; positive controls verify lookup inspection.
- 完了: Calculate exact remaining-budget proof requirements: 2048 output tokens would require input independently bounded to <=123093 tokens under a fresh 10-AIC cap.
- 完了: Pass 64 Node and 33 Python tests locally, retaining blocked admission and all prior guards.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Input/framing bound must be independently established, pricing/quota rechecked and fresh owner inference authorization obtained. A mock pass or estimate is not approval.
- 再開する作業: Treat the missing request-specific input bound as a real blocker. Resume only when an attributable provider bound or independently validated exact model/framing path is available; never substitute an estimate or promise another routine step will enable inference.
- 未確認・制限: Only the request output bound was tightened; the input side still uses the full documented model ceiling.
- 未確認・制限: The required input ceiling is arithmetic for a missing proof, not a measured or certified input count.
- 未確認・制限: Local-tokenizer support findings apply to the exact inspected SDK commit; they are not an impossibility proof for all future mechanisms.
- 未確認・制限: No live CLI/reviewer routing, provider transport, credential read or inference was enabled.
- 未確認・制限: All implementation remains in unmerged drafts; Studio, multiplayer and mobile remain NOT_RUN.

## 未マージの提案（現在のPR状態はGitHubで再確認）
- PR #22: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Connect offline profile, model-ceiling adapter and persistent shared ledger / https://github.com/kk051780/toy-wars-factory/pull/22
  - QA: 40 existing Node + 19 connected container tests, 33 Python, 37 Lua and 4000 stress checks PASS. No live inference. https://github.com/kk051780/toy-wars-factory/actions/runs/40072355807
- PR #21: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Native admission correction and reservation-runner candidate / https://github.com/kk051780/toy-wars-factory/pull/21
  - QA: 40 Node, 33 Python, 37 Lua, 4000 stress checks PASS; offline candidate only. https://github.com/kk051780/toy-wars-factory/actions/runs/40069599840
- PR #19: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Fix shallow-history handoff churn and retain incident provenance / https://github.com/kk051780/toy-wars-factory/pull/19
  - QA: PASS: 33 Python, 37 Lua regressions, 4000 deterministic stress, exact installer and deterministic handoff. Offline only. https://github.com/kk051780/toy-wars-factory/actions/runs/40067722798
- PR #17: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Server-side distance validation for toy-selector prompts / https://github.com/kk051780/toy-wars-factory/pull/17
  - QA: Offline: 37 Lua regressions, 4000 stress cases, 33 Python tests; no Roblox engine verification. https://github.com/kk051780/toy-wars-factory/actions/runs/40061153081
- PR #13: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / HUD prices follow canonical balance / https://github.com/kk051780/toy-wars-factory/pull/13
- PR #12: DRAFT_UNMERGED / PROPOSAL / Reduce idle QA frequency; current schedules are unchanged / https://github.com/kk051780/toy-wars-factory/pull/12
- PR #6: DRAFT_UNMERGED_DO_NOT_ACTIVATE / PROPOSAL / Recurring AI candidate; no recurring execution authorized / https://github.com/kk051780/toy-wars-factory/pull/6
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
