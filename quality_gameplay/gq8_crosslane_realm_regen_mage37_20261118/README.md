# GQ8 cross-lane 37: Realm + Regen + Mage, no new gameplay owner

## Motivation & difference from existing work
Existing [#780](https://github.com/kk051780/toy-wars-factory/pull/780) proves Realm #764 plus Regen #775 as a 36-script private composition. This **distinct** QA extends that exact author-constrained result by one **original Mage rescue runtime source #777**, without implementing a second Mage policy or rewriting the original Combat/Host. Earlier duplicate pure policy PR #776 was closed unmerged.

**Source author pins**: Realm #764 `c51de1ed4feb7a7500ada95d21282402053ef988`; Regen #775 `5b82f300e6dee08ea1ac20ccd1449db0cd73dbc3` (original policy #773); Mage #777 `2f4c1e43a7802929de3f633370b32791f7bf8d96`; QA bridge #780 `8f7984c1a9db2c016321d16d47a3ea8d1b5081df`. Official base V3 RC SHA `261b75d0a7093db5c13db3b95dad9a2911f78689` (refetch before promotion). Existing 31 untouched in OFF.

## Real SOURCE verification (not a Studio claim)

- Rehydrate genuine formal same-HEAD source 31 from official same-HEAD successful CI and artifact. Abort if branch HEAD moved.
- Run immutable original #764 composer to Realm34, original #775 composer to Regen33, original #780 independent exact-author QA to shared Realm+Regen36, and original #777 composer to Mage32.
- Combine just the **one** original Host (two `NaturalRegen.attach` and two `MageRevive.attach` hooks) and original Mage ModuleScript, yielding source count **37**. All 30 other canonical game scripts remain original exact; three Realm and two Regen extra sources plus Mage extra source are original author exact Git source content. **Regen attaches first** to set role MaxHP; Mage attaches second and observes actual current HP. No duplicate Combat, damage, Remote, Store, score or XP authority.
- Verify real cross-lane interface: downed status is set on both player and Humanoid by Mage, and Regen consults those signals before positive passive heal; no passive healing during 60s downed window. Mage clears both flags on recovery/death/round cleanup. This checks actual source contracts, **not** engine timing or matchmaking behavior.
- Source exact + 8 synthetic structural/mutant Python cases, 37 Native Luau compiles, real original Mage native VM normal+cooldown-mutant RED, real Rojo 37/37 Source/Class, OFF31 exact 31/31 Source/Class. No synthetic substitute for the canonical real31.
- Full fatal damage is **not** rescued by #777: its status only triggers nonlethal HP crossing <=20%. Magic healing remains existing +25 from #510, not new 30% active heal. These gaps remain YELLOW/functional blockers. The green source-composition result does not upgrade them.
- OWNER-specific prior Studio/FUN visual-feedback issues remain open; no fake mobile/ART/FUN claims.

## RC adoption contract

This branch is **independent source-gate rehearsal only**, never an RC writer. #220 sole authenticated writer must choose original authors after current latest SHA rebase, use one Host and feature flags / OFF reverting all 31 exact, pass same-head official Native/Rojo/rollback and nonforce expected-SHA CAS with readback and official Actions. All nonfatal YELLOW tracks get FB ID, owner, repro, rollback and trigger. Any duplicated HP authority/source drift/old CI SHA is RED. Keep main/Publish/paid changes prohibited. Studio 2client/Android15/FUN and owner acceptance remain NOT_TESTED/NO_GO. Progress is not 37 official scripts until the actual formal branch has 37 selected source and same-head CI.
