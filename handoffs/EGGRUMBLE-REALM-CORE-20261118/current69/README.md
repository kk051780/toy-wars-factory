# #764 current69 BOMB occlusion source QA proposal

This directory makes the already frozen **+695-byte Realm BOMB proposal** reproducible against the actual private69 companion from official commit `fb5d9b693c48d4ffcce05c3f89d490593e0cecfd`. It is a local preparation for an independently reviewed source scope. It does not grant a scope, change a CLAIM, register approval, promote an RC, or prove engine acceptance.

**BOMB occlusion was not specified in the original #764 proposal.** This is a quality proposal to align BOMB with existing AoE line-of-sight policy, not a claim that the original distance-based AoE violated its written specification. The unchanged original can apply the same 46 damage through a fixture wall as through open space; the proposed difference is tested explicitly.

## Scope and original ownership

The preparation adds ten files below this `current69/` directory and appends one job to `.github/workflows/p0d-gq8-realm-core34.yml`. The entire original 7,685-byte workflow is retained as an exact prefix. Original Core34 Realm source, Controls source, composer, tests, and README stay byte-for-byte equal to PR #764 HEAD `c51de1ed4feb7a7500ada95d21282402053ef988`. Their byte lengths, SHA256 and Git blob IDs are pinned in `INPUT_LOCK.json` and checked before and after a run.

The existing Core34 job is not skipped, weakened, relabeled, or replaced. It selects a real historical31 artifact. An expired historical input can independently make that job fail. The new job's success does **not** mean the existing job or the entire hosted workflow succeeded. Restoring a genuine historical artifact is a separate coordinator operation, outside this gate.

No canonical Union22 producer, common workflow, other pitch, ControlsV2, authority, RemoteEvent, or world-balance table is changed.

## Exact source proposal

| Input | Byte length | SHA256 |
|---|---:|---|
| Original official Realm | 35,282 | `8670511af9289ed6edcff8ffc244af997da4a24fa3e8b5a57da97c6459d0235e` |
| Candidate Realm | 35,977 | `a3c9122b95694fbe14dff5bebab058b3f9c3dc05f7e5b3e8a8e5090269cb384b` |
| Exact source patch | 2,266 | `31429a1da023e93e544b1f4b5d7f1de45ef59cd461c43d71e40c298495480b06` |

The patch only changes the existing BOMB branch. One local helper checks a server Raycast from the blast origin to each target, shared by the three target loops. `RespectCanCollide=true` makes collidable walls and Terrain block the path while noncolliding decorations remain transparent to this query. A hit within the target's descendants is accepted. When the bomb's downward ray hits a surface, its normal offsets the sight origin by 0.1 studs to avoid self-occlusion on the same floor surface. The radius and visual effect stay centered at the original impact.

Radius 27, damage 46, ammunition 3, cooldown 8 seconds, own-craft exclusion, TEAM craft protection, and unchanged human health are retained. The other 68 selected source files must remain exact. Applying the same patch in reverse must restore all 69 original source bytes and the original Rojo Place bytes.

## Immutable artifact and toolchain inputs

The gate accepts only artifact `14761404772`, named `P0D-EGGRUMBLE-V3-REAL69-CANONICAL-PRIVATE-STUDIO`, from run `45041527167`, attempt 1, successful `push` at the official commit above, workflow `.github/workflows/gq8-real63-source-composite.yml`.

The original ZIP is 5,325,025 bytes with SHA256 `6e1c7cecb39b88a33f9c68b7698eaf21a178461852331c98e7583cbf47ab1793`. Provider run metadata, artifact ID, digest, size, unexpired status, and workflow lineage are checked. All 110 ZIP member names and bytes are pinned. Unsafe paths, duplicate entries, symlinks, encrypted entries, extra or missing members, and altered source bytes are rejected before an output directory is created. There is no latest-artifact fallback.

Luau is built freshly from clean commit `f46d879e28302a430029304f7f6a162aed66f103`, tree `2432c996fc9fa73680b5e2cfe172d36114fe3746`, with its exact 2,336 tracked files. A dedicated new build directory creates both `Luau.Repl.CLI` and `Luau.Compile.CLI`. The helper is an unchanged 12,479-byte prefix of the official canonical `native/run_profile.py`; its origin and excerpt hashes are locked. Existing compiler binaries cannot substitute for this fresh build.

Rojo 7.7.1 release ZIP and binary bytes are both pinned. ON and inverse OFF each compile all 69 selected scripts and build a Rojo Place. The gate checks every script's class and exact Source, all 75 instance routes and non-Source properties, and byte-exact OFF equality with the original official Place. The original artifact itself is never edited.

