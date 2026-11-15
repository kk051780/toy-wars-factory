# EGGRUMBLE V3 — Owner's superseding match contract (2026-11-16)

**V3 overrides V2 where V2 assumed an egg-deposit victory, separate one-egg vs five-egg modes, or an optional/secondary personal castle.** Existing historical source and Game S1 code must be safely migrated by the authenticated writer; do not delete it blindly.

## A. Confirmed V3 victory & match economy

- **TEAM**: Red vs Blue. The **team whose entire roster of personal castles has been destroyed loses**. A player is personally eliminated once their own core falls, while surviving allied players continue to fight.
- **BATTLE_ROYALE**: Everybody competes individually. The **last surviving personal castle wins**; no team protection.
- **Castle fall**: A destroyed castle's banked eggs and its eliminated owner's carried eggs are physically released into the battlefield for any surviving player to collect. Elimination must be server-owned, prevent respawn to active competition, and handle disconnections.
- **Eggs**: Several in each personal castle, plus many throughout the field. First test balance: 3 eggs per castle and 24 field eggs. Carry cap: 3. Steal enemy castle eggs and physically return them to the player's castle. Team delivery earns limited siege supply; it does not immediately win. Eggs are the incentive for raids; ultimate victory is total castle elimination.
- **One-egg and five-egg modes retired**: No longer offer two mostly identical modes. Both TEAM and BR use a dynamic multi-egg economy. Migration of saved settings/game modes and rollback are required before changing official RC.
- **Time**: Use the historical 15-minute time as an engineering benchmark, with overtime siege pressure if multiple castles remain. No unapproved egg-score instant wins. A hard maximum round length/draw resolution remains to be balanced.

## B. Lobby / teams / AI

- Lobby contains **exactly two legible physical portals**: チーム戦 TEAM, バトルロワイヤル BATTLE_ROYALE. No giant permanent instruction overlay.
- The selected portal enters a queue. A short countdown starts with the first participant. **AI heroes fill missing match roster slots** to the target; AI has a castle, eggs and combat/raid rules, not merely a cosmetic teammate.
- Initial cap **16 TOTAL HERO SEATS** = human + bot heroes, e.g. TEAM 8 RED versus 8 BLUE, or BR 16 independent owners. Start with one human if needed and complete the rest by AI; real pathfinding and attack behavior must be verified in Studio before saying bots are complete.
- True production matchmaker will use separate authenticated match instances (reserved servers/places) for TEAM and BR. The isolated local preview runs in a single Studio place and does NOT implement platform teleport/production queues.

## C. Castle parity & builder freedom

- Every castle has same base core **1000 HP**, standard defensive attack hitbox, same objective vault reachability, same baseline footprint, same total pre-battle loadout budget.
- **Defensive option budget**: 3 slots and 10 equipment points for ALL owners. Example modules: HARDENED=5 cost, +50HP one-time shield; REPAIR=5 cost, +50HP one-time recovery; TURRET=4 cost; TRAP=3; SENSOR=2. HARDENED and REPAIR are mutually exclusive: any direct effective extra HP stays within **+5%**. The exact active turrets/traps are still separate gameplay implementations.
- **Two build styles**: template castle + modular optional defenses; or a **My Home/free-construction aesthetic** with roofs, furniture, windows, garden, banners, ornaments and architecture. Custom decorations cannot add indestructible walls, change the standard competitive core/egg hitboxes, block entrances, exceed plot safety limits or grant runaway power. The source rules prototype permits owner-only cosmetic placements in a defined personal plot (up to 48 harmless decorations); a full mouse/touch drag-and-drop house editor is NOT yet implemented.
- Keep personal ownership persistent in a later versioned saved profile. Ownership and rewards must be authenticated, and premium players must not gain bigger core durability budgets than free players.
- **Castle monetization**: sell explicitly chosen homebuild decoration packs, castle skins/roof designs, premium flags/banners, VFX skins for defense equipment, and optional early access to sidegrade defensive blueprints. Free users can unlock the same competitive modules and receive the same 10-point/3-slot defense budget. Never sell unbounded raw wall HP, extra unattackable gate geometry or >5% effective direct endurance. The current code contains a NONTRANSACTIONAL catalog only. Paid random items would require clear numerical odds and eligibility checks; avoid paid random defense crates in a children-oriented game.

## D. Map and siege strategy

- World design target: approx **3,000×3,000 studs** as a single **streamed** tactical flagship world, compared to the existing simple 1,380×1,380 studio-only nine-sector flat preview. The full map dimension is a design target, not a measured performance guarantee.
- Two team castle districts with separated ownable plots; BR castles distributed across different biomes to prevent spawn trap. Three or more meaningful approaches to objectives: high-ground ridge, forest ambush, river/bridge chokepoint, cliff passage, tunnels or narrow valley, coast and ruins. Landmarks, scouts and side entrances must matter tactically.
- Neutral soldier hordes should make fighting enjoyable even with no enemy humans. 7 jobs' large-area attacks and during-match evolution remain part of the core; server confirms each genuine neutral death individually.

