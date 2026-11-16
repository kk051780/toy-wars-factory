# GQ V3 dead-caster life fence — source-selective gameplay patch

Feature: `GQ_V3_DEAD_CASTER_HEALTH_FENCE_20261116`, issue #470; author #482 fixed commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, original Combat Git blob `66e666418b7c23d41f87faa5d61eb6e2770a463e`.

## Actual defect and one-source repair
The original SevenRoleCombat `execute` verifies role, active castle and presence of Humanoid but **not Health>0** before stamping cast signature and charging cooldown. The MAGE C branch runs `healAllies` **before** the downstream `blast` dead-health check. A dead caster with an equipped Tool may therefore trigger a heal pulse while dead; downstream `blast` is not sufficient protection. This patch adds `Health<=0` or explicit downed-state rejection **before** cast signature/cooldown for all seven roles.

No new Game, Combat module, Remote, save, scoring, boss, AI, egg or authoritative state. This is a deterministic **private overlay generator** against the one existing author Combat, not a duplicate implementation. It does not implement Mage resurrection; that is a separate missing release requirement.

## Test / private source composition
`python3 -m unittest discover -s quality_gameplay/v3_dead_caster_fence_20261116/tests -v`
`python3 quality_gameplay/v3_dead_caster_fence_20261116/tools/compose.py --output /tmp/EGGRUMBLE_SevenRoleCombat.luau`
`python3 quality_gameplay/v3_dead_caster_fence_20261116/tools/compose.py --off --output /tmp/EGGRUMBLE_SevenRoleCombat_OFF.luau`

All inputs fail closed if original source Git blob changes. OFF returns original exact bytes. ON adds two lines only, no removals. CI should syntax-compile real generated Luau; Python tests are structural/mutation tests **not real Roblox runtime tests**. Author #510/#516/#524/#529 already selectively modify same Combat, so formal intake **must recombine with their latest patches**, run same-HEAD source/native/Rojo and verify no clone Combat. Do **not** merge whole branch on top of them and overwrite their work.

## Eight-domain impact and release gate
Character: 7 roles share the guard. Battle: a dead/downed hero cannot cast/heal/cause cooldown side effects. Field, castles/eggs, neutral mobs, items, lobby/mode selection, balance/score: original author source unchanged; cross-domain regression is still needed in a real combined Place. Candidate changes `Game/Store/Remote/HP/score` authority zero; no Studio/Android claim.

`#218 CLAIM_GRANTED=NOT_OBSERVED; #482 AUTHOR_ACK=PENDING; PATCH_PRODUCED=SOURCE_ONLY; PREP_READY=NO; OFFICIAL_RC_ADOPTION=0; STUDIO/ANDROID/ART/FUN=NOT_TESTED; OWNER_ACCEPTED=0.`

Required for RC: source-selective author ACK + #218 explicit grant, recomposition over newest #529+author sources, native parse and VM negative tests, real private 8-domain Rojo SourceExact with reversible OFF, then authenticated B #220 non-force CAS and official same-HEAD Place+ZIP bytes; 2-client Studio/15m Android/#420/#470/OWNER follow. No main push, normal merge, Roblox publish, billing or PC.
