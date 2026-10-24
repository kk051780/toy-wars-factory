# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: c111784330e71bf49d61f2cee2813a1a12e49734
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 既存GitHub AIワークフロー: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- ChatGPT定期ゲーム修正: ENABLED_FIRST_AUTOMATED_REGRESSION_PR_VERIFIED
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
- 記録済GitHub QA: PASS_OFFLINE_URL:https://github.com/kk051780/toy-wars-factory/actions/runs/40108475671（最新Actionsを別途確認すること）

## 次の開発優先事項
- PR #34 setup is merged at 40c79ae0f06d472ed5a1184d5c27d9421afee3c0; main QA 40108475671 and handoff 40108475650 pass. Do not ask for setup integration again.
- Hourly ChatGPT task 6adbf0d6a7d881918ce181dff2468867 is enabled. Routine game edits/tests/draft PR updates are authorized without another 進めて.
- Initial service run 9fd5c391-5054-832e-b21b-9527e78d6733 completed and actually created draft PR #35, head 116ab1fd56d736d10994008dfcdabaccd76afce9. CI 40108773948 passed, including all three new whole-server production regressions and trusted-base scope checks.
- First run added executable regression code only; game source and all 75 existing files were preserved. Do not claim it fixed a gameplay bug or proved continuous operation.
- Continue with the same auto/twf-game-repair draft branch: read actual CI, preserve successful work, choose the next bounded defect/regression. Do not recreate the completed initial production test.
- Keep Gemini/external API, keys, model/cap/billing and future automatic main merge/Roblox publication held. First task delivery is unknown; recorded completion and actual GitHub code/CI are the proof.

## 最新の再開地点（観測時点の記録）
- 記録: C00019 / 2026-10-25
- 照合したmain: 40c79ae0f06d472ed5a1184d5c27d9421afee3c0
- 証拠: history/C00019_chatgpt_repair_activation.json
- 完了: Complete the owner-requested repository setup by merging PR #34 at 40c79ae0f06d472ed5a1184d5c27d9421afee3c0 using reviewed head 829d25515f75479ec606edda8fbbab64db476fd5.
- 完了: Confirm exact reviewed tree 7a0655b4b61dfef30c466768ae3d086889ccf3fa, all 13 reviewed setup blobs, 62 untouched blob/mode matches and all four unchanged game sources.
- 完了: Verify setup post-merge QA 40108475671 and handoff 40108475650 both pass, including 61 Python tests, all legacy native controls, compiler and installer checks.
- 完了: Read the new enabled config on the actual main merge, then request a single real automation validation run. The service confirmed acceptance without changing the existing hourly schedule.
- 完了: Verify the service run completed at 2026-10-24T15:50:27.202124Z; latest_result run_id matches the requested run and was created after its start. No delivery claim is made.
- 完了: Independently fetch actual draft PR #35, its two changed files, head 116ab1fd56d736d10994008dfcdabaccd76afce9 and tree bd98f2e95c0dad162c25fa4f795f3d7cd556858a; all 75 pre-existing files/modes remain identical.
- 完了: Verify exact-head CI 40108773948 passes. The trusted-base path gate ran successfully, all three AUTO_PRODUCTION regressions passed, and all prior QA remained successful.
- 完了: Record first_run_verified for this narrow code-producing regression PR trial. No gameplay defect was fixed, no game source was changed and no automatic main merge was performed.
- 完了: Clarify the saved task prompt: accepted main regressions/history stay protected, while defects in the task own unmerged additions can be repaired on the same draft PR without weakening assertions.
- 新規推論承認: False
- 定期AI承認: True
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Routine connected-GitHub edits/tests/draft PRs no longer wait for another 進めて. Main integration of future game fixes, external provider inference and Roblox publication still require their existing approvals. Validate the registered task by its service run, actual code PR and matching CI, not registration alone.
- 再開する作業: Continue the hourly task without routine user prompts. PR #35 CI passed; preserve its work and choose the next bounded defect or meaningful regression on the same draft branch. Main integration and release still require their existing approvals.
- 未確認・制限: One scheduled service execution and matching regression-code PR/CI are verified; repeated long-term operation is not yet proven.
- 未確認・制限: The first automatic change is three production/purchase regressions, not a reproduced gameplay-source bug fix.
- 未確認・制限: PR #35 remains draft/unmerged. Routine development continues without a user prompt, while main integration, independent review and Roblox publication conditions remain unchanged.
- 未確認・制限: Recorded notification delivery is unknown. Completion, actual code files and exact-head successful CI provide the evidence.
- 未確認・制限: Gemini/external provider API and financial-bound blockers remain held; no model/cap/billing or credential changes.

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
