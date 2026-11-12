# P0-D FIELD → H1 actual S1 source compatibility QA
Date JST 2026-11-13. Independent field QA issue #249, original concept #246, H1 implementation #248, product FUN gate #247, sole S1 integrator #220.

**Immutable original**: GitHub commit `3120b9d3c0a5ec58c9f2613c5d186f3493b54f83`, `releases/P0D_S1_KIDS_RC01`; branch is based on that commit, no original Game/Map/HUD/Config source edits. Tests read the six ACTUAL original source files and verify their frozen SHA256 from the original 37-source manifest, not approximate descriptions.

## Critical finding to the H1 world integration writer
The playable 8-safe S1 has **exactly RAIDER / GUARDIAN** role selection (S1 Config/Game/HUD), NOT seven executable classes. The other seven planned archetypes in the product/World studio are future design-only. RAIDER health100/speed19; GUARDIAN health135/speed15, guardian alone may place a trap in the team's valid flat half on the ground but NOT when carrying an egg. All classes have to use the same free route, with no VIP shortcut.

Current actual GrassArena 250×142 studs. X outside ±130 or Z outside ±76 or Y below −30 triggers server-owned respawn **and drops egg**. The original opponent egg remains x±98 z−20, own score pad x±82 z20, spawn x±68, core x±107. Neither an overseas castle nor an unbounded outer island can participate in existing egg play unless the sole Game server implementation is carefully revised under a separate explicit owner review. Do not create a new damage/round/event authority or an alternate egg-drop Remote.

## Proposed H1 route study only; NOT 3D movement proof
Four logical approach/return waypoint studies: RED_SEA, RED_SKY, BLUE_SEA, BLUE_SKY. Each is a fair free alternate, uses original own SCORE PAD, supports RAIDER/GUARDIAN and egg carry, fits inside existing X/Z boundaries. Even if one *entire logical route* is temporarily unavailable, the other is available. Sky route includes elevated hypothetical waypoints and requires real physical ramps/platforms; sea route includes hypothetical dry bridge. **No actual bridge, collision, streamable Roblox instances, ramps, camera path or real game model are created in this pack.** Do not imply successful traversal or that any existing Game has been patched.

## Source-first acceptance
Run `python3 -B -m unittest discover -s handoffs/P0D-H1-S1-WORLD-COMPAT-20261113-01/tests -p 'test_*.py' -v` in a full checkout from this branch. It reads S1 exact original source from the parent commit, checks role data, buttons, server roles, egg/pad/raycasts, out-of-map egg drop, trap legal limits, mirrored RED/BLUE routes and SOURCE mutants. Tests are strict to the frozen source only; future changes must obtain a **new source digest and review**. No claim of Roblox Studio simulation or human fun evaluation.

Actual #248 H1 integrator should evaluate this as **review feedback**, not inject unchanged: retain exact original Game, no added Remote, use two free accessible routes inside map bounds, both team sides, objective interactions and egg return physically reachable with real collision. Record owner H0/H1 play with two real players and mobile before calling world verified. Avoid seven roles or monster abilities unless the game server/HUD can really exercise them.

**Impact**: master #222 remains 4/8=50%; S1 #220 last official75/100; our own progress is separate and cannot grant release points. main/RC/merge/publish/pay/PC/Codex/P0A/B/C/automations unchanged.
