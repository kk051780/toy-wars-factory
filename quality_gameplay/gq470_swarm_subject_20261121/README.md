# GQ470 FB-008 / FB-015 — Swarm display-distance ownership

**Isolated A source candidate only, NOT formal RC or Studio/Android/ART/owner accepted.**

The immutable official REAL69 selected source `ServerScriptService/EGGRUMBLE_SwarmCombat` SHA256 `cc40d9902834b63db15bc8ff63a0be0f092cdc17e5a962d9669784f4e15dd75a` already contains the merged #915 suppression `h.NameDisplayDistance=0; h.HealthDisplayDistance=16` but leaves `Humanoid.DisplayDistanceType` unset. The 2026-11-21 16:26–16:50 JST real Studio Play (#470 comment 7059635245) still reports dense overlapping HordeSoldier names obscuring the player. Roblox official docs distinguish Viewer and Subject ownership: https://create.roblox.com/docs/characters/name-health-display . This causal theory needs actual in-engine before/after proof.

The exact existing `soldier` constructor receives one additional assignment immediately above those two original limits:

```luau
h.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Subject
h.NameDisplayDistance = 0
h.HealthDisplayDistance = 16
```

Original server AI, enemy count/HP/KO, egg, castle, damage, data, Remote, model parts, scripts, and update loops remain unchanged. This is a **continuation of existing merged #915**, NOT a duplicate feature nor #924 BotActors. No new script or instance.

## Source verification
- Lock formal base `e80973c354f14a0d0088577f3cc1a875454f0f8f`, exact original source hash, all69 hashes, classes and routes from official artifact #14610422120
- Fail closed on drift, duplicate source, invalid anchor, changed HP distance/owner, wrong source class, missing script or second application
- Native Luau ON69/OFF69; real pinned Rojo7.7.1 OFF69 Place byte-for-byte exact, ON69 candidate selected source, same commit HEAD CI required
- Rollback: `OFF69_SWARM_SUBJECT_EXACT`; never change official RC or merge all PREP files
- Studio Solo/2client, 32 real PC/Android paired screenshots, Android 15m FPS/heat, 3-minute kid FUN and owner: **NOT_TESTED**, `ART_NO_GO`

## Intake
#218 soft scope 7060661797 **is NOT CLAIM_GRANTED**. #910 visible avatar/full egg/castle/win is P0. The quality gate #470 must review this after official P0 and #250 ADOPT/REWORK. Only verified #220 B writer may source-select actual Swarm ModuleScript into freshly obtained sole official RC HEAD by nonforce expected-SHA CAS and same-head full official CI, real ZIP/Place, rollback and Studio followup. No work on main, Publish or paid resources.
