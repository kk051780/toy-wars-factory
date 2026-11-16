# EGGRUMBLE V3 — boss shockwave wall occlusion (GQ non-overlap)

**Scope/claim:** `GQ_BOSS_SHOCKWAVE_WALL_OCCLUSION_20261116`; #218 SOFT claim comment 6908767688, **not GRANTED**. **Not merged, not the official RC, and not Studio/Android tested.** Original game author #482 / composer #484 / B only authenticated RC writer #220 retain their respective authority.

## Reproduced source defect

Original #482 `EGGRUMBLE_NeutralStoneGiant.luau`, commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, Git blob `2670618cba320c51936c750a10e43c194cada0f0`, telegraphs for 2 seconds, checks the human root's horizontal distance <=11 studs and vertical distance <=8 studs, then directly executes `h:TakeDamage(28)` without checking solid walls. A human behind a castle wall can be damaged by a boss strike even if the wall is supposed to provide cover. **This is an observed source logic gap, not a Studio-reproduced bug.**

## Actual implementation

`tools/compose_patch.py` accepts *only* that exact original author blob. It generates a scratch **single original boss module source** and inserts `shockwaveClear` before the original attack prompt. The helper performs a server-side `workspace:Raycast` from boss center to human torso, with `RespectCanCollide=true` and filters for the boss model and the target avatar. The existing horizontal + vertical gate now also requires unblocked LOS before its existing 28 HP attack. Unblocked targets keep the identical 2s warning, 5s interval, 28 HP hit, no change to boss 900 HP, hero 36stud skill reach, castle/win/KO/egg/loot/score or mode state. Invalid source SHA, missing/duplicated anchors or a second patch fails closed.

**Production safety:** no new Game, Store, Remote, boss spawner, damage authority, bot AI, ITEM, HUD or paid asset. No original author file edited. The generated original boss is for selective review by #482 and #484, not a replacement branch/RC. **Rollback:** do not select the generated boss module at intake, or restore exact original blob `2670618...` and remove the optional gate.

## Eight-domain review (reuse, don't duplicate)

| Area | Existing owner / coverage | Effect of this slice |
|---|---|---|
| Character | #482 seven roles, #510 mage, #516 DOT | No class/HP/role edit; hero receives radial damage only if cover ray is clear |
| Field | #482 arena, #485 field art | Castle wall / terrain is now cover, no map edit |
| Battle | #482 real skill combat, #503 FX, #504 audio | 28 HP boss strike retained, block through solid wall |
| Castle/egg | #482 rules, #500 defense, #509 egg ledger | Cover decision only, no castle authority |
| Neutral | #482 original StoneGiant, #494/#501 Swarm, #514 boss KO counter | Only original boss radial attack LOS |
| Items | #489 egg-carrier buffs, #517 fullHP HEAL | No item change |
| Lobby | #482 TEAM/BR and #513 host lease | No lobby/queue change |
| Balance/SCORE | #487 score, #499 900s timeout | Reduces cover-ignoring hits; telemetry and real Studio acceptance required |

## Verification / RC intake

The dedicated read-only workflow checks original full commit + Git blob, ten source tests including source drift, mutation, authority and exact two-hunk isolation, native Luau compilation of the **actual generated authored source**, and artifact of diff/generated source. It does **not** run Roblox Studio, a real collision engine, live 1+15AI/2+14AI games, Android FPS, #420 ART/FUN or OWNER review. Do not record it as effective wall protection until real engine test.

For B intake: #218 exclusive CLAIM_GRANTED decision -> #482 original owner ACK for two-hunk change -> #484 one-boss source-selective composer -> no duplicate Game/Role/Store/Remote/Swarm -> latest official RC HEAD authentication+nonforce CAS by #220 -> same-HEAD official source/native/Rojo/Place/ZIP/rollback ACK -> Studio wall cover test + PC/Android 15-minute performance + OWNER acceptance. Retain YELLOW debt record if nonfatal, block RED, never merge whole DRAFT PR. No main changes, publish, purchases or PC actions.
