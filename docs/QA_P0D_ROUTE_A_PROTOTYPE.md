# P0-D Route A: isolated Robot Post Office trial

**Tracking**: https://github.com/kk051780/toy-wars-factory/issues/213
**Frozen A/B specification**: https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6720253560

## What this change actually ships
- One ORIGINAL, self-contained Roblox **Server Script** in `examples/p0d_sorting_postoffice/RobotPostOffice.server.lua`.
- Three color-coded parcels, matching delivery bins, a REPLAY pillar, and a visible progress HUD.
- A server-owned per-player unique-color delivery state: RED, BLUE and YELLOW must each be delivered once. Wrong color and repeat deliveries do not increment; REPLAY is enabled only after 3/3.
- No assets from others, network/API, DataStore, purchases, external models or production integration.
- Python checks in `tests/test_p0d_sorting_postoffice_contract.py` verify **source markers and forbidden APIs only**; the script also has **real Luau state-machine smoke assertions** that must run during Studio Play.

**Important**: Passing these static tests, even in GitHub Actions, is NOT proof of successful Roblox Studio loading, gameplay, touch usability, T1–T7, or profitable retention. Keep A as `ENGINE_NOT_TESTED` until actual official Studio MCP/OWNER play evidence.

## Safe install for later authorized manual Route A trial
1. Open a fresh, backed-up, locally isolated, unpublished Baseplate test Place. Record its actual Studio ID, local file identity and place name, and verify the identity differs from all Toy Wars and PR209 Places. A zero PlaceId is necessary here but **NOT sufficient** for file identity. The actual Windows operator must explicitly approve the exact Studio instance/file before any modification.
2. Read-only preflight: `list_roblox_studios` for the intended Studio ID, confirm edit state and that Workspace contains **only** default Camera/Terrain/Baseplate/SpawnLocation objects and ServerScriptService has no other Script. Stop, never clear or delete assets, on any mismatch. The script also refuses execution outside unpublished local Studio, or with unexpected workspace/server scripts; its strict Workspace guard allows only default root objects and simple Texture/Decal decorations, plus models proven to be active Player.Character. It rejects duplicates and hidden descendants. This is **defense in depth** and NOT an authenticated target-file check.
3. Add a **Script** inside `ServerScriptService`, named `P0D_RobotPostOfficeTrial`, containing the exact contents of `RobotPostOffice.server.lua` pinned to the PR HEAD. Source code creates a temporary spawn point aimed toward the parcels; desktop/mobile camera and first-action usability are still NOT VERIFIED.
4. Use only local Studio Play (no Save/Save As to production, Publish, enabling API Services, DataStore, plugins or external URLs). Confirm the startup log contains `P0D_STATE_MACHINE_SMOKE_PASS` and `P0D_SORTING_POSTOFFICE_TRIAL_READY`; any `P0D_STATE_MACHINE_FAIL_*` is a FAIL, not a successful game.
5. T1: visible room / parcels / bins / objective. T2: select parcel then matching bin → `1/3`; repeat the **same** parcel → still `1/3`. T3: wrong bin → remains same progress and retry possible; early REPLAY before 3/3 must preserve progress. T4: deliver **all three distinct colors** → `3/3`, click REPLAY → `0/3`. T5: check legibility on narrow Desktop and real supported mobile emulation separately. T6: Stop returns Edit, no production changes.
6. Collect script SHA, workspace inventory, Play/Stop evidence and metrics in P0-D benchmark schema; never claim T7 until reproducible GitHub diff, exact-head CI and independent assessment.
7. For comparison B, use **identical frozen interaction requirements** but separate untouched initial Baseplate and bounded single Codex natural-language instruction. Do not run B without owner-side opt-in / security gates.

## Offline QA
`python -m unittest discover -s tests -p test_p0d_sorting_postoffice_contract.py -v`
This requires only Python standard library, not Roblox Studio.

## Known limitations
- Physical parcels are permanent re-usable click targets, not a production inventory/scheduler.
- Per-player progression is session-only; the world remains shared; no data is saved.
- Small-screen UI, camera framing and touch input have **not** been verified; Source-level guard and spawn initialization do not prove real gameplay.
- The runtime guards intentionally reject any already populated workspace or other ServerScriptService scripts, even if they are harmless; never bypass the guard by deleting someone else's objects.
- No automated PC receiver is started by adding this code; all P0-A/B/C security gates remain.
