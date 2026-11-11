# P0-D S1: original D07/D08 selection-locked source stage

Game: TRAP_RAIDERS / p0d-siege-v19 / S1 release candidate source selection.

**NOT a runnable game, integrated RC, Studio PASS or publication approval.** This package is a direct, byte-for-byte stage of eleven already-delivered PUBLIC original Luau modules under `staged/src/server` and `staged/src/client`, with original Git object IDs, original immutable commit references, per-file SHA256, and explicit anti-duplicate exclusions in `SOURCE_LOCK.json`. No newly invented boss AI or second event selector.

Base S1 author Game is fixed at `35d7d0525388e885aac8281eff2315a59831e0cf`. Sole RC integrator is GitHub Issue #220 and owns `rc/p0d-s1-kids-rc01`; this staging branch never writes that branch.

**Critical compatibility:** D08 `CanonicalEventBridge.onBossActivate` passes `{phase,stage,epoch,validUntil,kind,subtype,matchId}`, but D07 `GoroganCombinedRuntime:start` requires `{event="ACTIVATE",kind="BOSS",subtype="GOROGAN",matchId,untilAt}` and a true original server-table attestation. Passing one directly to the other fails. We **reuse** the already-delivered `TrustedGoroganActivationMapper` from fixed commit `d3159f9b5369ff28163a92ffc8123f4f3e816631` instead of writing a second mapper.

The D07 Visual client expects a *different server-to-client-only* `TRAP_BossVisualEvent` than current S1's `TrapRaidersS1Remote`. The integration writer must set up one reviewed server-owned visual broadcast and its one client mount, with no second client-to-server authoritative listener.

**Source stage acceptance:** all 11 modules were fetched individually at their canonical Git commits and their Git blob IDs and byte sizes matched. The on-disk source stage reuses these exact original Git objects; source SHA256 values come from the respective PUBLIC_SOURCE_V1 manifests. The stage is not yet wired through Rojo or the existing S1 game loop. See `docs/INTEGRATION_GATE.md` for exact decision and final tests. The user-approved no-key/public-original-source policy applies only to TRAP_RAIDERS; no private Place, secrets or unrelated game assets.

The source stage contains no active `.server.luau` script; its sole `.client.luau` depends on a reviewed server-owned RemoteEvent. Nothing in this repository commit starts a new round/event scheduler or modifies Game.server.luau, the original source packets, main, Roblox production or charges.
