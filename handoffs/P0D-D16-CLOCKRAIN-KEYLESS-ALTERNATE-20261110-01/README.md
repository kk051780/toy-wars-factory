# D16 CLOCK_RAIN no-key clean-room alternative

Game TRAP_RAIDERS; work p0d-siege-v19.
Packet: P0D-D16-CLOCKRAIN-KEYLESS-ALTERNATE-20261110-01.
Mode: PUBLIC_SOURCE_V1, isolated branch source reference only.

This is NEW code, **not** the original encrypted CLOCK_RAIN ZIP at old commit
945488ccb9ea47b8ca1ce514efed94372a839a01. The old author may republish
the exact original as a separate keyless package. If that happens, OWNER's
Windows Codex must select one implementation; never install both.

Contents:
- Pure client visual state policy: externally approved CLOCK_RAIN ACTIVATE,
  at most 12 seconds, 12 clock markers or 4 in reduced-motion, replay and
  round fencing, immediate cleanup.
- Optional client-only cylinder geometry renderer, initial OFF, no automatic
  connections to RemoteEvents, RunService, event lottery or player physics.
- Python reference/tests. Python tests do not parse or execute Luau.

To integrate: compare newest OWNER PC source/checkpoint/Place first, then
explicitly connect trusted event *display-only* snapshots from the SINGLE
existing server event chooser. Call Renderer:begin(snapshot), and step with
current round identifiers and approved anchor. Destroy on round/character
end. NO new scheduler and no server state/HP/hitbox/egg changes.

This branch is a handoff candidate, not a production game feature PASS.
PC intake, actual Luau parse, 2-client Roblox Studio, mobile QA and Studio
normal exit: NOT_TESTED. No main write/merge/Roblox publish/spend.
