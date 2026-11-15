# EGGRUMBLE — Seven Hero Playable Studio Slice (SOURCE only, not official RC)

**Canonical player-facing product name: EGGRUMBLE**. Historical internal repo/game and source IDs are retained for compatibility.

OWNER instruction (2026-11-16): "ゲーム品質ゲートとして、各キャラを作り上げて".

## V3 owner rules — supersede earlier assumptions

Read [EGGRUMBLE_V3_CASTLE_ELIMINATION_MULTI_EGGS_GAME_MODES_CAPACITY.md](EGGRUMBLE_V3_CASTLE_ELIMINATION_MULTI_EGGS_GAME_MODES_CAPACITY.md) before working on this repository. The match outcome is **last castle standing for BR / last surviving team's castles for TEAM**, not an egg score threshold. A castle fall eliminates its owner and releases vaulted/carried eggs. Each castle and the field have multiple eggs; the 1/5-egg game mode split is retired. Two physical lobby portals select TEAM/BR; empty seats are filled by AI. Competitive castle foundations and hitboxes are standard while cosmetic housebuilding/optional prebattle defense modules allow individuality; the shop catalog is nontransactional.

**Three separate Studio-only examples** exist here; DO NOT place all three server scripts into the same running Place:

1. SevenHeroArena.server.luau — all 7 role abilities and 武神 ranged sword waves against training dummies.
2. EGGRUMBLE_MassBattleCastlePreview.server.luau — 9 sectors, a capped horde, KO counting and owner banner changes.
3. EGGRUMBLE_LobbyCastleModesPreview.server.luau — **now one connected V3 Studio battle slice**: 2 mode gateways, 16 combatant slots (human + AI), individual castle HP/elimination and multi-eggs, visible roaming AI soldier models which must reach eggs/gates physically before state changes, neutral swarm spawns/real Humanoid deaths and KO evolution, human TestBlade vs AI and neutral, team-aware castles/strategic route terrain, AI takeover on disconnect. **Bots now request budgeted paths using PathfindingService, but full route success and real Studio/Android performance are NOT tested**. Not an official RC. Build a private Studio source project with `EGGRUMBLE_V3_STUDIO.project.json` (one server script + FOUR ModuleScripts), or manually create exactly FOUR sibling ModuleScripts in ServerScriptService:
   - `EGGRUMBLE_CastleMatchRules` ← paste `EGGRUMBLE_CastleMatchRules.luau`
   - `EGGRUMBLE_BotPathRouter` ← paste `EGGRUMBLE_BotPathRouter.luau`
   - `EGGRUMBLE_BotActors` ← paste `EGGRUMBLE_BotActors.luau`
   - `EGGRUMBLE_SwarmCombat` ← paste `EGGRUMBLE_SwarmCombat.luau`
   Then paste `EGGRUMBLE_LobbyCastleModesPreview.server.luau` as one sibling **Script** (not a ModuleScript). Open a private Studio copy, enter Play, choose a defense module, then TEAM or BATTLE_ROYALE portal. The match starts after a 12-second trial countdown, fills vacant seats with AI and makes actual attack/pickup/deposit positions important. Equip `EGGRUMBLE_TestBlade` to strike real neutral NPCs and hostile AI heroes; the leaderboard counts actual NPC deaths. The enemy castle's approach gate and vault can be reached through the standard open doorway.

**Source update 2026-11-16:** The formerly number-only AI battle loop was removed and replaced with visible moving 3D models, distance checks, neutral combat and owner-disconnect AI takeover. The V3 slice still lacks proven pathfinding through full production mountains, optimized rig/animations, real queue teleport, reliable mobile performance, persistent home builds and integrated official egg/Remote/Game authority.\n\n**Independent rules regression smoke:** in another private Studio copy, put `EGGRUMBLE_CastleMatchRules.luau` into a sibling ModuleScript named `EGGRUMBLE_CastleMatchRules` and place `tests/EGGRUMBLE_CastleRulesSmoke.server.luau` in a server Script. Press Play and check the server Output for `[EGGRUMBLE V3 SOURCE SMOKE] PASS`. The smoke file covers 16-slot AI fill, equal castle HP/defense budget, permission and friendly-fire safety, genuine multi-egg raids, entire opponent team castle defeat and BR last-castle win. **The source is committed but no Studio run was performed in this chat.**

These are SOURCE-WIP preview slices, not a complete integrated game. Default roster size 16 total heroes (real+AI); 24/32 player settings are NOT validated and must not be asserted as capable. Read tools/eggrumble_capacity_model.py for assumed arithmetic; real devices and official RC acceptance pending.

## What is implemented as actual Luau

`SevenHeroArena.server.luau` is a **Studio-only**, opt-in ServerScriptService preview, additive to (not replacing) the official Game/Store/egg/Remote source. It creates **7 selectable 3D hero stands**, **three Roblox Tools per selected job**, **12 respawning training dummies with actual Humanoid damage**, and server-side abilities/effects. No network assets, no external IP characters, no new charges.

