# Acceptance matrix (check only when real Windows Codex / Studio evidence exists)

| Scenario | Expected | Evidence now |
|---|---|---|
| S1/S2/S3/S4 win/loss/draw | Only final server result maps to progress | Python fixtures only |
| Blue egg delivery by red roster member | Reject inconsistent receipt | Python PASS |
| Client forged win/egg/XP/mastery fields | Ignore; server match ledger is sole input | Python PASS; spoofed Roblox Remote NOT_TESTED |
| Guest participant, wrong team or duplicate roster member | Reject | Python PASS |
| Invalid duration/negative action/NaN/fake boolean | Reject | Python PASS |
| Zero-action AFK | Gate passes zero action; Core awards no XP | Gate reference only; real Core NOT_TESTED |
| Repeated saved match / cross-server reconnect | No new XP or fanfare | v42.2 integration NOT_TESTED |
| `UpdateAsync` retry / loss | No side effect callback, no false stored UI | NOT_TESTED |
| Lv1 vs Lv25 same class/conditions | exact identical combat/CC/summon/boss durations | NOT_TESTED |
| 2 clients / phone / Studio shutdown | real Play/Stop and owned PID gone | NOT_TESTED |

No release green signal can be derived from the 40 Python tests.
