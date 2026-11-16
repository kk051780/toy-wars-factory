# P0D GQ unique: DASH delayed rollback across match boundaries

## Defect and exclusive scope
Source-trace finding in original #482 V3 `EGGRUMBLE_FieldItemPickups.luau`: DASH schedules an unconditional 5-second delayed speed restoration guarded only by Humanoid presence, Health and speed equality. If a player reuses an avatar across TEAM/BR round reset (or receives a new DASH), an old scheduled callback can restore the wrong speed during a new session. This is a source-level potential regression, not a Studio-observed exploit.

**Distinct from** #489 egg-carrier ITEM fairness; #517 full-health HEAL; #525 cross-mode pickup authorization; #516 DOT epoch; #527 AI siege pace; #528 neutral cap; #529 Assassin combat; original #482 Game/ITEM/Replay authority. No new Game, Remote, Store, HP, egg/score, spawn system, lobby, caste or world.

## Real source files
- `EGGRUMBLE_DashLease.luau`: pure server-side lease, unique per-Humanoid ticket, old-match/removed-world/retired-owner fences, speed-effect conflict preservation, cancel hook.
- `compose_dash.py`: immutable original author `FieldItemPickups` Git blob `24a35a2e6004c635456cc6f2288cf13f8365ba27`, original V3 HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, exact one-hunk private composition. OFF returns byte-for-byte original. ON only imports this module and substitutes the original DASH expiry block. It does **not** overwrite the original author file.
- `tests/test_dash_lease.luau`: native Luau behavior tests, including repeated DASH, TEAM→BR old callback, retired session, detached world, lost session ownership, speed-effect collision, dead Humanoid, cancellation and invalid session.
- `tests/test_compose_dash.py`: blob, exact hunk, unchanged HEAL/SHIELD authority, rollback and mutation tests.
- Read-only Actions `p0d-gq-dash-epoch-native.yml`: source-exact ON/OFF + native compile and VM.

## Eight-domain nonoverlap check
| Area | Retained owner / no edits |
| --- | --- |
| 7 roles / character | #482, #510, #524, #529 |
| Field / terrain | #482, #520, #523 |
| Battle effects | #482, #516 |
| Castles and eggs | #482, #500, #527 |
| Neutral AI | #494, #501, #528 |
| Items | original #482/#489 + #517/#525; only *DASH expiry lease* proposed here |
| Lobby / replay | #482, #513; no independent queue or replay callback |
| Balance | #487, #527; no damage/KO/score change |

## Intake and proof boundary
`SOURCE_WIP` / `SOFT_CLAIM_ONLY`. No `CLAIM_GRANTED`, original #482/#489/#517/#525 author ACK or #220 sole writer CAS yet. The initial source lock is #482 original ITEM; #489/#517/#525 **must be recomposed and author-selected** before any production adoption. Do not merge the whole PR, do not alter `main` or formal RC, and do not publish/enable paid features. Same-HEAD Native CI needs success before `SOURCE_QA_PASS`. A real combined 34-source Rojo Place, Studio 2-client, Android 15 minutes, art/FUN and OWNER acceptance remain untested.

## Integration contract
- `FEATURE_ID=GQ_V3_ITEM_DASH_EPOCH_FENCE_20261116`
- `BASE_ORIGINAL=fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`
- `AUTHOR_ITEM_BLOB=24a35a2e6004c635456cc6f2288cf13f8365ba27`
- `BASE_RC_LAST_OBSERVED=d2f3ed1a47558fdaf07be0181c83c698bdb2ce34` (must refetch)
- `ROLLBACK`: private compose OFF => exact original ITEM; drop added pure lease module; keep other authors untouched
- `NEXT`: #218 CLAIM_GRANT / #482 + #489/#517/#525 author ACK → #484/#504 original single-source composer reconciles existing ITEM patches → native source exact private composite + actual Place → #220 sole authenticated non-force CAS latest RC with same-HEAD official CI, ZIP/Place receipts → Studio/Android #420 and OWNER acceptance.
