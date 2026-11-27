# EGGRUMBLE V2 — OWNER-major game loop reset, 2026-11-16

**OWNER's latest highest-priority gameplay instruction**: 「武神が良い。様々な武器が使える、遠距離に斬撃を飛ばす。神を宿すと個人能力大幅上昇、1対1最強。大量のフィールド中立兵をプレイヤーがなぎ倒し続けるのがゲームの本筋。ダダサバイバーのバトルロワイヤル。1試合、多いときは数万撃破。フィールドを大規模化。城はプレイヤーそれぞれが持ち自由に装飾。チーム分けは維持。全Chat周知。」

## 0. Name, historical IDs and scope

- **Product title = EGGRUMBLE**, do not put TRAP RAIDERS on visible new screens.
- **Class = 武神 / WAR GOD** (OWNER's final name); formerly 戦士/神将（仮）; internal **WARRIOR** must not change for existing saves/remotes/contracts. Keep seven jobs.
- Existing Game/HP/egg/Store/server authority still belongs to the original code authors, #220 authenticated RC integrator and #218 CLAIM policy. This V2 document plus the NEW source in existing #482 is **SOURCE only, NOT integrated**.
- Genre pitch: **Horde-survival musou × team-based egg-heist battle royale × per-player customizable castle**. Clash with Survivor.io at the *fun mechanism level*, not its protected visual/character/equipment IP or identical skill names.
- DO NOT reduce this to egg-only stealth capture, or generic hit once per job: horde survival progression must be fun with zero enemy human players.

## 1. Two equally visible gameplay pillars

**Battle as a primary loop**:
- Neutral hordes come in waves throughout large traversable areas, include varied small troops + elites + occasional bosses. Intro can dispatch 10+ minions in seconds, then selectable within-round evolution branches at milestones; abilities broaden AOE and combos.
- Earn XP/gear materials through actual server-verified neutral kills; unlock *within-round* weapons and active/passive upgrades (NOT permanent paid power). At the finish display personal verified KO (neutral/PvP separate), longest combo, evolved skills, eggs captured and delivered, castle defense assists.
- A motivating **stretch goal** for successful late-game players is **10,000+ personally verified neutral kills per 15-minute match**; aggregate match total can exceed **30,000+**. These are **product aspirations not test evidence**. Targets imply average 11.12 individual KOs/sec and 33.34 match KOs/sec respectively. Spawn throughput, DPS, hit traces and device tests must establish feasibility.
- The official game sells power fantasy + battle spectacle, but should never fake counts by awarding 1000 for one enemy, nor build 30,000 simultaneous replicated Humanoids. Physically spawn and resolve active enemies in capped interest-based pools; pool them, LOD/StreamingEnabled, cull and batch nonessential effects, keep server-owned death attribution. "10000 KOs" means 10000 actual enemy deaths recorded, not fabricated batch kills.
- Solo play gets AI team/opponents; no external opponent should be necessary to test fun in first 3 minutes.
- **Within-match** progression loop: Kill → XP → choose weapons/skills/upgrades → change attack topology (projectile sweeps, arcs, pets, area blasts) → faster horde clears → collect rare eggs/objectives.
- **Touch**: thumbstick + optional auto basic/aim + 1–3 deliberate special buttons. No big permanent guide; show level-up choices briefly and collapse.

**Eggs and PvP as high-stakes layer**:
- Maintain RED vs BLUE **team assignments**. At least one egg heist and return remains a meaningful victory path; battles generate the power, map control and risk/reward that enable egg raids.
- New per-player-castle model gives each participant an **owned castle** on their team's side. Proposed objective: each castle protects an egg/objective; stealing from opposing player castles and physically returning it to one's own (or team deposit, after OWNER decision) credits authenticated team capture.
- **Important**: old shared team-castle assumption / 1-egg / 5-egg Game modes need source-conformity review. These are no longer the final world layout, but cannot be deleted in an unreviewed migration. Final deposit routing and castle-egg respawn are explicit **unsettled design decisions** to resolve before authoritative Game changes.
- Neutral KO is meaningful through within-round power, personal results and tie-breaker/secondary scoreboard. Egg captures still determine the primary match result unless OWNER changes scoring.
- **Anti-exploit**: position exchange/warp/flying/UFO cannot teleport egg carriers to instant victory, team ownership/source and scoring must be server owned, disconnect/rejoin/respawn/castle-owner reassignment safe.

## 2. Bushin: strongest duelist and best weapon master

**Official visible class name 武神 / WAR GOD**, code ID WARRIOR.
- One player can use **odachi / spear / twin swords / axe / bow / taijutsu** with role-specific switchable attack motions. Ranged sword-arc is a true hitbox/projectile/sweep, not elemental Mage spell. Not all planned weapon types are implemented in current source.
- **1v1 specialty**: combo links, parry, perfect guard, counterattack, dash pressure, stance weapon reach/attack speed. On equal progression and player skill, intended highest **duel win rate**, tested across class matchups. It must still permit skilled counters and escape; no invulnerability or forced auto-win.
- **神憑き**: unlockable seals (storm/flame/serpent and expand), ~6-second transformation for prototype, major self damage/defense/movement boost, visually dramatic war-god aura/armor. Long term 八百万神威 = large collectible catalogue with small equip slots, NOT millions rendered.
- **Mass KO**: fast close-range cleaves + flying slash with long-range arc, high combo and horde DPS. Boss/duel effectiveness separate from generic mass-burst power.

## 3. Map and neutral density

- The current tiny map is disqualified as a finished design. **Massive contiguous field** with neutral spawn-rich wilderness, enough spacing for raid preparation, distinct mountain/forest/coast/ruin/sky/valley regions, 3+ routes, chokepoints, transport and exploration. Single map polished before many separate maps.
- **NEW stand-alone SOURCE prototype** `EGGRUMBLE_MassBattleCastlePreview.server.luau` creates 3×3 color-coded sectors of **460×460 studs** (= ~1380×1380 studs theoretical footprint), capped **96 live neutral humanoids in test field**, continuous spawning near heroes, chase, auto slashes, source-confirmed KO stats and XP-based slash tier upgrades. Precise final field dimension, number of visible NPC and FPS budgets must be derived from native Studio/Android tests; do not imply this simple flat color terrain is finished art.
- This preview creates one own castle per joined player, split by RED/BLUE side (uses Team when available, Studio-only fallback), with owner-only **three-color banner decoration**. Full castle structure personalization, modular architecture, saved cosmetics, siege and egg storage are **NOT implemented**.
- Game engine target: live enemy count chosen adaptively per player device/camera/network and grouped navmesh, minimize clients' replicated physical NPCs, schedule spawning and collision/hits server-side. Low-end Android gate remains official #420 metrics; a nominal large map or KO count cannot supersede device target.

## 4. Per-player castle ownership & cosmetics

- One castle allocated to each player, visibly belongs to their chosen team. Castle has entrance, interior, stairs, egg vault/objective, defense points, siege damage/repair and access routes; team allies can defend it.
- **Decoration** is personal (roof color, flags, stone skins, courtyard props, banners, banners, gate ornaments); cosmetically separate from HP/hitbox/clearance so rich players cannot buy a stronger castle and mobile navigation does not fail. Cosmetics should persist with server-backed keys once integrated, must not overwrite the existing profile schema without migration.
- Multiple personal castles inside a shared team territory. Player entrance spawn location should never clip into terrain or trap guests. Spectators/teammates can see each owner's unique castle.
- Capture rules need to be resilient to uneven parties and no-opponent solo AI; owner disconnect must not remove an active team's target unfairly mid-match.

## 5. Mandatory quality-gate evaluation

**Mandatory RED for release**:
1. Real map supports multi-route raid + horde brawls + travel with no invisible walls/leaf collision dead ends.
2. 7 classes have distinct basic moves, movement, special and ultimate with PvE crowd impact; War God 1v1 vs all 6 classes tested (no fake deterministic victory).
3. 30s neutral-KO demo shows multiple enemies in single attacks + hit/damage/heath/death and accurately attributed KOs; increasing wave difficulty and real growth skill selection.
4. High-end goal >10k player KO or >30k match KO is a *stretch benchmark*, require recorded same-HEAD match telemetry and measured device FPS before claim. Record observed per-minute KO, active NPC max, entity spawn/despawn count and p50/p10 FPS; do not manufacture.
5. Every player owns individual castle, can personalize, keep team layout, siege/egg vault works, server-side egg custody/return and score verified; owner disconnect handled.
6. Strong camera/VFX/audio impact, enemy burst and hit feedback, crowd readability and nonblocking HUD. #420 art+mobile, #470 game FUN/competition, OWNER accepts only after actual playing.
7. Safe changing of actual Game/Store/Remote/historical identifiers only via existing author #297/#303/#305 and #220 authenticated source-selective integration. YELLOW developer debt may remain in private work per V6 rules, RED core breaks cannot.

## 6. Implementation status — avoid conflation

- [Draft PR #482](https://github.com/kk051780/toy-wars-factory/pull/482): ***SOURCE_WIP*** has 武神 in Studio 7-hero arena, ranged slash demo, extra 1-target damage and stronger simulated divine attack, and separate 9-sector/individual-castle/horde preview source.
- The crowd preview's **auto-attack is a test scaffolding**, not true seven-class Game/HUD/egg PvP; castle decoration is palette-only and session-only.
- **Native / Studio / Android / owner-accepted / genuine official RC integration = NOT TESTED / NOT DONE**. One working private *code source* does not meet the new product specification.
- New public name **EGGRUMBLE**, legacy internal remote and DataStore paths intentionally retained. No publishing/merge without authorization. This huge change cannot be represented by just updating an issue title; other chat teams need to re-plan actual Game/World/Art/QA work packages.

## 7. Cross-chat handoff and no duplicated work

- **#218 common**: OWNER top-priority V2 new loop; everyone checks current product directions.
- **#219 planning**: source of truth; FEATURE_CATALOG change must be explicit for legacy egg-only and shared castle fields; queue source changes, not brainstorming-only.
- **#220 RC integrator**: do not overwrite base Game/HUD or merge preview wholesale. Select genuine appropriate source and integrate with CAS, same-HEAD QA.
- **#470 product quality**: job-specific horde/duel/egg/personal castle tests, 67+ feature mapping and source repair, strong benchmark targets.
- **#420 art**: real scenic massive world / hordes / hero transformation / personalized castles; Android performance.
- **#222 world field**: sector streaming, spawn/AI route, team territory and owned castles, map traversal.
- **#364 owner trial feedback**: broad-world / crowd musou / individual castle / warrior-brand changes trace to actual defects and fixes.
- **#250 adoption gate**: tag release objective and candidate source/RC proof distinct.
- **Existing A workers #297/#303/#305/#476/#481**: existing job/game authority prevails; prepare safe source-selective slices using #218 CLAIM. #482 only includes isolated Studio preview; do not treat it as an authorized second Game writer.