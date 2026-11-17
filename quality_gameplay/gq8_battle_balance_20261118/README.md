# BATTLE-BALANCE-QA (#765) — independent native Realm source gate

- **Owner scope:** QA only; no Game/Combat/Host/Swarm/HP/Store/Score writes and no duplicated Realm runtime.
- **Actual input:** PR #764 `EGGRUMBLE_RealmBattleCore.server.luau` from the checked-out Git HEAD.
- **Native positive cases:** eleven direct Luau calls into the **unaltered extracted** `damageMultiplier` and `damageRealm` functions: underwater FIRE, LIGHTNING, neutral damage, surface-vs-sea, rounding, negative damage, missing/zero HP, missing Parent, fighter crash/removal, post-destroy replay, and default gun hit.
- **Native negative mutation:** change only FIRE underwater coefficient from .15 to .95 in an isolated test copy; genuine Luau must fail at `RED_FIRE_UNDERWATER_MULTIPLIER`. This is not shipped game code.
- **Static authority:** server limits, valid PilotSeat, queued mode, TEAM PvP hold, per-weapon cooldowns, warning interval, and non-Studio runtime.
- **Owner #765 *specification-only* QA:** all 64 8x8 affinities, six standard elements in a closed counter-cycle, DIVINE/CURSE mutual checking, seven proposed starting HP values, two-hit normal/strong survival, regen rate, mage heal/revive proposal.
- **Critical admission truth:** the 64 affinity policy, 7-role higher HP, global damage timestamps, passive regen, mage revive and weapon/HUD visual effects are **NOT integrated or dynamically tested** by this QA. The unit oracle merely defines a gate to apply when each separate gameplay owner's source becomes available. No placeholder PASS may be presented as functioning gameplay.
- **Base:** PR #764 fixed source parent `9e020f284d83f333b695041b17ab29c94281a0db`; base is a feature candidate and **not the official RC**. Rebase onto exact current #220 RC after #764 adoption, ensure same-head 34/31 Native+Rojo and inverse31, retest the native source and mutant.
- **Studio/Android/2-client/low-FPS/FUN:** NOT_TESTED. **Release:** NO_GO.
- **Rollback:** delete QA files/workflow only; production scripts unchanged.
- **RED:** missing Realm source, native compilation failure, actual function drift, mutant unexpectedly green, canonical 31/source-lock mismatch when promoted.
- **YELLOW:** absent gameplay linkage for the independent #765 implementation slices, owner #764 still unmerged, human/fortress/egg damage not bound to core34.

Handoff: #765 BATTLE-BALANCE-QA role 9; #220 sole authenticated non-force CAS RC integrator. Do not merge to main, publish, or claim 8-domain gameplay completion from standalone tests.
