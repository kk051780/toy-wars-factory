# EGGRUMBLE — Warrior / Beast Tamer / Mad Scientist evolution contract (2026-11-16)

## OWNER directives

- Beast Tamer's **food must change the beast's form and play style**, not merely stats. Growth examples: **giant form** and **multiple split beasts**.
- Previous class 戦士 ("Warrior") is becoming **a weapon/martial-arts master + Japanese warlord + kami-empowered hero**. OWNER is considering names; **武神 / WAR GOD is now OWNER-CONFIRMED 2026-11-16**; prior 神将（仮） and 戦神 are historical suggestions. A final "八百万の神" achievement lets players assemble multiple divine manifestations/transformation powers rather than simulating millions of avatars. Japanese myth theme; eight-headed serpent-inspired spectacle.
- Scientist receives a parallel **scientific "異能コア" invention/equipment** concept to give collectible weird powers (e.g. gravity, plasma, phase/morph). This is a game-original discovery mechanism, NOT a replica of One Piece's devil fruit system. Do not copy its icons, swirls, rules, character designs, animation signature, water weakness, story setting or terminology. Kingdom-style martial heroism inspires energy, but no unique characters, banners or names from that manga/anime.
- Class count remains 7, internal role codes WARRIOR/BEAST/BUILDER unchanged; no new eighth job.

## Role identities that must remain different

| role | Core mechanism | Growth | Unique match benefit |
|---|---|---|---|
| 武神 (WARRIOR) | weapon-stance + martial mastery + short divine avatar **on self** | odachi, yari, taijutsu; elemental kami seals; eventual eight/many seals | martial AOE KO, gate breaking, front-line morale, boss-counter |
| 魔獣使い (BEAST) | one core tameable pet + food-based **pet body evolution** | GIANT / SPLIT / ARMORED first, flight/shadow/element as later growth | change allied beast into tank/pack/flanker for egg path |
| マッドサイエンティスト (BUILDER) | artificial science core changes **gear, inventions and vehicles** | plasma/gravity/phase, UFO, rockets, construction | customize battlefield equipment, terrain/transport |

### 武神 / WAR GOD battle design

1. First 30 seconds: powerful default odachi splash and weapon mastery. Choose yari for reach, taijutsu for multiple close hits.
2. C ultimate: **神憑き** for 6 seconds, with one selected seal: storm (three successive thunder pillars), flame (wide burn-like sweep), or legendary **eight-headed serpent-shaped divine phantom** rushing enemies. The serpent is a temporary spectacle, not an independent pet owned by the fighter.
3. Future: additional original kami seals for wind (air dash), mountain (shatter terrain/shield), ocean (tide sweep), night (brief shadow armor), sun (flash), etc. "八百万" represents a large long-term collection system with **finite equip slots and cooldowns**, not thousands of simultaneous abilities.
4. PvP guards: telegraph the attack, cap AOE and 6s transformation time, give counterattack/dodge. Egg carrier remains subject to egg movement/teleport restrictions. No permanent invulnerability.
5. Full-art goal: high-quality kabuto and fluttering battle mantle, evolving ceremonial armor, sword/spear/fist-specific locomotion and hit animations, divine halo and 8-headed illusion at mobile-safe LOD.

### Beast Tamer food

| Food | Visual + REAL behavior in first Studio preview | Full game target |
|---|---|---|
| 巨獣餌 / GIANT | single pet body scales 2.15x at B and 3.1x at C, high impact | slow giant, wide stomp, protects egg route |
| 分裂餌 / SPLIT | produces **3 physically separate smaller AI followers** (B 0.75x, C 1.15x), each pursuing dummies | multiangle pinning, weak per-unit, pathblocking limits |
| 甲殻餌 / ARMORED | separate metal-looking shell appears in B | defense aura, interception, no damage-only buff |
| 飛翔餌 / FLIGHT (future) | not yet implemented | wings + dive path; flying cannot carry egg |
| 幻影餌 / SHADOW (future) | not yet implemented | short concealment for companion with visible counterplay |

Food selection occurs in a world `ProximityPrompt` ahead of combat in the Studio-only preview so extra mobile on-screen buttons are unnecessary. The beast is summoned with the selected appearance and count. Next production stage: server-owned food resources, fair unlock rules, beast identity/collection persistence (without replacing DataStore identity), real movement AI, mount for appropriate forms, resource costs, catch/tame and PvP.

### Science core (proposal, not yet implemented in this code slice)

- **GRAVITY core**: magnetic lifts, controlled gravity field and modified turret trajectory. Unlike ESPER, it affects own inventions or gadgets rather than directly swapping enemy positions / sealing roles.
- **PLASMA core**: superheated energy weapon, multi-stage electric bomb FX, overheat mechanic.
- **PHASE core**: temporary matter-like movement and object reconfiguration for artificial vehicles or walls; *never* bypass game egg-carrying or castle fairness logic.
- Discover blueprints/cores through gameplay and craft/modify equipment. Do not enforce paid advantage.

## Actual source state and evidence

**Updated source file** `SevenHeroArena.server.luau` in [draft PR #482](https://github.com/kk051780/toy-wars-factory/pull/482):
- WARRIOR displayed as `武神`, selectable odachi / spear / fist normal attack patterns and airborne flying sword slash, and storm/flame/eight-head myth-inspired C ability; all three choices have distinct test-dummy effects.
- BEAST selectable GIANT / SPLIT / ARMORED feed stations, with B/C summoning modified model sizes/count and follower AI. Split summons three, constrained in preview by cooldown/lifetime. Armored shell is **visual only in this current source**; gameplay interception/defense not yet written.
- Old source contained a display-stand color error `c` without a definition; corrected by `local c=data.color` on the preview stands.
- Additional source contract checks authored but **not executed in a Luau or Python runtime**. No valid claim of Studio/Android gameplay, final art quality, actual egg/PvP or official RC admission. `SOURCE_WIP / ENGINE_UNKNOWN / OFFICIAL_RC_UNCHANGED / OWNER_ACCEPTED=0`.
- Major features still missing: true flight food and later feeds, actual warlord 3D animation & full divine seal collection system, scientist core gameplay, real player combats/egg interactions, collision/LOS safety, team and double-spawn constraints. A standalone prototype is not a complete playable shipping game.

## Cross-chat duties

**Common #218, concept #219, quality writer #470, official RC writer #220, art #420, trial feedback #364** use this document and PR #482 as a **shared proposed source slice**, not a second Game/HUD writer. Actual role Game/HUD/SevenJobs original authors #297/#303/#305 and corrections #476/#481 keep their source locks, and the owner has confirmed `武神` as the label but has **NOT** accepted production gameplay. No main pushes, unauthorized PR merge, paid tools, or Roblox Publish.

Next small implementation slices: (1) unique visual weapon animation and staged divine transition, (2) Beast Tamer armor interception and split AI/path balance, (3) original scientific core modes, (4) actual PVP+egg integration, (5) real engine/native/source exact/mobile tests, (6) #420/#470 quality PASS and OWNER approval.

## Major product reset — V2 supersedes egg-only balance and shared-castle model

See [EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md](EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md). Team assignments remain, every player has an individually decorated castle, battles against vast crowds are a main mode and eggs are a co-primary tactical win objective. Tens of thousands of **verified actual** NPC deaths per match are an aspiration, not an excuse to fake KO stats; mobile and performance limits decide live enemy cap.
