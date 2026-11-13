# EGG RAID RUMBLE 40-Luau + MUSOU V5 — independent QA: evolved scout PvE height and guard duration

**2026-11-13 JST | READ-ONLY SOURCE QA | NOT GAME-ADOPTED | NOT REAL ROBLOX STUDIO TEST**

Frozen original input #288 authored non-destructive 40+v5 Game (not official #220 RC):
- Immutable integration commit: `d514ac3642cb8eb385f3ec925fc0525ee256409e`
- Verified actual GitHub Actions artifact ID `14018281374`, ZIP 105908 bytes
- Real extracted unpublished Rojo Place `.rbxlx` SHA256: `01be347bda8aa48d4c0127fcc3360cc66a8e1e673fdd5ac52cf759e00c15bfdf`
- Parsed actual XML contains 40 original source scripts = 33 ModuleScript, 5 LocalScript, 2 Script; 1 original Game and 1 original Remote declaration
- Actual full Place Game.source GitBlob `d125bf45caa147666685955bb0a5a1230f334453`
- Actual MusouHorde.source GitBlob `8c147c801e7fa1ff362922d66c9a6fd432fc8b6e` = original #288 V5, including red 9-stud warning and fair KO/respawn
- Actual MusouCombatRules `R.SWEEP_MAX_VERTICAL=5`, and `canSweep` requires `abs(originY - mobCenterY) <=5`

## Two related source findings

### A. Guard protection time is not the indicated eight seconds

- One `local SCOUT_DURATION=5` and authenticated `token.duration~=SCOUT_DURATION` gate.
- `evolutionGuards[player]={untilAt=serverNow()+8,hits=3 or 5}` is set upon valid GUARD scout activation.
- One scout lifecycle `while t<SCOUT_DURATION` then `cleanupScout(player)`; cleanup deletes `evolutionGuards[player]=nil`.
- Therefore **at most approximately five seconds while the current scout remains**, even though guard envelope says eight seconds. Additional early death/round/leave can terminate earlier. This is a **source contract mismatch**, not a measured real-engine duration.

**Minimal gameplay-preserving choice**: specify `untilAt=serverNow()+SCOUT_DURATION`. That honestly represents the shield bound while keeping existing 5-second authentication, visible aura, 3/5 hit cap, no PvP shielding, no scope change. If owner explicitly prefers a *real eight-second* experience, separately change both original authenticated token and visible FX/cleanup semantics in its own author branch, then native+Studio QA; do not blindly change this single constant.

### B. Stage2+ assault scout can miss ordinary minions due to source origin height

- On every scout tick `anchor=currentRoot.Position+Vector3.new(0,4.5,0)+LookVector*3.5`, used for the floating **visual** body. The current AoE feeds **that visual anchor** to `horde:hit(anchor,...)`.
- Actual Horde source checks `Combat.canSweep(dist,vertical,facingDot,ray==nil)` with `R.SWEEP_MAX_VERTICAL=5`.
- Original minion body height3.3 -> center1.65 above GrassArena/CenterRoad floor. For a specific reasonable test case avatar-root center3.0 above the same floor, visual anchor is7.5 above floor -> vertical difference **5.85 >5**, so a minion meeting horizontal/LOS/facing conditions still fails the vertical hit test. Using model center is **not** a valid guarantee of combat feasibility.
- New candidate keeps scout visually flying but uses only `Vector3.new(anchor.X,currentRoot.Position.Y,anchor.Z)` as the PvE sweep origin. In that same test case, vertical difference **1.35 <=5**. This preserves real avatar height (cannot sweep targets on remote floors), facing, horizontal reach and server LOS validation. The source analysis is conditional; Roblox actual avatar rig heights must be verified.

## Isolated, TWO-HUNK source QA patch

`SCOUT_GUARD_HEIGHT_40V5_SOURCE_QA_CANDIDATE.patch` modifies **only** the 40+v5 Game.source copy; does not modify #288 owner source, #218 evolution owner, #220 official RC, main or any published game. It intentionally **does not** touch Score, HP, XP, ownership, DataStore, Remote, PowerRules, underlying Horde code, hit cooldown or PvP multipliers.

Local container verifications performed on the **actual extracted fixed SHA256 Rojo Place** (not a speculative draft):
- 20/20 source and bounded geometry `unittest` assertions PASS.
- Both source replacements have exactly one matched input context; round-trip reversing both hunk replacements yields byte-identical original Game.source.
- Frozen actual Game blob `d125bf45...`; patched candidate Game blob `ba94fbf4fb54a32cdc0c919b98664f1469513cf7`.
- **NOT DONE**: patched candidate Luau native compile or Rojo40 full rebuild, actual Roblox Studio play, Android, real success rate. Do not promote patch to a working game or count S1 score.

## Owner native and gameplay acceptance

1. Verify exact current original #288 author/Game source and #218 evolution owner state; if newer than pinned source, **STOP and rebase**.
2. Author accepts/adjusts duration contract (5s vs true8s) and height-origin fix. Add actual Luau tests for root-height relative to grounded minion body over grass/road; no hits through wall/high cliff; no client forged damage.
3. Rebuild original ONE Game/ONE Remote 40 source on isolated branch; native compile all40, Horde V5 50, Bind20, Combat26, Evolution98, Store atomic44, Power32, data persistence and source digest lock before any use.
4. Studio 2-client/Android owner test: Stage2 ASSAULT hits neutral minions in front but cannot hit through cover or a vertically distant floor; Stage2 GUARD blocks minion attacks for **displayed & actually active** duration then stops; 3/5 hit caps + egg/round/role/score/XP parity; first90 FUN measured.
5. #250 PRODUCT_SELECT -> #220 only official RC hunk integration, never full source wholesale. Official S1 last75, FUN_GATE NO_GO.

**Protected:** main, original source branches, merge, public Roblox publish, payments/extra spend, Windows PC/Codex, P0-A/B/C, CAS, existing automations unchanged.
