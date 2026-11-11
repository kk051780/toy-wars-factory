# P0-D / TRAP RAIDERS: original lobby planner native execution

This is a **test-only** immutable source handoff. It does **not** introduce another gameplay owner or modify the 28-file integrated candidate, official S1 RC branch, repo main, automations, or Roblox Studio.

## Why

The S1 lobby team deadlock fix is now physically included in the 28-file corrected D07/D08/spatial + lobby composite, source commit `9de6496282c7bd4dcea586563f75da71d08d77ec`. The earlier 66 Python tests validated source-level behavior but did **not** run original typed Luau. The independent native compiler verified parsing of the preceding 27-file candidate, but did not execute this lobby module. This packet exercises **the actual original planner function** using Luau-lang's official interpreter, pinned to `f46d879e28302a430029304f7f6a162aed66f103`.

The CI workflow downloads precisely `candidate/src/server/LobbyTeamRecovery.luau` from `9de6496282c7bd4dcea586563f75da71d08d77ec` and verifies SHA256 `35c546f33e0454ceaf7fa26cf5ee44763673c6764906cc249ef282bb096ea404`. It *wraps* unchanged module bytes in a Luau local closure so Roblox-specific `require` is not necessary, then executes actual original `LobbyTeamRecovery.plan` against exhaustive masks and seeded large input/invalid-input tests. No client objects, Roblox API, or game state is simulated and the source is never rewritten.

## Actual execution contract

- Exhaustive 0–8 users: **511** team configurations.
- Seeded deterministic 1–64 users, eight configurations per size: **512** more configurations.
- Input mutation, minimal transfer count, final 0/1 balance, ID order and permutation invariance checked for every valid configuration.
- Invalid arrays, duplicated IDs, NaN/infinite IDs, unknown teams, extra fields and 65 users must fail closed.
- Negative Studio test UserIds and maximum safe integer cases covered.
- Positive Luau typed-function and intentionally failing runtime controls verify the command is executing code rather than always returning 0.

Final output must include `P0D_LOBBY_NATIVE_SEMANTIC_PASS` and `LUAU_NATIVE_RUNTIME_SEMANTIC_PASS`, the exact expected original SHA, and an assertion count of at least 5,000. **Do not claim PASS until an actual Actions run yields a completed SUCCESS and readable execution log.**

This is a pure Luau planner semantic test, **not** real player/team teleports, Roblox server loop, native Studio, PvP, mobile latency, monetization or first-release approval. Only Issue #220's sole S1 integrator may use the source evidence and authorize integration and eventual OWNER-directed real Studio QA.
