# TRAP RAIDERS — S1 FTUE + D07/D08 + lobby + Japanese results: integrated source candidate

**STATUS: ISOLATED_CHAT_SOURCE_CANDIDATE / NOT OFFICIAL #220 RC / Studio NOT_TESTED / PUBLISH NOT_APPROVED.**

This is the actual full source tree copied by original immutable Git blob objects from source-built 30-file S1 candidate `b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc`, with ONLY ONE changed EXECUTABLE: `src/client/HUD.client.luau` replaced with the OWN native-Luau-tested Japanese RESULTS display source from `f3a58a64b20f103648adfce52320c05a8b7bc406`.

## Real integrated behavior in this selected candidate
- Single Game.server server owns join/team/spawn, eggs, score, castle HP, melee, victory/results/rematch and one Remote.
- Corrected D07 original Gorogan server modules, D08 canonical host/mapper and spatial warning ring are physically present, but BOTH **`CANONICAL_S1_ENABLED=false` and `D07_D08_RELEASE_REVIEW_APPROVED=false`** in Game: actual boss/event behavior is **OFF**, NOT Studio certified.
- Lobby deadlock recovery planner and four source changes are already in the selected Game; FTUE first-minute original model and client overlay are mounted in Rojo.
- The patched single HUD now displays server result codes in Japanese (win/loss/draw, egg/castle/quit/team empty/time limit), clamps invalid countdown seconds; original attacking, boss packet rendering and input remain byte-exact around this narrowly identified region.
- All **other 19 of 20 Luau source files** and `default.project.json` are Git-blobs byte-identical to the chosen 30-file original. No additional HUD, Remote, server script, paid item or persistence.

## Proof and constraints
- A strict six-key PUBLIC_SOURCE_V1 `BUILD_MANIFEST.json` covers all file bytes except itself. `docs/INTEGRATION_PROVENANCE.json` pins original 19 Luau blob SHA1, SHA256 and sizes, plus the replaced HUD.
- This packet includes `tests/test_result_full_composite.py` for exact 20 runtime Lua source pins, no extra Luau, strict manifest/readback, Rojo single mount and safety flags. Original 80+ offline tests are retained.
- Previous QA `docs/OFFLINE_TEST_LOG.txt`, source selection files and any previous outside-root source-plan/receipt are HISTORICAL evidence of the parent, **not** evidence that this new composite was tested. New CI must run for this commit.
- Full real-game Studio two clients, mobile, physics, attack/eggs and cleanup are **NOT TESTED**. Do not call this CHAT_RC_READY. The official sole writer at [#220](https://github.com/kk051780/toy-wars-factory/issues/220) must independently select and integrate into its own release branch.
- No direct Windows Codex instructions or PC work, main/merge/publish/payment/spend, P0-A/B/C CAS or existing 5 automation changes.

## Rollback
Replace ONLY the HUD with its exact original blob `7a699f35cd3f5e7cf6178f7a45a71d0ead3247c5` and original SHA256 `50d9d9a6fc56ee796bc7999ce030c9cfc5d5af697591760c9e444eaefeb5de07`, or simply leave the official #220 RC unchanged. This candidate has no installed runtime authority beyond the inherited Game.
