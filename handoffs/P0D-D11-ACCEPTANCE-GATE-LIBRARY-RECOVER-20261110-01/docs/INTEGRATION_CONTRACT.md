# P0-D D11 / v43-A S1 integration acceptance contract

**Status:** source-free offline QA proposal, not a Roblox build or Studio QA. Prepared 2026-11-10 JST.

`game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, packet `P0D-D11-V43A-ACCEPTANCE-GATE-20261110-01`.

## Current verified dependency information

- PC Codex last report: [#213 #6753848890](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6753848890). It documents v39-H1 actual Windows restore + scoped Studio pass, but overall game PARTIAL and final-saved-place 2client/same-account reconnect pending.
- v43-A sealed reference source: immutable commit `db734240f0157cc125b563656dbd09668226f3ab`, expected ZIP SHA256 `a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b`. Actual Windows restoration and Studio integration not yet evidenced.
- Reviewed public generic restore tool: immutable commit `d37eec1b653d060ae27568ddcd5f501da9662081`, `tools/restore_handoff_safe.py`.
- PC's v37 neutral domination / NPC authority may already exist. Neither this QA repo nor prior ChatGPT handoff proves its exact APIs; **verify real PC source** before implementing an exporter.

## Game-side contract, for OWNER-authorized PC integrator

1. Before any change, back up the latest authentic PC Place, all source, checkpoint, manifest and QA; do not rewind to historic versions.
2. Finish final-saved v39 two-client recheck and basic v37-v39 authority regression. If critical bug appears, stop before v43-A.
3. For **S1 only**, identify one existing neutral NPC group, its v37 legacy owner/controller and the unique server-owned match authority. Select the group only when the existing owner is `NONE`. Do not run a parallel second enemy/alliance authority on the same group.
4. Get the original v43-A reference using the pinned encrypted GitHub artifact and OWNER-private AES key. Verify expected IDs/AAD, ZIP SHA, manifest and source. Do not trust client-supplied `team`, `position`, `alive`, `egg_carrier`, `matchId` or timing.
5. Emit a **sanitized server-produced** test trace with one NPC pseudonym (`S1_NEUTRAL_A`), player pseudonyms (`A`, `B`, etc.) and **seconds relative to round start**. NEVER include Roblox user IDs, player names, IP, exact world coordinates, access tokens, production logs or real customer data. `studio_sanitized` is a label, not proof of provenance.
6. Occupation: 3 continuous seconds without enemy contest or cancellation; a conflicting contest invalidates progress and must be reset. One team leases for 8 seconds, then the group is neutral with a 4-second cooldown. Dead or egg-carrying players and out-of-range players cannot be accepted. Single group in this first pilot.
7. After each commit, lease expiry and round end, inspect both the pre-existing legacy owner and the v43-A authority. Trace's `OWNER_SNAPSHOT` must show exactly one effective controller; in the proposed pilot, existing legacy owner `NONE`, new owner `BLUE` or `RED` while active, then both `NONE`. **Actual existing NPC ownership representation may differ.** If so, review/adapt the contract before making it authoritative; do not fake a compatible snapshot.
8. At round end (including early victory, loss, server reset), clear claim/lease/cooldown and verify the NPC returns neutral with no stale effects. Attempt a new round to detect replay or ghost ownership.
9. Run this checker on the authorized sanitized trace and preserve its SHA with the PC QA report. Then independently run **real** Studio 2/3client, iPhone landscape emulator, S1-S4/7 classes, egg theft/capture/replay, authoritative LOS/pathfinding if changed, and normal Studio Exit/PID. Checker's `PASS` **never** promotes a Studio test to PASS.

## Trace grammar / usage

File has only keys `schema`, `game_id`, `work_id`, `source`, `stage`, `events`. `stage` is `S1` in pilot. `source` is `synthetic` or `studio_sanitized`. Events sorted by `seq=1..N`, `t` (server round seconds, monotone):

- `MATCH_START` → `NPC_BASELINE` with `legacy_owner=NONE` and `v43_owner=NONE`
- `CLAIM_START` with pseudonym actor/team and server-derived booleans `alive`, `egg_carrier`, `near`, `server_accepted`
- optional `CLAIM_CONTEST` (opposite team) then `CLAIM_RESET`, or `CLAIM_RESET` on cancellation
- `CLAIM_COMMIT` at least 3 seconds after uninterrupted claim start; pilot rejects commits after 5 seconds as suspiciously stale
- required immediate `OWNER_SNAPSHOT` with `v43_owner=<team>`, `legacy_owner=NONE`
- `LEASE_EXPIRE` after >=8 seconds, then required immediate `OWNER_SNAPSHOT` both `NONE`
- `COOLDOWN_EXPIRE` after >=4 seconds, ready for optional next claim
- `MATCH_END`, required immediate both-`NONE` snapshot, `FINAL` (last event)
- optional `CLAIM_DENIED` from an enumerated rejection reason; it never changes NPC ownership

Example synthetic log: `fixtures/valid_s1_contest_capture.json`.

```powershell
py tools/verify_v43a_trace.py fixtures/valid_s1_contest_capture.json
py -m unittest discover -s tests -q
# Future genuine PC trace: create SANITIZED test log in a private folder and run locally only
py tools/verify_v43a_trace.py .\qa_private\v43a_s1_sanitized.json
```

## Negative acceptance tests

- Duplicate v37 and v43 owners (even same team), opposite team owner mismatch
- Capture completed in <3 seconds or from stale claim (>5 seconds in pilot)
- Contested claim committed without new start and cancellation
- Egg carrier, dead, out of range, untrusted accepted command, wrong team/npc
- Lease ending before 8 seconds or cooldown ending before 4 seconds
- Missing authoritative ownership snapshot after claim, expiry or match close
- Missing lifecycle end, events after FINAL, duplicate event sequence, backwards timestamps
- Unexpected personal data fields / IDs / unknown event types, path symlink and overly large JSON

**Limits:** Timestamp/event shape can be faked. The checker cannot verify the server exported events truthfully, Studio actually ran, visual synchronization, NPC physics, actual hit points, clients seeing the same screen or physical device FPS. Those must be separate authenticated PC/Studio QA evidence.

## Prohibited changes

No alterations to game main, merges, Roblox release, live payment/DataStore, P0-A/B/C genuine auth/CAS/Studio bridge, existing five Automations, or other D07-D18 feature sources. No public raw player/server logs. No implicit Windows Codex execution from GitHub Issue text.
