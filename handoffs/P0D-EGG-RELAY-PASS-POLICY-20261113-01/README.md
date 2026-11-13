# P0D Egg Relay — isolated S2 pure policy

Original gameplay idea: a stolen egg can be passed to a nearby teammate under strict **server-only** authorization. This branch is an optional S2 product experiment and does NOT change the actual Roblox Game.

- `src/EggRelayPolicy.luau` — original pure eligibility policy, returns allow/deny receipt without mutating Game/Remote/Store/score/XP.
- `tests/reference_policy.py` — independent Python behavior reference (NOT a native Luau interpreter).
- `tests/test_reference_policy.py` — 35 offline happy-path and negative tests, including replay, cross-team, distance, blocked LOS, double-carry, cooldown, death, stun.
- `INTEGRATION_CONTRACT.md` — exact server-state mapping, atomic handoff transaction requirements, genuine Studio 2-client/Android acceptance and rollback.

Local Python 3 test command:

```bash
python -m unittest discover -s tests -p 'test_reference_policy.py' -v
```

At source handoff: local Python reference 35/35 PASS; **native Luau compiler NOT_TESTED, true Roblox Studio NOT_TESTED, source-in-Game NOT_IMPLEMENTED, 2-client/Android/FUN NOT_TESTED, Product #250 selected NO, official #220 RC adopted NO**. The source-only tests cannot demonstrate real game playability.

Every future adoption decision must pass #219 Product DRI, #250 Product Selection and #220 sole official RC writer, followed by OWNER actual private Studio testing. S1 progress remains last official 75/100 / FUN_NO_GO. No main/merge/Roblox publication/payments/PC Codex/automations were touched.


## V2: native Luau QA path (2026-11-14)
- Original source stays byte-identical to Git Blob `dd5e5e19fb16c79bc54bfdef04c941cde418b0b4`. It remains policy only and **cannot transfer an egg in the actual Roblox Game**.
- `tests/native_policy_cases.luau` contains **41 deterministic Luau CLI test cases** for success, replay, transfer epochs, no-double-carry, team, range, LOS, alive/stun, cooldown and *zero state mutation*. These cases are genuine Luau source **prepared**, not an engine test.
- `tools/generate_native_runner.py` checks original SHA256/Git Blob and the native test source Git Blob before producing a standalone runner. No Roblox mock Game/Remote/DataStore is created.
- `tests/test_native_runner.py` contains 8 additional Python source-drift and false Studio/RC PASS guard unit tests.
- Workflow `.github/workflows/p0d-egg-relay-policy-native-20261114.yml` uses pinned Luau source commit `f46d879e28302a430029304f7f6a162aed66f103`, builds actual native CLI, compiles and executes the 41-case harness after Python tests. **Merely committing the workflow is not a successful Actions run.** Confirm the run ID/logs before claiming native PASS.

Example after native Luau CLI tools are installed:
```bash
python3 -B tools/generate_native_runner.py --out /tmp/p0d_relay_native.luau
luau-compile /tmp/p0d_relay_native.luau >/dev/null
luau /tmp/p0d_relay_native.luau
```
Expected stdout on genuine native success: `P0D_EGG_RELAY_NATIVE_POLICY_41_CASES_PASS`.

Actual local Python **original reference suite 35/35 PASS** independently rerun against previously pinned source archive. New native test **CI execution status UNKNOWN until verified**. Roblox Studio/2client/Android/FUN remains NOT_TESTED. This cannot raise #220 S1 75/100 or constitute #250 product selection.


## V3 critical high-ID compatibility fix (2026-11-14)
The prior `isInt` threshold (`abs(UserId)<1_000_000_000`) could wrongly deny teammates with modern billion-scale Roblox UserIds, regardless of distance, egg, or server authority. The original Luau policy and exact Python mirror now accept integer magnitudes up to the maximum exactly representable 64-bit-double integer (`9007199254740991`); the separate bounded world coordinate check is unchanged. Two new executed Python cases test a 5-billion-scale sender/receiver and an unsafe integer above the exact bound. **35/35 Python reference tests passed locally** using byte-verified GitHub source. The native Luau matrix now has **41 authored cases**, with the same two ID boundaries. The native compiler/runtime and GitHub Actions result are **still NOT VERIFIED**; compilation or game integration must never be inferred from the 41 source cases. The authoritative Game still owns player identity and all transactions; this only fixes its potential future policy integration.
