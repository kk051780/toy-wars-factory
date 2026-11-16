# GQ RC31 original #523 field eggs vs castle foundations

**Existing-author reuse, no duplicate gameplay:** original [#523](https://github.com/kk051780/toy-wars-factory/pull/523) pinned HEAD `54ea74aa15e387d83512566715f44216ba8587a2`, original patch Git blob `bd70e14c44341e0c827c43af1990ad8e11a4c698`. Its original #482 host is pinned to Git blob `7162b209bf67b74a71553217f3f744e072a0365d`.

The actual source grid had 8/24 TEAM field eggs and 4/24 BR eggs geometrically inside existing 72×72 castle foundation footprints. The original #523 patch **changes only the 3 row Z coordinates** by inserting mode-specific `rowZ` and swapping one old vector expression: TEAM [338,506,610], BR [338,448,676]. All 24 original FIELD egg IDs, columns, physical pickups, win conditions, castle HP and 7-role abilities unchanged. Source-derived AABB, not a Studio playthrough.

This RC-only integration reuses **the already-written original author's patch** and original native geometry harness; the only new code here is fail-closed source selection, revert, native+Rojo test and provenance. Patch goes AFTER official #547 castle+egg boards on existing ONE V3 Host. It must retain all other 30 official script bytes including CHAR7, FIELD, BATTLE, CASTLE and eggs, neutral soldier/stone boss, ITEM489, two-mode lobby, SCORE/ART/BALANCE, and already selected #536 Router / #555 BotActors. No second Game/Host/Remotes/Store/AI/Item.

- OFF: current latest `artifacts/gq547_official_select/GQ547_SELECTED31.project.json`, all 31 currently official. 
- ON: same 31-name manifest, exactly one changed `EGGRUMBLE_LobbyCastleModesPreview` generated Host.
- Python 8 fail-closed and mutation/reversibility tests, ORIGINAL #523 source-extracted native Luau geometry TEAM8+BR4 → 0+0, true Luau31 native compilation, actual pinned Rojo31 Script Source+Class exact, other 30 script bytes identical, no extra module.
- Authenticated #220 single writer expected-head nonforce CAS only after latest same-head PREMERGE CI success; revalidate latest RC to avoid dropping other in-flight #574 Host (stale avatar), #562 Item #517 HEAL, #571 Boss #518, #573 Result GUI #538. If Host changes first, update PR to current Host and reverify.
- This is PRIVATE source proof only until *official push-event same-HEAD* V3+S1 CI, exact Place vs artifact ZIP byte/hash ACK. No main, Roblox Publish, money, Windows changes.
- Actual Studio 1+15AI/2-player, Android 15min, quality #420 ART/FUN and OWNER remain NOT_TESTED / NO_GO.
