# P0D S1 SIX-safe preview — actual native Luau dynamic integration QA

This is a **separate independent QA lane**, not an official release/RC branch write. It reads exact frozen complete S1 preview `65785c2e3b9bc37a6962f9ace128fbfcbb670901`. The official sole-writer RC remains `1263a03701211a652b99b91d2339575dc8104eff` until #220 integrator explicitly chooses INCLUDE_OR_SKIP.

## Coverage

The script imports the SHA-locked #234 proven 6-real-module runner and uses the **actual Game.server, actual Japanese MapBuilder, actual Config, actual S1Rules, actual LobbyTeamRecovery, and actual S1TrapRules**. Source authority is unchanged. Only test-side Roblox service fakes provide a `Vector3.zero` value and explicit heartbeat ticks.

New dynamic cases: active RED joiner takes true BLUE egg; exactly X+130 must preserve possession; X+130.25 drops egg, re-enables prompt, resets velocity and puts player at fixed RED spawn without ending round; Z<-76 also respawns; Y<-30 behavior preserved. Existing native team-leave order tests from #234 execute before and after player removal. Negative tests deliberately disable X, Z, egg drop, velocity zero and revert PlayerRemoving ordering. Native tests must see the expected assertion failures, not just exit code nonzero.

All six original-source pins and 37 source manifest are locked. No new game script is introduced into the actual place, no local Studio or real 2client or mobile tests are claimed. Treat any change in official RC and frozen SHA as **BLOCKED**, requiring a new independent review, not silent reinterpretation.

## Provenance

- Own lane: `CHAT-QA-S1-SIX-ARENA-EXIT-NATIVE-20261112-07`
- Source review: `65785c2e3b9bc37a6962f9ace128fbfcbb670901`
- Existing #234 native source: `4024c21238f913ffa226a38e4bd092de43d02af6`
- Existing #233 original roster harness: `664284d6ec29741060bead3bd0df66e9ea6b1e76`
- Actual Game Git blob `a575ef5175ace5aab59f1dbe3ad8dc74d3d1860d`
- Expected MapBuilder Git blob `94655d019fdf9798fa24a350ebf49f8290465ac0`
- Genuine upstream native Luau source pinned `f46d879e28302a430029304f7f6a162aed66f103`

Do not claim native PASS before inspecting the actual actions run head SHA, result and logs. GitHub Issue comments are NOT Windows Codex commands. No main/RC modifications, merge, Roblox public release, payment, P0ABC CAS or existing automation edits.
