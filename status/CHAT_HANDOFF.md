# TOY WARS FACTORY — 新チャット用・継続引き継ぎ

このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。

## 現在地
- GitHub: https://github.com/kk051780/toy-wars-factory
- 基準ソースコミット: 8910cd3005aee53d6e65fe52de7893ab1da0e051
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
- 記録済GitHub QA: PENDING_ISOLATED_BRANCH_CI; prior stop implementation passed https://github.com/kk051780/toy-wars-factory/actions/runs/40075974239（最新Actionsを別途確認すること）

## 次の開発優先事項
- Review the direct-main operational stop and continuity correction; it has no dependency on experimental budget PRs.
- Confirm independent CI and exact official compiler regeneration, then obtain owner approval before merging; automatic merge remains unapproved.
- After an approved merge, resolve main HEAD and check on-change QA plus generated handoff; a draft or status page alone is not deployment evidence.
- Keep Gemini inference blocked. The inspected Python, Java, Go and JavaScript SDK snapshots do not map Gemini 3.8 Flash; no complete input/framing bound was established.
- Do not repeat identical SDK inspections as new progress. Require changed sources or new attributable provider/framing evidence.
- Keep the 10-AIC cap, consumed trial markers, independent-model review requirement, inactive recurring AI and no Roblox publication. Preserve separate gameplay PR #25 and related drafts.

## 最新の再開地点（観測時点の記録）
- 記録: C00009 / 2026-10-24
- 照合したmain: e62bddc469e5edfbc97c2ccd67e9ae05ff8e5904
- 証拠: history/C00009_isolated_hold_review.json
- 完了: Read canonical main, current drafts, Actions, issues and PR #25 without overwriting separate gameplay work.
- 完了: Confirm PR #24 exact official compiler regeneration and complete QA passed in CI 40075974239.
- 完了: Inspect exact official Java, Go and JavaScript local tokenizer lookups in addition to the previously inspected Python snapshot; none maps gemini-3.8-flash.
- 完了: Keep the native full-request CountTokens question distinct from a contents-only mismatch example and the separate Cloud multimodal caveat; no complete input bound was certified.
- 完了: Extract the tested operational stop and real-history continuity correction into a draft directly based on canonical main, excluding all budget runtime candidates.
- 完了: Pass all 43 Python regressions and 21 repository policy checks on the independent branch; exact official compiler and native Lua CI must still be confirmed.
- 新規推論承認: False
- 定期AI承認: False
- 自動マージ承認: False
- Roblox公開承認: False
- 再実行の前提: A reviewed merge of the operational stop is separate from future inference consent. Inference still needs complete bounds, shared enforcement, current pricing/quota and fresh owner approval.
- 再開する作業: Finish independent QA and present the direct-main stop/continuity PR for owner review. Merge only after owner approval, then verify main and its QA. Do not treat merging a stop as inference consent. Revisit the input blocker only with changed sources or new provider/framing evidence; independent gameplay work remains in separate drafts.
- 未確認・制限: This direct-main proposal remains unmerged; main still has its previous incident state.
- 未確認・制限: The input/framing bound and a hard financial cap remain unproved.
- 未確認・制限: Historical workflow snapshots are not retrofitted and the consumed trial must not be rerun.
- 未確認・制限: Experimental budget runtime, pricing, SDK tooling and Docker code are excluded from this branch.
- 未確認・制限: Studio, multiplayer and mobile remain NOT_RUN.

## 未マージの提案（現在のPR状態はGitHubで再確認）
- PR #25: DRAFT_UNMERGED / SEPARATE_GAME_PROPOSAL_NOT_ATTRIBUTED_TO_GEMINI / Integration QA: selector authority plus workshop backfill (no merge) / https://github.com/kk051780/toy-wars-factory/pull/25
  - QA: PASS: separate gameplay integration offline CI; Studio, multiplayer and mobile NOT_RUN. https://github.com/kk051780/toy-wars-factory/actions/runs/40076928524
- PR #24: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Hold Gemini activation and remove the unreserved reviewer transport / https://github.com/kk051780/toy-wars-factory/pull/24
  - QA: PASS: 43 Python, 64 Node including 24 container checks, exact compiler, Lua/stress, installer and handoff. Node/runtime candidates are excluded from this independent branch. https://github.com/kk051780/toy-wars-factory/actions/runs/40075974239
- PR #23: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Tighten request output reservations and record the unresolved input proof / https://github.com/kk051780/toy-wars-factory/pull/23
  - QA: 64 Node (24 network-disabled container), 33 Python, 37 Lua + 4000 stress, official SDK inspection and deterministic handoff PASS. Input proof remains BLOCKED; no live calls. https://github.com/kk051780/toy-wars-factory/actions/runs/40074151010
- PR #22: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Connect offline Gemini price bounds to a persistent shared budget runtime / https://github.com/kk051780/toy-wars-factory/pull/22
  - QA: 40 existing Node + 19 connected container tests, 33 Python, 37 Lua and 4000 stress checks PASS. No live inference. https://github.com/kk051780/toy-wars-factory/actions/runs/40072355807
- PR #21: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Reject unpriced native Gemini requests and test reserved call budgets / https://github.com/kk051780/toy-wars-factory/pull/21
  - QA: 40 Node, 33 Python, 37 Lua, 4000 stress checks PASS; offline candidate only. https://github.com/kk051780/toy-wars-factory/actions/runs/40069599840
- PR #20: DRAFT_UNMERGED / SEPARATE_GAME_PROPOSAL_NOT_ATTRIBUTED_TO_GEMINI / Admit waiting players when a workshop plot becomes free / https://github.com/kk051780/toy-wars-factory/pull/20
  - QA: PASS: separate plot backfill offline CI; Studio, multiplayer and mobile NOT_RUN. https://github.com/kk051780/toy-wars-factory/actions/runs/40069151903
- PR #19: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Fix shallow-history handoff churn and retain Gemini failure provenance / https://github.com/kk051780/toy-wars-factory/pull/19
  - QA: PASS: 33 Python, 37 Lua regressions, 4000 deterministic stress, exact installer and deterministic handoff. Offline only. https://github.com/kk051780/toy-wars-factory/actions/runs/40067722798
- PR #17: DRAFT_UNMERGED / CHAT_ASSISTANT_NOT_GEMINI / Reject spoofed distant toy-selector prompt activation on server / https://github.com/kk051780/toy-wars-factory/pull/17
  - QA: Offline: 37 Lua regressions, 4000 stress cases, 33 Python tests; no Roblox engine verification. https://github.com/kk051780/toy-wars-factory/actions/runs/40061153081
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
