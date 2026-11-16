# EGGRUMBLE V3 GQ — egg-carrying Ninja stealth / AI fairness fix

STATUS: A-PREP SOURCE candidate only. Unpublished; no game RC integration or Studio result.

## Verified root cause in original PR #482
In the original SevenRoleCombat, NINJA B/WIND checks `owner.heldEggs==0`
only when the ability is cast, then grants `EGGRUMBLE_StealthUntil=now+3`.
The original BotActors tests stealth before allowing an AI sword strike, but
did not ask the authoritative `session.rules.castles[userId].heldEggs`.
A player could trigger WIND with zero eggs, collect an egg during the following
three seconds, and remain invisible to AI attacks while carrying the objective.

## Minimal gameplay change
- Original author BotActors stays the only moving bot implementation.
- One pure `EGGRUMBLE_CarrierBotTargeting` module controls whether the
  existing bot strike checks may target a player.
- **Any authoritative carried egg overrides stealth instantly**, without
  timers, duplicate spawn loops, RemoteEvents, new score or HUD.
- Non-carriers keep the original 3-second WIND stealth; original bot TEAM
  enemy filter, BR behavior, health, distance, solid ray LOS, and damage cooldown stay untouched.
- Source host `EGGRUMBLE_V3_STUDIO.project.json` maps one extra module.
- This does not cancel class abilities, modify inventory, or duplicate #489's
  field-item DASH/SHIELD carrier fix. Same rule applies to TEAM and BR.

## Rollback
Remove module mapping, revert one require and one predicate in BotActors,
delete this pure module. Original #482 source is the parent commit.

## Acceptance before #220 RC adoption
1. Native pure Luau behavior and source contracts pass at the same pinned HEAD.
2. #482 author reviews selective change; #484 original AI pathfinder + #485
   art + #487 scoring remain source-exact. New module is not a second AI service.
3. #220 sole authenticated CAS writer source-selectively combines the fix
   into latest official RC, with native compile, Rojo source-exact,
   fixed SHA, source-lock, same-HEAD CI, official ZIP byte/KiB and rollback ACK.
4. Real Studio tests: TEAM and BR, NINJA WIND then egg pickup within 3s,
   nearby hostile AI must hit if range/LOS/cooldown permit; empty-handed
   NINJA must remain stealthed; castle death/round change cannot keep an
   old buff. Verify mobile/performance and OWNER FUN separately.

Unverified: Studio 2-client, Android 15min, device FPS/thermal,
art aesthetics, FUN and OWNER acceptance. Main, official RC, publish,
merge, expenses and PC control remain untouched.
