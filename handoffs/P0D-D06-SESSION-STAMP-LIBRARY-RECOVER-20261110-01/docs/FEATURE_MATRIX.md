# Feature matrix (this packet vs actual game)

| Feature | Packet | Existing PC live game |
|---|---|---|
| Session-only TRAP_STAMP policy | `REFERENCE_LUAU_CREATED` | `NOT_INTEGRATED` |
| Duplicate & AFK checks | `PYTHON_REGRESSION_PASS` | `STUDIO_NOT_TESTED` |
| Win or assist max+1 bonus | `PYTHON_REGRESSION_PASS` | `STUDIO_NOT_TESTED` |
| 3/6 cosmetic preview unlock | `REFERENCE_LUAU_CREATED` | `STUDIO_NOT_TESTED` |
| Result UI view only, saved=false | `REFERENCE_LUAU_CREATED` | `STUDIO_NOT_TESTED` |
| DataStore persistent rewards | `EXCLUDED` | `UNKNOWN` |
| Server MatchCoordinator adapter | `INTEGRATION_SPEC_ONLY` | `UNKNOWN` |
| v37 alarms/pins 2client | `EXCLUDED` | `LAST_GITHUB_STATUS_INCOMPLETE` |
| v43 monster contest | `DESIGN_ONLY` | `NOT_IMPLEMENTED_BY_PACKET` |
| Source publish/merge | `NO` | `NO` |
