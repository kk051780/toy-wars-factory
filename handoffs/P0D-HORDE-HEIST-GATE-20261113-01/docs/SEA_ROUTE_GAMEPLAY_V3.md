# P0D / EGG RAID RUMBLE — Shared SEA shortcut physical gameplay V3

**As of 2026-11-13 JST. Status:** S2+ isolated original source, NOT selected for S1, NOT mounted into official RC, Roblox Studio/Android/FUN **NOT_TESTED**. Existing S1 B42 private trial and sole #220 RC decisions take priority.

## Why this changes play rather than merely decorating the scene

The original first `GateVisual` was a standalone physical door on wide open grass: a player could run around it and ignore the feature. Source-checked H1 world includes physical SEA causeway `SEA_LOW_CAUSEWAY` x -60..+60 at z=-22, its free entries x±60→±72 and a SKY bypass z18. The new optional `GateRouteOverlay` adds **two mirror-symmetric gate doors** at x±36,z=-22 and stationary stone barricade arms around each. The gate corridor opening is 10 studs wide, same as source H1 sea passage. One original `GateRules` snapshot opens both after a legitimate neutral elite KO: warning2s → open10s → fail-open while a real character occupies either doorway. The other routes never require a player to pay, own a beast, or use a particular role.

The price of rushing the egg is a central battlefield gamble: neutral elite must be defeated before the short SEA lane unlocks; either team can steal and intercept via the same open gates. If the elite is ignored, teams may use the outer grass/SKY detour without ever being stuck. Never add a second game/round/Remote, score, combat, XP or event authority.

## Exact source-derived physical model

Read-only original sources:
- B42/first90 original Game SHA `837853e66278e38bb79f6399c3e8bfc9a2403be6`, Game Git blob `21b866e801a53ba7ebd66132ae55fe28608750d6`: 2 true server Horde-hit pathways (normal attack and earned beast strike).
- Original #288 V7 Musou Horde SHA `76cc75b71f0a1a7a5a9976f14c10276c636493f2`, blob `fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38`: real elite HP72 and once-per-death 8s respawn.
- Frozen original S1 MapBuilder blob `94655d019fdf9798fa24a350ebf49f8290465ac0`: grass ±125X,±71Z; five center pillars, castle sidewalls x±103,z±44, spawn x±68, eggs x±98,z-20, scoring pads x±82,z20.
- Frozen H1 fast-route source blob `7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea`: physical sea x±72,z-22; SKY x±62,z18. It is a **candidate source anchor**; actual selected Studio Place and collisions require human engine verification.

New optional S2 overlay part positions:
- Doors: x=-36,+36, z=-22, 10-stud WORLD-Z width, 12-stud height.
- North barricade: for each x±36, WORLD-Z center -3.5, length27, spans z=-17..+10. Height10.
- South barricade: for each x±36, WORLD-Z center -34.5,length15, spans z=-42..-27. Height10.
- Upper grass alternative beyond z≈12 and SKY path z18 remain reachable; lower grass z<-45 also passes. All colliders within original world and separated from canonical center minion homes and castle walls in conservative AABB source check.
- H1 source guard requires scene and exact sea part orientation before adding any part. Duplicate-overlay guard rejects a second mount.

### Conservative independent model outputs

| Route (1-stud grid with 1.7-stud avatar clearance) | Doors OPEN | Doors CLOSED |
| --- | ---: | ---: |
| Red spawn (-68,0) -> Blue egg (+98,-20) | 186 | 210 |
| Blue spawn (+68,0) -> Red egg (-98,-20) | 186 | 210 |
| Existing SEA crossing (-72,-22) -> (+72,-22) | 144 | >=174 |

**Not measured in Roblox Studio:** these are 2D grid steps under explicit static AABB geometry, not physical walk time, real ramps, jump animation, physics collision, actual egg carrying, frame rate, or FUN. A player might find unintended jumping shortcuts; only 2-client engine QA can clear the risk.

## Contract before #250/#220 adoption

1. Confirm exact H1 sea source and scene are mounted once. DO NOT add `H1_FUN_WORLD` a second time. This overlay creates only its own Model, never auto-runs a Script.
2. Confirm original #288 authoritative Horde elite KO receipt. Wire `EliteKOBridge.capture/didConfirmEliteKO` to ALL valid B42 `horde:hit` callsites, without changed combat cooldown or permissions.
3. Existing original Game alone constructs one `GateRules.new(tostring(match.serial))` per round and calls `step` in its existing tick. It renders one snapshot through `GateRouteOverlay.render` for **both** doors. NO extra independent timer/Remote/selector.
4. Ensure `occupantCount` is calculated with a **server-only physical overlap query**, including living body parts and egg carriers; never pass `0` blindly. Any occupied door stays passable after timeout until clear. Team/death/respawn/round reset must not trap characters.
5. Independently run actual selected source Luau and full Rojo. Then Roblox private 2client: both teams approach, hit true elite normally and with evolved beast, egg pickup/delivery, trapped player rescue, no cross-wall cheat, failure case no elite, 10s expiry, rapid rematch, close without embedding avatar; actual Android tap/FPS/first90/visual clarity and OWNER enjoyment.
6. If any world-map identity, geometry, performance, or child play failure exists, reject this candidate and return to unchanged S1. For S2+ backlog it must not delay `P0D-FUN-H1-001`.

Source test suite `tests/test_sea_geometry.py` and `tools/check_locked_upstream.py` is deliberately independent of the real engine. The CI result must match an **immutable source SHA** and have completed SUCCESS before counting static/native quality. No main/RC write, merge, Roblox publish, monetization or paid item was authorized.