| Internal role ID kept | Visible role | A / B / C implemented as runnable Studio behavior |
| --- | --- | --- |
| WARRIOR | 武神 | odachi/spear/taijutsu stance basic / earthquake AoE / storm/flame/eight-headed serpent divine avatar |
| MAGE | 魔法使い | ranged magic / AoE thunder + ally healing / falling meteor |
| NINJA | 暗殺者 | dash hit / temporary speed + transparency / extended strike dash |
| TRAPPER | 超能力者 | gravity hit / short levitation + swap of two training enemies / temporary two-point portal |
| BUILDER | マッドサイエンティスト | energy shot / tracking autonomous turret / 3D mobile UFO demonstration and blast |
| BEAST | 魔獣使い | beast impact / feed-altered giant or three split smaller companions / feed-altered giant or split ultimate beast |
| ZOMBIE | 呪術師 | damage + short slow curse / three attacking undead units / oversized dark creature |

**武神 is OWNER-confirmed 2026-11-16; internal ID remains WARRIOR.** All seven playable display names must use EGGRUMBLE's latest OWNER choices. Existing WARRIOR/BEAST internal IDs are unchanged to minimize migration risk. For the complete design, current source coverage and missing functionality, read [ROLE_EVOLUTION_20261116.md](ROLE_EVOLUTION_20261116.md). Abilities target **test dummies only** for safe preview and **do not demonstrate finished real PvP**.

## Try privately in Roblox Studio

1. On an isolated Studio copy (never the production place), create a **Script** in ServerScriptService.
2. Paste the complete file `SevenHeroArena.server.luau` into that Script.
3. Enter **Play**. Find the EGGRUMBLE-branded marker and seven job stands about 42 studs from the existing SpawnLocation; a flat test floor and twelve red test dummies appear.
4. Use the stand ProximityPrompt to choose a job. If 神将 or 魔獣使い is selected, interact with the extra ground choice stations for weapon style/divine seal or giant/split/armor food before using the skill Tools. Equip a Tool from the backpack (or Android hotbar): A=basic, B=special, C=signature. Each can be activated against the training dummies, which respawn.
5. Stop Play to remove all prototype entities. Script is inert outside Studio because of `RunService:IsStudio()`.

## Safety / honest test status

- Preview **works only when installed into a Studio test place**; GitHub code existence is not a Studio test record.
- No source was added to the canonical RC, no normal merge or game Publish, no DataStore writes, no real network Remotes, no game economy modifications.
- No source-exact Rojo/native Lua compiler, Studio 2-client, Android FPS/Art/FUN or OWNER acceptance has run for this slice yet. It remains **SOURCE_WIP / ENGINE_UNKNOWN / RC_NOT_INTEGRATED**.
- The beast's ARMORED shell is visual in the present preview; real armor interception is future work. The scientist's superpower cores, 8+ divine seals, real mounting/flying, PvP and egg capture are still missing.
- This is a playable mechanics scaffold, **not** the finished art/style/animations, enemy-team AI, map, egg capture or advanced skill trees. Role-specific full product quality remains NO_GO.
- Follow the existing Game/HUD/SevenJobs author PR #297/#303/#305 and latest private role fixes #476/#481 for all shared integration paths. No edits to another writer's path. #220's authenticated RC writer alone decides any source-selective official adoption.

## Next concrete source integration order

(1) Lock existing author source-IDs and map all 7 roles/21 skills; (2) author-integration into genuine Game/Tool/HUD for real server role authority and mobile; (3) add physical character models, locomotion and hit animations at #420 art quality; (4) test opponent interaction, anti-permaCC, egg carrier, death/rejoin/respawn, AI/rideable, missiles/vehicle controls and anti-P2W; (5) source exact QA → authenticated RC CAS → real Studio/Android/competitive/OWNER verification.

Roll back by removing the single preview Script, which removes all spawned prototype objects on next Play.

## V2 core-loop reset — the new main game direction

OWNER now requires **massive horde-musou battle as a co-primary loop**, with teams still fighting to steal and deliver eggs. **武神** is the dedicated duelist/weapon master and sends flying sword slashes (not a Mage spell), with large self-boosting kami transformation. **One customisable castle per player**, grouped by Red/Blue team. Experienced matches aspire to 10,000+ individual verified neutral KOs / 30,000+ aggregate KOs with a genuinely huge multi-sector map. These are unproven product goals, not current QA results.

The new standalone `EGGRUMBLE_MassBattleCastlePreview.server.luau` is **another optional Studio-only script**. **Run it ALONE on a separate private Studio copy, not simultaneously with `SevenHeroArena.server.luau`** (their preview worlds are independent). This creates 9 large map sectors, a capped continuous neutral horde, automatic attacks and server-attributed real KO counts, XP-based slash upgrades, a castle for each joined player, and an owner-only banner-palette decoration station. It does **not** implement real PvP, capture/return eggs, production AI, advanced castle customization or Roblox/Android verification. The full contract, including performance/fairness/ownership, is in [EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md](EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md).

## P0D quality: exterior vault AI route (stacked #484, 2026-11-16)

The existing author's `EGGRUMBLE_BotPathRouter` / PathfindingService remains authoritative for preview bot movement. This isolated quality patch only corrects BotActors's impossible `inside solid castle core` egg target: bot navigates enemy front, exterior east flank and exposed EggVault side before any `Rules.takeEggs`; existing LOS and true damage/KO/egg ID server owner remain untouched. Spawn height is aligned with foundation, and target changes/respawn clear staged navigation. ModuleScript `EGGRUMBLE_BotPathRouter` must be installed alongside Rules and BotActors. CI source-negative + native targeted Luau compile is not a real Studio, Android or product FUN result; a real Studio path test must show both steal AND return against actual collidable castle geometry.
