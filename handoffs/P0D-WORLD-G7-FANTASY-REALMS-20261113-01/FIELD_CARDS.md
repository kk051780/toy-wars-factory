# P0D WORLD-G7｜幻想フィールド3世界（S2+提案、未統合）
Date: 2026-11-13 JST. Parent canonical #222 / #219. Original design, not derived visual reproductions of other games.
Source observational principles: Roblox Creator Hub onboarding https://create.roblox.com/docs/production/game-design/onboarding ; performance https://create.roblox.com/docs/performance-optimization/design ; official Roblox charts https://www.roblox.com/charts?SortFilter=3 (retrieved 2026-11-13, current ranking is time/location/device dependent). Observation: FTUE needs short action, low end mobile performance requires proof; inference: 3 short, well-signed optional worlds likely produce interest better than an empty sprawling map. NO gameplay/retention uplift measurements.

## WORLD_MECHANIC_CARD G7 — Three S2+ pocket-worlds, actual prototype restricted to visual showroom
### WF-13 / 星環の宇宙回廊 (SPACE)
- **3秒理解:** 紫の大きな輪、浮く黄色い星、「ここで宇宙が始まる」見える; path remains physically freely accessible
- **Future real-game action:** any role walks through star gate to a short low-gravity traversal lane; low gravity must ONLY apply within a 6-second server-authoritative field, bound jump strength, no permanent flying or invincible egg carrier
- **Counterplay:** arrival/exit visible from both teams, guardian can defend exit, one always-open ground bridge; no exclusive access/paid upgrade
- **Neutral rarity:** original rare astral beast purely noncombat and distinct from ordinary SPACE #232 creature (if authored later); no direct capture P2W
- **Fail-safe:** fall = safe edge return, carrier cannot get unreachable egg, no weightlessness in current prototype
- **7-sec clip:** egg thief slips through luminous asteroid ring while defender rings the counterbell
- **Performance hypothesis:** >=24 scenic Parts below ~35 for portal stage near player, far constellations very low detail; actual FPS UNKNOWN

### WF-14 / 雲上の光庭 (HEAVEN)
- **3秒理解:** white/gold sky tower, open cloudy bridge and bell; child walks from hub to view an enormous upper castle
- **Future real-game action:** any role can trigger a warning bell making the alternate cloud staircase visible for 6 seconds, not an egg teleport
- **Counterplay:** both sides see cloud staircase and the same visual cues; Guardian can hold safe gate, Raider wind helps reach but no free captive skip
- **Fail-safe:** permanent free ground bridge, protected railing and respawn at nearest safe tile; no moving dizzying camera
- **7-sec clip:** friend rings the bell, cloud path glows, two teams race under the sky fortress
- **Performance:** distant castle uses silhouettes, not costly full tiles; mobile/streaming QA required

### WF-15 / 灼熱の奈落洞 (ABYSS)
- **3秒理解:** warm red safe floor with obsidian pillars and a distinctive red gate, obvious bright safety path
- **Future real-game action:** a telegraphed periodic gate reveals a shorter tunnel. A full ground path ALWAYS remains open. Lava is visually scenic without unavoidable HP drain; no pay-to-cross.
- **Counterplay:** defenders see a 5-second cue, same entry options; don't trap a carrying player behind a timed solid wall
- **Fail-safe:** no fatal lava in initial version, no forced carrying resets, short walk-back
- **7-sec clip:** gateway glow changes, attacker takes a tunnel and defender counters at next stair
- **Performance:** use bounded decor, avoid flashing lights, no persistent world-global Lighting changes

## Realm director, actual coded scope
- Source code Studio-only 3D **showroom** with permanent 14-stud wide accessible hub-to-island paths and 3 original scenic landmarks. These ARE physical 3D Parts in source but have NOT been tested in Roblox physics.
- One deterministic PURE native Luau event scheduler: cycle95s = WAIT20s -> ANNOUNCE5s -> ACTIVE25s -> COOLDOWN45s; one selected realm each cycle (SPACE, HEAVEN, ABYSS), selected from fixed seed. Every active event only changes cosmetic beacon/sign, NO gravity, collision, HP, egg, capture, role, inventory, RNG reward, or economy. Supports both teams identically.
- Reality proof required: actual native Luau rule VM + static source policies + actual Rojo native Studio .rbxlx. No #220 RC adoption or original #222 cards modification.

## S1 vs S2 priority / decision
- S1 P0: original H0/H1 real Studio+2client/Android/human FUN gate remains highest priority; do NOT replace #255 game or #220 official RC with the showroom.
- S2 first: WF-13 low-gravity lane ONLY after native safe return + two-team/mobiles pass; then WF-14 cloud bell; WF-15 timed gate last due to trap/egg and mobility safety.
- H0 experiment: original game route vs S2 same-match + ONE new optional space corridor and same roles/teams; compare early-90s child understanding, successful egg captures, fair red/blue winrate, rescue rate, FPS and voluntary rematch. Baseline and thresholds NOT_MEASURED.
- S3+ possibility WF-16 海底虹ガラス港 physically links #222 WF-05 bubble tunnel to surface; distinct task, NOT authored or live now. Always preserve freely walkable surface route.
- No copying of competitor IP, no Robux payment switches. Design Source / Studio / Owner Approval distinct.