## Native evidence and preserved limitations

Two distinct suites run for both original and candidate sources:

1. **Unchanged original Native10+7.** The original generated program, fixture prefix, full body ranges, case suffix, and expected case vector are pinned. Each program loads the same 28 full game bodies. **Realm and LSS are absent from these 28 bodies and are not exercised by these cases.** This gate does not expand their coverage claim.
2. **BOMB13 source comparison.** The same 28-body prefix plus the complete original LSS and original/candidate Realm form 30 full game bodies, exactly once each. Actual Host role selection, READY to ACTIVE transition, LSS/Realm craft setup and the existing Remote handler dispatch the BOMB action. The gate reconstructs all 26 previously frozen program hashes exactly and requires their full stdout, individual observations, summary, exit status, and normalized stderr to match the frozen reference.

The thirteen conditions are:

| Mode | Conditions |
|---|---|
| TEAM | Solid wall, open path, neutral target self-hit, radius exactly 27 |
| BATTLE_ROYALE | Solid wall, open path, noncolliding decoration, transparent collidable wall, Terrain fixture, below floor, fighter target self-hit, LSS target self-hit, outside radius with exact cooldown/ammunition boundaries |

The frozen comparison oracle expects original **5 green / 8 exact source-acceptance RED** runs, totaling 164 passing and 16 failing observations; candidate **13 green** runs, 180/180 observations. Those numbers are acceptance expectations, not a claim that this newly prepared hosted job has run. Three original target-self-hit REDs concern absence of the newly proposed query, and do not establish separate damage defects. A boot failure, unrelated exception, missing output, extra output, malformed observation, wrong exit, or changed failure reason cannot count as the expected RED.

`bomb_cases_original12.luau` is the exact first accepted 12-condition file. Its historical OUTSIDE_RADIUS branch used fractional repeated clock increments; one elapsed interval became `7.9999999999999858`, correctly below the game threshold. That branch is not used as a success case. Only OUTSIDE_RADIUS uses `bomb_cases_exact_clock.luau`, the separately frozen case with an integer first-fire clock and exact offsets 7.99, 8, 16 and 24 seconds. Fixture and case files are retained byte-for-byte, and the gate enforces this selection. No game numeric policy was relaxed.

Instances, signals, CFrame, clock and AABB intersections are Native fixtures. The Terrain case maps an intersected fixture wall to a Terrain instance; it does not prove Roblox voxel behavior. Movement, collision, network ownership, latency, streaming, touch/gamepad controls, Android performance, real combat feel, and a live complete match remain untested here. Studio/Android remain `NOT_TESTED`, fun acceptance remains `NO_GO`, and formal RC adoption/registered approval remain false.

## Run and inspect

The added workflow job downloads the exact provider inputs, runs `test_gate.py`, then `gate.py` with `GITHUB_NONCANONICAL_QA`. Hosted execution checks checkout HEAD against `GITHUB_SHA` and requires all eleven scope files to be exact blobs from that HEAD. It verifies those bytes and the execution context again after the build and suites. Push, pull request and workflow dispatch are allowed; local mode cannot be claimed inside GitHub Actions.

For a local reproduction, use the same three provider input files, fixed release ZIP and clean Luau Git source. Invoke these scripts with `python3 -B`:

```sh
python3 -B handoffs/EGGRUMBLE-REALM-CORE-20261118/current69/test_gate.py \
  --artifact-zip /absolute/input/official69.zip \
  --run-metadata /absolute/input/run.json \
  --artifact-metadata /absolute/input/artifacts.json

python3 -B handoffs/EGGRUMBLE-REALM-CORE-20261118/current69/gate.py \
  --artifact-zip /absolute/input/official69.zip \
  --run-metadata /absolute/input/run.json \
  --artifact-metadata /absolute/input/artifacts.json \
  --luau-source /absolute/input/clean-luau-f46 \
  --rojo-zip /absolute/input/rojo-7.7.1.zip \
  --out /absolute/new-output \
  --context LOCAL_NONCANONICAL
```

If CMake is installed through a launcher, pass `--cmake` with the actual CMake executable that appears in `CMakeCache.txt`; the helper deliberately requires exact identity. Ninja, Git, C and C++ compiler paths can also be explicit. A preexisting, overlapping or symlinked output is rejected.

The receipt records 138 compile invocations, two actual Place builds, four unchanged canonical Native runs, 26 BOMB Native runs, source/class checks, actual inverse, fresh toolchain evidence, source scope snapshots, and separate hosted/local status. Raw process stdout/stderr, generated programs and body ranges are retained. A local receipt remains local evidence; same-HEAD hosted success and scope/controller authorization are separate requirements.
