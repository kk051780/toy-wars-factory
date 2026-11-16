# GQ V3 AI navigation fault-recovery slice (source-only DRAFT)

## Observed original-source defect

Original #482 HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, file `EGGRUMBLE_BotPathRouter.luau`, blob `810155857fcd56bd93623e4deb5a4f7de530031b`. `maybeCompute()` increments the **global** navigation in-flight counter (max 2) before starting a spawned task. Inside the task, `CreatePath()` happens **outside** the pcall protecting `ComputeAsync()`. If creation throws, both the global permit decrement and actor-state unlock are skipped. Repeated faults can block navigation in **both** game modes.

This is a **source-level error-path gap**, not proof that Roblox currently throws here in a live match.

## Actual repair candidate

`patch_nav.py` verifies the exact pinned Git blob then source-selectively replaces **only one** CreatePath+ComputeAsync+cleanup block in a *generated private* copy. `CreatePath` and `ComputeAsync` share a protected call. Regardless of success, the global permit is returned; if no Path object was created, the same surviving actor state is unlocked and allowed to retry after the existing delay. Successfully created paths and all legacy navigation handling remain unchanged. No second AI engine, Game, Remote, Store, castle, egg or score authority.

**Flag OFF / rollback:** do not select the generated patch, instead use the original author Router byte-for-byte. **Flag ON:** source-select this one patched Router *only after original author #482/#484 ACK, #218 CLAIM_GRANTED, same-HEAD native Luau + Rojo, and #220 sole authenticated non-force CAS*. Never merge this entire branch or copy an old composite blindly.

## Eight-domain preservation contract

| Domain | Scope |
| --- | --- |
| CHARACTER | Original seven-role abilities untouched; bot identity/seat preserved |
| FIELD | Original three routes and solid obstacle checks untouched |
| BATTLE | Original hit, health, damage and KO authority untouched |
| CASTLE | Original castle/egg attack/deposit authority untouched |
| NEUTRAL | Original swarm/boss pacing and targets untouched |
| ITEM | Original item pickup/effect authority untouched |
| LOBBY | TEAM and BATTLE_ROYALE session namespace unchanged |
| BALANCE | Global max two concurrent nav computations preserved, permits can recover on exception |

## Acceptance / honesty

- [x] Isolated actual patcher and Python negative tests authored
- [ ] Same-HEAD GitHub Actions source test SUCCESS
- [ ] Native Luau fault-injection mock for CreatePath exception
- [ ] Original author ACK and claim grant
- [ ] NonDraft `P0D_PREP_READY_V1` with full source lock/rollback
- [ ] #220 official RC same-HEAD adoption, source lock and official ZIP + Place bytes
- [ ] Studio TEAM+BR AI movement and Android/FUN/OWNER acceptance

Canonical baseline official RC at scope discovery: `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34`; new V3 official adoption for this slice **0**. Old canonical CI does not test this patch.

No main, original #482/#484 code branch, official RC branch, Roblox publication, spending or local Windows operations are modified.
