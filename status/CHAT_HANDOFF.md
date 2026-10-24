# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: c763ae8be63d5bbecc51e36eda3a8f391fdba9a6
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
- Review docs/GEMINI_BUDGET_RUNTIME_CANDIDATE.md and C00005: native admission correction and reservation runner pass offline tests; neither is deployed.
- Connect a trusted request upper-bound adapter, verified per-model prices and a single-attempt transport in an offline candidate runtime; include CLI and independent reviewer in the same budget.
- Ensure shared/persistent budget across all workers and processes; the current candidate ledger is in-memory.
- Validate a real candidate container without a provider key, then verify authoritative provider quotas/billing.
- Obtain fresh owner authorization before any new inference; never reuse the consumed one-shot marker.
- Keep PR #19 and this follow-up reviewable and unmerged; PR #17 is a separate chat-assistant game proposal.
- Do not activate recurring AI, automatically merge, or publish Roblox; engine/mobile/multiplayer remain unverified.

## 最新の再開地点（観測時点の記録）
- 記録: C00005 / 2026-10-24
- 照合したmain: e62bddc469e5edfbc97c2ccd67e9ae05ff8e5904
- 証拠: history/C00005_native_gemini_admission.json
- 完了: Re-read canonical main, PR #19 and current Actions/issues before continuing.
- 完了: Implement hash-pinned native Gemini admission overlay: URL model identification, mismatch and unpriced-model rejection; preserve original common guards.
- 完了: Implement a candidate exact-integer reservation ledger with concurrent admission, terminal request limits and no retry/refund for uncertain charges.
- 完了: Pass 40 Node regressions, including original upstream pricing/common-guard code and real loopback HTTP.
- 完了: Keep all model invocations, recurring AI, automatic merging and Roblox publication inactive.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Verified runtime integration, shared request/price bounds, authoritative provider quota and fresh owner approval before new inference.
- 再開する作業: Review this candidate; integrate a trusted token-bound adapter and approved prices with all model transports in an offline candidate container, then verify provider quotas before seeking fresh inference approval.
- 未確認・制限: Candidate only: no runtime image installed or deployed.
- 未確認・制限: Overlay hooks native admission only; reservation runner is not connected to the Gemini CLI.
- 未確認・制限: Real prices, trusted token upper-bound adapter, cross-process/shared budget and independent-review accounting are not configured.
- 未確認・制限: Loopback fixture costs do not certify a real provider bill or financial ceiling.
- 未確認・制限: Studio, multiplayer and mobile remain NOT_RUN.

## 未マージの提案（現在のPR状態はGitHubで再確認）
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
