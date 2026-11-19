# RC85 → RC86 → REAL65: single formal RC non-loss integration

Owner directive: all useful historic RC85/RC86 features must be retained or reimplemented in ONE live V3 build, not copied as a second Game/Store/HP/Remote/score writer. The only formal branch is \`rc/p0d-s1-kids-rc01\`; **do not merge the old RC85/RC86 Place or their entire S1 Game/HUD into REAL65**.

## Immutable verified input objects
- RC85 original PR #479 parent: Actions 43707821050, artifact 14158848286; \`P0D_FB026_NECROMANCER_SIEGE_CUMULATIVE_PRIVATE85.rbxlx\`, **85 Luau** (old TrapRaidersS1 architecture), 830,812 bytes, SHA256 \`fdd7ed3397c02825c67e986ca0fb1755dbe15f9523ac065cbef1cdc66d81d978\`.
- RC86 cumulative PR #479: Actions 43714858562, artifact 14161823401, \`P0D_RC86_SIEGE_V3_STAGE_WEAPONS_UNDEAD_PRIVATE.rbxlx\`, **86 Luau**, 843,641 bytes, SHA256 \`11fa894c4ebfa2303e3f7cef8590d14a6a26f359699b6eda3d2e692bc161c707\`. S1 Game, original UndeadSquad, StagePickupLoot, seven arms, castle/bot/egg features stay on this lineage.
- RC86 wall-safe successor PR #479: Actions 43754858996, artifact 14177514150, \`P0D_RC86_STAGE_WEAPONS_UNDEAD_WIND_WALL_SAFE_PRIVATE.rbxlx\`, **86 Luau**, 845,972 bytes, SHA256 \`d67f9f68912cb67de0e184844d57649fbe50e5b70ab30cffbe3ee320e6a15cd8\`. Single StagePickupLoot new source, other 85 exact. Guarded server raycast stops a closed castle gate/wall bypass.
- Formal RC REAL65 source input: post-#863 current canonical source (65 selected), unique Combat/Swarm/Host/Realm. Native/Rojo65 and OFF63 tested by official #44510286705 and subsequent audit PR #836. Studio/Android/FUN **not tested**.

Source inventories compared from the *actual original Place XML*, not only PR titles. RC85/RC86 use \`ServerScriptService/TrapRaidersS1/Game\` as main owner, V3 uses \`ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview\` and \`EGGRUMBLE_SevenRoleCombat\`. Naively concatenating 85+86+65 is unsafe and would violate ONE playable game.

## Nine-domain functional reconciliation: verified, newly ported, still outstanding

| Domain | Old RC85/86 useful feature | REAL65 disposition |
|---|---|---|
| Character | 7 role weapon silhouettes; Assassin Wind/R; 7-job melee combos | Existing V3 \`EGGRUMBLE_WeaponSilhouettes\` and 7-role Combat; **Assassin Wind exact parity not proven**, do not count as adopted |
| Field | Original S1 coastal sea, castle details, meteor/starshards, twilight twin biomes, Realm Hunt | V3 land/sea/sky and Realm exist; **original specific scripted events are not verified ported** |
| Battle | 7-job armament M1; original RC86 weapon buff (1.35 / 1.08 / 1.22 for 18s) | Existing V3 Basic/Dodge/Combat; this PR ports RC86 **six world weapon pickups and three 18s damage buffs** into existing Item and Combat, with no second damage owner |
| Castle/egg | Old siege wall gate, castle art and S1 egg escort | V3 CastleRules/siege/egg code present; **feature parity and engine runtime are not established** |
| Neutral | Three genuine old UndeadSquad model companions with FOLLOW/GUARD/FOCUS + neutral horde | V3 existing \`ZombieCommander\` in original \`EGGRUMBLE_SevenRoleCombat\` includes three summons; \`CurseConversionPolicy\` and existing Swarm conversion are wired. Do not import S1 \`UndeadSquad\` (duplicate 3-summon engine) |
| Item | Old RC86 SUN_BLADE/WIND_SPEAR/THUNDER_BOW world pickup; StageLoot line-of-sight gate | V3 prior HEAL/DASH/SHIELD + InteractionGuard; this PR adds **three other weapon classes**, reusing V3 InteractionGuard and current single Item owner |
| Lobby | Old 3D dojo, 4 Tools, First90/coach | V3 safe spawn and social/shop; **old dojo/training exact physical game port not proven** |
| UI | Old mobile Wind, skill X/C, result, Attack feedback, forest fog | V3 HUD/Basic/Dodge/impact exists; **old mobile Wind full parity not proven** |
| Balance | Old 15min round, class buffs/XP/beast evolution | V3 ScoreBalance/CombatBalance/Deadline; **old persistent mastery, beast evolution and training not proven adopted** |

### Historical 48-feature group non-loss backlog
RC85/RC86 RC_FEATURE_LOCK contains 48 enabled old-S1 feature flags. None may be called "official V3 adopted" merely because same concept exists. Pending semantic parity review includes Realm Hunt, SIX_SKILL_DURABLE, SAVED_PVE_MASTERY, SAVED_BEAST_EVOLUTION, SCOUT_SPECIES, CrystalCanyon, EGG_RELAY, STARry paths, meteor/star shards, twin biomes/training/bond companions, H1 sea, Dojo, FUN/First90, original physical fortress/castle world, forest sightline, Gorogan rig/AI, mobile role selection, original hit FX / coach / personal result. Compare original author source/behavior, not names.

### This PR's *real* change
One source-locked post-composer overlay touches **only** \`EGGRUMBLE_FieldItemPickups\` and \`EGGRUMBLE_SevenRoleCombat\`; all 63 other chosen REAL65 sources stay byte-identical to the pre-PR composer output, original 65 routes remain the same. Original current 9 HEAL/DASH/SHIELD pickups stay active. Two player-safe checks gate each pickup: current server-owned TEAM/BR roster/egg-carrier and preexisting wall/proximity \`InteractionGuard\`. Temporary server-owned buff is only consumed by the **single preexisting Combat neutralAndBotHit** path; no client damage grant, no extra Store/Score/Remotes/second Game. No bonuses to summoned minions; stale player, avatar, expired/retired session, or egg carriers cannot use the boost. Original #863 late-Host LSS/Realm wait repair and all previous 65-source work preserved.

Performance changes: 6 noncolliding world weapon pedestals and 6 low-poly silhouettes *per currently active match*. No P2W, no persistent unlock. Native/Rojo/65-source and OFF63 receipt gate must pass at the EXACT PR HEAD before any official adoption. All ART/Studio/Android/child FUN remain NO_GO until measured.

### End-to-end acceptance, explicit unfinished obligations
1. Run same-PR-head exact SHA/source/class Native65/Rojo65/OFF63 workflow GREEN, then certified #220 successor updates the ONE formal RC with fresh expected SHA/nonforce merge/CAS and checks official same-HEAD artifact + ZIP/Place bytes.
2. Owner Studio test V3 start, both TEAM and BR pickups, weapon buff 18s, three weapon appearances, all seven roles and old triple-undead, field items, egg-carrier reject, no-through-wall, match reset, and no stale buff across matches.
3. Audit each remaining distinct old-S1 feature and source-selectively port real functionality into canonical V3 *without replacing V3 Host/Combat/Item/Store/Score*. Old source artifacts stay immutable reference evidence; not a second official RC.
4. Compare Android 15min and first3min FUN / art with owner before any release/publish/monetization.

Work/Codex, main, Roblox Publish, spending, Robux purchases: **NO**.
