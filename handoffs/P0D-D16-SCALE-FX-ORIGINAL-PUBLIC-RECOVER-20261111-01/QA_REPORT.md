# D16 QA / scope gates
- Python oracle tests: see runner output, not Studio proof.
- Luau parse and runtime: NOT_TESTED (no Luau compiler in this environment).
- Roblox Studio/multiplayer/mobile/physics/appearance: NOT_TESTED.
- Server remote and one-event safety: INTEGRATION_PENDING. Never expose `begin` through client-authored event.
- PC local game: UNVERIFIED_PC_LOCAL; no base source or .rbxlx in this ZIP.
- Acceptance on an isolated unpublished S1 Place only after v37 QA and D08 compatibility:
  1. Real D08 server picker owns single event; second picker not created.
  2. Giant-one scales visual proxy to 160% for exactly 8 sec; mini-all scales 70%, then clears.
  3. Real avatar body collision/hitbox, damage, movement and egg carrying **unchanged**.
  4. Two clients: both see same targets, late join doesn't alter active roster, disconnect cleanly clears.
  5. Different match/reconnect, round-end, duplicate eventId, expired event and unauthorized Remote reject.
  6. GUI has optional no-flash accessibility mode and never blocks egg/return objective.
  7. Play/Stop/Edit/save, owned Studio normal exit + PID disappear: NOT_TESTED.
- No v37/v39/v42/v43 reference modules imported, modified or silently replaced.
