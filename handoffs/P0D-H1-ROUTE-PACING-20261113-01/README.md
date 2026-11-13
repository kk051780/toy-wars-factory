# P0-D WORLD-FIELD — H1 sea/sky route pacing, *next iteration only*
Date: 2026-11-13 JST. Owner lane Issue #256. **Not an adopted or tested game.**

## Why this field change matters
The initial H1 candidate built meaningful 3D path geometry and visible creatures, but raw route lengths were not yet checked as a kid-facing *choice*. The wall-clear corrected source #253 (exact Git blob `cc764b9caaa293ff747489e02e607af4502ddca4`) produces these theoretical origin→opponent EGG→own SCORE PAD geometric distances, mirrored on the RED and BLUE sides:

| Route | #253 wall-clear source | New optional candidate | Direct original-ground shortest Euclidean |
|---|---:|---:|---:|
| SEA | 541.6 studs (+54.1%) | **405.7 studs (+15.4%)** | 351.6 studs |
| SKY | 514.3 studs (+46.3%) | **406.9 studs (+15.7%)** | 351.6 studs |

Pure distance ÷ existing S1 baseline speed gives a *no-combat optimistic lower bound*: RAIDER speed19 ≈21.4s vs direct18.5s; GUARDIAN speed15 ≈27.1s vs direct23.4s. Wind power in separate #251/#255 source can affect these times; it is **not** included in these numbers. There is no measured avatar navigation, Roblox collisions, real team success rate, age cohort result, D1/D7 retention, mobile FPS or real Studio QA here.

The reason to retain 15% alternate penalty: children see a visible, readable strategic tradeoff—straight center crossing for speed versus walking around defenders from above or by the water. Both RED/BLUE, both actually implemented base roles (RAIDER/GUARDIAN), players carrying an enemy egg and players not carrying must remain able to enter/exit. No additional server gameplay authority, class paywall, forced gate or teleport.

## Genuine unmounted Luau candidate
`candidate/H1FunWorld_short_routes_REVIEW_ONLY.server.luau` is an exact copy of prior #253 original S1 H1 scenic overlay except for the route geometry block. The candidate preserves its two actual moving fantasy creatures, original H1 visual events and *Studio-only* execution guard; there is **no new Game/Remote/role/damage system**.

- **SEA**: dry, golden sea corridor x∈[−72,72], z=−22, Y0, 10-stud width. Three continuous playable road parts 12+120+12 studs (RED entrance, central bridge, BLUE entrance), water visual z≈−30 with side rail gaps and obvious signs. This stays 1.5 studs clear in the simplified horizontal collision boxes of original x±20,z−32 center rocks and clear of side castle walls at x±103,z±44.
- **SKY**: RED ramp x−62→−30 at z18, Y0→16, 12-stud width; sky crossing x−30→30 at Y16, 16-stud width; BLUE ramp symmetric. Sky upper path is visible, walkable *source parts* with simple ramp slope 16/32=0.50≤original Luau guard 0.55. Rails and signs are moved with the walkway. Its projected 2D path avoids current castle walls and center rock footprints, and starts outside the original team SCORE PAD footprints; original core and egg remain unchanged.

Names/numbers are source positions, not physics pathfinding proof. All F2P routes are accessible to both currently coded roles. No claim all conceptual seven roles are executable in S1.

## Test and acceptance
`tests/test_route_pacing.py` source-pins original S1 MapBuilder/Config and #253 exact prior Luau blob, reads the new candidate by exact Git Blob hash, parses all six game route Part creation calls, checks connected segment graph, both team egg roundtrip length, worst-case one route closure, collision-box intersection with original four solid castle sidewalls/five center rock pillars/two team score pads, slope, arena/recovery boundaries, source outside the world route block unchanged, preserve original Studio guard and no unauthorized remotes. Includes explicit unsafe mutants. `tests/test_manifest.py` validates exact source SHA256/GitBlob and bans false Studio approval.

Run in an isolated full checkout:
```bash
python3 -B -m unittest discover -s handoffs/P0D-H1-ROUTE-PACING-20261113-01/tests -p 'test_*.py' -v
```
CI workflow under own branch runs the exact tests if triggered by GitHub; job result must be verified separately. No personal secrets/keys.

## Product adoption sequence
Existing #255 four-way H1 game assembler already owns its own source and uses #253 geometry; **do not overwrite or merge it here**. Pass this #256 proposal to #219 product studio/#222 field owner/#248 H1 writer and sole official #220 integrator **only after the initial H1 integrated source test is stabilized**. The integrator can select this as a separate *post-H1* candidate, run exact full 28+ script Rojo build, independent QA, OWNER private Roblox Studio 2-client and Android/iPhone run, and side-by-side first 90-second clarity/beauty/fun A/B. A faster source proxy does not prove players prefer a route.

Stage `S2_PLUS_OPTIONAL`; current WorldField #222 formal4/8=50%, last sole official #220 S1 75%, no credit from this source-only branch. No main/RC/merge/publish/paid/extra spend/PC Codex/P0A/B/C/five automations changed.
