# GQ802 physical six-cell visual tile source (independent B-lane)

Claim: #802 comment 6978030769. This is NEXT distinct task after #803's deterministic manifest policy; not its duplicate.

## Actual code
- Server-callable Roblox 3D renderer with 6 zone Models and 36 anchored collision-free no-touch/no-query Parts per match world. 25 original visual palettes/silhouettes built from original 25 prefab IDs. Each has low translucent floor accent, pedestal, relic, two corridor markers and a beacon. Source includes a pure data blueprint and a Roblox Instance module.
- Preserves old TacticalBattlefield and 3 ground corridors exactly. Does not move existing Castles/Eggs, alter Neutral/Item authority, write new Combat/HP/Store/Score/Remote/Weather, grant drops, damage people or set global gravity/time. No player-created seed allowed.
- The renderer requires upstream #803 policy's recomposition validator. It fails closed on wrong world/floor, duplicate folder, small map, manifest tampering, collision-dangerous specs or part-count mismatch. World-local folder can be cleared and is destroyed with the world; no heartbeat/event listener.
- Native Luau test covers 180 seeds, 25 variants, 36/36 noncolliding parts, 90+ distinct visual layouts, BR/TEAM and hostile mutations. Dedicated CI compiles blueprint/renderer and checks real Rojo ModuleScript and exact Source.
- IMPORTANT: 3D *visual* variety is implemented as code, not a new collidable 3D modular route. Original routes remain. Studio/Android visual acceptance and fun are not tested. #802's true dynamic navigable geometry and gameplay integration remain outstanding.

## Intake/rollback by sole authenticated #220 B writer
Current official starting RC f77b4d4393d9e9b19b65566413432a7a9f13962b (refetch before CAS). Original #803 manifest HEAD d6080df13d07792160a52b4c7025e0ae7950379c. On a later feature-enabled build, select its one authoritative policy plus these two modules; call exactly once per actual server stage after current MapBuilder's floor and castles/eggs are ready, then destroy local visual folder on round end. Do not bind new Remote/Store/Weather/Gravity. Feature OFF means exact original Core36/31 without this source. Same-HEAD Native/Rojo Source+Class, OFF rollback and all source locks are mandatory; #220 uses nonforce expected_sha CAS and post-CAS readback. No author approval wait. Main, Roblox publishing, cost and paid features excluded.

## Eight areas
CHAR = unchanged 7 jobs; FIELD = 25 original six-zone visual silhouettes; BATTLE = no extra collisions; CASTLE = existing walls/spawn unchanged; NEUTRAL = original spawner unchanged; ITEM = item hints are only descriptive art references, never fake pickups; LOBBY = original gates unchanged; BALANCE = 36 render parts, three free existing routes, zero new timers/HP/score.
