# GQ8｜真正サーバ受理スキルの極小キャストCue（既存CombatFeelのみ）

- **Scope**: Server-accepted cast cue for 7 roles, using existing replicated `EGGRUMBLE_SkillCastSignature`. A brief 20x3px bar; **NOT** HIT/KO confirmation. Real hit reticle remains driven solely by `EGGRUMBLE_ImpactSequence`. No fake damage, cooldown authority, Remote, persistent UI, or input hijack.
- **Original**: #482 immutable commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, original `EGGRUMBLE_CombatFeel.client.luau` Git blob `5509326beed0827b020d967cd9562724d8abbd2a`.
- **Patch selector**: `select_cast_cue.py`. It fails closed on source/anchor drift and produces exact byte-equivalent OFF by `undo` or `--off`.
- **Intake**: Only REPLACE the existing CombatFeel LocalScript in the 31-source companion after the final pinned composer. Keep 1 Game/Combat/Swarm/BotActors, all other 30 byte identical, source count 31. NO extra LocalScript, new HUD authority, status Remote or root overwrite.
- **CI**: native Luau compile of the actual original-source-derived `ON/OFF`; Python inverse/guard negatives. Existing official 31 Rojo + all-domain regressions and fixed SHA are still mandatory at integration. Studio 2 clients, Android 15m, CHILD FUN and OWNER remain NOT_TESTED/NO_GO until human acceptance.
- **Rollback**: select `--off` / original Git blob (restores original bytes). Integrator remains #220 sole authenticated nonforce expectedSHA CAS writer. main/publish/merge/paid forbidden.
- **Avoided overlaps**: #714 land/sea/sky, #721 real31→32 bridge, #725 live part budget, #723 neutral KO, #729 castle defense, legacy FB019 80-source PRs.

- **GQ8 2026-11-18 recovery:** #735 is rebased after GQ504 confirmed-hit audio and GQ732 castle decor in latest 54-flag RC. Same 31 real sources, only existing CombatFeel LocalScript changes, other 30 byte-exact, reversible flag. Studio/Android/FUN/Publish still NO_GO.
