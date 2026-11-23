# P0D033 persistent-base admission dependency

This is an **unattached server dependency candidate**, within the existing
`P0D-GQ033-MATCH-GROWTH-20261123-817BC984` claim and its separate root03 partition.
It does not install a Host, alter the selected 69 scripts, create a Place, grant
XP, save profiles, or make the current V3 game use persistent levels.

## Purpose and immutable inputs

The accepted growth direction needs the confirmed persistent level at match
entry. A delayed read must not replace an admitted starting level, cross into
another round or rejoin, or turn an old value into a successful new read after
a failure. This module separates account reads from a single current admission
and freezes the values admitted by the authoritative Host.

`prepare_bridge.py` reads the exact H72 official ZIP and H84 donor ZIP pinned in
`source_lock.json`. It validates all 69 current Source bodies against project
selections, exact Instance routes, classes, Place and delivery records. It copies
six original ModuleScript bodies without changing a byte, then adds
`EGGRUMBLE_PersistentBaseAdmission`. The seven output files live in the new
`EGGRUMBLE_PersistentBaseSupport/` namespace. There is no generated project or
automatic runtime attachment. Rollback removes only these nine new repository
files and their independent generated output.

## Host contract

The future Host constructs the component with
`new({store, readOptions?, eligible(player, fullUserId), member(player, round)})`.
It supplies the original development namespace read handle. The component never
obtains or wraps a DataStore. Its only donor calls are the unchanged
`PersistentHatchStore.load` and `toProgressProfile`.

Both trusted callbacks must be synchronous and non-yielding. `eligible` checks
genuine Studio, the concrete current Player and its positive full UserId.
`member` checks the actual current Host session, concrete participant and actual
ACTIVE Rules phase. FINISHED/ABANDONED must return false immediately. A false,
non-boolean or thrown result rejects the operation. Native fixtures do not
authenticate these real-environment predicates.

| Method | Boundary |
|---|---|
| `bind(player)` | Opaque account token; current binding is idempotent. Remove followed by bind creates a new token even for the same Instance. |
| `read(account)` | Only yielding method; at most two reads per account. Latest accepted generation wins. Each returned completion releases its own old-account slot once. |
| `peek(account)` | Current confirmed read, or current failure/pending/unloaded code. No fallback to an old successful value after a new failed read. |
| `admit(account, round, admission)` | Clone and freeze one confirmed snapshot. The same current triple returns it during later pending/failed/successful reads. |
| `get(account, round, admission)` | Check current Player, exact triple and current ACTIVE membership, then return the fixed snapshot. |
| `endAdmission(account, round, admission)` | End only the exact admission. Cleanup does not require eligibility or membership to remain true. |
| `remove(account)` | Permanently invalidate the old account token and synchronously clear component-owned Player/profile/round references. Late reads cannot touch a fresh account. |

Data methods return `value, "OK"` or `nil, code`; cleanup returns `true, "OK"`
or `false, code`. Snapshot fields are `{userId, revision, level, xp, equipped,
mastery}`. `userId` is the full ID, `xp` is within-level XP, and `mastery` is item
mastery, not role/B/KO progression. Revision is a safe integer from 0 through
9007199254740991. Smaller revisions are rejected; the same revision with changed
public values or mastery leaves is rejected. Equal values in different tables
or insertion orders are valid.

The original Store normalizes raw `nil` and an equivalent stored blank to the
same successful result. This adapter does not expose raw-record existence or
claim `SAVED`. A successful normalized Lv1 read is distinct from an unloaded
account or failed read.

Codes: `OK`, `INVALID_ARGUMENT`, `INELIGIBLE`, `STALE_ACCOUNT`, `NOT_LOADED`,
`READ_PENDING`, `READ_BUSY`, `STALE_READ`, `INVALID_STORE_OR_PLAYER`, `READ_FAILED`,
`CORRUPT_RECORD`, `INVALID_PROFILE`, `DONOR_ERROR`, `REVISION_REGRESSION`,
`REVISION_CONFLICT`, `ADMISSION_CONFLICT`, `STALE_ADMISSION`.

## Future Host ordering, outside this support scope

H72 creates the roster while Rules are LOBBY. A later scoped integration must
admit after `Rules.start` and world binding, before publishing ACTIVE or starting
runtime tasks, in a non-yielding section. FINISHED immediately makes membership
false, including during the delayed result screen. closeRound must unbind/retire
the round and end all admissions before yielding cleanup. PlayerRemoving must
remove the account and clear the Host's joined entry before yielding or allowing
another bind. Ordinary respawn retains the existing admission.

The component creates no timer, task, retry queue, second readiness authority,
permanent retired-token history or Store write path. It cannot cancel an already
yielding GetAsync; the Host must not abandon live read coroutines and must call
remove at account lifetime end. Public snapshots are immutable copies. Clearing
component references does not promise to clear external Host stacks or force GC.

## Reproduction and evidence

The dedicated push workflow on
`quality/gq470-persistent-base-support-03a0fba0-20261123` downloads the exact two
artifacts and verifies successful source runs, metadata digest and ZIP identity.
It runs 11 artifact/path refusal tests in normal and optimized Python, builds
clean pinned F46 Luau source, compiles seven full modules plus the Native program,
then executes 14 cases / 92 ordered checks / 42 GetAsync calls / zero saving
writes. It binds the clean nine-file Git HEAD before and after execution.

The unchanged H72 build helper is a hashed capsule in `native/INPUT_LOCK.json`.
Later shared-helper edits cannot silently replace this build recipe. The runner
pins the lock and compares every file with actual Git HEAD, including itself
and the lock. The lock does not try to contain its own hash.

```sh
export P0D033_OFFICIAL_ZIP=/absolute/path/to/H72.zip
export P0D033_DONOR_ZIP=/absolute/path/to/H84.zip
python3 -B tests/test_gq470_persistent_base_bridge_20261123.py -v
python3 -B -O tests/test_gq470_persistent_base_bridge_20261123.py -v
python3 -B quality_gameplay/gq470_persistent_base_bridge_20261123/prepare_bridge.py \
  --official-zip "$P0D033_OFFICIAL_ZIP" --donor-zip "$P0D033_DONOR_ZIP" \
  --output /absolute/new/output-directory
```

Unittest discovery with both artifact variables absent reports a specific
`NOT_RUN` skip. Direct execution with absent/empty/partial inputs fails. The
dedicated gate requires all 11 tests and zero skips. Explicit runner options
`--debug-runtime` and `--debug-compiler` report only `PASS_AUTHOR_DEBUG`; CI
requires a fresh source build and rejects that status.

## Authority and remaining integration

Scope was registered at `b1bb1e71f4d15e65f77fb17e3e2f94e9f9411560`, after independent
metadata review. Actual readback and metadata696 normal release are bound in
[issue218](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7093854719).
The sole support author/publisher is `CODEX_ROOT_03A0FBA0D83E:/root`; its registered
nonauthor reviewer is `CODEX_ROOT_03A0FBA0D83E:/root/integration_authority`.
Original 817 S1A paths, authorship and PR1028 remain separate.

A passing Native gate is component evidence. Registered nonauthor review of the
published HEAD, actual paths and actual CI artifact is still required before
**DEPENDENCY_SOURCE_READY**. This package does not declare gameplay PREP_READY,
S1 completion, RC adoption, actual DataStore success, Studio, multiplayer,
Android, ART, FUN or owner acceptance. Later Host integration needs its own
exact scope and fresh official RC input.
