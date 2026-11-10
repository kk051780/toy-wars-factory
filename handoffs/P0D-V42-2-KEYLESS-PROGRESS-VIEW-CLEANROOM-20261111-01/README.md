# TRAP RAIDERS — v42.2 progression display, public-source cleanroom candidate

**Game** `TRAP_RAIDERS` · **work** `p0d-siege-v19` · `PUBLIC_SOURCE_V1`.

This is an **independent, new, keyless reference** for the missing historical v42.2 level/mastery *display slice only*. The original v42.2 ZIP was not available in this environment and **has not been decrypted, recovered, or migrated**. It must not be counted toward the original-source recovery total. Historic v42.2 is still a `WAIT_ORIGINAL_ZIP` candidate. If OWNER PC already has equivalent presentation, do not install this candidate.

## What this actually does

- Pure `src/ProgressViewModel.luau` maps an already authenticated **server-owned** read-only level/XP snapshot to labels and fractions. Required: 1..25 level, seven allowed job IDs and 0..5 mastery level; no newly assumed job names or XP threshold formula.
- Validates actor/match/epoch/active round context, allowed job IDs, exact job roster, finite whole-number progress. Invalid inputs reject rather than clamp. Never invents awards or saved data; `sessionOnly` and `saved` only echo server-provided flags.
- Emits display values only: `levelLabel`, `levelFraction`, `jobs`, `grantsGameplayStats=false`. No GUI objects, economy, combat, purchases, DataStore, new Remote listeners, rewards or scheduler.
- `reference/progress_view.py` is a test oracle, **not** production Roblox code.

## Integration: OWNER Windows Codex only

1. First re-read #218 current handoff ledger and #213 actual newest PC checkpoint, and preserve latest PC Place/source/HEAD/manifest. Current original v42.2 may now have been recovered by another author; prefer identical original, otherwise compare UI only.
2. Resolve real existing server projection structure and actual seven job IDs. The `authority='SERVER'` field **cannot authenticate a client Remote**. Only a server-validated round snapshot and server-known `viewerId`, `matchId`, `epoch`, `allowedJobIds` may call this module; enforce network ownership in existing server authority.
3. Do **not** replace or instantiate a second XP ledger. v40–v42 `FairProgressionFallback`, historical v42.1/v42.2, v39 SessionStamp and any PC newer XP code must each have only one true reward sink. Do not add UpdateAsync just to show progress.
4. If selected, attach display values to existing HUD exactly once; verify 2client separation, rejoin, round restart, false remote, max-level/multiple jobs, landscape phone readability, FPS, Studio normal exit. No existing PC/Studio trial is claimed here.

Offline: `python -m unittest discover -s tests -p 'test_*.py' -v`.

## Delivery status

Actual source and tests are plaintext and public in one isolated GitHub handoff branch with SHA manifest. Tests are offline only. Lua parser/PC intake/Studio/play/2client/mobile are `NOT_TESTED`. No change to main/merge, production Roblox, real payments, P0-A/B/C CAS or reviews, existing automations, or other chat branches.
