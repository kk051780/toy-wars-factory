# P0 #431 — Private live-coast visual parity candidate (stage 1)

This does **not** recreate the old Studio H1 sea channel in live. The old sea scripts require Owner361-expanded Studio terrain; simply removing `RunService:IsStudio()` guards would change physical `GrassArena`, water volume, collision/boat routes and egg travel.

The new `P0DLiveCoastalVista.server.luau` Script adds only a **decorative maritime vista outside the original MapBuilder play boundary**. It is not a player-swimmable sea, not a bridge, and not a new game route. Target: recognizable water/coast/headlands/sails when looking north from the existing arena, while preserving every authoritative Game/MapBuilder/HP/egg/remote source and low-end mobile performance intent.

## Hard runtime safety contract

- **Default OFF in all engines, including private Roblox non-Studio**. No source deploy automatically enables this feature. Requires server-side `workspace:GetAttribute("P0D_PRIVATE_LIVE_COAST")==true` configured on a separately authorized private test place **before the Script starts**. Client toggles do not authorize server changes.
- Checks the real `TRAP_RAIDERS_S1`, `GrassArena` size 250×142 at Y=-3, `CenterRoad` Z=0 and width 24, and northern wall `ARENA_BOUNDARY_N` Z=-71 and width 4; missing/moved anchors => **no write**. Explicitly rejects the Studio-expanded 370×294 scene.
- 40 parts total: two colored smooth surface bands, six sand strips, twelve static foam bands, eight rocks, two islands (base/palm/crown each), two sailboats (hull/mast/sail each). The near ocean only begins north of the original boundary. No Terrain editing, no physics water, no collidable or queryable geometry; no lights, particles, Tween, heartbeat, ScreenGui, permanent labels.
- No modifications to the seven studio-gated legacy visual scripts. Other coastal/ocean feature source and physics are unchanged. Source/Mode switch is atomically reversible.
- **Private source-only stage** is 81 scripts with all prior canonical ART4 80 scripts byte-identical, one extra scenic Script. The script is not officially integrated in RC or published.

## How to validate without confusing Studio and live

1. Full source QA: check fresh canonical RC80 ART4 source hash/feature flags; stage one author-GitBlob pinned Script; compile 81 Luau; build and examine exact real Rojo Place; match Game/HUD/MapBuilder + new visual Script Source to each instance. Test negative guards, OFF zero-write and rollback.
2. The mandatory engine test remains separate: OWNER authorizes a private production-like test server, with this script opt-in correctly set on **server workspace**. Verify the actual baseline arena and that `P0D_PRIVATE_LIVE_COAST_V1` has `ActualPartCount=40`, not merely that source compiled. Confirm there is no new walking collision or effect on eggs, movement and attack.
3. Capture real screenshots and video from northward facing three different points in the baseline map, at both PC and low-end Android. Check ocean visibility, art coherence, 15-minute median≥30/p10≥25 FPS/thermal degradation≤20%, no crash/OOM and fun/first3min≥4/5. If the boundary doesn't show water from the playable camera, reject or redesign the placement, not manufacture a screenshot.
4. The private Studio test may not reproduce this candidate: original Owner361 Studio overlay resizes GrassArena, so the coast **correctly refuses to load** when the arena is 370×294. Do not disable this fail-closed check just to get a screenshot. Studio source CI alone is NOT proof of private nonStudio visual parity.
5. At any mismatch, keep `LIVE_ART_NO_GO / ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO` and revert by omitting the one Script. #220 B alone handles any official source CAS. No main write/regular merge/Roblox public publish/paid use/Windows operation without authorization.

All screenshots and tests are still NOT_RUN / OWNER_ACCEPTED=0 until actual owner testing. The ocean is **scenic, not traversable**, by design.
