# OWNER Windows Codex review — D08 single canonical event bridge

## Dependencies and exact IDs

- Authentic PC Place / RoundCoordinator: read latest PC checkpoint, SHA, active Studio PID **first**; do not replace newer local PC source with historical SHA.
- v40 pure old `ChaosEventCore.luau` ZIP delivered as AES-GCM packet at GitHub `c0b0bf692410cb651893c38f1a453c93d9f8b3b5`. Reference core SHA256 `f6d6901a8dcb61cec1095e383e485950144d39ea43737c9b33d4351a66e88726`.
- D07 Gorogan combined server runtime `05fb3b1b986a2d8dfb925bce7592b13da6f61316`; D07 AI, physical rig and client visual are separate sealed dependencies.
- Genuine Windows v43-A scoped QA exists #213 #6758415195, saved Place SHA `a60ed5f7497ae0c3cbac717e32f2c62577c3ec3bef7eceb0b4b40f44b834e28f`. Cold reopen from exact saved Place is still a follow-up check.

## Critical integration decisions

1. Confirm the PC current source contains **no competing live boss/weather RNG or chooser**; if it does, stop and reconcile without creating a second authority. The old v40 core pure module **does not install itself** into a running game.
2. Introduce one server-only dispatcher, disabled by default until its `readRound`, `serverRoll`, `onWarning`, `onBossActivate`, `onWeatherActivate`, `onCleanup` are mapped to reviewed **true server** runtime APIs. No client Remote data. The `serverRoll` must be a one-off integer 0..99 from an authorized per-server RNG, not a client suggestion.
3. For a first S1 test, **do not enable S2/S4 alias** or weather activation without reviewed code. `RAIGALD` old source vs `LIGARDO` new source is a real incompatibility, not a spelling fix the agent can guess.
4. Existing visual warning→activation needs its own player-snapshot permissions, and all consumers must re-check round epoch/match/server state on activation/cleanup. A callback must be idempotent.
5. D07 Gorogan combined runtime is allowed ONLY after canonical `ACTIVATE kind=BOSS subtype=GOROGAN`, and only one Gorogan runtime can apply `TakeDamage`. Use `STOMP_RESOLVE` one-time receipt, real LOS/safe-zone and player states.
6. If the actual old `ChaosEventCore` API differs from the pinned reference, stop and review the diff instead of adapting by guess.

## S1 minimum acceptance

- Before any new events, reopen the true latest saved v43-A Place cold, run 2 client capture/expiry/cleanup + v39 result/regression, then protect current Place/ZIP/source/manifest with SHA.
- Match 1 with server roll 65–89 should produce once WARNING at >=20s, `ACTIVATE` >=2.5s later, and cleanup after proper round termination. Match 2 with roll 0–64 should never show boss/weather; replay must not roll again.
- Both-team 2client (3client if available), no duplicate boss, no missed cleanup on round end, stop/restart, two successive matches. No concurrent legacy weather controller.
- Negatives: wrong epoch, stale match, clock rewind, malformed roll, handler failure, alias mismatch S2, missing weather handler, insufficient match remaining, client-supplied RNG attempt, fake Remote activation. Confirm all are blocked.
- S1 Gorogan runtime/physical rig is **separate stage-gated task**. To call that a real pass, also demonstrate actual AI/rig footsteps, <=8 HP/hit, no duplicate target, no hits through walls/safezone, meaningful boss tell, mobile FPS, and proper Studio close owned-PID. Do not conflate bridge contract PASS and Studio gameplay PASS.
- Preserve final saved Place SHA, source set, ZIP/manifest hashes, QA logs, `CHECKPOINT` and `RESUME`, normal Studio Quit and owned-PID disappearance. Report no raw commercial source/Place/private keys/player identities to PUBLIC GitHub.

**Hard limits:** No main push/merge/production Roblox publish/paid items, no extra spend, no P0-A/B/C CAS/auth/independent review bypass, no automatic PC work from Issue comments, no unauthorized public commercial source.
