# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: b337fe8377cac153d2bb2bf5f957ea2f2f75c149
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
- Read docs/GEMINI_OPERATIONAL_HOLD.md and C00008; the reviewer direct transport is removed and a literal false workflow condition is proposed.
- Verify the pinned official compiler reproduces the checked-in hold and all offline CI checks pass; a static assertion alone is not compilation evidence.
- All proposals are DRAFT_UNMERGED; main has not deployed the new hold or budget candidates. Do not rerun historical workflow snapshots.
- Request-specific input/framing proof from PR #23 remains BLOCKED. The current 2048-output reservation is still 79.4112 modeled AIC using the full model input ceiling.
- Require independently established complete input/framing bounds, shared enforcement for both roles, current pricing/quota and fresh owner inference consent before reopening.
- Keep the 10-AIC cap, consumed approval markers, independent-review gate, inactive recurring AI, no automatic merge and no Roblox publication.

## 最新の再開地点（観測時点の記録）
- 記録: C00008 / 2026-10-24
- 照合したmain: e62bddc469e5edfbc97c2ccd67e9ae05ff8e5904
- 証拠: history/C00008_operational_hold.json
- 完了: Read canonical main, current drafts, latest Actions and open issues; PR #23 QA 40074151010 passed and main is unchanged.
- 完了: Reproduce latent reviewer budget bypass with one injected synthetic dispatch and zero real provider calls.
- 完了: Remove direct reviewer HTTP transport and block --online before patch/credential access or transport selection.
- 完了: Add literal-false source/compiled pre-activation hold; marker edits and environment flags cannot release it.
- 完了: Invalidate stale safe verdict artifacts on every scanner CLI attempt, including offline and blocked attempts.
- 完了: Pass all 43 Python tests, including 10 new operational hold regressions; retain pure verdict-schema tests.
- 完了: Add pinned official compiler regeneration and exact lock comparison to offline CI; verify result before claiming CI success.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Reopening needs independently established complete input/framing bound, shared live enforcement, current pricing/quota, fresh owner inference consent and separately reviewed code changes.
- 再開する作業: Confirm pinned compiler regeneration and all offline CI checks. Review the draft operational stop alongside the existing handoff/budget proposals. Keep inference blocked until the independent input/framing proof and shared live enforcement are established; do not substitute estimates or reuse approval markers.
- 未確認・制限: All changes remain unmerged drafts; canonical main still has the previous incident state.
- 未確認・制限: The literal hold is an operational stop, not proof of a request-specific input bound or financial cap.
- 未確認・制限: The real developer/reviewer clients remain disabled and no Gemini key was read.
- 未確認・制限: Historical workflow snapshots are not retrofitted; never rerun the consumed trial.
- 未確認・制限: Studio, multiplayer and mobile remain NOT_RUN.

## 未マージの提案（現在のPR状態はGitHubで再確認）
- PR #23: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Tighten output reservations; reproduce unresolved request input proof / https://github.com/kk051780/toy-wars-factory/pull/23
  - QA: 64 Node (24 network-disabled container), 33 Python, 37 Lua + 4000 stress, official SDK inspection and deterministic handoff PASS. Input proof remains BLOCKED; no live calls. https://github.com/kk051780/toy-wars-factory/actions/runs/40074151010
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
