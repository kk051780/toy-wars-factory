# GQ804 siege protection + guardian call policy, source-only
Owner #804: https://github.com/kk051780/toy-wars-factory/issues/804
Shop/collection #805: https://github.com/kk051780/toy-wars-factory/issues/805

Implementation candidate `EGGRUMBLE_CastleSiegeGuardianPolicy.luau`:
- 180 gate HP external to original 1000 CastleHP; no core damage without a gate breach.
- Trusted original Host may request core damage permit only with 2 coordinated players, free siege kit, original AI helper, earned weapon/skill siege rating>=2, or mastery10+ earned siege skill.
- Actual *existing* Rules.damageCastle retains sole HP/shield/egg/win authority. Pure candidate limits proposals to 60 per strike / one per attacker each second / 150 per castle 5 seconds. **commitCorePermit only after genuine existing source acceptance**. Integration must protect every original castle damage entry path (human prompt and BotActors) without permitting bypass.
- True original castle HP <=700/400/200 yields limited guardian summon proposals; each castle max 2 active and 3 per round, min 40s between, 45s lifetime, boss/CastleFall/round cleanup must be realized in existing AI. Guardians from shop #805 are cosmetic and horizontal tactical role variance; current CastleDefense #500 TURRET/TRAP/SENSOR preserved.
- role7 guardian stance, 3 free tier cues from verified mastery; no paid HP or extra unit cap, no infinite defense.
- Native actual compile+VM regression and 7-role source candidate workflow. No existing 31/Core36/Game/CastleRules/Host/BotActors scripts changed. Core36 baseline OFF exact.
- **NOT YET connected to real original CastleRules/Host or #805 wallet/shop. Studio not tested, no authenticated #220 RC CAS.**
- Follow-on: original single Host delegates gate and guarded core permits; original Rules remains sole damage, same session/match/visible 3D wreck FX; original #500 defense and #527 pacing no duplicates; #220 same-head Native/Rojo/rollback expectedSHA nonforce CAS; actual 2-client+Android testing.
