# GQ8 — EGGRUMBLE official RC31: lobby void / missing spawn

## Reproduced source evidence
Official RC HEAD: ad2a1d885510966c5d946fdf97e0f44f07c15fb7. Same-HEAD official Actions run: 43955472445 SUCCESS. Artifact 14271996855.

Actual 31-source Place SHA256: d8ffd1bb2957056f7a0dc69b9d4cb8a6b52c0a4140c5a7971bf89dce86cddeca. Parsed official .rbxlx contains zero Part/SpawnLocation Instances under Workspace. Single server Host EGGRUMBLE_LobbyCastleModesPreview SHA256: 9fd1f9211ff8f99cecc1dff1c09ff66e61ea4575a19e6c7f440b6932f00ddc37. It uses an existing SpawnLocation or (0,4,0) and creates class/gate stands but no solid lobby floor or fallback SpawnLocation. This is a source-confirmed void-spawn risk consistent with OWNER "no lobby; dies immediately"; Studio causality is NOT TESTED.

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
