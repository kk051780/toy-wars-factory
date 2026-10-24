# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 6490802297a91a764b786f4515f0c1200e2ef763
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 既存GitHub AIワークフロー: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- ChatGPT定期ゲーム修正: ENABLED_QUEUE_V2_DEPLOYMENT_PENDING
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
- Read C00023 and the actual automation service state. C00019 enabled-state observation became stale: the worker later paused itself for PR #35 review wait. This incident is now documented.
- Deploy queue v2 and verify the resumed task produces a new independent source-fix PR while preserving successful PR #35. Do not merge PR #35 or other game proposals without their existing authorization.
- Use the three-PR queue and tools/repair_queue.py. Never let a scheduled worker modify/disable its task. When full, wait and recheck rather than asking for another routine 進めて.
- Prioritize the reproduced walkable-floor collision property defect. Require whole-server regression evidence, exact source-size history and unchanged decorative/character behavior.
- Keep independent review, no automatic main merge, Gemini/external API holds, original 10-AIC cap and Roblox release HOLD. Native attributes do not prove real physics or playability.

## 最新の再開地点（観測時点の記録）
- 記録: C00023 / 2026-10-25
- 照合したmain: 0e66049e95bc555bfb2a12aeafe46e73ea420c90
- 証拠: history/C00023_queue_continuity_setup.json
- 完了: Read actual task state and matched latest service result: task was disabled after run c7058bdc-64e4-8332-95ba-06037acb5d28 reported self-pausing for PR #35 integration wait.
- 完了: Confirm PR #35 evolved to seven added files, six commits and successful exact-head CI 40114787373 after repairing its own wave-fixture mistakes. Preserve that review-ready work.
- 完了: Implement a bounded queue: failed CI first, pending CI wait, successful PRs preserved, fresh main-based UUID branch if under three open PRs, full queue waits without scheduler changes.
- 完了: Add branch namespace validation for both legacy and UUID lanes and apply the existing trusted-base scope check to the full repair namespace. No path permissions or QA gates are removed.
- 完了: Resume the existing hourly task with explicit prohibition of self-disabling or scheduler changes. The new prompt waits for queue_version>=2 on main before edits.
- 完了: Execute whole-server native baseline property probe: FeltBattlefield, FactoryFloor and LobbyGround all have CanCollide=false. Prepare this concrete source defect for the next automatic repair trial; no physics/Studio claim.
- 完了: Keep all four game sources unchanged in this controller setup; exact source baseline/history and all model/cap/credential/release holds are preserved.
- 新規推論承認: False
- 定期AI承認: True
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Routine connected-GitHub edits/tests/draft PRs no longer wait for another 進めて. Main integration of future game fixes, external provider inference and Roblox publication still require their existing approvals. Validate the registered task by its service run, actual code PR and matching CI, not registration alone.
- 再開する作業: Deploy queue v2, then validate one real automatic game-source fix on a new UUID branch while PR #35 remains review-ready. Verify the task stays enabled. Keep failed-CI repair priority, three-PR cap and all existing merge/provider/release boundaries.
- 未確認・制限: The new queue/scheduler behavior and a source-changing automatic repair still need real service/PR/CI validation after deployment.
- 未確認・制限: The queue is limited to three pending draft PRs; integration remains an owner decision, and full capacity must wait without disabling the task.
- 未確認・制限: Floor baseline proves object properties in native Lua substitutes only, not Roblox physics, actual falling, mobile or multiplayer.
- 未確認・制限: Gemini/external API, automatic main merge and Roblox publication remain held.

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
