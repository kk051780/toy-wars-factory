# Offline QA — V2

- Test environment: standard CPython, `python -m unittest discover -s tests -p 'test_*.py'`.
- Python interleaving analogue and static Luau source contract: **60 cases PASS, 0 failures, 0 skipped** in authoring workspace.
- Scenarios: ordinary giant/mini, explicit approval/mapping gates, one D08 event authority, duplicate/stale rounds, invalid input/roster/time, stopped/expired round, wrong cleanup, intentional clock reversal, stop/cleanup reentrancy **during each trusted callback**, unexpectedly suspending `Core.begin`, rollback and close failure fail-safe.
- V1 findings: pending activation not cancelable from D08 cleanup, STOP does not call Core.close; V2 changes tested in Python analogue, not live Luau.
- Dependency source: D08 canonical `70dcc3b50129c288441452776360588184ca6c22`, D16 cleanroom scale core `883ca3b790c938587c5d9c305a887a1ffff1249f` (not modified).
- LuaU parse/type checker: **NOT_TESTED**.
- Real Roblox environment, PC integration, actual callback scheduling, 2/3-client, mobile, Studio normal exit: **NOT_TESTED**.
- Main/merge/publish/paid changes: **NONE**.
