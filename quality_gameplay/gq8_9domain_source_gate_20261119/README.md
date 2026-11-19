# EGGRUMBLE formal REAL65: independent nine-domain source integrity
Owner: existing PR #836; latest maintainer successor; policy #839; sole RC #220.

This is a source-only QA gate, **not** nine gameplay passes and not an additional
gameplay authority. The audited input is the **fresh exact formal RC HEAD**
same-head successful official REAL65 GitHub Actions artifact, not a candidate
from another branch. The audit hashes every 65 game source, class, Rojo route,
and receipt before counting nine source-presence domains. A missing/duplicate
singleton Combat/Host/Swarm/Realm rejects the build.

## Real damage-source evidence (official REAL65)
There are 14 direct executable `:TakeDamage(` callsites. Twelve contain
`:TakeDamage(InvulRuntime.filterDamage(` inline. The other two are inside
the same **EGGRUMBLE_SevenRoleCombat** and pass *precomputed* guarded damage:
`enemyHum:TakeDamage(originalAttackDamage)` and
`atHum:TakeDamage(realDamage)`. The audit requires the original exact
`InvulRuntime.filterDamage` assignments nearby, guards the victim, damage,
source kind and attacker identity, checks both site names once only, and
rejects mutated/unowned/bypass source before reporting PASS. See
`test_audit.py` for negative mutants. This static gate does **not** certify
indirect health writes, physics knockback, studio multiplayer or FUN.

## Non-loss / adoption
Original official 65 in-game Luau source/class/bytes unchanged by this PR.
One canonical `rc/p0d-s1-kids-rc01` branch, private REAL65 companion only,
original S1 rich51 preserved. This PR also adds a paths-only official
composer workflow trigger to ensure a new **same new official HEAD** native
65/Rojo/OFF63/Place artifact after the accredited #220 expected-SHA
non-force integration. No main writes, no external Work/Codex tasks,
no Roblox publication, paid settlement or owner approval wait.

## Product acceptance
Studio solo/2-client, Android 15-min FPS/heat, visual character/castle/sea
quality, first three-minute child FUN and public monetization are
NOT_TESTED/NO_GO until measured on the exact artifact. Rollback removes the
audit and trigger; never deletes any existing gameplay features.
