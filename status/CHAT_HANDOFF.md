# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 8074962057fbe9c564725fd59327e6b0dec240c9
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
- Review docs/INCIDENT_TWF_0006.md and history/C00004_gemini_credit_audit.json: the native-model pricing gap is reproduced offline, not fixed in the deployed runtime.
- Validate native URL model resolution, fail-closed pricing admission and a bounded local-server credit regression in a separate reviewed runtime correction; do not call a provider.
- Confirm authoritative provider quotas/billing and obtain fresh owner approval before any new Gemini inference; the consumed marker must not be reused.
- Preserve fail-closed independent security review; do not convert missing patches or failed runs into SAFE.
- PR #17 is a separate offline-tested chat-assistant proposal, draft/unmerged; do not credit Gemini with it or merge automatically.
- Keep the 20-minute AI schedule inactive; QA/audit schedules are distinct. Budget-saving PR #12 remains unmerged.
- Actual Roblox Studio/mobile/multiplayer verification is still required before release.

## 最新の再開地点（観測時点の記録）
- 記録: C00004 / 2026-10-24
- 照合したmain: e62bddc469e5edfbc97c2ccd67e9ae05ff8e5904
- 証拠: history/C00004_gemini_credit_audit.json
- 完了: Read canonical handoff/state/policy and inspect current main, Actions, draft PRs and open issues.
- 完了: Confirm Gemini run 40060119253 failed on attempt 1, produced no safe-output PR and was not rerun.
- 完了: Confirm PR #17 was authored through the chat assistant separately from Gemini and remains draft/unmerged.
- 完了: Reproduce an unpriced native Gemini request bypassing model-price rejection and accumulating zero internal AIC in tagged upstream modules, without provider calls.
- 完了: Trace repeated snapshot-only source_revision advancement to depth-1 CI checkouts; add full-history checkout and fail closed on shallow history.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Fresh owner authorization AND independently validated enforcement before a new Gemini run.
- 再開する作業: Review the offline credit-audit/continuity proposal; prepare a priceable native-model admission fix and bounded local-server regression before requesting a new inference run.
- 未確認・制限: Reported AIC is not a verified bill.
- 未確認・制限: Tagged source reproduction is not an attestation of every deployed container byte.
- 未確認・制限: Runtime correction and provider-side spending control remain unverified.
- 未確認・制限: Roblox Studio, multiplayer and mobile remain NOT_RUN.

## 未マージの提案（現在のPR状態はGitHubで再確認）
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
