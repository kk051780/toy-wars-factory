# EGGRUMBLE — Seven Hero Playable Studio Slice (SOURCE only, not official RC)

**Canonical player-facing product name: EGGRUMBLE**. Historical internal repo/game and source IDs are retained for compatibility.

OWNER instruction (2026-11-16): "ゲーム品質ゲートとして、各キャラを作り上げて".

## V3 owner rules — supersede earlier assumptions

Read [EGGRUMBLE_V3_CASTLE_ELIMINATION_MULTI_EGGS_GAME_MODES_CAPACITY.md](EGGRUMBLE_V3_CASTLE_ELIMINATION_MULTI_EGGS_GAME_MODES_CAPACITY.md) before working on this repository. The match outcome is **last castle standing for BR / last surviving team's castles for TEAM**, not an egg score threshold. A castle fall eliminates its owner and releases vaulted/carried eggs. Each castle and the field have multiple eggs; the 1/5-egg game mode split is retired. Two physical lobby portals select TEAM/BR; empty seats are filled by AI. Competitive castle foundations and hitboxes are standard while cosmetic housebuilding/optional prebattle defense modules allow individuality; the shop catalog is nontransactional.

**Three separate Studio-only examples** exist here; DO NOT place all three server scripts into the same running Place:

1. SevenHeroArena.server.luau — all 7 role abilities and 武神 ranged sword waves against training dummies.
2. EGGRUMBLE_MassBattleCastlePreview.server.luau — 9 sectors, a capped horde, KO counting and owner banner changes.
3. EGGRUMBLE_LobbyCastleModesPreview.server.luau — **now one connected V3 Studio battle slice**: 2 mode gateways, 16 combatant slots (human + AI), individual castle HP/elimination and multi-eggs, visible roaming AI soldier models which must reach eggs/gates physically before state changes, neutral swarm spawns/real Humanoid deaths and KO evolution, 7職の固有スキルが中立兵・bot英雄・人間英雄と同一ラウンドで命中, team-aware castles/strategic route terrain, AI takeover on disconnect. **Bots now request budgeted paths using PathfindingService, but full route success and real Studio/Android performance are NOT tested**. Not an official RC. Build a private Studio source project with `EGGRUMBLE_V3_STUDIO.project.json` (one server script + the sibling ModuleScripts listed in its current JSON), or manually create ALL the sibling ModuleScripts listed in the JSON, including these in ServerScriptService:
   - `EGGRUMBLE_CastleMatchRules` ← paste `EGGRUMBLE_CastleMatchRules.luau`
   - `EGGRUMBLE_BotPathRouter` ← paste `EGGRUMBLE_BotPathRouter.luau`
   - `EGGRUMBLE_BotActors` ← paste `EGGRUMBLE_BotActors.luau`
   - `EGGRUMBLE_SwarmCombat` ← paste `EGGRUMBLE_SwarmCombat.luau`
   - `EGGRUMBLE_InteractionGuard` ← paste `EGGRUMBLE_InteractionGuard.luau`
   - `EGGRUMBLE_SevenRoleCombat` ← paste `EGGRUMBLE_SevenRoleCombat.luau`
   - `EGGRUMBLE_CombatBalance` ← paste `EGGRUMBLE_CombatBalance.luau`
   - `EGGRUMBLE_SkillFX` ← paste `EGGRUMBLE_SkillFX.luau`
   - `EGGRUMBLE_AttackGeometry` ← paste `EGGRUMBLE_AttackGeometry.luau`
   - `EGGRUMBLE_ImpactFeedback` ← paste `EGGRUMBLE_ImpactFeedback.luau`
   - `EGGRUMBLE_WeaponSilhouettes` ← paste `EGGRUMBLE_WeaponSilhouettes.luau`
   - `EGGRUMBLE_DivineMantle` ← paste `EGGRUMBLE_DivineMantle.luau`
   - `EGGRUMBLE_MatchResultService` ← paste `EGGRUMBLE_MatchResultService.luau`
   - `EGGRUMBLE_RoundReplay` ← paste `EGGRUMBLE_RoundReplay.luau`
   - `EGGRUMBLE_FieldItemPickups` ← paste existing item author file `EGGRUMBLE_FieldItemPickups.luau`
   - `EGGRUMBLE_RaidItemIntake` ← paste `EGGRUMBLE_RaidItemIntake.luau`
   - `EGGRUMBLE_NeutralStoneGiant` ← paste ORIGINAL boss author module `EGGRUMBLE_NeutralStoneGiant.luau`
   - `EGGRUMBLE_BossSessionFence` ← paste pure match-isolation module `EGGRUMBLE_BossSessionFence.luau`
   Then paste `EGGRUMBLE_LobbyCastleModesPreview.server.luau` as one sibling **Script** (not a ModuleScript). Add `EGGRUMBLE_CombatFeel.client.luau` as a **LocalScript** under StarterPlayer/StarterPlayerScripts; the supplied Rojo project already wires it. Add `EGGRUMBLE_ProceduralSkills.client.luau` as a second **LocalScript** in the same StarterPlayerScripts folder; it renders server-confirmed weapon gestures for all visible heroes. Open a private Studio copy, enter Play, choose a defense module, then TEAM or BATTLE_ROYALE portal. The match starts after a 12-second trial countdown, fills vacant seats with AI and makes actual attack/pickup/deposit positions important. Before entering TEAM or BR, choose one of the seven **job pedestals** (or default to 武神), then use **three hotbar Tools** per class (A basic, B special, C ultimate). All 21 abilities damage or affect the SAME V3 neutral/AI battlefield; the leaderboard counts actual NPC deaths. The enemy castle's approach gate and vault can be reached through the standard open doorway.

