# P0-D ORIGINAL FOUR RARE REALMS / 3D SOURCE V1

Parent World Field Engine Issue #222; unique feature Issue #230; existing immutable WF13 gravity and G5 land/sea/sky remain unchanged.

**Goal:** four vivid 3D regions: 星くず銀河城, 光の天空神殿, 紅蓮の魔界城, 光と闇のはざま. Every realm has *two free wide physical routes*, a landmark castle, an original static 3D sculptural rare-creature silhouette, kid-readable Japanese wayfinding signage, and tactical + defender counterplay + 7s/15s promo scripts. No copyrighted assets or copied game names/characters. No actual neutral NPC AI, inventory, drop, paid access, level, or egg stealing is implemented here.

Sources:
- `RareRealmCatalog.luau`: exact four realms, eight route IDs, kids/tactic/counter/ad copy.
- `RareRealmScene.luau`: original fixed Part geometry; one green shared hub, four far-separated themed islands, **eight** dual walking paths. Entire map read-only in an unpublished test Place.
- `RareRealmCycle.luau`: server-only deterministic 30-second decorative moon/sun phase.
- `RareRealmDemo.server.luau`: OFF by default; fails on non-Studio/live game and official S1 overlap. Only optional localized color opacity changes for two noncolliding ornaments.
- `docs/TacticsAndTrailers.json`: source-independent 4 biome-specific role/item combos, opposing counterplay, 7/15 sec storytelling, H0/H1 and truth rules.
- `tools/build_native_four_realms_runner.py`: runs EXACT original Catalog/Cycle/Scene code with test-only external Roblox API mocks; deliberate unsafe variants should fail. CI native PASS is NOT a real Roblox Studio pass.
- `default.project.json`: isolated Rojo 7.7.1 Place only. No official RC/merge/public game.

**True rarity** is not connected to the matchmaking map rotation or spawn probabilities. `RARE` here means a designed themed world, NOT an RNG promise or paid exclusivity. Future NPC canon names require D18 owner alignment. Cosmic ZERO_G bubble is **VISUAL ONLY**: actual WF13 must be integrated separately by sole approved owner after native and 2client mobile tests. Underworld lava is harmless neon scenery. Eclipse day/night cycles decoration only, never traps players by removing a route.

## OWNER-run protected real Studio QA (NOT performed)
Copy source to a new BACKED-UP UNPUBLISHED test Place with the standalone Rojo project; flip ENABLE_FOUR_RARE_REALMS_DEMO true **in that disposable local copy only**. Confirm 2 test clients spawn in green hub, can walk both routes to each of all four castles and return. Verify safe stair/ramp slopes; children's wayfinding signs, no motion sickness, FPS/memory/streaming on actual phone. Visually check rare creatures are only sculptures. Explicitly show no workspace.Gravity modification, no paid access, no reward or score. Stop and restore Studio; never publish automatically.

Owner #220 official first S1 release progress is separate and unchanged by this optional S2+ packet. Parent world #222 G5+ acceptance requires actual protected Studio tests and is not earned by source-only CI. Public keyless source / locked SHA evidence only.

Original graphics/manifests/trailers: no ad or viral growth result is claimed until actual player, media, and conversion measurements exist.
