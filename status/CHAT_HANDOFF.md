# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: fc946fa68bd729fabdaafaafe438b0e71d6d19cb
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 既存GitHub AIワークフロー: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- ChatGPT定期ゲーム修正: ENABLED_FIRST_RUN_UNVERIFIED
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
- The owner has authorized hourly ChatGPT connected-GitHub repair without another routine 進めて. Read C00017, config/autonomous_repair.json and docs/AUTONOMOUS_REPAIR.md.
- The existing task was updated and enabled successfully. Before claiming repair works, verify one real service run, actual code commit/draft PR and matching CI. Registration alone is not proof.
- Use the fixed auto/twf-game-repair branch and one [TWF auto-fix] draft PR. Repair failed CI on that same PR before starting new changes. Preserve successful work between runs.
- First validation: add whole-server Heartbeat production/purchase coverage for sufficient and insufficient coins in tests/auto/production_spec.lua; fix source only for a reproduced defect.
- Keep old 27 server and 6 HUD fixtures unchanged; add executable tests in the new discovery paths, preserve source-size history and all prior QA.
- No new external provider/API calls, model/cap/billing changes, automatic game merge or Roblox publication. Gemini holds and release requirements remain unchanged.

## 最新の再開地点（観測時点の記録）
- 記録: C00017 / 2026-10-25
- 照合したmain: abadea9f853670ed6eae7215361e6aeb2c73887b
- 証拠: history/C00017_chatgpt_repair_setup.json
- 完了: Owner explicitly requested autonomous game repair without repeatedly sending 進めて, superseding the prior lack of authorization for this separate ChatGPT route.
- 完了: Inspect the existing hourly task 6adbf0d6a7d881918ce181dff2468867 and its actual latest recorded run. It completed an audit comment on PR #32, with no code change; task existence alone was not autonomous repair.
- 完了: Read current official scheduled-task documentation: web tasks can use connected plugins and do not retain a local checkout between runs. Use GitHub as the durable source.
- 完了: Update the existing task to TOY WARS 自動ゲーム修正, preserving its hourly cadence and confirmed enabled state. Saved prompt directs actual changes, tests and one maintained draft PR, not status-only comments.
- 完了: Add a main-repository enable switch, bounded edit policy, trusted-base diff checks, native additional-test discovery and evidence archiving, while preserving all old gates.
- 完了: Keep all four game Lua files unchanged at 678 lines / 26,753 bytes; initial baseline and historical source changes remain intact.
- 完了: Separate the registered ChatGPT route from held Gemini/GitHub provider workflows in the generated handoff. First code-producing automation run is still unverified at setup creation.
- 新規推論承認: False
- 定期AI承認: True
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: Routine connected-GitHub edits/tests/draft PRs no longer wait for another 進めて. Main integration of future game fixes, external provider inference and Roblox publication still require their existing approvals. Validate the registered task by its service run, actual code PR and matching CI, not registration alone.
- 再開する作業: Finish and verify the owner-requested ChatGPT scheduled repair setup, then validate one real scheduled-task execution that writes a regression/code PR and triggers existing CI. Keep the task running without routine user prompts; preserve Gemini stops, existing regression gates and draft-only integration policy.
- 未確認・制限: Task update success is not proof that the new repair prompt has run. First-run code/PR/CI evidence is required and pending.
- 未確認・制限: The existing service schedule is hourly; it is not the old proposed 20-minute Gemini runner.
- 未確認・制限: Web tasks use connected GitHub and service availability/plan limits. They do not rely on the current scratch checkout or a running PC.
- 未確認・制限: Gemini input/framing and shared financial enforcement remain unresolved; all Gemini/external API transports stay held and no provider key is read.
- 未確認・制限: Future game fixes remain draft PRs until integration approval. Independent review and Roblox release requirements remain intact; engine/multiplayer/mobile/visual/player-fun evidence is absent.

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
