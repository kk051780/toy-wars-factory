# TRAP RAIDERS — v39-H1 Session Stamp Chat Lead Packet

Game: TRAP_RAIDERS / work_id: `p0d-siege-v19` / packet: `v39-h1-chatlead-ref-20261110`

**A real coding handoff, not a Roblox integration or a released game.** The package contains an independent reference Luau reward core, read-only UI view model, isolated Studio smoke script, Python mirror, 50 deterministic regression tests, and integration checklist. Its only reward is **session-only, non-persistent, free cosmetic milestone progress**.

- Participation earned: **+1** for a legitimate completed round with at least one server-recognized meaningful action and sufficient active seconds.
- Win **or** validated contribution: **+1 extra**. Maximum **2 per round**.
- Session milestones at **3** and **6** stamps: cosmetic-only preview IDs `FREE_EGG_BANNER`, `FREE_TRAP_TRAIL`.
- Local anonymous `matchId` idempotence: repeated finalized rounds do **not** award again. Hard cap 512 finalized matches per user session; fail closed instead of evicting old history.
- A zero-stamp AFK round is still marked finalized, preventing later award replay under the same match ID.
- `sessionOnly=true`, `saved=false` and visible `This session only - not saved` label. **No DataStore API and no persistent claim.**

## Security boundary

The module is pure and assumes the **caller is an authenticated, server-owned MatchCoordinator** that has validated round lifecycle, match ID, roster, job, winner, contribution, and meaningful actions from actual server-side events. `kind=SERVER_FINALIZED_ROUND` is a **shape marker, not proof**. Do not pass RemoteEvent payloads, client-supplied state, arbitrary reward claims, or assume this code itself authenticates matches.

## Running offline checks

`python -m unittest discover -s tests -v`

`python verify_packet.py TRAP_RAIDERS_v39_ChatLead.zip`

## Next Codex integration

**Wait for v37's actual Studio QA**. First read the latest PC `CHECKPOINT.md`, `RESUME.md`, `BUILD_MANIFEST.json` and `.rbxlx`/Luau source; inspect existing result UI and rematch button. Implement one thin server-only adapter from authoritative `RoundCoordinator` to `SessionStampCore.apply`, store user session state in a server-only map, and send the redacted view to the UI. For the UI, reuse the existing result screen and lobby pedestal; do not duplicate HUD or existing monster gallery. Keep base v36.1/v37 and other P0 projects unchanged.

**Not tested here**: Luau runtime, Studio, DataStore, 2 client, real/mobile devices, existing game API integration. Existing P0-A/B/C protections and source privacy apply. Read `docs/CODEX_HANDOFF.md` and `QA_REPORT.md`.
