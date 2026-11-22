# GQ BEAST-ESCORT real unit — distinct source-quality slice (2026-11-17)

## Current69 targeting continuation (2026-11-23)

The original GQ618 source was adopted through PR #629 at RC
`82cd7b5b7be2cb326959f9b1d7a66e7ac6f49949`. The original21/current31
documentation below is retained as historical source-contract context. This
follow-up continues the same feature and PR #618; it does not introduce another
Beast implementation or damage authority.

Claim: `P0D-GQ618-BEAST-TARGET-20261123-B8C8E7B7`, registered at
`d10214caf6d24eda42cd89e9e9f844993071b37d` in `coord/p0d-work-claims`.
It permits the eight enumerated source preparation paths only. Canonical
Union22 producer changes and formal RC writes require a subsequent scoped
handoff and independent acceptance.

### Reproduced problem and bounded repair

In the frozen formal69 build `fb5d9b693c48d4ffcce05c3f89d490593e0cecfd`,
the existing Beast picker can follow a nearer charmed neutral or hidden human
that the existing damage path refuses to attack. That target occupies the
nearest slot and prevents pursuit of a farther eligible enemy. Following a
hidden human also exposes its position through the pet's movement command.

`patch_current69.py` changes only two anchors in inline `BeastEscort.pickTarget`:

- Exclude every neutral whose existing server-owned
  `EGGRUMBLE_NeutralFriendlyOwnerId` marker is present. This matches actual
  Swarm damage eligibility for all charm owners, including the interval before
  the existing release routine clears the marker.
- Reuse `currentHumanMember` and `humanCombatTargetable` for human selection.
  The latter preserves the authoritative held-egg exception to NINJA stealth.

Combat changes from 73,774 bytes / SHA-256
`1b4ec066f4273c7cfc88d075a4a1df4855233e759f81d0241b134383bef42f76`
to 73,889 bytes /
`ba37d904cc9a5529ffaae7602ae25830a65abb4634fe3e3cdbfa95a767c87f4a`.
The delta is +115 bytes. Pet lifetime, leash, radius, scan cap, cooldown, one-pet
limit, damage callback, geometry and every other source body remain unchanged.
The OFF transform restores the exact prior Combat.

### Separate current69 evidence contract

`native/INPUT_LOCK.json` pins the complete 69-route source profile, project,
baseline Place, frozen formal helper/fixture files, new Beast fixtures and
historical21/31 files. It consumes the exact formal run `45041527167`, artifact
`14761404772`, ZIP 5,325,025 bytes / SHA-256
`6e1c7cecb39b88a33f9c68b7698eaf21a178461852331c98e7583cbf47ab1793`.
Input drift or an unavailable/expired artifact fails closed; do not silently
replace this baseline with another run.

The dedicated current69 job checks out the actual PR head, verifies that the
eight reviewed files match that Git commit, builds Luau Repl and Compile from
the pinned clean source commit, then performs:

1. All 69 sources compiled and compared by full route, class and embedded
   source for ON and OFF Places; 68 source bodies remain byte-identical.
2. An actual inverse whose 69 sources and full OFF Place exactly equal the
   baseline. The baseline and OFF generated native programs are also identical.
3. Twelve Beast cases using 28 complete selected server bodies, including real
   Host TEAM entry, real ZOMBIE Tool conversion, real NINJA Tool stealth,
   authoritative egg transfer, charm release, stale membership and caster death.
   Baseline/OFF must reproduce exactly the three recorded failures; ON must
   pass all twelve. An arbitrary nonzero exit does not count as reproduction.
4. The unchanged frozen combined10 and objective7 clear-LOS suites against
   the ON source. Their original assertions, inputs and game bodies remain
   intact.
5. Negative admission tests for source/route/identity drift, duplicate inputs,
   unsafe output placement and incomplete or falsified native case vectors.

Local invocation, with the formal artifact unpacked and a checkout of the
frozen formal repository and clean pinned Luau source available:

```sh
python3 -B quality_gameplay/v3_beast_escort_20261117/test_patch_current69.py \
  --artifact-dir /absolute/formal69 --baseline-repo /absolute/formal-repo
python3 -B quality_gameplay/v3_beast_escort_20261117/native/run_current69.py \
  --artifact-dir /absolute/formal69 --baseline-repo /absolute/formal-repo \
  --luau-source /absolute/clean-luau-source --build-dir /absolute/new-build \
  --out /absolute/new-evidence --rojo /absolute/pinned-rojo
```

These are source-quality gates. The frozen API fixtures approximate scheduling,
geometry and players. `Humanoid:MoveTo` records a command and does not simulate
Roblox physics or pathfinding. The other41 source bodies are compiled and
embedded, not all behaviorally executed. Studio, Android, ART/FUN and formal
RC acceptance remain separate. ACTIVE rich51 and private REAL69 remain distinct.

## Historical original21/current31 contract

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
