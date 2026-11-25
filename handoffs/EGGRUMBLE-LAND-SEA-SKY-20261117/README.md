# EGGRUMBLE陸海空×7職（2026-11-17）Studio-only実装候補

**FEATURE:** `GQ8_LAND_SEA_SKY_ROLE_TRAVERSAL_20261117`  
**Base formal RC:** `6e71e4ce446005b23c5e359245ac113e281596a1` at branch creation  
**Policy:** no change to `main`, `rc/p0d-s1-kids-rc01`, publishing, payment or owner PC. #220 only formal RC CAS writer.  
**Status:** source candidate, not formal RC, actual Studio/Android/game FUN NOT TESTED.

## Working code
- A **single additional Studio-only server script** waits for existing V3 `TEAM_Arena` / `BATTLE_ROYALE_Arena`, checks actual `TacticalBattlefield` and installs a disposable child folder. If the original Host is absent, it creates nothing. This protects the already accepted V3 31-script Game, Combat, Swarm, Castle, AI, Item, Lobby and Score sources, and the older rich51 S1 profile.
- LAND: existing arena, three routes, fortresses, eggs, AI, neutral Horde, original combo source are **unchanged**, with a visually marked coast and public dock.
- SEA: a 550×295-stud **off-floor navigable offshore lane** extends 260 studs past the battlefield edge. Builder boats and Beast sea mounts travel on it using server-steered, clamped VehicleSeat movement; two safe docks and public transport allow all seven roles to visit. Pilots who dismount while offshore near the craft are rescued to the shore dock. **This remains visual/non-Terrain water, NOT real player swimming, physical boat buoyancy, currents or underwater combat**. The original solid arena floor is unchanged.
- SKY: 2 collision platforms 90 studs above the ground; **two public lifts and returns** allow all seven roles access. Flying craft now also have pilot-only step altitude controls (18 studs per command, server movement at <=22 studs/s, absolute altitude 28..148 studs above ground) with bounded 3D Blockcast. Both climb and descent require actual owner plus seated pilot, not a trusted client CFrame.
- MAD SCIENTIST (`BUILDER`): builds a role-locked boat or airship at a physical launch pad.
- BEAST TAMER (`BEAST`): summons a role-locked sea beast or flying beast at a physical nest.
- PSYCHIC (`TRAPPER`): places a highly visible short-lived tidal portal trap; in this first slice it is **BR-only** because authoritative TEAM ally IDs are private to Host. An opponent touching the portal is moved to a safe sea raft. Team trap requires a server-authoritative team/round hook, not guessed from cosmetics.
- Others: can walk the coast and access both sky islands via public lifts; no paywall or class-exclusive mandatory objectives.
- Mobile/desktop: uses native VehicleSeat throttle/steer inputs rather than a newly trusted client Remote. Flight supports discrete climb/descent via two on-board ProximityPrompts; **continuous analog climb/dive is still not implemented**. VehicleSeat prompt/seat replication and Android touch behavior require actual Roblox Studio evidence. True ocean navigation and physical swim are **not complete**.
- **MUSOU coast:** the existing coast beacon now shows a once-per-second count of **actually alive nearby NeutralHorde Humanoids**, not an artificial spawn forecast. When the canonical Swarm server confirms an increasing neutral KO count and a 12× combo milestone for a player near the beacon, one short 3D shockwave appears. It is cosmetic only, no damage, no created enemies, no XP/score write, no extra Combat/Swarm/KO authority. Bounded to 2 waves/s and 0.46s TTL, with source listeners cleaned up on round teardown. More simultaneous enemy density remains unproven until actual Swarm budget/Android/Studio validation.

## Limits, containment and rollback
- Limits: 4 craft/arena, 95 permanent decorative Part creations/arena, at most 2 live traps, trap TTL 24s, craft TTL 180s, model movement tick >= 0.10s; confirmed-KO shockwave limited to 2/s and .46s lifetime (transient additional Part). Additional Script exists only when this optional profile is built.
- Scene and movement loop clean up when the corresponding Match World is removed; actions validate server role, mode, alive state, distance, match World existence, current match castle membership and seat occupant. Server controls the movement and world limits. Current prototype must still be tested for Roblox-seat physics and latency; test assertions cannot prove that.
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
- Full 3,000×3,000 streamed battlefield with navigation and Android budget (currently **890×1,050/arena**). Pilot-only variable-altitude flight is a first playable candidate, **not** a complete freely flying open world.
- Terrain Water/ocean currents, boat buoyancy on true water (current offshore lane only simulates water), smooth analog altitude controls (current up/down step prompts are discrete), mount animation, sky island air bridges, underwater fortresses and multiple castle entrances.
- TEAM trap needs authoritative Host team lookup and no friendly fire; area attacks/neutral armies need direct #220 Swarm-budget integration, never a duplicate spawn manager.
- This prototype uses basic shapes deliberately to test movement topology: **ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / RC_NOT_ADOPTED**.

**Cross-lane nonduplication:** #222 owns world atlas/design cards; #476 owns earlier H1 wings/ride candidates; #522 owns current V3 Builder wall; #710 owns neutral spawn obstacle checks; this slice only owns independently gated V3 movement topology and new optional travel script.

## GQ8 LSS trap owner fairness / 2026-11-18
- A BR psychic caster can place **at most one active sea-warp trap**, preventing one player from monopolizing both global slots (2 slots still available to two different players). Destroying or expiring the old trap frees its slot immediately; opponent casts remain possible. No TEAM ally-trust inference.
- Existing `traps` index stores the original server-verified `owner.UserId` instead of a boolean; only the already optional 32nd Studio server script is changed, all canonical31 source bytes preserved. No new Remote, Save, combat, Castle, Score, or HP ownership.
- A native Luau VM harness derives the actual `canReserveTrapSlot` function, runs 11 owner/global/expiry cases and requires an owner-bypass mutant to fail. The exact official31→optional32/OFF31 Rojo bridge remains the admission gate; Studio 2-client/Android/OWNER FUN remain untested.
