# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: eaa51d414de310e79073a8f0a781f999cad8ba0d
- ゲーム公開可否: HOLD_ENGINE_UNVERIFIED
- 既存GitHub AIワークフロー: NOT_ACTIVE_AI_INFERENCE_UNVERIFIED
- ChatGPT定期ゲーム修正: ENABLED_QUEUE_V3_CONFIGURED_LIVE_RUN_VERIFY_REQUIRED
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
- Present approval packet #35 / #38 / #40 with exact-head CI and a ready-to-send approval sentence; never answer only approval waiting.
- Manual go joins the existing game task; acquire a shared DISPATCH ticket only if idle with capacity. Game, META and manual integration use the same fenced coordinator.
- With explicit owner integration approval, recheck the listed heads/CI, take CONTROLLER ownership and integrate #38 then #35 then #40, validating actual main after each step. Roblox publication is excluded.
- Keep hourly game task enabled under queue v3; full queues recheck capacity without self-pausing. Check live service/coordinator state before writing.
- Run the registered daily system/game review: current web primary sources, observed failures, minimal tested improvement PR, concrete game experiments and measured outcomes. Reassess the architecture every cycle.
- Observe the first scheduled v3 and daily service runs before claiming their unattended protocol works end to end. Preserve all provider, quality and release holds.

## 現在の取り込み承認待ち（観測時点）
最新一覧: https://github.com/kk051780/toy-wars-factory/blob/twf-repair-coordinator/status/PENDING_APPROVALS.md

| PR | 内容 | 現在headのCI |
| --- | --- | --- |
| [#35](https://github.com/kk051780/toy-wars-factory/pull/35) | 生産3件・ウェーブ2件・敗北リセット1件の回帰検査。ゲーム本体の変更なし。 / 回帰検査追加 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40114787373) |
| [#38](https://github.com/kk051780/toy-wars-factory/pull/38) | 戦場・工場・ロビーの床だけ衝突を有効化。追加5検査が合格。 / ゲーム本体修正 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40137069031) |
| [#40](https://github.com/kk051780/toy-wars-factory/pull/40) | 工場アップグレードの不足金額・ぴったり購入・上限・収入の4検査。ゲーム本体の変更なし。 / 回帰検査追加 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40138956623) |

承認する場合の返信: #35・#38・#40のmain取り込みを承認
対象headのmain取り込みのみ。公開・課金・外部モデルは含まない。現在GitHubでhead/CIを再確認する。


## 手動goと自動実行の競合防止
- 手動goは既存ゲームタスクへ統一。実行中は追加起動せず確認へ合流する。
- 共通ロック: twf-repair-coordinator / ops/REPAIR_COORDINATOR.json。expected_sha・force=false・epochを必須にする。
- ゲーム修正・日次体制改善・手動統合が同じロックを使う。docs/REPAIR_COORDINATION.mdを読む。

## 体制とゲームの日次改善
- タスク: 6add445e4138819197d9cf2b1a02534d / 毎朝（Asia/Tokyo）
- 実測の欠陥と最新WEB一次資料から、体制の最小修正・回帰検査・draft PR、ゲームの根拠付き実験候補を進める。
- 現在の方式を最適と固定せず、前後の結果と未解決点を記録する。docs/SYSTEM_REVIEW.mdを読む。

## 最新の再開地点（観測時点の記録）
- 記録: C00027 / 2026-10-25
- 照合したmain: 658b69a4328de55c9c5129ad1f8894518c9efb49
- 証拠: history/C00027_serialized_execution_daily_improvement.json
- 完了: Read all three pending PRs, actual diffs and exact-head CI. #35 is regression-only, #38 fixes three floor properties, #40 is regression-only. All current heads pass.
- 完了: Add fenced WORKER/META/CONTROLLER leases plus a DISPATCH ticket for manual go. Unknown/active service joins instead of creating a second writer; expiry alone cannot steal ownership.
- 完了: Create shared coordinator branch and verify real same-parent contention. A stale ref request fails; a current-head but non-fast-forward update explicitly rejects with first owner retained.
- 完了: Add actionable exact-head approval packets and deterministic handoff sections with PR links, contents, evidence, scope and a ready-to-send approval sentence.
- 完了: Register a separate daily ChatGPT system/game review task with current primary-web research, measured failures/effectiveness, tested draft improvements and game experiment backlog under the shared lease.
- 完了: Preserve game source (4 files / 678 lines / 26,753 bytes), existing tests/negative controls, Gemini hold, budget/model/credentials and all integration/publication approvals.
- 完了: Local 108 Python tests (34 new coordination/system cases) and 21 policy checks pass. Current candidate combination also passes eight native suites including four upgrade cases and pinned old floor control.
- 新規推論承認: False
- 定期AI承認: True
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: General go does not approve game main integration. List the exact pending PRs, changes and CI; explicit approval applies only to listed heads and not publication.
- 再開する作業: Present all three exact-head integration approvals now. Keep game and daily tasks enabled; use shared ownership and verify future runtime outcomes.
- 未確認・制限: Controller lock contention tests do not establish every future unattended worker follows the protocol. Observe service runs and matching artifacts.
- 未確認・制限: Daily task is registered but not yet completed. Current references are primary sources checked today, not a claim all were newly published.
- 未確認・制限: Native combined regressions are Lua mocks, not Roblox engine/physics/multiplayer/mobile or fun evidence.
- 未確認・制限: Game PRs #35/#38/#40 remain unmerged. Automatic main integration, external inference and Roblox publication are not authorized.

## 未マージの提案（現在のPR状態はGitHubで再確認）
- PR #35: DRAFT_UNMERGED / CHATGPT_SCHEDULED_TASK_NOT_GEMINI / 生産3件・ウェーブ2件・敗北リセット1件の回帰検査。ゲーム本体の変更なし。 / https://github.com/kk051780/toy-wars-factory/pull/35
  - QA: PASS_EXACT_HEAD_NATIVE_OFFLINE; engine, physics, multiplayer, mobile NOT_RUN https://github.com/kk051780/toy-wars-factory/actions/runs/40114787373
- PR #38: DRAFT_UNMERGED / CHATGPT_SCHEDULED_TASK_NOT_GEMINI / 戦場・工場・ロビーの床だけ衝突を有効化。追加5検査が合格。 / https://github.com/kk051780/toy-wars-factory/pull/38
  - QA: PASS_EXACT_HEAD_NATIVE_OFFLINE; engine, physics, multiplayer, mobile NOT_RUN https://github.com/kk051780/toy-wars-factory/actions/runs/40137069031
- PR #40: DRAFT_UNMERGED / CHATGPT_SCHEDULED_TASK_NOT_GEMINI / 工場アップグレードの不足金額・ぴったり購入・上限・収入の4検査。ゲーム本体の変更なし。 / https://github.com/kk051780/toy-wars-factory/pull/40
  - QA: PASS_EXACT_HEAD_NATIVE_OFFLINE; engine, physics, multiplayer, mobile NOT_RUN https://github.com/kk051780/toy-wars-factory/actions/runs/40138956623
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
