# TRAP RAIDERS v43-A — Neutral Skirmish (Chat-led reference)

This is a **standalone, unintegrated** reference implementation for PvPvE neutral zombie/beast faction conflicts. It never edits the user's current Windows Roblox Place, GitHub main, or the v37/v39 build.

## Completed here

- `luau/NeutralSkirmishCore.luau`: pure server-side state machine without Roblox APIs.
- `tests/reference.py`: Python comparison model; `tests/test_core.py` randomized and scenario cases.
- `tools/verify_packet.py`: ZIP manifest SHA, size, path and corruption checks.
- `tools/seal_handoff.py` / `tools/restore_handoff.py`: reusable secure GitHub handoff tools (source safe to publish, **never publish keys**).

## Example gameplay contract

- In S1, existing neutral ZOMBIE and BEAST groups can fight each other as different neutral species.
- Capturing a neutral group is a **contested, 3-second action**; BLUE vs RED simultaneously prevents progress.
- A successfully captured group fights for its new team for 8 seconds and reverts to neutral, followed by a 4-second rearm delay.
- At most one neutral group per team and two neutral groups in the reference test; the AI uses existing entities, not extra spawns.
- An egg carrier cannot capture a group; changing control never changes the egg's owning team or victory rule.
- The game server must validate alive state, team, distance, player intent, active match, and unit identity from actual server-owned objects before calling this module. **Client-provided data is never authoritative**.
- NPC movement, damage, targeting hooks, capture input UI, mobile UX and 2/3-client balancing **still need a real Windows Codex/Roblox Studio integration and QA**.

## Run offline tests

```bash
python -m unittest discover -s tests -q
python tools/verify_packet.py TRAP_RAIDERS_v43A_ChatLead.zip
```

The ZIP integrity tool runs on a complete packaged ZIP, not on the source tree.

## Design and status

- `docs/INTEGRATION_GATE.md`: prerequisites, restrictions and Studio tests.
- `docs/GITHUB_HANDOFF_STANDARD.md`: cross-P0 secure distribution process.
- `QA_REPORT.md`: factual offline test report. `STUDIO_QA=NOT_TESTED`.
- `RESUME.md`: next action for Windows Codex.

All functionality is optional, free and symmetric in RED/BLUE. Never interpret offline Python PASS as proof that Studio's Luau compiler or real gameplay passed.
