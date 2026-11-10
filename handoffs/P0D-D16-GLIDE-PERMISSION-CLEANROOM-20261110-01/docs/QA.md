# QA / acceptance status

- Python offline contract tests: run `python -m unittest discover -s tests -p 'test_*.py' -v` from this packet root.
- Luau parser/Roblox execution: NOT_TESTED.
- Real Windows owner-PC restore: NOT_TESTED.
- True 2-client/mobile Studio gameplay / physics movement caps: NOT_TESTED.
- Real saved Place SHA / normal Studio exit: NOT_TESTED.

## Invariants and integration prerequisites

1. `config.enabled` is default false. Only the server may supply all `snapshot` fields, `userId`, integer `epoch`, monotonic `seq` and `now`; never trust client timing, team, role, motion or item assertions.
2. The decision `START` requires 3–60 studs of already-fallen distance and strictly descending velocity, and aborts on carried egg, snare, D14 vehicle seat occupancy, D09 rewind, death, landing, team/round change, time limit or feature disable.
3. Replayed sequence/time/epoch never produces START. The server physics adapter must obey STOP even on stale/invalid snapshots and enforce real horizontal/vertical speed caps; this policy returns target caps without applying force.
4. The existing D16 GlidePermissionCore old AES packet and this new cleanroom may never both own a player. If old exact ZIP becomes available, prefer vetted original or explicitly compare/select one; record the selected commit/source SHA.
5. Python oracle is not an executed Luau test. Do not label as Studio PASS; use actual unpublished 2-client/mobile runs before ever enabling.
