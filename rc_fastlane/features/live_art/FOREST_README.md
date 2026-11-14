# LIVE forest source canary — #431

This creates a separate 82nd source script, P0DLiveForestArt, over the
official RC81 ART-STACK4-plus-live-castle source (not a merge). All original 81 sources,
including Game, HUD, AI, 7 guarded original art scripts, remain byte-identical.

The visual script depends only on the original production MapBuilder
TRAP_RAIDERS_S1 / GrassArena / CenterRoad / RED_CASTLE / BLUE_CASTLE;
it explicitly does not use the Studio-only Owner361CastleBattlefield,
the 370x294 expanded arena, Terrain water, or geometry-changing art.
Each of the two real-map side-groves receives six recognizable, muted
stylized trees, 5 non-colliding static parts per tree = 60 parts.
No dynamic lights, physics, particles, UI, movement control, Terrain, or
repeating RunService render/physics callbacks. The game's real egg at z=-20,
score pad z=20, center road z=-12..12, boundary z≈71, castle
sidewalls z≈44 are visually unobstructed, based on static coordinates.
Actual player camera clearance is NOT_TESTED.

Default OFF on Studio and public servers. A private Roblox server may
render it only after an OWNER-authorized server sets Workspace boolean
P0D_PRIVATE_LIVE_FOREST=true before the script starts AND Roblox server
reports a nonempty PrivateServerId. In Studio, an authorized private
preview can set Script attribute EnablePrivatePreview=true. These
attributes are NOT set by the generated source or this PR.

Static source/LoC/native tests and Rojo embedded-source exactness
demonstrate only source readiness, NOT engine execution, visibility,
performance, beauty, safety of public publishing, or mobile acceptance.
LIVE_ART_NO_GO / ART_NO_GO / FUN_NO_GO / MOBILE_NO_GO until real PC/Android
private-runtime evidence, user play feedback, and OWNER approval.
Rollback: omit one additive script; original 81-source ART-STACK4 plus live-safe castle unchanged.
Other A teams cover private castle (#439) and client FX/beast (#442);
do not double-adopt or overwrite latest canonical RC. B #220 sole writer.
