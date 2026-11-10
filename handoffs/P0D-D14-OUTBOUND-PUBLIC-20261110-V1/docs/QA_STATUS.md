# QA status / LIMITATIONS

- Python 55/55 independent synthetic reference+static tests PASS (2026-11-10 JST).
- Luau parse / actual Roblox Studio / multiplayer / physical mobile: **NOT_TESTED**.
- Public encrypted-only handoff is a **reference candidate**. It is NOT an integrated game.
- The `D14VisualPublisherCore` is a pure intended contract; the ServerAdapter uses existing external PC server callbacks and does not start unless `enabled=true`, with legitimate authoritative seats/round/roster/map and reviewed snapshot mapper.
- Server timestamps must be monotonic and `sourceSeq` must continue increasing across driver epoch resets. If the current PC SeatCore doesn't provide that sequence, the OWNER integrator must assign a canonical server-side monotonic counter. No fake `authorizedServer=true` constants in production.
- Test-only `test_outbound_policy.py` models the intended contract; does **not** execute Lua bytecode.
- Security boundary: a malicious client cannot inject commands through this packet, but client-originated data passed by a faulty PC adapter would invalidate the guarantee. STOP if actual client visual snapshot field naming differs from the generated DTO.
- `Core.publish` updates its bookkeeping before the optional encoder/recipient checks; a refused send drops that visual frame. This is fail-closed but may leave the client waiting for a later permitted update. Future PC integration may refactor staging/commit if real Studio UX needs it after security review.
- No player character attachment, physics, actual Seat, Model PivotTo, cart collisions, client display construction, or input Remote.
