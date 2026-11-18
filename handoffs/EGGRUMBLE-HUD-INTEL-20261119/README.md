# GQ8 HUD × Fog Intelligence (SOURCE-PREP, not official RC)

FEATURE_ID: GQ8_HUD_INTEL_FOG_20261119
OWNER_SPEC: https://github.com/kk051780/toy-wars-factory/issues/828
BASE_RC_OBSERVED: f77b4d4393d9e9b19b65566413432a7a9f13962b
TARGET: rc/p0d-s1-kids-rc01 (only #220 accredited non-force CAS writer)
STATE: ISOLATED_SOURCES; GAMEPLAY_WIRING_NOT_DONE; ANDROID/STUDIO/FUN NOT_TESTED

This source does not implement another Combat/Host/Remote/Store/HP authority.
`HudPresentationPolicy.luau` is purely visual and consumes certified server snapshots.
`MapVisibilityPolicy.luau` is server-only: fog, public castle/coarse-terrain positions,
seven role reveal gates, exact/sector precision and expiring pulses; no hidden coordinates
may be sent to clients. The function expects a server-verified view; server replication
and true LOS are future actual-game integration work.

## Wiring contract
1. Original Game/Host must verify initial castle spawn (TEAM or BR) and call
   `newExploration(castle.X,castle.Z)`. The revealed cells persist only for the
   current server match epoch. Call `reveal` only on server-validated motion.
2. A **single** map replication owner filters the actual world entities with
   `project(viewer, markers, serverNow)` before RemoteEvent dispatch. Never
   ship hidden real coordinates, even with client opacity 0. Enemy markers must
   carry server-confirmed LOS, team, stealth, realm layer and epoch.
3. Reuse already existing GUI + mobile controls (HUD and RealmBattleControls).
   `layout(w,h,hand)` outputs safe-area anchors and reserved center. Do not
   add a second attack button or new RemoteEvent; modify original GUI through
   a small source-select adapter during the authorized integration.
4. Only replicated genuine HP, buffs, element, armed/awakening and musou
   snapshots may drive `display()`. #823 owns invulnerability; #825 owns
   musou. Client never predicts a READY entitlement or extra remaining seconds.
5. Selection drawers use server-owned equipped loadouts only; selection does
   NOT purchase. Robux purchases/shop are disabled in this PR. A future
   opt-in commerce UI must preserve free core roles, invulnerability, musou,
   and map essential access, show explicit prices/confirmation, and avoid PvP
   power for sale. Children must not be pushed to paid random rewards.
6. Hover/expanded map should not cover action buttons during combat. Collapse
   on attack, hit, enemy proximity or thumb release; map access remains via
   miniature map. THREE realm layers, TEAM and BR spawn tests are required.

## Visual acceptance (targets, not measurements)
Baseline 851x393 safe area, landscape 1280x720, portrait 393x851,
left-handed mirroring: touch targets in bounds and non-overlapping. Fullscreen
combat safe corridor x27%-71% and y20%-79%. Small map top-left;
HP/3 debuff chips/attribute upper bar; right edge attacks and
contextual item/skill drawers; center remains clear for stylish VFX.
Native QA is not Studio gameplay acceptance. Before official release:
same-head native+Rojo/source-lock/OFF and measured Studio 2-client,
Android 15min including performance+heat, and real aesthetic comparison.

## Duplicate exclusion and rollback
Read #795 realm compact controls, #789 affinity guide, #823 invul, #825 musou,
#808 shop and #802 field. Do not reauthor them. Rollback: omit these isolated
source files from official selection and restore original Core36 byte-exact
selected code. No main writes, Roblox publish, Robux spending or protected
RC direct write.

## Handoff
Successor on this feature must take isolated source through actual GUI/map
server adapter with source-lock, CI, #220 authenticated fresh expected-SHA CAS
and same-HEAD artifact receipt. No author ACK necessary.
