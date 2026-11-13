# P0D #288 V4 → earned-power H1: integration readiness static audit

**2026-11-13 JST. QA-only.** This supersedes the earlier v3-only source-blocker note for choosing the **latest safe source baseline**; previous original findings remain historically valid.

## Exact compared source identities

| Component | #288 v2 — OLD | #288 v4 — FIXED SOURCE | Earned-power 39 — OLD INHERITED |
|---|---|---|---|
| immutable commit | `55ad13b45907a5a3e9deae7196a7c202a0672c0c` | `376e943673dc089a5381e0d46570b92185a5d32a` | `cb2540dc4a3e5b819c0e3598d4af5e2b6dca76d3` |
| Horde module Git Blob | `c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553` | `7edfda9e5a1d4ac8ae47d66ea7cf908eb8e4af6e` | **`c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553`** |
| one original Game.server Git Blob | `f8c45bcf109dc3229c0459e4fb9fa224ab6c38a4` | `fba78a510ba7f9044cd7ce7a6d40b69ee59c1a03` | `ac995ea5e960942a557ee0a2a4116bff8ceadfe8` |
| server earns combat power | No | No | Yes, via original #285 Power policy |
| actual original Studio2client/Android QA | **NOT_TESTED** | **NOT_TESTED** | **NOT_TESTED** |
| official sole #220 RC adopted | No | No | No |

## Three separate gameplay regressions if power branch is promoted as-is

1. **Elite stale pending attack** — v2/power Horde `Horde:hit` on `m.hp<=0` stores death delay but not `tellUntil=0,target=nil`; respawn restores HP/location not queued tell. V4 (as V3) cancels pending windup at kill and at respawn plus attack grace; test must validate 1.5s warning after 8s respawn.
2. **Hovering NPCs / misleading melee range** — v2/power Horde uses `local base=Vector3.new(x,if elite then 3.4 else 2.7,z)`. The actual original map ground top is grass -1, road -.70. V4 derives floor top from `world:FindFirstChild("GrassArena")` and `world:FindFirstChild("CenterRoad")`, then `feetY+halfBody` at each spawn. This is a source-level improvement; the actual Studio rendered result is unobserved.
3. **Single swing potentially damages a minion and a castle** — v2 and earned-power `applyAttack` call `horde:hit` and subsequently fall through to original castle HP damage if no PvP target found. V4 stores `mobHits=touched` and does `if mobHits>0 then return end` *before* `match.hp[enemy] =...`. The power bridge lacks that gate. Any proposed replacement must preserve V4 priority alongside legitimate #285 PvE and PvP multipliers. This is a source-control-flow risk, not a measured exploit in real Studio.

## Root reason: source-locked inheritance

Power bridge `tools/assemble.py` at fixed GitBlob `04f89fa61f773ecd3342c969a9e354ed6703170e` copies the 38-source original V2 parent and overlays only Game/HUD, plus new PowerFantasyRules. Its `parent_game_sha` and Game SHA checks still pin the old parent, and it never overrides Horde. **Passing 39/39 native compile and original Power32/32 confirms source correctness in its own scope, not V4 safety.**

## Safe minimum upgrade acceptance (for the separate earned-power author, not this independent QA author)

- Select exact immutable **#288 V4** full38 source SHA (or a newer verified original #288 commit), not V2; preserve *all* 3 fixes in Horde + original Game.server (and V3 hit/KO HUD).
- Reapply power feature Game/HUD changes at **function/hunk** level against latest corrected V4; keep single Game, single Remote, single authoritative score, egg, XP, owned/equip and atomic save.
- Explicitly retain `earnedDamageMultiplier(player,"MINION")` and `earnedDamageMultiplier(player,"PLAYER")`, original #285 Lv1 baseline and PvE/PvP cap, one per-round 2s tell/8s awakening. Do not multiply castle core damage or grant XP/charge from mob kills.
- Update `parent_game_sha`, source blob guards, all inherited module hashes; **assert the output** `src/server/MusouHorde.luau` is the current V4 blob, not a manually invented independent replacement. Require V4 ground map parts to be real and present.
- Check the **actual assembled** `Game.server.luau` for the V4 mob-to-castle guard, not only the pure policy or README.
- Repeat original #286 XP/save/score/scout native tests, #288 v4 Horde35 + Bind20 + Combat26, Power32, full source39/39 Luau/Rojo, negative protection tests and independent QA.
- Only after #250 explicit PRODUCT_SELECT and #220 sole official RC merge may OWNER run real **private** Roblox Studio two-client/Android first60-90 seconds/round/retention/fairness/latency/FPS H0-vs-H1 FUN. Public publish and payments remain disabled.

## Reproducible source check

New own independent tool: `tools/audit_v4_inheritance.mjs` plus `tests/test_v4_inheritance.mjs`, 31 source tests authored. Dedicated source-only Actions workflow `.github/workflows/p0d-horde-independent-v4-ci.yml` with exact pinned SHA refs (v2, v3, v4, power) and Git blob locks. GH completed run not verified; do not call it CI PASS until run/job log is fetched. 

**Verified this turn**: 33/33 distinct V8 source-check assertions executed against the 7 actual GitHub fixed-ref files (v2 Horde/Game, v4 Horde/Game, power Horde/Game/builder), including five mutated cases, all PASS. These establish observed text/source invariants and provenance, **not full JS Node test, native Luau or Roblox engine execution.**

Overall sole #220 official S1 historical 75%, FUN_GATE_NO_GO and source lock unchanged. Independent QA should not modify author code, protected RC/main, merge, publish, paid, OWNER PC/Codex, CAS, P0-A/B/C or five automations.
