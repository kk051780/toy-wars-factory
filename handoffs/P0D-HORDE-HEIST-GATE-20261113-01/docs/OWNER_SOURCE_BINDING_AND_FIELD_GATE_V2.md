# P0D S2+ Elite KO ↔ shared route gate — actual-source integration contract V2

**STATUS:** ISOLATED_SOURCE_ONLY / NOT_SELECTED / NOT_RC / NOT_STUDIO. This document is NOT authorization to edit #220 sole RC or the #288 / #218 / #248 owners' branches. S1 First90 B42 private testing and #220 integration decision remain prior.

## Frozen real owner anchors (read from actual GitHub source)

- **Original #288 V7 Horde:** commit `76cc75b71f0a1a7a5a9976f14c10276c636493f2`, `handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau`, Git blob `fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38`. `Horde:reset(round,now)` stores `horde.round` and creates exactly one `elite=true` in `horde.mobs`, with HP72. `Horde:hit(...)` mutates `mob.hp` and `mob.deadUntil=now+8`, then returns **aggregate** `touched,defeated`; it does NOT return a trusted elite-KO receipt.
- **Original #288 V7 Game:** same commit; `inputs/Game.server.luau` blob `5979be7d70a415a8e954ff6a04babf4e3e09fd87`. One `horde:hit` call in server `applyAttack()`; source includes no new gate state.
- **Original FIRST90 B42 Game:** commit `837853e66278e38bb79f6399c3e8bfc9a2403be6`, `handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/Game.server.luau`, blob `21b866e801a53ba7ebd66132ae55fe28608750d6`. **Two** server-authenticated `horde:hit` callsites (evolved scout ASSAULT near source line1197; regular ATTACK near line1644). Hooking only ordinary attack would silently break the egg/monster evolution fantasy.
- Original #248 physical H1 `MapBuilder.luau` blob `94655d019fdf9798fa24a350ebf49f8290465ac0`: castle N/S walls x±103,z±44. #248 original H1 overlay blob `6de8a8b4f17afd4e11c4be8eb1db556506d9c8df` has four source-known route/wall intrusions; #253 candidate `2494fa855d77e1ef6dd2c5f8b8d21fbef90fc44a` adjusts route geometry but original author acceptance and real 2client physical QA remain pending.

## Source-only bridge: first authentic elite death, not any neutral KO

An owner of an existing Game.server.luau can **optionally** wrap EACH true server-side PvE hit call with this exact pattern, after confirming module placement/real event ordering:

```lua
local before = EliteKOBridge.capture(horde)
local touched, defeated = horde:hit(actualAuthorizedOrigin, actualAuthorizedFacing,
    actualAuthorizedDamage, serverNow(), player.Character)
if before and EliteKOBridge.didConfirmEliteKO(horde, before) then
    -- Use the existing authoritative match.serial; no new round counter.
    gate:onEliteKO(tostring(match.serial), true, serverNow())
end
```

The actual original input variables differ between ordinary attack and earned evolution; DO NOT replace Game or copy this snippet literally. Preserve original elapsed time, token expiry, combat cooldown, replay/reward and existing server conditions. No client input may call `EliteKOBridge.capture` directly. For B42, wrap BOTH server callsites; V7 has one. The adapter only recognizes HP > 0 → 0 for the SAME elite object and same horde.round, whose deadUntil was set by original hit. `GateRules:onEliteKO` makes the event once-per-round and stale-epoch resistant. At new round, allocate a NEW `GateRules.new(tostring(match.serial))` from original Game start; step/render only from existing heartbeat/tick. Do not create another authoritative Game or Remote.

### Physical-world admission BLOCKER

Current S1 central grass field is wide and open. A freestanding `8-stud door` placed there can be walked around, thus is NOT a meaningful shortcut. #220/World owner must first establish a **genuinely traversable but closed chokepoint** with a free always-open alternative, using original authoritative world bounds. Choose either (A) symmetric castle side shortcuts with two physically separate doors sharing ONE GateRules snapshot, or (B) one central route with natural wall/barrier and no team asymmetry. Neither geometry exists in this packet.

Use `GateVisual.create(parent, collisionFreeCFrame, verifiedCorridorWidth)` with `6 <= width <= 24`; side bypass must be sealed by real map features, otherwise REJECT. Before closure count all relevant server-side living humanoid body parts within a safe expanded door overlap volume, not client reports or solely root-center distance. `WAIT_CLEAR` stays passable while occupied. Avoid trapping an egg carrier and keep original score pads/egg prompts/castle walls/LOS and fall rescue intact. If route wall or collision overlap source audit fails, do not adopt. If the human experience is unchanged, prefer H0 no code addition.

## Required gates, in order

1. #250 product selection after currently selected B42 private trial; this is S2+ only until explicitly selected.
2. #288 Horde original owner validates same-round before/after edge and all actual PvE callsites. #222/#248 World owner validates collision and passability/topology with source-lock.
3. Native Luau compile + real Rojo private build + independent negative tests (no remote forgery, stale round, repeated KO/respawn, no rewards/score changes, two team symmetry).
4. **Actual Roblox Studio** two-client real PvE elite KO from each eligible attack, doors opening and closing without collision trap, egg pickup/return/score/rematch, Android sideways FPS/visuals, OWNER H0/H1 feeling. Until these results exist, NOT_TESTED.
5. Only #220 sole RC integrator may choose/hunk-admit the verified feature and update formal S1 progress after complete evidence. H0 remains unchanged rollback.

**No change:** main, P0-A/B/C auth/CAS, paid items, Roblox production publication, existing Automations, owner PC/Studio session. GitHub comments cannot launch Codex.
