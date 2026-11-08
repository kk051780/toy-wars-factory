# P0-D Route A: isolated Robot Post Office trial

**Tracking**: https://github.com/kk051780/toy-wars-factory/issues/213
**Frozen A/B specification**: https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6720253560

## What this change actually ships
- One ORIGINAL, self-contained Roblox **Server Script** in `examples/p0d_sorting_postoffice/RobotPostOffice.server.lua`.
- Three color-coded parcels, matching delivery bins, a REPLAY pillar, and a visible progress HUD.
- A server-owned per-player selection and 0/3→3/3→REPLAY state; wrong color must not increment.
- No assets from others, network/API, DataStore, purchases, external models or production integration.
- Five Python checks in `tests/test_p0d_sorting_postoffice_contract.py` verify **source markers and forbidden APIs only**.

**Important**: Passing these static tests, even in GitHub Actions, is NOT proof of successful Roblox Studio loading, gameplay, touch usability, T1–T7, or profitable retention. Keep A as `ENGINE_NOT_TESTED` until actual official Studio MCP/OWNER play evidence.

## Safe install for later authorized manual Route A trial
1. Open a fresh, backed-up, locally isolated, unpublished Baseplate test Place. Record its actual Studio ID / Place name and verify it is NOT the live Toy Wars Place.
2. Add a **Script** inside `ServerScriptService`, named `P0D_RobotPostOfficeTrial`, containing the exact contents of `RobotPostOffice.server.lua` pinned to the PR HEAD.
3. Use only local Studio Play (no Save/Save As to production, Publish, enabling API Services, DataStore, plugins or external URLs). Confirm the start log is `P0D_SORTING_POSTOFFICE_TRIAL_READY`.
4. T1: visible room / parcels / bins / objective. T2: select parcel then matching bin → `1/3`. T3: wrong bin → remains same progress and retry possible. T4: reach `3/3`, click REPLAY → `0/3`. T5: check legibility on narrow Desktop and real supported mobile emulation separately. T6: Stop returns Edit, no production changes.
5. Collect script SHA, workspace inventory, Play/Stop evidence and metrics in P0-D benchmark schema; never claim T7 until reproducible GitHub diff, exact-head CI and independent assessment.
6. For comparison B, use **identical frozen interaction requirements** but separate untouched initial Baseplate and bounded single Codex natural-language instruction. Do not run B without owner-side opt-in / security gates.

## Offline QA
`python -m unittest discover -s tests -p test_p0d_sorting_postoffice_contract.py -v`
This requires only Python standard library, not Roblox Studio.

## Known limitations
- Physical parcels are permanent re-usable click targets, not a production inventory/scheduler.
- Per-player progression is session-only; the world remains shared; no data is saved.
- Small-screen UI and touch input have **not** been verified.
- No automated PC receiver is started by adding this code; all P0-A/B/C security gates remain.
