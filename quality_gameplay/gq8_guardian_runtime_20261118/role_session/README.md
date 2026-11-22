# Guardian roles belong to their match

Continuation of `GQ815_GUARDIAN_ACTUAL_MATCH_AI`, specification #804 and existing
runtime PR #796. This six-file package verifies one current69 source repair. It
does not replay the historical Real42 producer or select a new official profile.

## Defect and change

The official Host passes its mutable lobby `chosenRole` table to Guardian.attach.
PlayerRemoving clears that table entry, but the former player's castle can remain
in its active match under Bot takeover. A new Player object with the same UserId
can choose a different role and enter the other mode. Guardian.refresh originally
read the shared table again at each new wave, changing the old castle's defender
archetype, health and equipment.

The two source hunks create a private role snapshot at attach, keyed by the
existing `session.rules.castles` roster, and use it during refresh. They retain
CONFIG validation and the WARRIOR fallback. Each attachment owns its own table.
The real Host already creates siege states before Guardian.attach; this repair
does not depend on those states being initially empty.

No Host, Policy, HP constant, budget, cooldown, lifetime, damage, membership,
score, shop or authority changes are included. The existing outgoing Guardian
LOS +30-byte proposal in #218 comment7077957972 remains a separate candidate.

| Identity | Before | Candidate |
|---|---|---|
| Guardian source bytes | 13707 | 13877 (+170) |
| SHA256 | `9455e263a450002a4c578993e508f37d0b6ea8233eae36c8de06210889410096` | `9885dd14eee029d95a1e32e504870aeb84ccc1d0fa64b799aba89822abebdb9a` |

All other 68 source files must remain byte-exact. The adapter accepts only the
locked original, verifies its exact output and rejects double application or
unrelated input changes. The inverse restores the original bytes exactly.

## Reproduction and regression contract

The independent lifecycle case uses complete current Host, BotActors, Guardian,
Rules, SiegeBridge/Policy, Combat and NaturalRegen bodies. The real role prompts,
12-second READY, PlayerRemoving, Bot takeover, new Player join and second match
run through the real Host handlers. Assertions inspect actual Model name, role,
maximum/initial health and signature gear. The official source fails two old-match
role assertions; the candidate must preserve MAGE70 in TEAM while new BR uses
NINJA68. Actual NaturalRegen and both-session cleanup must still pass.

A separate direct attach/refresh matrix covers all seven roles, missing/invalid
selection, nil/non-table role maps and a nonnumeric AI owner over three waves.
Every case checks actual policy reservations are zero after shutdown. Each source
variant runs in a new Native process. The runner requires the complete expected
case vectors, including the precise known baseline failures; any other failure,
missing case or reordered case rejects the experiment.

`run.py` performs:

1. Exact all69 input and original fixture/runner/lock verification.
2. A fresh Luau build using the unchanged original current-RC build function,
   verified source commit/tree and explicit compiler/CMake/Ninja identities.
3. Native compilation of all69 baseline and all69 candidate sources.
4. Lifecycle (10 cases) and archetype (49 cases) suites on baseline, candidate
   and exact inverse. The baseline and inverse must reproduce the known defect;
   the candidate must pass every assertion.
5. Both original current-RC suites (`combined_clear_los`, 10 cases, and
   `objective_full_clear_los`, 7 cases) on all three variants, using their original
   immutable cases/fixtures and assembly function. All must pass.
6. Rejection of already-patched, appended and truncated inputs, exact inversion,
   unchanged official69, unchanged package/fixtures/toolchain checks and raw logs,
   complete generated bodies, hashes and receipts for every run.

These are source/native checks. Their count is not a game completion percentage.

## Inputs and command

The immutable source baseline is official RC
`fb5d9b693c48d4ffcce05c3f89d490593e0cecfd`, Actions run45041527167, artifact14761404772
`P0D-EGGRUMBLE-V3-REAL69-CANONICAL-PRIVATE-STUDIO`. Original ZIP identity is
5325025 bytes / SHA256
`6e1c7cecb39b88a33f9c68b7698eaf21a178461852331c98e7583cbf47ab1793`.
The artifact's `sources/` is the input; it is never modified by this runner.
Use a separate checkout of that exact RC for `--rc-root`, as the historical PR796
branch does not contain the later current69 Native runner/fixtures. Their exact
contents are pinned in INPUT_LOCK.json; a newer incompatible RC fails closed.

Luau source must be a clean checkout of
`f46d879e28302a430029304f7f6a162aed66f103`, tree
`2432c996fc9fa73680b5e2cfe172d36114fe3746`. The original builder verifies all2336
tracked files and creates its binary in a previously absent build directory.
Do not substitute a prebuilt interpreter.

```sh
python3 -B quality_gameplay/gq8_guardian_runtime_20261118/role_session/run.py \
  --sources /absolute/official-artifact/sources \
  --rc-root /absolute/rc-fb5d9b6-checkout \
  --luau-source /absolute/luau-f46-checkout \
  --build-dir /absolute/new-guardian-luau-build \
  --output /absolute/new-guardian-evidence \
  --cmake /absolute/cmake --ninja /absolute/ninja \
  --git /absolute/git --cc /absolute/cc --cxx /absolute/c++
```

Output/build directories must be new and separate from the inputs. RESULT.json
is produced only after the full contract passes; FAILED.json and suite raw logs
record failures. `official_rc_adopted` remains false. The output contains the
original package, generated programs with full-body byte ranges, stdout/stderr,
fresh compiler build evidence and the candidate/inverse Guardian bodies. Temporary
69-file execution copies are deleted; this is not another project producer.

## Boundaries and next admission

Four existing engine fixtures remain byte-identical. The separately declared
boundary parks unrelated BotActors/Swarm movement jobs and rejects accidental
navmesh requests. Real start/takeover and cleanup execute, but physical movement,
network replication, rendering and all background AI are not verified by this
fixture. Studio Solo/2client, Android and FUN remain NOT_TESTED; ART/PRODUCT remain
NO_GO. No main promotion, Roblox publishing, purchases or schedule changes.

The unchanged historical Guardian42 workflow pins an older live RC and can fail
`RED_FORMAL_HEAD_CHANGED_REBASE` on this continuation. This package does not weaken
that predicate, suppress its job or claim green whole-workflow CI. Local Native
results and GitHub checks must be recorded separately.

Canonical admission requires a new coordinated producer handoff after the
existing HUD/BotActors queue, a fresh official head, an updated reviewed source
identity that preserves any intervening repairs, same-head checks/Place/OFF
evidence, an independent candidate review and the sole RC writer lease. Never
merge all historical PR796 content as a substitute for that bounded adoption.

Claim: `P0D-GQ815-GUARDIAN-ROLE-20261123-3B3ACF42`; scope grant
[registry683f0032](https://github.com/kk051780/toy-wars-factory/blob/683f0032bc0f524dd363a27f223018f783096249/rc_fastlane/P0D_WORK_CLAIMS.json),
[#218 grant7086712962](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7086712962).
The grant covers these six files only and does not authorize an RC write.
