# GQ8 — EGGRUMBLE official RC31: lobby void / missing spawn

## Reproduced source evidence
Official RC HEAD: 0aa30990a205e67400d31728e39d87e48c6b886d. Same-HEAD official Actions run: 43956786259 SUCCESS. Artifact 14270948701.

Actual 31-source Place SHA256: 1392bf09e31d16c3994c8b800982a8b378ec69c3063b1a963697ec785e28c2e9. Parsed official .rbxlx contains zero Part/SpawnLocation Instances under Workspace. Single server Host EGGRUMBLE_LobbyCastleModesPreview SHA256: 086d8125c2c2f76e7de3c13bb14f7519c36bec91502ff57ae9b1574cd321b846. It uses an existing SpawnLocation or (0,4,0) and creates class/gate stands but no solid lobby floor or fallback SpawnLocation. This is a source-confirmed void-spawn risk consistent with OWNER "no lobby; dies immediately"; Studio causality is NOT TESTED.

## Distinct source modification
- One preexisting Host source only, all other 30 original scripts unchanged, 31/31 class/identity exact, no new Game/Remote/Store/Combat/SCORE/AI authority.
- New anchored lobby ground (210 x 220 studs), fallback SpawnLocation, and delayed safe idle-avatar correction fenced by current match membership, same Character, Player existence, and Humanoid state.
- Not GQ539 boards, GQ615 queue ETA, S1 FB007 rebalance, GQ611 prompt reach, GQ580 AI takeover, or existing field fixes. TEAM/BR gameplay worlds are distant (x +/-620). Studio-only existing sandbox guard remains.
- No changes to seven role combat, field, castle egg, neutral Swarm, field items, score/balance, match timer, or client Remote.

## Verification and rollback
patch_official_place.py fails RED on official Place SHA, Host SHA, script membership or Studio guard drift, emits PRIVATE candidate Place and Source Lock receipt. test_repair.py verifies all 31 and OFF exact rollback; negative tests reject source drift, double patch, noncolliding floor, active-player relocation, missing SpawnLocation and foreign script mutation. Dedicated CI uses immutable official artifact and native Luau compiler, never updates the official RC.

Rollback: remove the single exact Host inserted fragment. The original Host and all 30 other sources are byte-identical to the official parent.

## Intake and next gate
#220 is the sole authenticated nonforce-CAS RC writer. It must recheck LATEST official HEAD before integration, source-select this exact one Host fix (or reconcile source drift without forcing), run same-HEAD Native+Rojo+GQ8, record real ZIP/Place bytes and adoption ACK. Candidate is NOT formally RC integrated.

Studio Solo: first avatar lands on real floor; all 7 class stands and both portals reachable; wait/queue/cancel; match start; death/respawn at own castle; results return to lobby; reconnect; 2 clients; low-end Android 15 min; kid FUN first 3 min. Until confirmed: STUDIO_NOT_TESTED, ANDROID_NOT_TESTED, FUN_NO_GO, PUBLICATION_NOT_AUTHORIZED.

Eight-domain cross gate: Characters / Field / Battle / Castle / Neutral / Items / Lobby / Balance preserved by 30-source exactness; lobby collision, transitions and gameplay must still be verified in actual Roblox engine.

Latest official 0aa includes P0D-006 rare FIELD_4/5 eggs in the same Host; this patch inserts only before the existing board helper and leaves all rare egg code exact.
