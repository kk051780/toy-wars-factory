# EGGRUMBLE V3 — Round-local attribute cleanup / GQ isolated candidate

**Original author**: PR #482 exact commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9` (21 original Luau scripts unchanged).  
**Scope**: One server-owned *round attribute* fence only; no Game/HUD/role skill/map/castle/egg/bot/neutral/item/score/Remote/DataStore changes. Existing #484 AI, #485 ART, #487 SCORE, #489 item and other GQ claims are untouched.

## Root-cause check
Original `EGGRUMBLE_SwarmCombat.credit` writes player attributes `EGGRUMBLE_Combo` and `EGGRUMBLE_BestCombo`; original StoneGiant callback adds `EGGRUMBLE_BossDefeats`. Original `EGGRUMBLE_RoundReplay.resetHuman` restores HP movement state and resets `NeutralKOs`, `BattleLevel`, `SlashEvolution`, but omits all three attributes. Those presentation/round-local stats can therefore remain visible in the lobby and next TEAM/BR match even though server score and neutral kills are reset. This is source-derived, not yet a real Studio repro.

## Fix
New `EGGRUMBLE_RoundAttributeFence.luau`: independent `TEAM/BATTLE_ROYALE → nil` server-owned queued-mode transition predicate and only three stat resets to 0. New `EGGRUMBLE_RoundAttributeFence.server.luau`: Studio-only Player attribute transition hook and PlayerRemoving listener cleanup. No new authority, leaderstats, rewards, data persistence or remotes. If queued-mode transitions are suppressed by engine scheduling, this additive observer does not guarantee the cleanup; test in Studio and ask the #482 owner for a one-line direct reset hook if needed.

## Rollback and integration
Private project `EGGRUMBLE_V3_ROUND_FENCE.project.json` adds exactly 2 sources to original 21 (23 total); exclude the module + server script to switch OFF without touching 21 original scripts. Only #220 genuine authenticated non-force CAS writer may selectively adopt after author/CLAIM review, latest official HEAD lock, native+Rojo same-HEAD success and replay QA. This DRAFT neither merges to official RC nor publishes Roblox, charges, or touches Windows.
Studio 2-client TEAM/BR, Android 15min, old/new visuals, kid FUN and OWNER acceptance: **NOT_TESTED / NO_GO**.

## Source contract & target engine test
Python source negatives and original 21 mapping byte invariance; native Luau executable test on actual module; genuine Rojo private 23/23 exact source. Studio should verify: 1) TEAM bot combo+boss -> win -> 10s -> lobby (three attrs zero), 2) BR repeated, 3) queue switch TEAM/BR while waiting does not erase live match reward, 4) replay after physical death, 5) both arena sessions simultaneous, 6) 2-client and Android no HUD conflicts. Until those real observations arrive, not READY for official intake.