**Source update 2026-11-16:** The formerly number-only AI battle loop was removed and replaced with visible moving 3D models, distance checks, neutral combat and owner-disconnect AI takeover. The V3 slice still lacks proven pathfinding through full production mountains, optimized rig/animations, real queue teleport, reliable mobile performance, persistent home builds and integrated official egg/Remote/Game authority.\n\n**Independent rules regression smoke:** in another private Studio copy, put `EGGRUMBLE_CastleMatchRules.luau` into a sibling ModuleScript named `EGGRUMBLE_CastleMatchRules` and place `tests/EGGRUMBLE_CastleRulesSmoke.server.luau` in a server Script. Press Play and check the server Output for `[EGGRUMBLE V3 SOURCE SMOKE] PASS`. The smoke file covers 16-slot AI fill, equal castle HP/defense budget, permission and friendly-fire safety, genuine multi-egg raids, entire opponent team castle defeat and BR last-castle win. **The source is committed but no Studio run was performed in this chat.**

**Battle interaction security:** every user ProximityPrompt is processed by `EGGRUMBLE_InteractionGuard.luau` on the server. It validates the living actor's range, line-of-sight and per-action cooldown before allowing castle hits, egg pickups, own-home decorations, lobby entry and loadout changes. Specifically, a castle attack cannot be repeated faster than once per 1.6 seconds by the same human at the same gate. A valid engine `Triggered` callback is not a substitute for the rule-level enemy/owner/egg checks.

**Additional CI (source only):** `.github/workflows/p0d-eggrumble-v3-native-luau.yml` builds the public Luau CLI to parse isolated `.luau` source and executes a sandboxed pure match-rule VM test (TEAM/BR, multiple eggs, conservation, anti-replay, castle collapse). These tests do **not** execute Roblox Services, Studio physics/navigation, touchscreen or Android profiling. A separate Python source-contract CI catches wiring/guard regressions. Refer to each GitHub Actions result rather than assuming success.

