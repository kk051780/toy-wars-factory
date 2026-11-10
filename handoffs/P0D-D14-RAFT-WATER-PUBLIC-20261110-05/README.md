# TRAP RAIDERS / P0-D — D14 RAFT-only water motion

This PRIVATE reference packet adds **server-side raft pose movement in authored, validated water**, not the separate cart rail system. It is NOT automatically executable from a GitHub issue.

## Design
- `RaftWaterMotionCore.luau` pure step function, S1/S2 only, max 8 studs/s forward and 3 reverse, 12 studs/s² acceleration, <=75°/s turning, <=200ms step, path validated at midpoint and endpoint, <=2048stud bounded coordinates.
- `RaftWaterServerAdapter.luau` opt-in disabled by default; only accepts anchored noncolliding server-owned Model with <=32 Parts and no Seat or VehicleSeat; `:PivotTo` moves only that model. Trusted server must supply actual driver, occupancy epoch, alive, seated, team, egg/snare/rewind state and water predicate. No client-supplied position/CFrame.
- Fail-closed on stale round, control replay, wrong seat epoch, time reversal, large dt, unauthorized driver, unsafe water and out-of-bounds. Driver change explicitly resets speed/sequence.

## Codex acceptance (after existing v39 QA then v43-A gate)
1. Verify actual PC game state/Place SHA; back up latest. Distinguish the separate cart rail motion claim and existing D14 VehicleSeatCore and vehicle visual model. NEVER overwrite their code.
2. Restore packet using `restore_handoff_safe.py` at immutable commit `d37eec1b653d060ae27568ddcd5f501da9662081`, private key in environment, expected game/packet/work/ZIP SHA from public README. Verify each ZIP manifest hash. Run Python tests then a real Luau parser.
3. Author **real** water region / safe routes from the actual S1/S2 map; do not guess any map coordinates. Bind D14 true driver-seat epoch and server clock. Test path edges, blocking at land/void, death/disconnect, egg and snare, double seat, spoofed Remote, 2client. Implement real passenger attachment ONLY as a separate reviewed pack.
4. In isolated unpublished Roblox Studio: test anchored server-owned noncollision model with no riders; verify server movement visible to 2 clients and iPhone landscape emulator, frame rates and cleanup. Stop->Edit->Save new Place->normal exit->verify owned PID stopped. Studio/PC status NOT_TESTED in this ChatGPT pack.

No main/merge/publish/paid assets/real transactions/extra costs. PUBLIC GitHub receives AES256-GCM ciphertext only, never plaintext private Luau or private key.
