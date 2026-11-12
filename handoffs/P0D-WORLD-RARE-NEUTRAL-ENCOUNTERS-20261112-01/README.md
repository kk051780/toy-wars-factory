# TRAP RAIDERS / Rare World — 動く中立幻獣の発見システム（S2+隔離プレビュー）

Issue #232. Parent #222. The previous four fantasy castle field is pinned to issue #230 immutable source SHA `2dd00f7932292f9f54d5c1cdc689d76cef4f9718`. This source packet **references** the previous `RareRealmCatalog.luau` and `RareRealmScene.luau` byte-exact, and never rewrites or mutates the previously tested world.

## Original game concept
Each of four child-friendly fantasy fields can have a different **moving, noncombat neutral visual** (not D18 collectible canon):
- 宇宙: 星くじら floats in a gentle orbit, free visual discovery
- 天空神殿: 虹羽ペガサス hops above a safe plaza, no ride mechanics
- 紅蓮魔界: マグマモグラ peeks above and hides slightly below a harmless magma-themed plaza
- 光と闇: 双面の幻獣 moves between sun and moon scenery; roads never lock

All four get server-owned low-frequency **configured test-only** 12% chance at each 45-second encounter window, at most 1 living encounter across the whole map, 28-second lifetime, 2-second preview before free `みつけた！` ProximityPrompt, user-near body distance check, no tickets, coins, loot, persistence, XP, PvP damage, power upgrades, paid odds, remote client trust or D18 registration. This 12% is a source parameter, **not a measured live drop probability** and should never be marketed as loot odds or a guarantee. No gamified monetary randomness.

## Exact source and audit
- `RareEncounterPolicy.luau`: pure finite-number safe spawn-window state machine, single global active lock, id cycling and distinct safe body movement.
- `RareEncounterModels.luau`: four source-made Roblox Models with real anchored but noncolliding 3D Parts, BillboardGui and ProximityPrompt. Movement uses actual server Model:PivotTo. No external mesh/audio/image asset download.
- `RareEncounterPreview.server.luau`: default `ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW=false`; if OWNER locally opts in only inside **unpublished backed-up Roblox Studio test Place**, builds original #230 scene unchanged, then single global server loop cycles rare encounters, moves the models, validates server-near actual live player on prompt, resets after despawn/disconnect/stop; prints **private local output only**, no user identifiers, no reward or external transmission. Stops in live Roblox or if S1 official game is already present.
- `default.project.json`: standalone Rojo project with **5** original Luau modules / server script: original previously pinned Catalog and Scene plus 3 new sources. No official Game/RC ownership.
- `docs/DiscoveryAndPromos.json`: per-biome child clue and 7/15-second honest hypothetical social clips, job/item class teamwork and counterplay, H0/H1 human fun assessment.

## QA acceptance
GitHub CI first runs Python source safety contracts, honest source manifest SHA256, then compiles exact real original Luau source in genuine fixed upstream Luau CLI and executes original Policy + moving Models against **external Roblox engine test doubles**. This is actual executable original source but **not a real Roblox engine**. Negative mutations (always spawn, overlapping encounters, rapid rerolls, no telegraph, paid prompt, colliding models, deceptive rewards, no movement) must be rejected.

Independent Rojo 7.7.1 SHA-checked build creates an actual isolated binary `.rbxlx` and verifies all **five original embedded source bytes** and script classes, disabled default and Studio-only safety. No automatic Roblox Studio invocation.

## Owner-only protected real test steps (not performed)
1. Keep the official S1 PC Place and its current backup fully untouched. Fetch CI exact immutable `.rbxlx` artifact and SHA evidence. Open **new unpublished test Place**.
2. Only in your local disposable copy set `ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW=true`; keep GitHub code default false.
3. Use private Roblox Studio Test/Start with 2 clients. Let the test run across encounter windows. Check exactly one roaming creature globally, four types reachable over a long isolated QA session, collision-free scenery and no rewards or native inventory. Since the preview is deliberately rare, use deterministic *local test-only* seeded overrides if needed for acceptance—never misreport artificial triggers as live probability.
4. Test ProximityPrompt from near and far, two users on one encounter, death/disconnect, leave/rejoin, expiration, movement smoothing, mobile FPS, text readability and low-bandwidth StreamingEnabled. Document Studio build, device, actual logs and fail cases privately.
5. D18 source owners must separately resolve whether any rare character becomes a canon collectible or wild NPC. Do not give this demo autonomous combat or paid advantage without a new documented design/QA.

This source packet **does not mean four creatures are live in Roblox**. WorldField parent formal progress is 50% pending real G5/owner Studio; P0D official S1 sole integration score last audit 75% and release remains unauthorized. Do not edit main/official RC/merge/publish/paid/PC Codex/automations.