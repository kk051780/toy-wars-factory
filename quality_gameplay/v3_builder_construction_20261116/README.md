# EGGRUMBLE V3 — GQ BUILDER WALL / BRIDGE, SOURCE candidate
**Status: SOURCE_WIP / SOFT_CLAIM_REQUEST / NOT_GRANTED / NOT IN OFFICIAL RC / NOT RELEASE-READY**

## Concept fidelity vs source
- Origin: #219 and #470 require all seven jobs' actual signature abilities. Existing author-owned #482 EGGRUMBLE_SevenRoleCombat.luau BUILDER-C draws a short-lived turret plus damage pulses but contains no physically traversable wall or bridge. This new slice covers only missing physical construction, not reimplementation of current skills.
- Original Game/7-role/castle/egg/AI/neutral/field/item/TEAM+BR lobby/ART/SCORE remain untouched at author HEAD fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9. The two server ModuleScripts add no replacement Game, Remote, Store, role selector or client input.
- #500 handles castle-defense turret/trap/SENSOR; #520 handles TEAM ridge/item. This module owns neither.
- A private Place that includes modules does NOT mean the BUILDER action is wired. Gameplay activation is UNTESTED.

## Original owner hookup contract; not done
Only after #482 author ACK and #218 hard claim may the original server-owned dispatcher invoke BuilderConstruction.place(session, player, "WALL", true) or place(...,"BRIDGE",true). The server selects kind; never trust client-supplied coordinates or introduce another Remote. BUILDER skill C must not silently lose existing turret pulses. The original owner must provide an explicit player choice and actual skill hook. The original session.closeRound should call BuilderConstruction.clear(session), with 9-second delayed cleanup as redundancy.

## 2026-11-17 independent server-owned Tool input implementation
- Added `Build.equip(session, player, serverEnabled)` to the same original Builder module; default OFF; no new Game, Remote, Score or duplicated source. It creates only two optional Roblox `Tool` instances, `EGGRUMBLE_SKILL_CONSTRUCT_WALL` and `EGGRUMBLE_SKILL_CONSTRUCT_BRIDGE`, *after* original seven-role tool equipment; does not replace the original Builder A/B/C attack/turret.
- Tool `Activated` callbacks invoke `Build.place` exclusively on the Roblox server. They refuse activation while unequipped, after character replacement, outside original live match membership, carrying eggs, after the match ends, or when the optional feature is OFF. Re-equip clears stale construction tools before recreating them.
- Native mock covers real Tool grant, activation, re-equip, old character and match-state fail-closed behavior. This creates the missing **input module/API**, but original Host source still must select the single `Build.equip` hook at both role grant and respawn, and must `Build.clear` on round closure. No premature RC/Studio claim.
- Original `BRIDGE` still requires true height/drop support; current flat demo grass returns `NO_GAP`. Reuse existing field-site author evidence in this PR's comments instead of creating a competing map.

## Current-match identity fence (source-only correction)
- Reuses original #531 Host `session.isCurrentHuman(player)` callback, already selected in the current official V3 companion Host, instead of creating another Game/Remote or trusting old `session.roster` alone.
- Builder placement now fails closed for same-mode stale sessions, missing Host membership callback, and callback errors; three new native runtime negative cases plus source contract assertions.
- The wall/bridge ability still requires a real server-owned skill hook and actual traversable map geometry. This correction is not formal RC adoption or Studio proof.

## Safety & limits
- Default feature OFF; human roster, match mode, alive castle, real Player+Character, role, no carried egg and active match checks.
- Uses ground only from the current match arena, bounds and support checks, castle/pickup/goal exclusions, occupied obstacle detection, and full rollback.
- Hero cap 2, match cap 12, WALL cooldown 13s, BRIDGE cooldown 17s, auto removal after 9s.
- Actual bridge gap traversal is UNPROVEN: current demo TacticalBattlefield is a largely continuous grass slab.

## Private native/source-exact CI
make_private_project.py selects precisely the original 21 scripts plus 2 optional server modules. Pinned Luau compile, native pure-policy negatives, pinned Rojo 7.7.1 PRIVATE Studio Place and 23 source+class exact XML audit. The private Place or artifact ZIP byte count is never official RC capacity. Even source PASS is not actual Roblox Studio gameplay verification.

## Balanced 8-domain intake
CHARACTER=BUILDER construction, FIELD=valid placement, BATTLE=no new damage, CASTLE=gate clearance, NEUTRAL=no horde/KO authority change, ITEM=no egg/collectible blockage, LOBBY=TEAM/BR real session and cleanup, BALANCE=bounded duration/rate/count; all original author systems left intact.

## Official RC adoption checklist
1. #218 hard claim and #482 author ACK; reconcile current original owner HEAD and reject overlapping Game/Combat authority.
2. Exact native Luau and private Rojo source proof, compare against current 8-domain host.
3. Only #220 authenticated sole writer selects the original-author hook plus optional modules for current rc/p0d-s1-kids-rc01 using expected-SHA nonforce CAS. Record new official HEAD, same HEAD native/Rojo/SourceLock, ZIP/Place bytes and rollback, ACK.
4. Studio 1+15 AI/2 clients TEAM+BR real bridge gap and wall occlusion, low Android 15min and #420 ART/FUN, #470 product/OWNER acceptance. Absent proof means PRODUCT_NO_GO.

Rollback: flag OFF, remove the two mapped optional modules and original-author hook, preserve original BUILDER turret, run clear(session); no persistent schema changes. No main write, PR merge, Publish, payment or Windows operations.

## 2026-11-16 independent follow-up — actual bridge gap safety
- Flat continuous TacticalBattlefield is now rejected as `NO_GAP`; a temporary BRIDGE needs existing real support at 7 and 24 studs and a central gap or a riverbed at least 4 studs below the lower bank. This is a player-visible behavior fix, not additional author-owned map creation.
- Real TEAM/BR generated demo has an unbroken grass slab, so this honest gate will reject bridges across that slab until original field author supplies a physically real watercourse or canyon. A blue visual river marking alone is not evidence. Do NOT claim working field traversal on the existing flat demo. No Game/MapBuilder changes in this PR.
- Native runtime mock tests: intact floor rejected, missing midspan accepted, lowered riverbed accepted; other real-CI source/field/egg/castle/neutral/role/round invariants unchanged.
- #482 author needs to ACK skill-input mapping and a real crossing site in existing authored battlefield. #220 sole writer needs signed source-lock/CAS and official exact-byte receipt. Without them the formal integration gate stays NO_GO.

## 2026-11-16 lifecycle hardening — 0.25s safety fallback
- Adds one 0.25-second callback chain *per match only while live temporary constructs exist*. After a phase != ACTIVE, nonnil winner, or destroyed arena, it invokes its own idempotent clear(session); no second Game/Remote or general background monitoring.
- Preserves the 9-second individual timeout and owner-issued clear(session). Explicit author closeRound hook remains mandatory for formal integration; fallback is defense in depth.
- Native source-exact mock covers terminal phase, winner, destroyed folder, duplicate/stale callback, plus existing two game modes/egg/NPC/hazard and 23-script Rojo audit.
- No original-author #482 Lua scripts altered; official RC adoption still zero until #218 hard claim plus #220 original author authorized source selection and real Studio/Android tests.
