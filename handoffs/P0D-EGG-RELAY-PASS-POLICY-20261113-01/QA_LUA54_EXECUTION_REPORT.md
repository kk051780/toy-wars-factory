# P0D-EGG-RELAY-001 / 41-case execution result — Lua 5.4 compatibility, 2026-11-14

## Verified outcome
- **Actual independently executed** Python mirror: 35/35 PASS in local Python 3.13. Exact source `tests/reference_policy.py` GitBlob `2e5bcc1fb2356f2552b1dc155c5babeaf3b22203`.
- **Actually executed** all **41 original Luau test source cases** in Lua 5.4's C runtime on Linux x86_64, via `gcc`-built C API shell using local system `liblua5.4.so.0`: `P0D_EGG_RELAY_NATIVE_POLICY_41_CASES_PASS`, process exit code **0**. This **IS NOT Luau CLI** and **IS NOT Roblox Studio**.
- Original production policy source remains byte-identical to immutable GitBlob `ef9b65bd6520231f299f21c5cfe2aa250798c8d0`; SHA256 `7515fecbb4994d39bccdd7dba49229bcb151ab64d084da84e332c41f7bc5dfa0`, local SHA256 checked.
- Original 41-case test source read from exact GitHub source: pre-fix GitBlob `801ac8f52cc3fec9bc159b73803853aea845a582`. Its Lua 5.4 execution **failed** on test `NaN server clock`: `policy mutated world state` (false test harness positive), because `NaN ~= NaN` even though the policy left the state untouched. This means the prior source would also be prone to incorrect purity assertion on a real Luau CLI.
- **Corrected** only `deepCopy/eq` test helper's non-table comparison to allow **both operands NaN**, under authoritative `tests/native_policy_cases.luau` new SHA256 `47734f250bac41ec37a5c214cc8a10a81c51433e1d49c03baeca5539d547b402`, GitBlob `004ae0569d89abcedaa6ddedff05f006246d2265`. All 41 cases then PASS in the Lua5.4-compatible harness. Test test-case count remains exactly 41. Original server policy was **not modified**.
- Compatibility adaptation: only replace **one Luau compound assignment** `tests += 1` with Lua 5.4 equivalent `tests = tests + 1`; all other test content and production policy text unchanged. Pre-existing Luau source still uses `+=` and pinned GitHub Actions workflow is intended to run untouched original Luau.

## Reproduce on compatible Linux with liblua5.4
1. Read the immutable current GitHub files `src/EggRelayPolicy.luau`, `tests/native_policy_cases.luau`; verify both SHA above.
2. Generate `local Relay=(function()\n` + unchanged policy source + `\nend)()\n` + test source with **only** `tests += 1` converted to `tests = tests + 1`. The resulting test script's local SHA256 in this execution was `c4c3e3bcac8b6a60c17ef5cad44ef086beffeeda8405cafa4b58ae6a3f49f78c`.
3. Execute with Lua 5.4 C API `luaL_newstate`/`luaL_openlibs`/`luaL_loadfilex`/`lua_pcallk` on system `liblua5.4.so.0`. Captured stdout exactly `P0D_EGG_RELAY_NATIVE_POLICY_41_CASES_PASS`, exit 0. Pinned source remained unchanged.

## Status boundary
- **Luau compiler/runtime under actual pinned Luau**: NOT_VERIFIED (GitHub run ID/result UNKNOWN; PR-only lookup does not establish push-trigger status).
- Roblox Studio engine, two actual clients, Android UI, user FUN: **NOT_TESTED**.
- Egg Relay is a pure **authorization policy**, not yet wired to the real Game or official RC. No public game, main, old Game/Remote/Score/HP/XP/Store, paid switch, automation schedule, or PC/Codex was changed.
- OWNER latest V5 direct-to-single-RC contract supersedes the old requirement for a human Studio session before every RC source admission. Sole official RC writer remains #220, actual source/authority/full build QA and reversible feature switch needed for future relay integration. Real Studio/FUN still mandatory before **public release**.
- Last official release-readiness score remains 75/100 FUN_NO_GO even though the canonical rich51 RC now has **53 Luau source paths** and accepted `REALM_HUNT_V1` in actual RC at `981b4b3616acb20001f4148fc02cc4b29f2b87ae` (authoritative #220 issuecomment6862363515). Do not conflate RC source inventory with release-readiness score.

## Handoff
NEXT=keep pure relay source fixed and supply the corrected 41-case Luau suite to #220. To make egg relay real gameplay under OWNER V5 fastlane: #220 must attach to canonical single Game/Remote, implement server-checked atomic egg transfer with epoch/version/LOS/2-client invariants, add `EGG_RELAY_V1` reversible switch (default OFF until accepted), perform one canonical Luau+Rojo CI. **Never claim that this source-only delivery is a gameplay integration.**
