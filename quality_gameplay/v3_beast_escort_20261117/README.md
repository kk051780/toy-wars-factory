# GQ BEAST-ESCORT real unit — distinct source-quality slice (2026-11-17)

**FEATURE_ID:** GQ_BEAST_ESCORT_REAL_UNIT_20261117
**SOURCE_WIP / PRIVATE21 source candidate; NOT formal RC or Studio proof.**

## Why this is not a duplicate
- Existing #482 original `EGGRUMBLE_SevenRoleCombat` BEAST-B only creates a short-lived giant neon Part and a player-centred blast. No BEAST minion Humanoid follows, selects neutral/human/bot enemies, or moves on server. This changes that *specific* real behaviour.
- Existing #582/#608 ZOMBIE command applies to the different ZOMBIE class. Reuse its **single existing Combat and immutable source composition principle**, not its summon code.
- Existing #522 builder construction, #508 neutral KO, #580 BotActors, #520 field clearance, #517 Item, #539 Lobby, #583 roster, #595 vertical hit geometry, and #607 egg deposit retain exclusive scopes. Do not rewrite any.
- No new Game, Combat controller, damage/KO authority, player Remote, Store, score or off-platform operations.

## What changes
- One caster at a time can spawn **one real temporary Humanoid beast** on server, with two identifiable body sections; physical MoveTo follows caster, seeks nearby hostile bot, player or neutral, short melee hit and 12-second lifecycle.
- Server enforces caster role/character/current mode membership/active round/alive castle; 28-stud leash, 26-stud search, 56 neutral scan cap, 1.4-second attack cooldown, 60 HP and 6 delegated damage. No attacks or cleanup after caster state ends.
- The companion asks **the existing SevenRoleCombat `neutralAndBotHit`** for an attack; no separate actual damage or KO. The single original Combat handles target/team/LOS. Same original six other class branches remain untouched.
- Source composer refuses original SHA drift and exact source anchor drift; OFF inverse yields exact prior Combat. An additional current31 source selector is necessary after all current adopted selectors, with full Native31/Rojo31, flag/rollback and #220 sole writer CAS.

## Eight-domain integrity contract (not completion)
| Area | Scope | Current state |
| --- | --- | --- |
| Characters | BEAST unique independent minion instead of neon giant | PRIVATE SOURCE |
| Field | 28-stud leash, real wall LOS, no free teleport | PRIVATE SOURCE |
| Battle | Single existing Combat hit callback, no new damage owner | PRIVATE SOURCE |
| Castle | owner castle alive/TEAM membership check, no castle writes | UNCHANGED |
| Neutral | bounded horde scan, only old Combat credit rules | PRIVATE SOURCE |
| Items | no Item source mutation or inventory shortcut | UNCHANGED |
| Lobby | no READY/entry or displayed job edits | UNCHANGED |
| Balance | one pet/12s/6 damage/1.4s cooldown | PRIVATE SOURCE |

## Required gates, and non-waivable product reality
1. Pinned original author #482 HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9` and source blob `66e666418b7c23d41f87faa5d61eb6e2770a463e`. Twelve Python negative and byte-exact rollback tests.
2. Original21 real Luau native all-scripts compile, true Rojo 21/21 Source/Class in PRIVATE Place; exact same PR HEAD CI. **This does not mean present official31 is compatible yet.**
3. Re-compose against the **latest** chosen 31-source current Combat after official #582 and all subsequent patches. Revalidate 31 native, pinned Rojo 31/31 Source/Class, no duplicate authority, single feature switch/OFF revert and fresh CI.
4. Only #220 authenticated sole writer: re-read current official branch HEAD, source-select minimal diff, **nonforce expected-SHA CAS**, same official HEAD V3+legacy CI, artifact ZIP bytes separate from .rbxlx bytes, post-adoption receipt. No old author individual ACK wait; no permission/CAS bypass.
5. Studio real solo + 2-client TEAM/BR, Android15m, ART/FUN under #420 and OWNER acceptance remain **NOT_TESTED / NO_GO**. Pet form and actual movement quality are placeholders pending device trial.

## Handoff
- OWNED path: `quality_gameplay/v3_beast_escort_20261117/**` and `.github/workflows/p0d-gq-beast-escort-20261117.yml`.
- Frozen base official HEAD at branch creation: `d2a14b3e4c20918c2a92f1410886c85548123e68`. Must recheck live HEAD when accepting.
- `ROLLBACK`: omit BEAST source-selection (the existing original BEAST-B remains byte-identical), leave other 30 selected V3 scripts and legacy rich51 untouched.
- `P0D_PREP_READY_V1=NO` until full current31 same-head CI; `OFFICIAL_RC_ADOPTED=NO`; `STUDIO/ANDROID/FUN/OWNER=NO_GO`.
