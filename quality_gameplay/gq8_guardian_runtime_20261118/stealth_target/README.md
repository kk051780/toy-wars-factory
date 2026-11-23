# Guardian cloak target eligibility: SAME-PR support proposal

This six-file package transports the already authored **+294-byte Guardian source proposal** and its frozen diagnostic cases. It is an isolated proposed amendment to [PR796](https://github.com/kk051780/toy-wars-factory/pull/796), based on existing head `233684a21411afe12289b18a61d78619061ec322`. The existing `role_session` and `role_los` files remain byte-exact. The package does not grant publication, create a competing gameplay producer, or adopt a release candidate.

The package author is `CODEX_ROOT_870491EA0B74:/root/planning_triage`. The +294 gameplay source author is the distinct `CODEX_ROOT_870491EA0B74:/root` context. Earlier independent diagnostic evidence remains historical evidence; it is **not independent approval of this newly authored helper, lock or runner**. This package was prepared without executing it. An independent reviewer must inspect and execute the frozen package before any later grant or registered approval claim.

## Pinned source, separately observed release head

The input is **PINNED_H93_SOURCE_CANDIDATE_ONLY**:

| Input | Identity |
|---|---|
| Source commit | `93a1147561a531610ac1609ebc68cc0ecf546623` |
| Official historical run | `45106580546` |
| Historical source artifact | `14787568439` |
| Artifact ZIP bytes | `5840240` |
| Artifact ZIP SHA256 | `1187e0f2ff176a286855e911495da84006d5c99841f68891aeca9630915f275d` |
| Original PR head | `233684a21411afe12289b18a61d78619061ec322` |

`INPUT_LOCK.json` pins the exact 69 extracted `.luau` sources. The caller verifies the artifact archive before extraction; the runner verifies the complete extracted file set and all byte/hash identities. It records `--latest-rc-head` separately as a caller-supplied observation and does no network lookup. Passing a later release head does not rebind this package to it. Formal canonical intake must revalidate the then-current source set and required gates.

Historical jobs in the original PR233 workflow are outside this package and remain unchanged. Their historical release pins can fail. A successful appended diagnostic job does not imply that the whole workflow is green.

## Narrow gameplay intent

[Owner issue804](https://github.com/kk051780/toy-wars-factory/issues/804) explicitly describes NINJA Guardian as “shadow scout / phantom duelist — cloak detect and ambush.” The NINJA exception is therefore preserved. The ordinary six roles respecting active empty-handed cloak is a bounded inference from this role distinction and the existing SevenRoleCombat human-targetability policy. Issue804 does not literally state that only NINJA may detect cloak; the source proposal's short comment is interpreted with this qualification.

The unchanged proposal adds the actor's existing role to `targetOf`, checks that role or authoritative `session.rules.castles[id].heldEggs` or server stealth expiry before admitting a human candidate, and passes `d.role` at the existing call site. It never trusts the replicated carrying attribute. Existing health, current-human membership, team, line-of-sight, attack timing and damage paths remain in place.

| Source base | Original bytes / SHA256 | Candidate bytes / SHA256 |
|---|---|---|
| H93 | 13707 / `9455e263a450002a4c578993e508f37d0b6ea8233eae36c8de06210889410096` | 14001 / `2c6f53526cb54b1a929db295ca189e7642b0c98c89c20df470642895a118f698` |
| PR796 role170 + LOS30 | 13907 / `1afd38a70a27ada58ad7418768ce5c6f3b6576635aa467e14a45056af0505825` | 14201 / `a6a4433966ba52212d42e12dc69e8bca7a63424fe31c25ade89724928d417ef2` |

`apply_stealth_target.py` contains exactly the parent's three byte replacements, with explicit source-base and direction selection. It rejects any input identity outside the two frozen pairs, requires one occurrence of each anchor, verifies the exact output identity and +294/-294 delta, and can invert each candidate byte-exactly. It writes only to a new output file. The runner reconstructs the PR796 input through the existing frozen `role_los/apply_existing_repairs.py`; it does not duplicate or alter the existing role/LOS transformation.

## Frozen tests and fixture provenance

`case.luau` is the completed independent review's `stealth_case.luau`, copied byte-exactly. `fixture_boundary.luau` is that review's `scenario_setup.luau`, also byte-exact. No case name, assertion, clock interval, role expectation, sensor exclusion, or target-position selection was edited for this package.

Execution uses the same four fixture bodies as that completed review, in the same order:

1. H93 native `fixtures/native_prefix.luau`.
2. H93 native `fixtures/fixture_additions.luau`.
3. H93 native `fixtures/speed_fixture_additions.luau`.
4. Frozen PR233 `role_los/fixture_boundary.luau`, 9041 bytes, SHA256 `8650af84ee20070946a5bcf2a651b08dcc1eab67d0a0ce713286e606e815c104`.

The fourth input is deliberately the existing 9041-byte PR233 boundary: it is byte-identical to the `combined_fixture_additions.luau` used in the completed independent review. H93's same-named native file is 8134 bytes and lacks the existing Guardian damage observer and earlier default-property correction. Substituting H93's 8134-byte file would change the frozen diagnostic fixture. No favorable new fixture was created. Both provenance sets are pinned distinctly. The entire H93 native directory and its original fixture contract are independently checked before reusing its fresh-build helper; its original positive suites are not rerun here.

The runner embeds all **28 complete game bodies**, including Host, and verifies byte slices against each exact selected source body. Every process receipt records byte-start, exclusive byte-end, first/last line, byte count and SHA256 for all 28 bodies. Guardian is the only varied gameplay body; the other 27 loaded bodies remain H93. All 69 original source files, all 12 existing PR files, all H93 native files and all six package files are checked before and after execution. The helper/cases/README have pre-execution pins in the hard-pinned input lock; the runner and lock are also included in the full before/after package receipt and in the externally reviewed Git/package identity.

## Exact matrix and interpretation

There are **13 distinct diagnostic scenarios**:

- MAGE: visible, hidden, authoritative carrier, expired, distinct same-team player, inactive player, and false replicated carrying attribute.
- WARRIOR, NINJA, TRAPPER, BUILDER, BEAST, ZOMBIE: hidden empty-handed NINJA target, one scenario per Guardian role.

The complete matrix executes **40 native processes**: 13 H93 baseline, 13 H93 +294, 13 PR796 +294, and one original PR796 MAGE hidden reproduction. It requires exactly **8 expected baseline RED processes** and **26 candidate PASS processes**. Six other processes are passing baseline controls. `HOST_READY` is a prerequisite case inside each process, not an additional unique gameplay scenario.

The six ordinary Guardian roles must leave a hidden empty-handed player at HP100; NINJA must retain one normal seven-damage attack. MAGE visible/carrier/expired cases require one six-damage attack. The actual same-team and removed-member controls require zero attacks. The false carrying-attribute case requires zero attacks while authoritative custody remains0. Each process requires the exact `HOST_READY PASS` plus diagnostic PASS/expected-FAIL vector and the matching native exit code. A baseline exit1 is accepted only with the specific `GUARDIAN_MUST_NOT_TARGET_STEALTH_NONCARRIER` failure marker. The runner exits nonzero on an unexpected pass, unexpected failure, wrong vector or changed input.

The earlier completed local matrix had the same 13 scenarios, 40 processes, 8 expected baseline failures and 26 candidate successes. Its result SHA256 is `6df69fc1193bede953a7e13f5719824a3d833dc468336ff8288d5937e6834aa7`. That historical result used a previously built native binary; it is not a fresh-build execution receipt for this new package.

## Portable execution after independent review

Provide an extracted exact H93 source directory, an H93 repository checkout containing its native helper, the original PR files, and a clean Luau source checkout at commit `f46d879e28302a430029304f7f6a162aed66f103`, tree `2432c996fc9fa73680b5e2cfe172d36114fe3746`. No prebuilt Luau binary is accepted. Build and output directories must be new and disjoint from all input directories.

```bash
python -B quality_gameplay/gq8_guardian_runtime_20261118/stealth_target/run.py \
  --sources /input/h93-sources \
  --rc-root /input/h93-repository \
  --pr-root /input/pr796-repository \
  --luau-source /input/luau-f46 \
  --build-dir /work/new-stealth-build \
  --output /work/new-stealth-result \
  --latest-rc-head ACTUAL_OBSERVED_40_HEX_SHA
```

`--pr-root` defaults to the repository containing this package. The explicit option permits a separate read-only frozen PR233 checkout during local review. Optional `--cmake`, `--ninja`, `--git`, `--cc`, and `--cxx` arguments select existing build tools. The pinned H93 native helper verifies the clean F46 source tree, 2336 tracked files, physical Git blobs/modes, fresh build directory, CMake recipe, actual link step and binary identities. It performs local Git reads and local builds, without network fetches.

The main outputs are `RESULT.json`, `GUARDIAN_TRANSFORMS.json`, `toolchain/receipt.json`, both candidate Guardian files, both inverse files, and `matrix/<group>/<role>/<mode>/` containing `generated.luau`, `receipt.json`, `stdout.log` and `stderr.log`. Failed native processes retain their evidence. A later gate error records `FAILED.json` only in the invocation's own newly created output directory. Existing evidence is never overwritten by a rerun.

For a standalone exact transformation, use `apply_stealth_target.py --input SOURCE --output NEW_FILE --base h93` or `--base pr796`; add `--inverse` only when the input is that base's exact candidate. The helper does not assemble or adopt an RC.

## Evidence limits and follow-up

This is an API-fixture source/native test. Host joins, role prompts, real NINJA B, authoritative custody, Guardian spawn/targeting and the actual damage filter execute. Unrelated Bot/Boss/visual APIs remain the pre-existing fixture stubs; two original Swarm tasks are explicitly parked. Character positions and clock/ray geometry are controlled by the fixture. The real CastleDefense SENSOR remains active and hidden cases stay outside its actual30-stud radius.

The completed diagnostic retained the initial sensor-clearing setup attempt and an obstructed expiry-control attempt, then froze the corrected fixture. The final same-team case uses a distinct actual teammate. No prior attempt is counted as another unique passing scenario.

This package does not establish Studio, physics, replication, navigation, Android, FUN or whole-workflow acceptance. Existing combined positive suites can be executed separately on a later authorized composition. Preserve the current owner's SAME-PR amendment procedure and Bot→BEAST→Guardian intake order. Revalidate the then-current parent before canonical RC integration.