**2026-11-16 seven-class V3 integration**: `EGGRUMBLE_SevenRoleCombat.luau` connects 7 jobs × 3 hotbar skills to the same TEAM/BR and horde controllers. 武神 has flying sword slashes + a six-second 神憑き and a lone-opponent damage advantage against preview AI; 魔法使い has ice/fire/healing; 暗殺者 uses short guarded wind-dash and stealth from bot targeting; 超能力者 applies real bot movement slowing and a guarded blink; マッドサイエンティスト uses rockets and a temporary area turret proxy; 魔獣使い uses giant and split body combat effects; 呪術師 has curse and multiple short-lived undead bodies with area strikes. **The latter summon models and turret are still VFX / timed attacks, NOT true independently navigated pet AI or elaborate rig/animation.** The actual 7-role PvP against real human players, egg/character skill interactions, full progression and Android/UI/art quality are not validated. Team assignment, egg custody and castle ownership remain in the existing single server rules module. Isolated `SevenHeroArena.server.luau` is still a separate test artifact and must NOT be started alongside V3.

## Real neutral StoneGiant in both matches (2026-11-16)

The ORIGINAL author `EGGRUMBLE_NeutralStoneGiant.luau` now supports **optional match membership and phase callbacks** while preserving its standalone `Boss.spawn(workspace,at)` contract. `EGGRUMBLE_BossSessionFence.luau` (pure native-tested small adapter) refuses damage or engagement between TEAM and BR, denied dead/retired castle owners, completed rounds or stale sessions. The single V3 host spawns **one real existing StoneGiant per match**; all seven role skills can strike its actual weakpoint using their existing **fan/lane/circle geometry, server cooldown and solid-wall line of sight**. Boss defeat increments a dedicated server-authored boss stat, **not a fake neutral-soldier KO**. Visual model / 2s dodge telegraph / 28 damage pulse are the original author's modules, not a reimplemented rival boss. Optional boss startup failure reports YELLOW and never blocks eggs, castle, item, human or horde gameplay. All Roblox Studio/Android behavior and final premium-art quality remain **UNTESTED**. [RC gate and multi-lane progress](EGGRUMBLE_RC_INTAKE_PROGRESS_20261116.md).

## Single-match eight-lane intake (2026-11-16)

[8-domain no-duplication and blocker matrix](EGGRUMBLE_V3_CROSS_LANE_INTAKE_MATRIX_20261116.md). The existing ITEM author `EGGRUMBLE_FieldItemPickups.luau` is now wired to **both active TEAM and BATTLE_ROYALE source matches** through a small `EGGRUMBLE_RaidItemIntake.luau` adapter. Its 3×3 physical sites give every raid route and lateral flank the three kinds HEAL / DASH / SHIELD once, with server-owned one-claim-per-spawn-cycle pickups with a 35-second respawn and per-player cooldowns; failures are rolled back and treated as YELLOW optional instead of aborting the core egg/castle match. This is a single V3 scene, NOT a second item preview. EnterableCastleInterior (overlapping gate/vault), ValleyLandmarkKit (potential collidable ground overlap) and LobbyUXStandalone (duplicate queue gates) are **NOT** automatically inserted; the original StoneGiant is now session-fenced and source-integrated; see matrix for owner and conflict reasons. Native Luau checks the 2-mode item adapter; Python checks all eight existing domains without declaring unfinished art complete.

## Procedural attack animations and actual 6-second Divine Mantle (2026-11-16)

[Full God form, animation and real-engine QA contract](EGGRUMBLE_PROCEDURAL_POSES_KAMI_QA_20261116.md). The server publishes one `EGGRUMBLE_SkillCastSignature` only **after** role/castle/alive/cooldown authorization. The new `EGGRUMBLE_ProceduralSkills.client.luau` reads the signature and locally blends seven distinct R6/R15/AvatarJointUpgrade arm/waist poses into the existing Animator using `RunService.PreSimulation` and `Transform` (no C0 changes), with at most 16 avatars within 130 studs; there is no extra gameplay-authority RemoteEvent. `EGGRUMBLE_DivineMantle.luau` is a six-part max server-welded golden god halo/flame/crest transformation on the living War God for 6 seconds. Its buff now lives on the **current Character**, not the Player, so death/respawn cannot carry the god-power into an extra life. **No professional authored animation clip, commercial sounds, Roblox Studio 2-client, or Android runtime has been verified**.

## Hit feedback + character weapons (2026-11-16)

