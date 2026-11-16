# GQ8 — P0 lobby safe floor/spawn/initial avatar rescue

## Non-overlap
- **Observed original source defect:** Author #482 V3 canonical Rojo project has only ServerScriptService and StarterPlayer source mappings. No Workspace SpawnLocation or LobbyFloor is created by the actual Host script. The original Host falls back to `root=Vector3.new(0,4,0)` if there is no preexisting spawn. The V3 live lobby role stands and TEAM/BR portals alone do not create a traversable surface.
- **Unique fix:** Add ONE anchored walkable 120×150-stud lobby floor, ONE neutral server-owned SpawnLocation and a guarded CharacterAdded rescue for already-spawned avatars. Do not alter the original mode gates/queues, world/battlefield, AI, castle, egg, item, combat, balance or score authority.
- **Scope:** ONLY `EGGRUMBLE_LobbyCastleModesPreview` existing Script source selected into formal 31; the other **30** original scripts are **byte exact**. No duplicate Game/Remote/Store/AI/Combat/Score/Host.
- **No other worker duplication:** Not #539/#615 lobby label/ETA, #611 prompt reach, #527 bot siege, #522 Builder wall, #509 late-death egg, #492 spectators or old S1 #376 physical dojo. This is source-level V3 spawn safety, not a second UX lobby or special mode.
- **Collision guard:** Lobby world centered on current original `root`, z=-40..+110 and x=-60..+60. Original gates z=28, defense z=47, roles z=69 remain supported by the floor; TEAM/BR battlefields stay at x±620.
- **Live-match guard:** Before any rescue teleport, the server checks `p.Character==character`, live Humanoid and `joined[userId]` plus `sessions[mode]`. The existing castle respawn flow remains authoritative. The SpawnLocation is added once at original Script initialization, never per player.
- **Rollback:** Drop only `GQ8_LOBBY_SAFE_SPAWN_P0_VOID_REPAIR` overlay. Restore exact selected GQ527 Host bytes, all 30 other runtime scripts unaffected. All prior 33 features retained.
- **Safety/Status:** Studio-only preview; this patch does **not** claim physical Studio playability until actual Studio/2-client/Android tests. Release remains FUN/ART/MOBILE NO_GO. No main push, normal PR merge, Roblox publish, additional spend or local desktop operation. ONLY #220 authenticated sole writer may move formal `rc/p0d-s1-kids-rc01` via nonforce expected-SHA CAS after exact HEAD dual CI.

## PREP verification
Workflow on PR HEAD compiles all 31 selected Luau sources natively, builds actual 31-script Rojo Place and checks every Script/ModuleScript/LocalScript Name + Class + Source, verifies Host-only change and exact OFF reversal, runs negative mutation Python tests, and GQ8 source evidence checks all 34 enabled manifest flags across eight domains.

## Remaining acceptance
1. Same-HEAD V3 and legacy S1 Actions success (no failures).
2. #220 latest formal RC comparison/lease/auth and sole nonforce CAS write, then real official post-CAS same-HEAD CI+artifact ZIP size and Place bytes.
3. Studio Solo/2-client physical lobby spawn + death/respawn + queue TEAM/BR test, Android 15-minute FPS and initial FUN retest. A code/CI green cannot replace (3).
