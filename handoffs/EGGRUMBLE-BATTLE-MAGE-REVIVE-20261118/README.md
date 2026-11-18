# #765 lane8 — BATTLE-MAGE-REVIVE server-only PREP source

- **Feature ID:** BATTLE-MAGE-REVIVE-20261118
- **Exclusive claim:** https://github.com/kk051780/toy-wars-factory/issues/765#issuecomment-6968027134
- **Frozen official base RC:** `261b75d0a7093db5c13db3b95dad9a2911f78689`
- **Scope:** one new pure `MageRevivePolicy.luau`, one source-derived native Luau positive/negative+replay mutant test generator, one workflow; NO original Game/Host/Combat/Swarm/Remote/Store/Score/XP or realm source changes.
- **Existing verified authority:** canonical #530/#510 Combat already implements BR self/TEAM allied +25 HP within 22 studs, server human-membership and wall LOS. It must NOT be duplicated. Existing #773/#775 passive HP regeneration and original 31 remain unchanged.

## Rules supplied, not yet wired to runtime

- A live Mage in an active current TEAM match may immediately heal a living teammate for up to 30% target max HP after 18s cooldown. No healing downed/eliminated targets, no BR teammate revival.
- Downed ally may be revived only within 60s of downing, by 3s uninterrupted channel with 40s cooldown, ending at ~35% of target max HP. Required server-only truth: authenticated caster/target, TEAM, current session+round IDs, both current avatar IDs, LOS, distance, alive mage, downed target, actual server clock, no hit/interruption, no elimination. A token is consumed synchronously before returning restore amount. A new attempt must be denied by the caller while one active.
- The pure policy **never** edits Humanoid/health or generates a Remote. Existing game Host/Combat must be sole HP/downed/round authority and must supply authenticated context (never trust client-supplied flags/token). Server authority MUST atomically record lastHealAt/lastReviveAt and mark downed false within existing transitions. If the canonical game lacks a true downed state, this feature is **BLOCKED_GAMEPLAY** until #220 connects the existing real authority; never fake a resurrection by spawning a second HP controller.
- Native test covers healing cap/CD and seven role HP targets, 3s/40s/60s bounds, cancellation, double completion replay, stale avatar/round/session, TEAM-vs-BR, line-of-sight, mage-only, caster damage, eliminated target, and deliberate replay-check removal mutant failure.

## Promotion contract

Stage: `PREP_SOURCE_CANDIDATE`; not connected to current gameplay. Integration request to the **sole authenticated #220 RC writer** requires pinned candidate HEAD, green native Luau good+mutant and Native/Rojo exact real31->32 build, single health authority review, reversible OFF retaining the exact original31 sources, then nonforce expected-SHA CAS. The integration must adapt existing original MAGE +25 behavior in-place rather than layering an independent heal; no second MAGE heal may coexist. No main push, non-authorized merge, publish, purchase, or Studio/Android/FUN claims.

Studio 2client: NOT_TESTED; Android15min: NOT_TESTED; ART/FUN/OWNER: NO_GO. `RC_INTEGRATED=NO` until verified current formal head after authenticated #220 write.
