# V1.1 D15 repeated-cast poison receipt correction

Game TRAP_RAIDERS / p0d-siege-v19 / P0D-S1-KIDS-RC01. This is an isolated optional server-only adapter; the sole integrator owns release RC.

**Failure mode (previous v1 source `3e055a584eb249331d2e6ed362c25d1b371bc627`):** Original D15 `TrapRescueCore.advance()` emits `POISON_DAMAGE` fields `matchId`, `casterId`, `targetId`, `tick` without a unique successful-cast ID. Bridge receipt `matchId:casterId:targetId:tick` suppresses all second cast ticks against the same victim in the same match. Original D15 permits recast after cooldown, and prior testing omitted the same-pair second cast.

**Corrected contract:** Keep a server-only monotonically increasing `castSequence` per active round, assigning `castGenerationByTarget[targetId]` only if `Core.tryCast` accepts. Include generation in the dedupe key. This distinguishes a new legitimate cast while suppressing duplicate tick from the same cast. Missing generation cannot apply damage. On new round/end clear both mapping and receipts; on PlayerRemoving clear the departing target generation. The original D15 source stays byte-for-byte unchanged.

**QA:** 10 additional offline negative/positive tests + original 52 = 62/62 PASS. No actual native Luau or Roblox 2-client match executed here; #220 must run real recast after 12s, victim immunity, team changes, and owner Game callback dedupe test as final Studio QA. No OWNER PC Codex requested per packet.
