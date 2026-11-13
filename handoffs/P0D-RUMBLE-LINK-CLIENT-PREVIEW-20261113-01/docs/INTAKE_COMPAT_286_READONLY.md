# RUMBLE LINK — #286 original Game source compatibility audit (read-only)

Checked: 2026-11-13 JST. This is product/game integration analysis, **not official RC adoption**.

## Inputs: pinned and distinguished
- Original #286 experiment: commit `a0331e2e452f4e8e6530d32562ba5ff657b011d9`; Game.server exact Git blob `28a51605efcee572029154f978761622959df587`; 1583 lines.
- Source origin: #286 (2 vote-selected modes, real physical scout, owned/equip, XP/focus/mastery, DEV-only atomic profile). The single original server Game and `TrapRaidersS1Remote` are preserved by their owner.
- The last separately audited official RC source is `1263a03701211a652b99b91d2339575dc8104eff` (different Game). **#220 alone** confirms current official RC HEAD, patches and source lock; never transplant the experimental Game wholesale.
- Our RUMBLE LINK pure display module: `6729608887ee1ea4960d98c67ab0e032925433c7`. A synthetic Studio-only preview is not an in-game cooperation event.

## Direct source evidence (exact Git blob above, line numbers of that blob)
1. `snapshotFor` line 586–635 returns `kind="SNAPSHOT"`, `serial=match.serial`, `updateId=snapshotUpdateId`, `team=getTeamName(player)`, and `scoutActive`; it has **no real co-op scene event**. `snapshotUpdateId` is a globally incremented view ordinal (line 559–562), **not** a per-round cooperation receipt.
2. `broadcast` lines 637–640 uses **existing** `remote:FireClient(p,snapshotFor(p))`; creating a second Remote or scoring ledger is prohibited.
3. `visibleCarrierTarget` lines 776–795 proves server alive enemy carrier + team + <=90 distance + unobstructed ray. `spawnActualScout` lines 797–884 consumes that proof, visually highlights target; **it does not emit RUMBLE_LINK's verified four scene cues**.
4. `spawnActualScout` currently requires `RunService:IsStudio()` at lines 797–803; it is private testing functionality, not a publicly playable released skill.
5. RUMBLE LINK client requires `packet.roundSerial` and same `roundId`. Valid canonical **candidate mapping only if chosen**: `roundSerial=match.serial`, `roundId="S1_"..tostring(match.serial)`, `team=getTeamName(receiver)`, `seq` monotonic per event receiver, `expiresAt=serverNow()+2` (time domain must be validated with client `workspace:GetServerTimeNow()`). Never synthesize a fake success from `SNAPSHOT.scoutActive` or `SNAPSHOT.carrying`.
6. Do not treat current `BOSS_VISUAL` lines 642–680 or `SNAPSHOT.updateId` as a cooperation proof: they have different authority semantics.

## One real event first, not four unverified events
**Only a #250-selected, #220-owned optional first trial:** on real server-side `visibleCarrierTarget` truth *after authenticated owned/equipped scout activation*, existing Game may emit a bounded `kind="TEAMWORK_CUE"` S1-server->client UI-only DTO for `SCOUT_ASSIST` on the **same** Remote. At most one per verified carrier discovery per receiver/round; no extra target coordinate leakage, no unbounded server spam, no points, XP, damage, saves, entitlements or new ability. Must be disabled unless selected and independent-QA accepted. The present pure display module cannot itself prove server authentication.

Other scenes:
- `SEA_ESCORT`: requires authoritative SEA zone, carrier + allied escort proof, currently not in `SNAPSHOT`; HOLD.
- `TRAP_GUARD`: must prove actual teammate protection using canonical trap/damage source, not just trap cooldown; HOLD.
- `CASTLE_RECAPTURE`: must prove canonical original egg recovery + defender contribution, not a score delta alone; HOLD.

## Adoption gate (new #250 precedence and max 2 WIP)
Recommendation: `S1_PLUS` / `DEFER_CORE` until #250 selects and #220 locks one canonical current Game source. Do **not** introduce RUMBLE LINK as a new first-release blocker while original FUN gate is NO_GO and original horde/elite/capture action-first S1_FUN is unintegrated. A single scene can be a low-risk optional enhancement only when measured useful.

Reversible test: H0 unchanged experimental game vs H1 same source lock plus one server-authenticated cue; first90, complete round, repeat, genuine two-client + Android, data/bandwidth cost, false-positive 0, egg/score/XP/owned/equip/DataStore equivalence, no client-sent success. Explicitly tag round and server time for stale replay/handoff. Exact SHA, run log and frame/recorded source must be supplied before #220 can promote into official RC.

## Verification status
- In-chat manually reconstructed **byte-for-byte matching original 4 Git blob source files** from fixed RUMBLE LINK commit: Rule `0eb806b1...`, test file `e8795953...`, preview `7f6ada41...`, Rojo project `1e543067...`. Git blob identities recomputed locally.
- Executed `python -m unittest discover -s tests -p test_contract.py -v`: **22/22 PASS** on those exact bytes in local container.
- Exact pinned GitHub Actions run / upstream native Luau: **NOT VERIFIED** (commit combined statuses empty; PR-run filter returns none); actual Roblox Studio, 2-client, Android, human FUN: **NOT TESTED**.
- Source compatibility observations are read-only. No original server Game / GUI / Remote / match or profile mutation.

Protected: main/merge/Roblox publication/paid spend/owner PC/CodeX/P0-A/B/C/CAS/five automations unchanged.
