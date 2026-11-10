# D16 exact-original two-package acceptance: Windows Codex

**Authority and priority:** Latest Issue #218 top (`PUBLIC_SOURCE_V1`) + latest comments; #213 genuine Windows/Studio findings; #217 P0 boundaries. This packet is a **read-only compatibility verifier** and not a PC authorization token. OWNER directly instructs Windows Codex if actual PC work is desired.

## Read-only intake gate

1. Preserve latest PC source/Place and checkpoint SHA; note currently recorded D07 S1 `PARTIAL_NOT_READY` status. Do not overwrite a newer checkpoint.
2. Stage D16 SCALE exact original commit `584b11ef24cf3d44695d86b505207491bbd3844e` and D16 VISUAL exact original commit `226a5664ed50131868391289723c130d35abf48f` in separate **new** directories; run existing PUBLIC_SOURCE_V1 manifest and full tree verifier independently. Existing 21/21 Windows receipt does *not* cover these.
3. Run `python tools/run_exact_pair_qa.py --scale-root <EXACT_SCALE_ROOT> --visual-root <EXACT_VISUAL_ROOT> --json-out <NEW_RECEIPT_FILE>` (use valid Windows paths), require `ORIGINAL_PAIR_OFFLINE_PASS`, 252/252 checks, SHA proof for 3 original Python files. Otherwise `HANDOFF_BLOCKED` and no import.
4. Compare actual original Luau `src/ScaleFxCore.luau` / `src/ScaleFxSnapshotBridge.luau` / `src/ScaleFxClientPolicy.luau` and renderer/bootstrap with genuine current PC source and D08 single event chooser. **Offline Python PASS is not native Luau syntax PASS.**

## Critical wiring

- Original Core has 8s deadline in the **same monotonic server clock** supplied to `begin`, `advance`, and `SnapshotBridge.build`; `expiresAt` is *not* Unix time, `os.clock()` on a different device or Roblox server-synced `GetServerTimeNow()` without an explicit conversion. Bridge transports `remainingSeconds` to a client-local 8s deadline.
- Only the real D08 server-authorized event may begin the original Core. `GIANT_ONE` requires one actual trusted UserId string target; `MINI_ALL` has `actorId=nil` and uses bounded real server roster. The original visual renderer is client-local, noncollidable and display-only.
- Existing cleanroom scale Core `883ca3b7...`, cleanroom visual `356dcd0d...`, their older D08 gates `ac503729...` and `1877222d...` must be **held**, not installed alongside the originals. Optional new original-compatible D08 gate `71d682e63ebb2de80c39aaeafdf0cf420202cc68` is an independent *unadopted* source candidate, not part of this QA.
- Do not add another event chooser/RNG/scheduler/remote input listener; allow only one approved server-to-client cosmetic channel. Ensure expired/round-ended effects visibly clear even when packets are delayed.

## Native Studio QA remains independent

- Parse/require the actual Luau modules in an isolated unpublished Studio Place, ensure no false client authority. Verify S1 and S2 rounds, GIANT_ONE and MINI_ALL, both teams, true 8s TTL, target leave, round replacement, replay/forged remote rejection, latency, rapid rematch, R6/R15/accessory rigs, 8 clients ×18 parts caps, 90-stud rendering and phone landscape emulator FPS.
- Prove actual character size, Humanoid HP, movement, physical hitboxes, collision/query/touch and revenue flow **unchanged**. Stop/Save normally and verify only Codex-owned Studio PID exit. Preserve negative logs and record actual PASS/FAIL/BLOCKED in #213 and receipt in #218.
- Respect protected branch/PR authorization and the existing five Automations.

**Current delivery state:** 2 exact-original source packets exist on PUBLIC GitHub; original pair Python cross-contract QA ready; actual PC second-wave intake and native Studio are `NOT_TESTED` in this lane.
