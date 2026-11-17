# GQ8_BOSS_INITIAL_HEALTH_20261118 — PREP candidate

The existing Stone Giant starts at 900 HP but its replicated `EGGRUMBLE_BossHealth` attribute is only populated **after** the first confirmed hit. This one-script fix initializes that same server-owned attribute at spawn (900) before attacks begin. It does not add a health GUI or affect damage, combat timing, boss KO, win conditions, spawn counts or scores.

**Nonduplication:** Original #482 exact boss Git blob `2670618cba320c51936c750a10e43c194cada0f0`, plus already accepted GQ518 #518 wall occlusion patch from `f31081d5cb2bea86d01c76c53bb60cd2f9a8355d`. Parent #518 is reused *as-is*. No overlapping GQ514 boss-KO reset, GQ742 boss-result display, or GQ8 castle/egg/audio source. Exactly 1 of existing 31 sources is eligible for a generated ON replacement; the other 30 remain byte exact. The original immutable author source is never edited.

**OFF:** `select_health.py --off` outputs the exact previously selected GQ518 boss script, not an earlier unpatched #482 script. The inverse `undo` is byte-exact. Fail closed on author blob drift, missing anchor, double application or source authority changes.

**QA:** Pinned original/GQ518 SHA, actual source Python regression (including negative cases) and native Luau ON/OFF compilation in dedicated GitHub Actions. The full current31 composition and same-HEAD canonical V3 Rojo + officially selected Place must be reverified on the **latest** RC branch before adoption.

**State:** source change and isolated regression workflow submitted for CI; not yet official RC gameplay selection. Do not count this as `RC_INTEGRATED` until the sole authenticated #220 integrator advances `rc/p0d-s1-kids-rc01` with nonforce expected-SHA CAS, verifies 31 actual source exact/real Rojo + official same-HEAD run and updates the feature registry. No original author ACK needed; main, publication, purchases and additional spending forbidden. Studio/Android/FUN/ART/OWNER **NOT TESTED / NO GO**.
