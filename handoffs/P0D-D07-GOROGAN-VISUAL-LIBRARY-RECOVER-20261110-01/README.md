# TRAP RAIDERS D07 — Gorogan Client-Only 3D Prototype

Packet: `P0D-D07-GOROGAN-VISUAL-20261110-01`
Game: `TRAP_RAIDERS`; work_id `p0d-siege-v19`.

## Why this exists
The prior v40 reference (`c0b0bf692410cb651893c38f1a453c93d9f8b3b5`) contains neutral boss scheduling and limited command decisions, **not a playable 3D monster**. This new separate packet supplies a client-only low-poly **Gorogan** visual for S1/S3. It creates an original giant rock silhouette with moss/eyes/core, a bounded visible stomp warning ring, reduced-motion and low-detail variants, 10Hz renderer throttle, max 14-second TTL, and cleanup on round reset/destroy.

It does **not** generate an actual NPC, run server boss AI, deal damage, own physics, play third-party sound, implement Dragon Raigald, trigger a boss, or change the egg win condition. It is not integrated with the PC's actual Roblox Place.

## Source files
- `luau/GoroganVisualPolicy.luau`: server-event visual packet filter/limited lifetime. This is a secondary client-side guard and **cannot itself authenticate a server**.
- `luau/GoroganVisualPrefab.luau`: a genuine Roblox `Model` made of anchored non-colliding primitive `Part`s. Limited rings and simple bobbing. Standard `Color3/Enum.Material` only.
- `luau/GoroganClientAdapter.client.luau`: **opt-in** LocalScript integration example. It stays inert unless a trusted server RemoteEvent `TRAP_BossVisualEvent` exists, and expects actual server-replicated player attributes (`TRAP_ActiveMatchId`, `TRAP_ActiveStage`, `TRAP_LowDetail`, `TRAP_ReducedMotion`) validated by the integrator.
- `tests/`: 70 policy/static tests and 14 transport tests (total 84) via Python unittest.

## Startup contract
`RoundCoordinator` / canonical v40 `ChaosEventCore` on the *server* must decide the only raid event and choose a safe neutral spawn position. The server must send a **visual-only** snapshot with `{kind: START|STOMP|END, matchId, stageId, bossId: "GOROGAN", eventId, seq, position={x,y,z}}` on a server-owned RemoteEvent, and replicate round identity/stage via approved attributes or adapters. In old v40 the boss's canonical identifier is `BOSS_GOROGAN`: map it to visual `GOROGAN` in exactly one trusted adapter. No client may request or determine boss appearance/attack/round outcome. No second event scheduler. Stage S2/S4 dragon visuals are out of scope.

The server must ensure S1/S3 orientation and coordinate frame, account for giant height and map collision, and validate no overlap with egg/respawn areas. This packet's visual-only ring is **not** authoritative attack geometry. Boss damage/telegraph avoidance must be implemented/tested separately by the PC integrator.

## Local test (offline, not Studio)
`python -m unittest discover -s tests -q`
`python tools/verify_packet.py <restored ZIP>`
The test suite checks Python reference logic and **static text properties of Luau**; no Luau VM/compiler was used. A PASS does not validate Roblox API runtime/Studio FPS.

## PC integration gate
PC Codex has to finish actual v37 final saved-Place 2/3client QA and v39-H1 server reward integration first. Then restore this packet in a new isolated folder through approved `restore_handoff_safe.py` tool, verify ZIP hash/manifest and test results, source-review Luau, integrate the prefab in an **unpublished duplicate Place** with one externally authorized S1 event, confirm 2client, mobile reduced motion, no physics/hitbox interference, performance and Studio clean exit. Never auto-merge, publish, or charge.