## E. Max player estimate and KO arithmetic (ASSUMPTIONS, NOT ENGINE MEASUREMENTS)

Roblox officially supports up to **200 human player slots** as a configured server limit, but that does NOT mean 200 actors plus thousands of NPCs is viable on a mobile battle server. Roblox documentation warns Humanoid NPC simulation/animation/respawn is expensive, and advises pooling and instance streaming.

Sources:
- https://devforum.roblox.com/t/experience-join-improvements-server-size-join-queues-and-social-slots-reservations/2294621
- https://create.roblox.com/docs/reference/engine/classes/Players
- https://create.roblox.com/docs/performance-optimization/improve
- https://create.roblox.com/docs/performance-optimization/design
- https://create.roblox.com/docs/workspace/streaming

Engineering PLANNING MODEL, not a Roblox published coefficient: assume 60Hz server heartbeat 16.67ms; 10ms game-script/AI allowance, remaining 6.67ms engine/network. Hypothetical milliseconds per update: baseline 2ms, human 0.16, AI hero 0.28, individual castle 0.035, **optimized lightweight active neutral** 0.012. Formula:

    game_script_ms = 2 + 0.16*humans + 0.28*AI_heroes + 0.035*total_castles + 0.012*active_light_neutrals

| Match scenario | Humans | Bot heroes | Lightweight live NPCs | Estimated script ms / tick | Budget result |
|---|---:|---:|---:|---:|---|
| initial, mixed | 12 | 4 | 240 | 8.48 | PASS in assumption |
| initial, all human | 16 | 0 | 240 | 8.00 | PASS in assumption |
| candidate expansion | 20 | 4 | 220 | 9.80 | borderline, only 0.20 margin |
| candidate expansion | 24 | 0 | 240 | 9.56 | borderline, only 0.44 margin |
| larger, mixed | 28 | 4 | 160 | 10.64 | FAIL in assumption |
| larger, all human | 32 | 0 | 160 | 10.16 | FAIL in assumption |

**Decision**: initial **16 total combatant castles** including bot heroes, 24 only if server/Android tests show headroom, 32 stretch after significant optimization, 200 not a meaningful goal. Every active bot is an AI simulation expense even though it is not a Roblox Player. Full Humanoid-heavy NPCs will be more expensive than the lightweight assumed 0.012ms.

15-minute KO throughput:
- 10,000 individual KO / 900 s = **11.11 actual deaths/sec** sustained.
- 30,000 match KO / 900 s = **33.33 actual deaths/sec** sustained.
- At 240 live neutral units and perfect continuous replenishment, average lifetime must be at most **7.20 seconds** to sustain 30k match-wide. At a 96-live ceiling the theoretical cycle is **2.88 seconds**. Real server pools require margins for downtime.
- A sword wave hitting and really killing 20 individual units each 1.8s yields **11.11 KO/sec**, only if enemies are continuously available. Do NOT multiply server KO counters without corresponding deaths.

Need on-device measurements across 8/16/24/32 human+AI mixtures and 160/240/320 live NPC configurations: server Heartbeat/script timings, delta replication, p50/p10 mobile FPS, AI response, overall memory, castle destruction peaks, full 15min true KO per second, actual neutral model pool reactivation. Existing art/mobile gate median >=30FPS, p10>=25 FPS/15min + heat and crash checks still applies.

## F. Concrete source vs remaining work

[EGGRUMBLE isolated DRAFT #482](https://github.com/kk051780/toy-wars-factory/pull/482) includes:
- EGGRUMBLE_CastleMatchRules.luau: pure server-side rules, TEAM/BR, AI roster filling, same HP/module budget, castle fall releases multiple eggs, egg pickups/returns and last team/individual castle win, owner-only decorating, cosmetic noncollision.
- EGGRUMBLE_LobbyCastleModesPreview.server.luau: Studio-only two physical portal queues, 16 total seats with bot filler, individual castle models/egg vaults, castle attack via prompt, eggs released on fall, basic scripted AI-state tactics. **Bots have no real navigated 3D hero combat yet**, so not a finished mode.
- EGGRUMBLE_CastleShopCatalog.luau: no-payment price/category and parity schema; no Robux IDs, purchases, or real store integration.
- tools/eggrumble_capacity_model.py: sensitivity arithmetic assumptions; the script is NOT a performance benchmark.
- Separate prior samples for mass hordes and seven jobs. Studio samples are **mutually exclusive unless integrated by authorized source owner**.

**STATUS SOURCE_WIP / native tests not run / Roblox Studio not tested / Android not tested / no official RC integration / no real monetization / no Owner acceptance.** Avoid claiming full 16-player matches are working. Existing real Game/Store/HP/Remote/egg is modified ONLY through #220 authenticated RC writer, after comparing original authors #297/#303/#305 and later patches #476/#481.
