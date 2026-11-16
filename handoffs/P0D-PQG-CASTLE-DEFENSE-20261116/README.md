# EGGRUMBLE V3 / personal castle live defense — isolated SOURCE candidate

Status **SOURCE_PREP / SOFT_CLAIM_REQUESTED / NOT_RC / NOT_STUDIO_VERIFIED**.
Parent: #218 claim request [comment 6906513949](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6906513949); PRODUCT QUALITY #470; owner-authored V3 #482; authenticated RC intake #220.

## Actual missing gameplay being repaired

The existing V3 source `EGGRUMBLE_CastleMatchRules.loadDefense` accepts TURRET (4 points), TRAP (3), SENSOR (2), max 3 slots / 10 points; the #482 existing castle preview currently gives real HP effect to HARDENED/REPAIR but has no live opponent targeting or physical effect for the other three. Repeatedly adding a cosmetic tower or another standalone game is not a fix.

New **server-only live mechanics** (isolated optional module, no duplicated Game/Remote/HUD):

| Defense | In-match effect | Server limits |
| --- | --- | --- |
| TURRET | Single nearby hostile hero takes 12 HP real Humanoid damage with a short visible pulse | 35-stud range, real collidable LOS, 2.4 s per owner |
| TRAP | At entrance, hostile hero takes 8 HP + 1.1 s slowing debuff | 9-stud reach, real collidable LOS, 7 s per owner |
| SENSOR | Removes stealth from a nearby *hostile* invisible human; reveals position with pulse | 30-stud radius, 1 s frequency, no damage; never touches own team |

Both TEAM and BATTLE_ROYALE use the same matched roster and each player's castle, not a global damage loop. KOs are actual Humanoid health changes only; no fake score event. Destroyed castles never attack. Paid cosmetics and durability caps unchanged. A module never appears unless `loadDefense` selected it. Maximum 16 players/bots and 48 non-colliding anchors per arena. Each session auto-ends after match leaves ACTIVE.

## Minimal original-author wiring — NOT applied by this lane

The author of existing #482 should copy both new ModuleScripts as sibling entries into its existing private `EGGRUMBLE_V3_STUDIO.project.json` and add this single import at the top of **the existing** `EGGRUMBLE_LobbyCastleModesPreview.server.luau`:

```luau
local CastleDefense = require(script.Parent:WaitForChild("EGGRUMBLE_CastleDefenseLive"))
```

After the already-existing `BotActors.start(session,Rules)` call (with the same `session` and already-loaded `Rules.loadDefense`), add:

```luau
CastleDefense.start(session)
```

When `session.closeRound` executes, call `session.castleDefenseStop()` if present before `session.world:Destroy()`. The current `world:Destroy()` also stops the loop; explicit cleanup is preferable. A reversible flag `P0D_V3_LIVE_CASTLE_DEFENSE=false` should make this hook a no-op for rollback. **Do not add a second server Game**, copy a Store, add RemoteEvents, create another lobby, or change the economy.

## Validation and claims

- Authored native regression: `luau tests/EGGRUMBLE_CastleDefensePolicy.spec.luau` from this folder. Expected: teammate/owner/defeated/no-module rejection; TEAM/BR target rules; turret/trap LOS; 16-hero cap; cooldown; unknown modes; NaN and negative values.
- Authored Python source check: `python -m unittest discover -s tests -p 'test_castle_defense_source.py'`.
- Exact binary native/Rojo build, real session hook, 1-human+15-bot and 2-human+14-bot Studio runs, Android 15-minute median/p10/thermal, FUN and OWNER acceptance remain **NOT_TESTED**. Tests authored are not reported as executed.
- Source-lock parent is #482 `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`. Only novel files under this handoff path were written, so author-owned feature source hashes are unchanged.
- Integration path: ORIGINAL #482 author adds optional hook + native/Rojo CI at its latest head; #484 composer checks source instance uniqueness; #220 only authenticated writer performs latest official RC non-force CAS + same-head CI/artifact bytes; #420 & #470 + Studio/Android/OWNER remain the release gates. A small private flag-off is rollback; no save-schema change.

This is an original, independent product feature implementation, **not** formal RC adoption.
