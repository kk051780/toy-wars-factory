# EGGRUMBLE V3 / independent quality writer — post-win egg drop fence

**Feature ID:** `GQ-V3-EGG-TERMINAL-FREEZE-001`  
**Scope:** pure `EGGRUMBLE_CastleMatchRules.onCarrierEliminated` ONLY (one existing function; no new Game/Remote/HUD/monetization).  
**Original author:** PR #482 at immutable `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`.  
**Original Git blob:** `27da5ca1e9e6d9a7afe0674030e387f094ee7492`.  
**Patched Git blob:** `ed87d70e7df94279af737871e8e439b9fc108d4f`.  
**Official RC baseline (read-only observed):** `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34`.  
**Non-overlap:** #508 controls neutral KO attribution; this slice controls only late player-death egg drop AFTER server winner/phase ends. #489 owns item fairness; #502 owns carrier AI; #482 owns original hero/egg rules; #484 owns multi-author compositor; #485 original ART; #487 SCORE; #220 sole authorized RC integration. No other files in those owners are touched.

## Repro and actual correction

1. TEAM: surviving RED hero steals a BLUE egg, BLUE castle falls, server transitions to FINISHED with RED winner.
2. A delayed Humanoid.Died/callback invokes `onCarrierEliminated` for the still-carried egg.
3. Original function silently added field egg/token/event AFTER FINISHED, changing the settled world and the winner's egg stock. No active-round gate existed in this function (other egg APIs already had it).
4. Fixed function returns `0,{}` when phase is not ACTIVE or winner already set, without changing held egg, field supply, eggSerial, field tokens, event ledger or result. In ACTIVE, physical death releases one valid collectible token exactly once.
5. Repeat also for BR final castle and a pre-start LOBBY; negative mutant removes this single gate and MUST fail the same native assertion.

## Gates (no fake success)

- G0 author fixed source/exact single-function diff: GitHub source-lock validation in dedicated workflow.
- G1 actual native Luau execution of unchanged rules plus amended single-function fence: TEAM and BR genuine castle-win paths, egg conservation, field token uniqueness, event freeze, active death idempotency.
- G2 mutant removed fence MUST fail same VM tests. This catches superficial source-only checks.
- G3 source-owner review / #484 latest-head selective 26-source composition; newly patched original file must replace only its corresponding mapped module, with source-exact Rojo+Native & same-HEAD evidence.
- G4 sole #220 authenticated non-force CAS official RC write, same HEAD full Native/Rojo, ZIP & Place actual bytes, feature adoption ACK and rollback.
- G5 real Studio solo 1+15 and TEAM/BR 2 clients race: last castle fall + carrier death; Android15min + #420 art & 3minute kid FUN, OWNER acceptance.

**Current:** G0–G2 are pending GitHub Actions result; G3–G5 NOT DONE. SOURCE candidate only; official RC adoption for this feature 0%, Studio/Android/FUN/OWNER NO_GO. No merge/main/Publish/payment/PC操作. Nonfatal YELLOW may be logged but never present source-only as game acceptance.

**Safe rollback:** revert only the inserted phase/winner check in the isolated author-diff candidate or omit this candidate from #484/#220 intake; retain original author source exactly. For official RC, #220 alone controls a source-locked revert with audited CAS and same-HEAD tests. **No direct official RC write from this branch.**
