# Guardian: reuse the role170 and outgoing LOS30 repairs together

This isolated current69 source/Native package continues **GQ815_GUARDIAN_ACTUAL_MATCH_AI**, specification #804 and existing PR #796. It composes two existing repairs without creating a second Guardian implementation or changing the canonical producer.

- The six-file `../role_session/` package at commit `8710eb04d55109f22c122bc9805101ed73e6a35c` remains byte-exact. Its two source hunks snapshot each castle's validated role at `Guardian.attach`, preventing a departing/rejoining player's new selection from changing an old match's Guardian model, HP or gear.
- Original author context `ca1ffba54bf0` published the outgoing `ray.RespectCanCollide=true` line in [PR796 comment7078362242](https://github.com/kk051780/toy-wars-factory/pull/796#issuecomment-7078362242). It makes the existing outgoing query agree with the already adopted incoming collision rule: a noncollidable queryable SiegeGate no longer prevents an attack, while a collidable wall still does. This is reuse of that exact +30-byte proposal.
- Prior independent LOS verification is [comment7079427679](https://github.com/kk051780/toy-wars-factory/pull/796#issuecomment-7079427679); its current-fb5 revalidation is [comment7085610778](https://github.com/kk051780/toy-wars-factory/pull/796#issuecomment-7085610778). Original packet identities and verbatim fixture/case byte ranges are retained in `INPUT_LOCK.json`.

## Four exact source states

All variants select the current official `fb5d9b693c48d4ffcce05c3f89d490593e0cecfd` 69-source input. Only `ServerScriptService/EGGRUMBLE_CastleGuardianRuntime.luau` changes.

| Variant | Bytes | SHA256 |
| --- | ---: | --- |
| baseline | 13707 | `9455e263a450002a4c578993e508f37d0b6ea8233eae36c8de06210889410096` |
| role_only | 13877 | `9885dd14eee029d95a1e32e504870aeb84ccc1d0fa64b799aba89822abebdb9a` |
| los_only | 13737 | `cbf71c44c7e6cf055127ba7e20b317bfce22c58da7998b33ac95081d3f2f6199` |
| combined | 13907 | `1afd38a70a27ada58ad7418768ce5c6f3b6576635aa467e14a45056af0505825` |

Combined is three existing source hunks, +200 bytes. CONFIG, damage/HP constants, range, attack period, membership, lifetime, movement, incoming LOS and the other 68 production bodies are unchanged. The adapter checks all 12 directed transitions between distinct states, including either partial rollback and the full exact baseline inverse. Role-only and LOS-only are negative controls, not additional features.

## Original tests retained

The new `case.luau` is a container for the original common setup, gate case and wall case. Their three byte ranges and hashes are pinned. The runner extracts the common block and one scenario block for each generated program. It never executes both original error footers in one program and does not rewrite their assertions. `fixture_boundary.luau` is the exact original focused fourth fixture; the first three fixtures are reused from the pinned current RC.

The gate and wall programs contain 28 current full production bodies, including the actual Host, Guardian, Combat and Invul runtime. The original focused boundary stubs unrelated BotActors/NaturalRegen dependencies and parks the original Swarm jobs. This remains the original bounded two-human TEAM/MAGE diagnostic, with observed target rays, real source damage calls and fixed gate/wall geometry.

The separate role scenarios reuse the frozen role package's 32-body assembler, original cases and explicit parked Bot/Swarm movement boundary. Existing `combined_clear_los` and `objective_full_clear_los` scenarios reuse the unchanged canonical Native assembler and cases.

Six suites run for each of the four source states: 24 generated programs. Combined has 49 role/archetype, 10 actual Host lifecycle, 5 gate, 5 wall and 10+7 existing regression cases: 86 case rows. The expected vectors require the original role failures only in baseline/LOS-only and the exact original open-gate failure only in baseline/role-only. Solid-wall and existing regression checks must pass in all four states. A known negative is accepted only with the original case IDs/order, exact expected process exit, exact numeric failure, generated-program line locations, stderr and ray trace outcomes.

All four first gate query endpoints/times and ten wall query endpoints/times must match. The original independent analytic plane-crossing calculation verifies 13 segments separately from the fixture's slab ray algorithm. Source ranges store byte offsets and identities so every production body can be verified against the selected input.

## Reproduce

Obtain the immutable official input artifact14761404772 from successful run45041527167, and check its ZIP length5325025 and SHA256 `6e1c7cecb39b88a33f9c68b7698eaf21a178461852331c98e7583cbf47ab1793`. Use a clean checkout of the official RC and the pinned Luau source `f46d879e28302a430029304f7f6a162aed66f103`.

```bash
python3 -B quality_gameplay/gq8_guardian_runtime_20261118/role_los/run.py \
  --sources /absolute/official-artifact/sources \
  --rc-root /absolute/official-fb5-checkout \
  --luau-source /absolute/pinned-luau-checkout \
  --build-dir /absolute/new-luau-build \
  --output /absolute/new-combined-evidence
```

The build and output directories must not exist and must not overlap the inputs or package. The pinned original Native build function verifies the physical 2336-file Luau tree and builds a fresh executable and compiler. All 69 baseline and combined sources compile. Output includes the 24 complete programs, raw logs, exact vectors, full-body offsets, four source variants, exact inverse, input/package identities and toolchain receipt. Inputs and binaries are rechecked after execution. Failure evidence uses the frozen runner's owned-directory device/inode, no-follow and exclusive-create boundary, without overwriting preexisting output.

If a tool name resolves to a launcher rather than the actual executable, pass the actual binary with `--cmake`, `--ninja`, `--git`, `--cc` or `--cxx`. The original cache contract requires CMake's recorded paths to equal the explicitly selected executable paths; a launcher-path mismatch is a failure and is not waived. The first local combined attempt stopped at this check before compilation; its failure is retained separately.

The dedicated appended workflow job additionally checks actual candidate HEAD, immutable official input provenance and all package pins, then builds/verifies baseline, combined and inverse Places with pinned Rojo7.7.1. Baseline and inverse must byte-equal the official Place. Its artifact is explicitly source/Native/Rojo preparation and is not the official RC artifact.

## Scope, rollback and acceptance boundaries

The v3 amendment request is [#218 comment7087309051](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7087309051) under the existing `P0D-GQ815-GUARDIAN-ROLE-20261123-3B3ACF42` claim. An actual registered amendment is required before publication. It adds six sibling files and permits only one appended dedicated workflow job; the original17951 workflow bytes, two existing jobs and frozen role six-file package are preserved.

Remove the six new files and the appended job to undo this submission without changing the prior role package. Use an explicit adapter transition to remove either source repair or both in generated evidence. This does not authorize resetting another writer's RC, applying the historical Real41/42 producer, or merging the old divergent PR branch wholesale.

Shared UNION22 producer/profile/Native and common GQ8 workflow remain under their existing owners. Canonical selection, a new official RC build, same-head independent acceptance and a separately owned RC writer lease are subsequent requirements. The old Guardian42 workflow failure is preserved and must not be called whole-workflow success. `PREP_READY=false` and `official_rc_adopted=false` remain explicit.

Native fixtures do not verify Roblox Studio, actual physics/navigation/networking, rendering, Android or enjoyment. Studio/2client/Android/FUN remain NOT_TESTED; ART/PRODUCT remain NO_GO. This package does not claim all roles/modes for the focused LOS route, an actual 24-hour session, background execution, main promotion or Roblox publishing.
