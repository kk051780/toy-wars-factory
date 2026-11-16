# EGGRUMBLE V3 result delivery — unique quality-gate repair candidate

**SOURCE_WIP, not granted, not adopted in official RC.** Original #487 score/result author owns the only authentic ResultService; this scope is a small *source-selective* retry of an existing exact result, never a second score/hud.

## Genuine original gap and trigger
At original #487 HEAD `438a406ccfda5563053d783d7561797ccd364361`, `EGGRUMBLE_MatchResultService.luau` original Git blob `b5ef844cff98173e3b2499b8aceca099f315adc4` sets `session.resultsDelivered=true` before calling `makeResultGui`. `makeResultGui` silently returns when `PlayerGui` is absent during transient character respawn; future refresh cannot retry. This is a **code-derived possible missed result**, NOT a Studio-reproduced outage. It changes no winner, score, KOs, egg credits or player's UI placement.

## Actual code and evidence
- `EGGRUMBLE_ResultRetry.luau`: one pure server callback utility. It attempts original GUI delivery immediately; only if missing/failing, retries at 250ms intervals at most eight times. It checks original server-owned session phase, same real player, current mode, living world and connected player before each attempt. A canceled/stale callback makes no GUI. It does NOT produce scores, create PlayerGui, start a new round or store data.
- `compose_result.py`: source-Git-blob-locked exact one-original-ResultService overlay, OFF byte-exact. Adds one require, makes original GUI factory return success boolean only upon actual creation, and routes its one original call through bounded retries. Preserves #487 original ScoreBalance.build, ranking, stats formatting, 8-second result and one `resultsDelivered`.
- `stage_private.py` + `verify_private.py`: genuine #487 V3 original 22-source project pinned Git blob `4f85b8313ad93744ac13d0480c3460643f96212e`, unchanged original #487 ScoreBalance blob `4de4b8068203ce93bba9c0810d54ab22367e5f35`. Stage OFF22 and ON23, compile all, build genuine unpublished Rojo Place for each, read XML Source/Class and assert exact.
- Read-only workflow `p0d-gq-v3-result-gui-retry.yml`: Python mutation and rollback, pinned native Luau VM with valid/invalid/late GUI cases, pinned Rojo, Source/Class and private artifact.
- These tests cannot assert engine/UI success; 2-client Studio and Android still required at #420/#470.

## Eight gameplay domains and non-overlap
| Domain | Existing writer retained / this candidate effect |
| --- | --- |
| CHAR | #482 7 roles — untouched |
| FIELD | #520/#523 terrain and eggs — untouched |
| BATTLE | #516/#529/#530/#535 — untouched |
| CASTLE & EGG | #482/#500/#527 true winner, stock, deliveries — untouched |
| NEUTRAL | #494/#501/#528/#533 — untouched |
| ITEM | #489/#517/#525 — untouched |
| LOBBY | #482/#513 — only server-authenticated result lifetime check |
| BALANCE & RESULT | #487 original rank/KO/score untouched; optional missing-GUI retry only |

## Intake / rollback
`FEATURE_ID=GQ_V3_RESULT_PLAYERGUI_TRANSIENT_RETRY_20261116`; claim #218 SOFT only, **not** CLAIM_GRANTED; #487 and #482 author must review/select one Result overlay and avoid another ScoreBalance/Result/GUI instance; #484/#504 original game composer source-selects current original score result with this generated only-once hook. Native/source CI success is **private PREP evidence**, not an official RC write.

Before #220 sole authenticated CAS: reconcile current #487 ScoreBalance/Result author SHA; source-exact full newest single Host, Result, Score, role, field, battle, castle, neutral, item, lobby; native negative (missing GUI then returns, mode change, disconnected, finished old session); latest RC HEAD nonforce CAS; same-HEAD official CI and unique ZIP/Place byte/SHA; ART/FUN and OWNER Studio/Android acceptance after. Rollback: use `compose_result.py --out OFF` byte-exact original ResultService and omit helper; nothing persisted. No main/author branch/RC write, merge, publish, purchase or Windows operations.