[Full impact/weapon/ultimate-art quality gate](EGGRUMBLE_V3_HIT_FEEL_WEAPON_ART_GATE_20261116.md) documents the source implemented **7 separate in-hand weapons**, the actual-hit-only flash and 0.16-second local confirmation, restrained and optional local camera movement, per-second effects ceilings and **seven C-skill ultimate silhouette accents**. Neutral KO bursts are tied to `Humanoid.Died`; there is no simulated score. These are original low-part *placeholders* and still lack final animated hero rigs, weapon motions, studio/Android profiling, and owner playtest. Studio source includes a server-side `EGGRUMBLE_ImpactFeedback` and `EGGRUMBLE_WeaponSilhouettes` plus a StarterPlayer LocalScript `EGGRUMBLE_CombatFeel`. They must be installed together.

## Latest skill balance + VFX

[21技の威力・中心射程・実攻撃形状・範囲・追加効果・CDと演出/Android品質契約](EGGRUMBLE_7ROLE_DAMAGE_RANGE_STATUS_ART_V1.md) を参照。`EGGRUMBLE_CombatBalance.luau`が唯一の数値正本で、`EGGRUMBLE_AttackGeometry.luau`をNPC/AI/人間の当たり判定に共用。`EGGRUMBLE_SkillFX.luau`は7職の個別シルエットと低負荷上限72を管理する。Roblox Studio/Androidの本物の美術・FPS・楽しさは**未検証**。

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
- Python source-contract CI and native Luau parser/pure-rule VM regression runs exist, but real Roblox Studio 2-client, Android FPS/Art/FUN and OWNER acceptance have **not** run. It remains **SOURCE_WIP / ENGINE_UNKNOWN / RC_NOT_INTEGRATED**.
- The beast's ARMORED shell is visual in the present preview; real armor interception is future work. The scientist's superpower cores, 8+ divine seals, real mounting/flying, PvP and egg capture are still missing.
- This is a playable mechanics scaffold, **not** the finished art/style/animations, enemy-team AI, map, egg capture or advanced skill trees. Role-specific full product quality remains NO_GO.
- Follow the existing Game/HUD/SevenJobs author PR #297/#303/#305 and latest private role fixes #476/#481 for all shared integration paths. No edits to another writer's path. #220's authenticated RC writer alone decides any source-selective official adoption.

## Next concrete source integration order

(1) Lock existing author source-IDs and map all 7 roles/21 skills; (2) author-integration into genuine Game/Tool/HUD for real server role authority and mobile; (3) add physical character models, locomotion and hit animations at #420 art quality; (4) test opponent interaction, anti-permaCC, egg carrier, death/rejoin/respawn, AI/rideable, missiles/vehicle controls and anti-P2W; (5) source exact QA → authenticated RC CAS → real Studio/Android/competitive/OWNER verification.

Roll back by removing the single preview Script, which removes all spawned prototype objects on next Play.

## V2 core-loop reset — the new main game direction

OWNER now requires **massive horde-musou battle as a co-primary loop**, with teams still fighting to steal and deliver eggs. **武神** is the dedicated duelist/weapon master and sends flying sword slashes (not a Mage spell), with large self-boosting kami transformation. **One customisable castle per player**, grouped by Red/Blue team. Experienced matches aspire to 10,000+ individual verified neutral KOs / 30,000+ aggregate KOs with a genuinely huge multi-sector map. These are unproven product goals, not current QA results.

The new standalone `EGGRUMBLE_MassBattleCastlePreview.server.luau` is **another optional Studio-only script**. **Run it ALONE on a separate private Studio copy, not simultaneously with `SevenHeroArena.server.luau`** (their preview worlds are independent). This creates 9 large map sectors, a capped continuous neutral horde, automatic attacks and server-attributed real KO counts, XP-based slash upgrades, a castle for each joined player, and an owner-only banner-palette decoration station. It does **not** implement real PvP, capture/return eggs, production AI, advanced castle customization or Roblox/Android verification. The full contract, including performance/fairness/ownership, is in [EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md](EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md).
