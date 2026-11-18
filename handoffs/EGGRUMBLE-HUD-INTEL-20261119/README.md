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

## Update: Actual Core36 → Real40 runtime source integration candidate (2026-11-19)

Four isolated live runtime sources are now available in addition to the two pure policy modules:
- `EGGRUMBLE_HudIntelRuntime.client.luau`: touch-safe 3-skill selector and existing server-owned Tool activation, HP/status chips and compact filtered fog minimap. No second skill or damage remote. Base Roblox movement/jump stays native; dodge is not fabricated. MUSOU/INVUL shows unavailable until exact server Tool and server Ready attribute exist.
- `EGGRUMBLE_MapIntelBridge.server.luau`: one server-created *send-only* `EGGRUMBLE_MapIntelUpdate_V1` RemoteEvent, `FireClient` after server-only fog and LOS projection, zero `OnServerEvent`. Reads actual `TEAM_Arena` / `BATTLE_ROYALE_Arena` and `Castle_<id>/StandardFoundation` positions, starts fog only after server-character arrival within 150 studs of own castle. No additional Combat/Game/Store/Score/HP writer.
- `compose_real40.py`: extracts the genuine exact 36 source files from the existing formal private Core36 `.rbxlx` artifact and adds exactly those two runtime scripts and two pure policy modules into ON40. OFF36 preserves all original 36 bytes; original source remains unchanged.
- `.github/workflows/p0d-gq8-hud-real40.yml`: exact-current-HEAD verification, Native compile all ON40/OFF36, pinned Rojo Source/Class, upload actual candidate private Place and receipt. Original Core36 artifact run 44232589275 must be available and current formal RC unchanged.

The map sender is a **separate display-only one-way RemoteEvent** (not a new command/damage/score authority), because selectively revealing secret player positions requires targeted server-to-client replication. No client search or information request is accepted. TEAM enemy/ally affiliation is now inferred **server-side only** from the original roster-authored `StandardFoundation.Color` RED/BLUE identity (same immutable actual Core36 castle author; no client team claims). Unknown/recolored castles fail closed: no TEAM player pins. The role scanner now uses original neutral `EGGRUMBLE_Neutral` actors, siege gates and HEAL/DASH/SHIELD pickups, plus explored field eggs. Seven role-specific passive 8-second recon windows begin at 20 seconds and repeat every 65 seconds by server time. These are initial balancing figures, not Studio-verified.

**Known limits:** HUD uses existing A/B/C combat Tools only; a dedicated zero-cooldown normal attack, a dodge mechanic, actual #823/#825 server awakening Tools, and optional player-triggered active scouting abilities still require original-author source integration. They are NOT declared complete. This source is a private source-selected candidate, not official RC, Studio-tested or shop-enabled. Studio/Android/UI art quality remains NOT_TESTED and source-only native PASS never implies playability.


## Latest successor correction: exact Real55 source → Real59 UI integration candidate

**Supersedes the historical Core36/Real40 instructions and statements above.**
Current official private V3 companion at the verified source lock is Real55 at
`a6020867fac80fa3b2ca47478625873fc6f3678e`. Selection is 55 authentic
sources unchanged plus exactly four HUD/Fog modules; the Real59 source profile
and adoption gate are in `rc_fastlane/EGGRUMBLE_V3_REAL59.json` and the
dedicated `p0d-rc-eggrumble-v3-real59.yml` workflow. Original Host/Combat/Swarm
and all original 55 routes are byte-preserved. This is still **not** formal RC
until #220 accredited writer performs non-force CAS and the same *new official
HEAD* checks pass.

**Critical genuine Tool fixes**, source-contract validated against the physical
Real55 selected .rbxlx itself:
- Server-owned offensive Tool: `EGGRUMBLE_MUSOU_AWAKEN`, and actual Player
  attributes `EGGRUMBLE_MusouPhase` and `EGGRUMBLE_MusouReadyIn`.
  The HUD never trusts obsolete non-existent `EGGRUMBLE_MusouReady`.
  Phases MUSOU/RUSH/KAKUHEN display as 無双中/連チャン/確変中 respectively.
  The charge indicator uses only last genuinely replicated ready-in snapshot.
- Server-owned reactive defensive Tool: `迎撃覚醒` (not an English
  `EGGRUMBLE_INVUL_` name). The real `EGGRUMBLE_InvulRuntime` server ModuleScript
  is read **without modifications** by the map sender and the read-only
  `currentPolicySnapshot(p)` phase/remaining is transmitted to only that
  player. Thus ARMED and AWAKENED visually distinguish and stale 3s arm states
  expire on server without inventing an extra HP damage authority.
- Both client buttons invoke only existing server Tool.Activated callbacks.
  No second action Remote and no predicted activation permission.

**Mobile interaction update:** separate A-skill fast attack and selected B/C
special-use button occupying the reserved (currently unsupported) DODGE touch
anchor. Dropdown A/B/C remains available. An independent fast normal-attack
Tool does not exist in this immutable Real55 lineage; therefore the quick attack
is visibly labeled `技A`, not falsely called cooldown-free basic attack.
Real dodge remains hidden. World HEAL/DASH/SHIELD remain original prompt-based
pickups: no fabricated inventory or purchase, `道具 0` when no owned
`EGGRUMBLE_ITEM_` Tool. Further authentic basic attack/dodge/item inventory
needs original authoritative Combat/Item owner source integration and a later
privacy/source-lock review.

**Mobile visual layout gate:** the current policy computes HP/status/charge
`layout.chrome` adjacent to the map instead of the fixed 19%-of-width text
box. Native verified shape cases cover 851x393, 1280x720, 393x851 and 320x260,
both handedness modes; center remains reserved for VFX. This is a static safety
test, **not** Studio screenshots or Android FPS evidence.

**Unmet acceptance:** Studio 2-client / Android 15-minute FPS / action feel /
artistic comparison / final user acceptance all remain NOT_TESTED. Do not
interpret Native/Rojo source/class PASS as actual device combat or real purchase.
