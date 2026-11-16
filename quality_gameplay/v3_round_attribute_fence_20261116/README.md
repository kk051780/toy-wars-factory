# EGGRUMBLE V3 — Neutral combo lifecycle-only fence (GQ nonoverlap)

**Base**: original author PR #482 exact `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, 21 original Luau source files immutable.
**Exclusive scope**: Neutral-horde combo/current-best-combo state when a human exits a TEAM or BR match, not Game/HUD/HP/egg/castle/role/bot/neutral spawn/item/score.
**Explicit nonoverlap**: Boss credit state is solely #514; this module does **not** touch `EGGRUMBLE_BossDefeats` and native VM verifies this value remains unchanged. Other GQ authors (#484/#485/#487/#489/#494/#500/#508) untouched.

## Root cause
Original `EGGRUMBLE_SwarmCombat.credit` writes `EGGRUMBLE_Combo` and `EGGRUMBLE_BestCombo` player attributes on authentic neutral deaths; original `EGGRUMBLE_RoundReplay.resetHuman` resets `EGGRUMBLE_NeutralKOs`, battle level and SlashEvolution on leaving match, not these combo attrs. Lobby and a following TEAM/BR match may visually inherit stale combo values despite reset server KOs. Source-derived gap, not real Studio repro.

## Source patch and rollback
New pure `EGGRUMBLE_RoundAttributeFence.luau` defines `TEAM/BATTLE_ROYALE -> nil` predicate and clears exactly the two neutral combo attrs. New opt-in Studio-only server Script listens to server-owned queued-mode transitions, removes PlayerRemoving listeners. No second Game, Remote, KO attribution, scoring, buyables or permanent save. Two additive scripts form 23-source alternate private Rojo project, all original 21 source-mapped unchanged. OFF/rollback: remove exactly two addon scripts, return to original project. On simultaneous boss credit fix PR #514, this patch never clears or writes boss credit.

## Proof / remaining gates
Nine Python source-positive/negative contracts, pinned Luau 23/23 syntax, actual pure module native VM including boss-attr noninterference, pinned Rojo 23/23 byte-source verification in Actions. Check exact candidate HEAD and CI before calling ready.
No in-engine Studio 2-client, 15-minute Android, ART/FUN comparison, human OWNER acceptance. Official RC is under authenticated sole writer #220. Requires #218 scope review/CLAIM, #482 original author ACK, same latest official HEAD source-selective CAS native+Rojo and ZIP/Place/rollback. No RC or main writes/merge/publish/payments.


## Cross-domain original-source integration (additional private QA)
The optional composer `tools/compose_private28.py` **reuses** original #484 26-game+ART+SCORE composer, then **only adds** the two combo Scripts, retaining all 26 original mapped file paths and Script sources (28 exact total). CI `p0d-gq-v3-combo-art-score-private28.yml` pinned original HEADs: #482 `fe67d31...`, #484 `6b52eaf...`, #485 `e86702...`, #487 `438a406...`. Original 7 jobs, 3 routes, real combat/egg/castle/neutral, 9 field items, TEAM/BR lobby, ART and SCORE stay owned by original authors. Native syntax28 and real Rojo28 source/class exact are **separate evidence** from engine, device and official RC acceptance. Source pin must be rechecked at #220 adoption.

Important: The 26+2 composite does not include all other pending optional PRs (#489 fairness, #494 pacing, #514 boss). It is a compatibility proof only, not a full latest release or formal source adoption.
