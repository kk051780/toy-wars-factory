# D07 Gorogan server AI – Codex-only integration gate

Packet: `P0D-D07-GOROGAN-SERVER-AI-20261110-02` (`p0d-siege-v19`). The two Luau modules are reference implementation, not live Roblox Studio code. Do **not** attach a public/client `RemoteEvent` to `start`, `tick`, or any callback.

## Canonical event mapping and conflicts

Existing v40 `ChaosEventCore.classify` chooses `kind="BOSS", subtype="GOROGAN"` only for S1/S3, and emits `ACTIVATE` with a total boss active event window of **17s**. Existing D07 client visual packet is 14s max, 2-second warning, 3 stomps max. Map authoritative server activation to `Core.start` with `endsAt = min(now+14, canonicalEventActiveEnd)`. Do **not** create another random chooser. D07 visual `START` must contain `matchId`, `stageId`, `eventId`, `bossId="GOROGAN"`, `seq`, valid `position`, then `STOMP` and `END` for the same event. Visual adapter uses matchId mapping. The visual telemetry is never treated as hit confirmation.

## PC server adapter requirements

- Before integration, validate authentic latest local Place/source SHA, backup, no main writes, no unauthorized release; v37 final QA and v39 one-packet Studio QA are preceding gates.
- Instantiate **real server-owned NPC rig** in the existing 4-map game once, with Humanoid and real server PathfindingService or MoveTo callback. Do not use the decorative client-only gorogan Part model as a physical rig.
- `integrationApproved=true` is a local safety interlock, **NOT evidence** of server authentication. `isCanonicalBossActivation` must compare authoritative v40 `ACTIVATE` event and actual match sequence (not `bool` supplied by a client). `getStageId` and the other seven required callbacks are purely server-side implementations; never bind player Remote claims directly.
- Movement commands are *bounded intentions* (≤8 studs per command, ≥0.75s apart, leash 42 studs), **not teleports**. `requestNavigation` must validate ground, wall, nav mesh, same match, arena and physical rig; if path blocked, stay put (no through-wall jumps).
- Same `eventId` spawn once per round, 14s max; attack warning 2s; max three, radius 7 studs, 8 damage each, at least 3s after previous resolution. Attack neutral to both teams. Fresh roster at resolution; independent server LOS and protected zone check, invulnerability rules, actual `Humanoid:TakeDamage`, deduplicated attackId/hitPlayer. Both teams see the same telegraph; no forced camera or non-optional flashing.
- Sample runtime's `isRoundActive`, `getRoster`, `getBossPosition`, `requestNavigation`, `isLineOfSight`, `applyServerDamage` are **integration points, not implemented game logic**. Review callback semantics and fail closed on unavailable services. `getStageId` and `isCanonicalBossActivation` must also be installed (runtime deliberately fails to start without explicit authoritative integration).
- On win, egg return, rematch, server shutdown, or early round exit: invoke `stop` and destroy only this job's server-owned NPC model. End signal clears visuals; if event stream fails, 14s visual TTL still prevents lasting ghost. No DataStore, credits, Robux, new reward source or hidden boss pay-to-win.

## Acceptance gate for unpublished Studio

S1 2-client/3-client: event trigger from canonical v40 only, client decorative boss and server-owned physical rig positioning; non-teleport navigation; alarm/egg unchanged; same stomp warning visible to both teams; approaching victim hit once after 2s only, player who escapes before impact no hit; behind wall no hit; safe spawn no hit; 3 attacks maximum; spoofed Remote rejected; rematch & stale-match cleanup; FPS (normal/reduced motion, landscape emulator) and NPC pathfinding; S3 next. Existing ChatScript error diagnosis independent. Studio Stop→Edit→Save→Quit and owned PID disappearance. Report PASS/FAIL/NOT_TESTED with actual gameplay evidence.

Critical: **Python tests model pure decisions only. Luau parse, server pathfinding, damage, real 3D rig, multi-client/physical phone and live revenue are all NOT_TESTED.**
