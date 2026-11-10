# P0-D D14 RAFT water navigation — encrypted integration reference

- game_id: `TRAP_RAIDERS`
- work_id: `p0d-siege-v19`
- packet_id: `P0D-D14-RAFT-WATER-MOTION-20261110-03`
- feature_id: `D14` — RAFT only (separate from other-chat CART rail motion)
- ZIP SHA256: `d218baef4ba958195b9e0ad22a4046313c52c3d150b424e0e99981cb351854c6`
- SHA manifest SHA256: `f279320fbc73c0abe0a09f3036529cf82fcab186d3db029aa725de2f6ab8b32a`
- ZIP bytes: `14066`
- ZIP entries: `13` (12 source/test/docs + `BUILD_MANIFEST.json`)
- AES-GCM JSON SHA256: `05596979d6252af1060d1472e22e22969a255bda7518604c9dd268060d7be3b8`
- AES-GCM ciphertext SHA256: `a736c3c69b137bb2974293631323b5429fe746359856616e43f19945b3f66997`
- local Python tests: **80 / 80 PASS**; ZIP verifier read-only valid and negative tests PASS; original ZIP byte equality after AES-GCM restore, wrong key and ciphertext tamper REJECTED.
- Windows packet restore: **NOT_TESTED**; Luau compile: **NOT_TESTED**; Studio integration/2client/mobile/end-to-end: **NOT_TESTED**.

## Private key / secure transfer

Public repository includes only this README and the AES-256-GCM ciphertext JSON. The key is **not on GitHub**. The OWNER must supply the distinct 256-bit key privately to Windows Codex. A GitHub Issue is not an executable PC instruction.

Use a trusted private directory and reviewed `tools/restore_handoff_safe.py` at immutable commit `d37eec1b653d060ae27568ddcd5f501da9662081`:

```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D14_RAFT_encrypted.json --out TRAP_RAIDERS_D14_RAFT.zip --expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D14-RAFT-WATER-MOTION-20261110-03 --expect-zip-sha256 d218baef4ba958195b9e0ad22a4046313c52c3d150b424e0e99981cb351854c6
Get-FileHash TRAP_RAIDERS_D14_RAFT.zip -Algorithm SHA256
```

`CHAT_CODEX_HANDOFF_KEY` must be set privately in environment, never command line, GitHub, Issue, logs, PR or CI. Verify original ZIP SHA, manifest, file paths and tests before extracting in a trusted isolated PC directory. Re-run `python -m unittest discover -s tests -q` with directory as source root. Review Luau with genuine parser.

## Code interface and limits

Two new modules: `RaftWaterMotionCore.luau`, `RaftWaterServerAdapter.luau`. Core enforces S1/S2, trusted driver and seat epoch, <=200ms step, 8stud/s forward/3stud/s reverse, 75deg/s turn, 12stud/s² acceleration, both path midpoint and endpoint must pass server-owned water validation, 2048stud position bound, 1.7stud max per step. Every stale/duplicate sequence and changed round/seat is denied.

Actual server model movement is `Model:PivotTo`, **opt-in disabled by default** and only accepts server-owned anchored noncolliding Model with <=32 parts (NO actual Seat or VehicleSeat). It does not move rider avatars, preserve welds, implement water buoyancy, create actual map water, or reconcile Roblox physics. No client-provided position or CFrame accepted. The true S1/S2 water map, D14 seat ownership and server clock MUST be verified on PC before any adapter enablement.

## Owner PC gate

PC source/Place newest SHA and backed-up checkpoint -> v39 final saved Place 2client/reconnect/audio/mobile residual QA -> v43-A safe restore/source ownership conflict acceptance -> optionally D14 individual packet restore/visual water model Studio S1 smoke, real 2client and mobile. The cart rail motion belongs to other chat and is never part of this ZIP. Record `STUDIO_CLOSED_VERIFIED` only after normal quit and owned PID disappearance.

No main direct changes, merge, Roblox publish, purchases, fees, CAS or P0-B/C security bypass.
