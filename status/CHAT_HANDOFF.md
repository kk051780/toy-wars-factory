# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 146f57c0261b0862713b6e842b8d8025747420d4
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
- Review docs/GEMINI_CONNECTED_OFFLINE_RUNTIME.md and C00006: public profile, model-ceiling adapter and persistent shared budget are connected offline.
- Keep the existing cap at 10 AIC; current conservative reservation is 103.2192 modeled AIC, so all real-profile generation is blocked before forwarding.
- Establish a defensible smaller request-specific bound; CountTokens alone is not an upper-bound proof and no arbitrary margin is accepted.
- Recheck the short-lived public profile and authoritative provider quota/billing before any fresh inference approval.
- Real CLI/reviewer routing and live provider transport remain disabled; never reuse the consumed one-shot marker.
- Preserve unmerged PR #19/#21 and this follow-up; do not automatically merge, activate recurring AI, or publish Roblox.

## 最新の再開地点（観測時点の記録）
- 記録: C00006 / 2026-10-24
- 照合したmain: e62bddc469e5edfbc97c2ccd67e9ae05ff8e5904
- 証拠: history/C00006_connected_offline_runtime.json
- 完了: Re-read canonical main and unmerged PR #21; preserve previous draft work.
- 完了: Verify official Standard rates and model limits; retain dated offline-only public profile and expiry.
- 完了: Connect the profile and documented model-ceiling bounds to a real loopback HTTP gateway.
- 完了: Persist reservations in SQLite; verify developer/reviewer sharing, restarts, lost leases and six separate worker processes.
- 完了: Keep the existing 10-AIC cap and reject the 103.2192-AIC model-ceiling reservation before any forwarding.
- 完了: Add a digest-pinned offline container test with Docker networking disabled and a minimal build context.
- 完了: Track runtime-only source changes in the portable handoff.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: A defensible smaller request-specific bound, current price review, authoritative provider quota/billing and fresh owner authorization are still required.
- 再開する作業: Validate a smaller request-specific input/output bound without treating CountTokens, character counts or invented multipliers as guaranteed caps; keep live inference blocked at the existing 10 AIC.
- 未確認・制限: The conservative connected adapter reserves full documented model limits; 103.2192 AIC is not an expected cost or bill.
- 未確認・制限: Live Gemini CLI and independent reviewer remain disabled and are not rerouted.
- 未確認・制限: No provider transport, key read or actual model call exists in this offline gateway.
- 未確認・制限: The candidate container is CI-only, not a production deployment.
- 未確認・制限: Roblox Studio, multiplayer and mobile remain NOT_RUN.

## 未マージの提案（現在のPR状態はGitHubで再確認）
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
