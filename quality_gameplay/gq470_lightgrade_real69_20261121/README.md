# GQ470 FB-015: mobile-conscious scene grade (REAL69 A only)

Status: **candidate source / not installed / ART_NO_GO**. The single formal RC
\`rc/p0d-s1-kids-rc01\` is not changed by this PR. This branch adds no runtime
route to the canonical 69 selected Luau scripts. No owner acceptance is implied.

## Player moment and original reuse

Improve battlefield depth, faction/egg readability and stylistic consistency
when the weather changes without drawing additional giant glow boxes or labels.
Reuses the *palette/art-direction concept* from original FB-015 world art
[PR #377](https://github.com/kk051780/toy-wars-factory/pull/377).
Does not change #377 or copy its large tree/ground Part layer. Disjoint from
active castle #934, canyon #933, canopy #926, reef #921, weapon #929,
ImpactFeedback #928, lobby #925 and composite #931 source targets.

The new \`EGGRUMBLE_LowCostSceneGrade.luau\` is an explicit-install ModuleScript:
- CLEAR / GOLDEN / OVERCAST / STORM palettes; 0 new Parts and 0 per-frame loops.
- At most one **new** Atmosphere (only if none exists) and one ColorCorrection.
- Never changes existing Atmosphere, Lighting clock/brightness or another lane's
  effects. Refuses duplicate installs, unknown moods and non-Studio runtime.
- \`setMood("STORM")\` for weather bridge; \`destroy()\` cleans up only objects
  created by this module. No game/host/combat/storage/Remote/HP/egg/score writes.
- A source-only static/negative gate checks these promises but **does not**
  compile or execute Luau on Roblox.

## B source-admission contract (not yet satisfied)

A registered #220 B writer must re-get the *latest* official head and ensure:
1. #218 distinct-path claim and #250 ADOPT value card; no overlap with #377.
2. Choose one existing presentation-owner integration location, **not** a second
   Game/Host/HUD authority. Wire its actual weather session boundary to
   \`install\` / \`setMood\` / \`destroy\`; no unbounded event subscriptions.
3. Source-lock the changed original selected route(s), check other original
   routes byte-exact, then run official same-head Native Luau + Rojo ON/OFF,
   original Place rollback, legacy17/48, and formal ZIP/Place size receipt.
4. Integrate only through fresh expected-SHA / force=false CAS to the sole RC,
   never by merging this entire PREP branch.
5. Compare fixed-view PC/Android screenshots for CLEAR/GOLDEN/STORM,
   readability of egg/team highlights, and mobile performance against #420.

Stage: \`SOURCE_WIP\`; \`PREP_READY=NO\` until genuine selected original route
and fixed-source CI; \`RC_INTEGRATED=NO\`; \`ENGINE_PASS=NOT_TESTED\`;
\`OLD_NEW_SCREENSHOTS=0/32\`; \`ANDROID15=NOT_TESTED\`; \`KID_FUN=NOT_TESTED\`;
\`HUMAN_ART=NOT_TESTED\`; \`OWNER_ACCEPTED=0\`.

Rollback: omit the optional module/integration on B build; at runtime,
\`controller.destroy()\` removes the owned ColorCorrection and, only when it
was created here, Atmosphere. Does not restore/alter any other lane's effects.

Trace: #910 P0-C; #470 F1/F7; #420 art/mobile; #364 FB-015.
