# TRAP RAIDERS S1 first-minute coach (PUBLIC SOURCE V1)

Original optional **client-only** first-minute contextual prompts for the current Chat S1 source-built Roblox project. No gameplay authority, no new remote, no telemetry, no purchases, no persistence. The game does not include this packet unless #220 integrator explicitly wires it.

**Packet** `P0D-S1-FTUE-FIRST60-CLIENT-COACH-20261111-01`; game `TRAP_RAIDERS`; work `p0d-siege-v19`; baseline `35d7d0525388e885aac8281eff2315a59831e0cf`; independent claim [#218](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6778973481).

Source: `src/FirstMinuteModel.luau` and `src/FirstMinuteCoach.client.luau`; offline QA `tests/test_ftue_contract.py`; integration instructions `docs/INTEGRATION.md`; `BUILD_MANIFEST.json` SHA256 and byte-size per non-manifest file.

Run `python -m unittest discover -s tests -v`. The 20 cases check a Python behavior oracle and static Lua interface invariants. **They do NOT execute Luau.** True Luau parsing, Roblox Studio, multi-client, mobile screen fit and actual first-action <=60s remain NOT_TESTED. Public source is permitted for this original TRAP RAIDERS feature only; no main/merge/publish/paid/spend/Windows Codex request.