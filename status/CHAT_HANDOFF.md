# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 5bf0a54f097507a6ecd55476b911805da0504815
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 既存GitHub AIワークフロー: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- ChatGPT定期ゲーム修正: ENABLED_QUEUE_V2_GAME_SOURCE_FIX_VERIFIED
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
- 記録済GitHub QA: PASS_OFFLINE_URL:https://github.com/kk051780/toy-wars-factory/actions/runs/40136758867（最新Actionsを別途確認すること）

## 次の開発優先事項
- Queue v2 setup PR #37 is merged and post-merge QA/handoff passed. Do not request that setup approval again.
- Read C00025 and the live task state. The worker now produced a real game-source fix in PR #38 on an independent UUID lane, with CI 40137069031 successful; PR #35 was preserved.
- Continue ordinary hourly code work without another 進めて. Prioritize failed CI, otherwise start a different issue if fewer than three review PRs remain. Full queues wait without scheduler mutation.
- PRs #35 and #38 remain draft/unmerged. Main metrics are still 678 lines / 26,753 bytes. Native floor properties do not establish actual Roblox physics or release readiness.
- Keep owner integration approvals, independent review, model/cap/billing/credential controls and all Gemini/Roblox publication holds. Check service and GitHub state rather than treating this snapshot as live state.

## 最新の再開地点（観測時点の記録）
- 記録: C00025 / 2026-10-25
- 照合したmain: efa4e67fd0cebe211a0696bb5ce0642d30cb3e58
- 証拠: history/C00025_queue_source_fix_verified.json
- 完了: Deploy queue v2 through PR #37 at efa4e67fd0cebe211a0696bb5ce0642d30cb3e58 using reviewed head f17a6d5c873f3234600a2e9d711aad0c55d1286e and exact tree 7a9ae89c80e00b903984f5e9d7a295cb21227f81.
- 完了: Confirm post-merge controller QA 40136758867 and handoff 40136758840 both pass, retaining all source, quality and provider holds.
- 完了: Validate real service run 039874ac-64a0-8323-bc57-5c35cf58ec90: completed result matches its run ID and time, and task remains enabled on its unchanged hourly schedule.
- 完了: Verify the worker chose START with open_prs [35] and limit 3, created a new main-based UUID lane and draft PR #38, while review-ready PR #35 head stayed 1fdc549d0d708230cc642b18ceb020f28efa0806.
- 完了: Inspect actual game patch: only FeltBattlefield, FactoryFloor and LobbyGround gain CanCollide=true. Server grows 160 bytes/3 lines; character stats, prices and decorative/unit collision remain unchanged.
- 完了: Verify exact-head CI 40137069031 succeeds on b8e543ada9e5613486cbcfc1819a3aba8cc7932c, including UUID namespace/scope gate, five native floor cases with pinned old-server control, 74 Python tests and all previous gates.
- 完了: Independently execute the new regression against old and fixed server snapshots: old has two failing cases, fixed all four canonical cases pass. The local pinned control was absent and skipped; CI executed it successfully.
- 完了: Compare the actual candidate tree: 78 existing blobs/modes are unchanged and only three allowed files differ. Keep the source fix draft/unmerged and main source at 26,753 bytes.
- 新規推論承認: False
- 定期AI承認: True
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Routine connected-GitHub edits/tests/draft PRs no longer wait for another 進めて. Main integration of future game fixes, external provider inference and Roblox publication still require their existing approvals. Validate the registered task by its service run, actual code PR and matching CI, not registration alone.
- 再開する作業: Continue the enabled hourly task under queue v2. Preserve review-ready PRs #35 and #38; CI failures are repaired first, successful work is not mixed with a new issue, and one remaining queue slot can start another main-based repair. A full queue waits and rechecks without self-disabling. Main game integration and Roblox publication still require their existing approvals.
- 未確認・制限: Queue v2 has one verified source-changing run and an enabled-state observation after completion; this is not a guarantee of indefinite operation or every future wait state.
- 未確認・制限: Up to three draft PRs may wait for review. The task stays enabled and rechecks capacity, but cannot auto-merge or publish without existing approvals.
- 未確認・制限: PR #38 is unmerged. Main still has four Lua files / 678 lines / 26,753 bytes; candidate metrics 681 lines / 26,913 bytes must not be represented as applied.
- 未確認・制限: Native tests verify collision attributes, not Roblox physics, actual falling, multiplayer, mobile or visual/player experience.
- 未確認・制限: Notification delivery is unknown. Service result, actual source commit/PR and exact-head CI are the evidence.
- 未確認・制限: Gemini input/financial blockers, provider transports, 10-AIC cap and release HOLD are preserved.

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
