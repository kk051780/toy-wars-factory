# EGGRUMBLE陸海空×7職（2026-11-17）Studio-only実装候補

**FEATURE:** `GQ8_LAND_SEA_SKY_ROLE_TRAVERSAL_20261117`  
**Base formal RC:** `6e71e4ce446005b23c5e359245ac113e281596a1` at branch creation  
**Policy:** no change to `main`, `rc/p0d-s1-kids-rc01`, publishing, payment or owner PC. #220 only formal RC CAS writer.  
**Status:** source candidate, not formal RC, actual Studio/Android/game FUN NOT TESTED.

## Working code
- A **single additional Studio-only server script** waits for existing V3 `TEAM_Arena` / `BATTLE_ROYALE_Arena`, checks actual `TacticalBattlefield` and installs a disposable child folder. If the original Host is absent, it creates nothing. This protects the already accepted V3 31-script Game, Combat, Swarm, Castle, AI, Item, Lobby and Score sources, and the older rich51 S1 profile.
- LAND: existing arena, three routes, fortresses, eggs, AI, neutral Horde, original combo source are **unchanged**, with a visually marked coast and public dock.
- SEA: visible semi-transparent coastal surface and a recovery raft. This is **not real swimming Terrain water** yet: original solid tactical floor stays intact to avoid cross-session Terrain damage or falling. A role-locked controllable boat and sea-beast mount are added.
- SKY: 2 collision platforms 90 studs above the ground; **two public lifts and returns** allow all seven roles access; sky-flight craft and flying-beast mounts have server-controlled horizontal movement within current V3 field bounds.
- MAD SCIENTIST (`BUILDER`): builds a role-locked boat or airship at a physical launch pad.
- BEAST TAMER (`BEAST`): summons a role-locked sea beast or flying beast at a physical nest.
- PSYCHIC (`TRAPPER`): places a highly visible short-lived tidal portal trap; in this first slice it is **BR-only** because authoritative TEAM ally IDs are private to Host. An opponent touching the portal is moved to a safe sea raft. Team trap requires a server-authoritative team/round hook, not guessed from cosmetics.
- Others: can walk the coast and access both sky islands via public lifts; no paywall or class-exclusive mandatory objectives.
- Mobile/desktop: uses native VehicleSeat throttle/steer inputs rather than a newly trusted client Remote. Flight has a **fixed safe altitude** for now; free vertical climb/dive, true ocean navigation and physical swim are **not complete**.
- No extra Combat or Swarm controller, no fake hit/KO or leaderboard authority; coast horde marker only. More simultaneous on-screen enemies is not claimed until existing neutral-budget/Android and actual Studio gates prove it.

## Limits, containment and rollback
- Limits: 4 craft/arena, 95 explicitly-created decorative parts/arena, at most 2 live traps, trap TTL 24s, craft TTL 180s, model movement tick >= 0.10s. Additional Script exists only when this optional profile is built.
- Scene and movement loop clean up when the corresponding Match World is removed; actions validate server role, mode, alive state, distance, match World existence and seat occupant. Server controls the movement and world limits. Current prototype must still be tested for Roblox-seat physics and latency; test assertions cannot prove that.
- No extra game Remote, no DataStore, no second Game/Combat/Swarm, no actual damage/KO; avoids shared Terrain mutations. 31 existing source file bytes remain unchanged, even with this companion ON.
- **OFF**: omit companion Script. `compose_optional32.py --off` emits a 31-source project referencing the same existing source files and verifies exact bytes; no reverse patch to existing Game/Host needed.
- New standalone CI tests 31-source **MOCK** exact ON32/OFF31 and actual Rojo+native Luau for the added source. It is **not evidence of the current official 31-source Playtest** and must never be labeled as such.

## Formal RC integration path — not delegated to this author
1. #220 selects the *current exact* canonical 31-source Rojo `.project.json` produced at latest RC HEAD (not the original stale #482 preview), reruns `compose_optional32.py --current31 ... --out ...`.
2. Compile **all 32 selected actual sources**, Rojo-build the exact selected32 and rollback selected31, verify exact Script classes + source bytes, and run same-HEAD V3/S1 CI with source-lock.
3. Independently review collision/authorization/performance; #220 only nonforce expectedSHA CAS to formal RC after RED gates pass. If RC HEAD moves, rebase/retake CI; no unguarded merge.
4. Roblox Studio solo+two clients: confirm VehicleSeat mobile steering, server authority, all seven roles, trap warning/recovery, sky lift, genuine neutral KO and round reset.
5. Android 15min median FPS>=30, 3-min child FUN and artwork/owner review. Only afterward consider activating this optional scene or using it as an S2 feature.

## Remaining real upgrades
- Full 3,000×3,000 streamed battlefield with navigation and Android budget (currently **890×1,050/arena**).
- Terrain Water/ocean currents, boats crossing true water, altitude climb/dive controls, mount animation, sky island air bridges, underwater fortresses and multiple castle entrances.
- TEAM trap needs authoritative Host team lookup and no friendly fire; area attacks/neutral armies need direct #220 Swarm-budget integration, never a duplicate spawn manager.
- This prototype uses basic shapes deliberately to test movement topology: **ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / RC_NOT_ADOPTED**.

**Cross-lane nonduplication:** #222 owns world atlas/design cards; #476 owns earlier H1 wings/ride candidates; #522 owns current V3 Builder wall; #710 owns neutral spawn obstacle checks; this slice only owns independently gated V3 movement topology and new optional travel script.
