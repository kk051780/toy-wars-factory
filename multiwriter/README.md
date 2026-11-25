# P0D MULTI-WRITER SCOPED CAS — candidate V1 (2026-11-15)

OWNER direction supersedes the throughput bottleneck of the **single official RC writer**, but does **not** grant an unauthenticated chat, Actions job or unknown actor unrestricted RC access. This is an isolated read-only prototype; no main/RC changes and **zero production writer grants**.

## New parallel workflow

1. #218 claim ledger + #469 existing duplicate-work guard remain canonical for unique FEATURE_ID, author, affected real paths and aliases. #470 Product Quality owns the closed loop `FAIL → original A author code FIX → VERIFIED candidate → official RC CAS → real Studio/Android/competitor retest → OWNER_ACCEPTED`. Never close an FB because a checker or static CI is green.
2. Multiple authenticated and explicitly scoped writers independently prepare separate **complete official-RC candidates** and run full Luau/Rojo, source-exact, authority, critical Sourcery, rollback and product evidence tests.
3. Trust source: separately protected coordinator registry with distinct `GRANTED` actor/paths/exclusive_groups/expiry. The example registry contains no grants. Neither self-authored PR metadata nor this script may mint a writer grant.
4. Shared original Game, HP, round, Remote, egg, score, Store, HUD authority requires an exclusive group. Unrelated paths are parallel; duplicate feature IDs, overlapping paths or logical authorities are blocked.
5. Official ref is updated by each eligible authenticated writer through **nonforce expected-HEAD atomic CAS** of the exact tested proposed commit (not a stale patch onto newer RC). After a losing race, compare original/current Git blobs: conflict → HOLD; no conflict → rebuild the full candidate from the newest RC and **rerun all tests on the new proposed commit SHA** before retrying. No force or blind regular merge.
6. SameHEAD official readback/CI/Place and ZIP bytes plus rollback receipt are mandatory after each commit. SOURCE_PASS is not owner FUN, art, Android or competitive quality acceptance.

## Implementation boundaries

`multiwriter/guard.py` is deterministic, read-only and fail-closed; it checks proofs supplied **only after** authenticated workflow API fetching. `multiwriter/test_guard.py` covers 27 authorized/negative/race cases. `TRUSTED_REGISTRY_TEMPLATE.json` intentionally denies all writers.

Run `python -m unittest discover -s multiwriter -p test_guard.py -v`. The accompanying workflow is **read-only candidate test execution**, not deployment or branch permission changes.

### Activation is not yet complete

Do not call this an active multiwriter policy until: (a) #219/#218 scoped grant ownership mapped to protected registry with the authorized GitHub actors; (b) real GitHub branch protection and required CI statuses verified; (c) independent reviewer approves authority/path logic and trust of GitHub-sourced current ref, file blobs and CI; (d) two **controlled private** disjoint writer attempts demonstrate nonforce CAS, losing-writer stale rejection, new full source test, readback, and rollback receipts. Automated push requires an independently approved credential/scope setup. Existing #220 writer-only branch protection remains effective in the interim; merely authoring this PR does not change it.

Existing #469 claim guard, #471 product-quality report, #472 competitor observation, game Luau, active RC, main, monetization, Roblox publication, Windows and all existing Automation schedules are not edited.
