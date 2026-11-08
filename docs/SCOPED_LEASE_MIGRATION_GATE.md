# P0: Legacy coordinator / scoped-lease migration barrier

Issue #123 · 2026-11-08 JST

## Confirmed incompatibility

The previously deployed exclusive coordinator's `tools/repair_control.py:acquire` only checked `state["holder"]`. The prototype `tools/system_parallel_shadow_leases.py` registers future scoped workers while that holder is null. **Without migration fencing, a legacy WORKER/CONTROLLER/REVIEWER could concurrently claim the same coordinator and write to otherwise overlapping resources.**

This independent root PR adds a conservative read of `shadow_parallel_leases`, `parallel_leases`, and the explicit `parallel_write_migration` marker in the *existing* `acquire` path. A non-empty valid scoped registry or marker `SCOPED_ACTIVE` returns `WAIT_SCOPED_LEASES`, `write=false` for every legacy role; malformed registry or marker fails closed. Even expired scoped entries keep the legacy lane blocked, pending authorized service evidence and CAS recovery. A current legitimate legacy holder is still allowed to release its own existing lock.

## Safe rollout order

1. Independently review this small PR; verify its exact HEAD, original GitHub CI and main protected branch rules. **No activation on PR creation**.
2. Integrate the legacy migration guard into protected main via the proper independent-review lane; obtain post-main QA and identify all existing long-running runners/checkouts.
3. Ensure every writer and reviewer is using the guarded version and check actual GitHub refs/actor run identities; disable/drain older unchecked revisions before any registry activation. **This source guard cannot fence a process that continues running old code.**
4. Review and integrate the dependent #173 → #174 → #200 → #201 → #202 candidates through formal gates. Check compatibility with main again and re-run exact-head CI if parents change.
5. Only when the genuinely provider-attested, least-privilege v2 CAS adapter is reviewed and proven, migrate to short atomic scoped claims and run two distinct authenticated nonoverlapping writers with independent CI/review. Do not infer actual parallelism from fake-host or a single GPT sending two CAS calls.

The current shadow registries are still non-authorizing. This guard is an **upgrade prerequisite, not a license to turn on 2-writer writes**. Do not change the current coordinator JSON to SCOPED_ACTIVE, add live entries or bypass host denial from Issue #57. No main direct write, paid models, Gemini activation, or Roblox publication.

## Integration decision also requires the migration barrier

A separate code inspection discovered that accepted-main `tools/repair_integration.py:decide` can return `MERGE` for a valid old REVIEWER holder without checking scoped-registry occupancy. During migration an inconsistent mixed legacy and scoped state must **never** pass the integration gate. The same `scoped_lease_migration_block(lease)` preflight now runs inside `decide` before the review/merge decision. On occupied scoped rows or `SCOPED_ACTIVE`, it yields `WAIT_SCOPED_LEASES`. Malformed registry/migration mode yields `WAIT_LOCK`, not `MERGE` or an unchecked exception. Nine dedicated negative tests, including an otherwise-mergeable review and an expired scoped row, are added in `tests/test_legacy_scoped_integration_gate.py`.

This still cannot prevent **old, unpatched production processes** from running pre-upgrade code. Neither the migration guard nor this follow-on merge gate authorizes normal PR #203 self-approval or main integration. Enabling v2 before all old runners are drained remains forbidden.

## Legacy owns() and owner-only finally cleanup (P0, follow-up)

A third path bypassed acquisition/integration fencing: accepted-main
`repair_control.owns` checked only a legacy holder tuple and expiry.
Callers could misinterpret that truthy response as authorization to write
while a v2 scoped writer already existed. The candidate implementation
now returns **false for all legacy write-role checks** whenever a scoped
entry or SCOPED_ACTIVE migration marker exists; malformed registries raise
rather than grant write rights. This must be deployed to *every* host
before scoped v2 activation, and its return value is **still not external
provider attestation**.

An already-verified existing owner must retain the ability to release
*only its own legacy holder* without deleting scoped entries. The internal
`owned_lease` finally path therefore separately verifies the exact owner,
epoch, authorized task and live original run against two unchanged GitHub
snapshots before one nonforced expected-SHA cleanup CAS. This exceptional
cleanup bypasses only scoped **occupancy**, not scoped schema validity;
invalid scoped data or changed owner/epoch aborts cleanup and reports
the situation rather than writing a false release receipt. It never grants
new gameplay or merge writes.

This change is tested in `tests/test_legacy_scoped_owner_cleanup.py`.
It does not solve a process still running pre-upgrade code, or a genuine
lost ChatGPT run with no authenticated service-completion evidence.


## Sourcery external audit: remaining critical atomic admission and merger gap

The external review of exact PR HEAD \`1d2f3a4c…\` reported **2 High + 2 Medium** issues. This follow-on patch addresses the legacy \`verify_pr\` historical authorization gap by checking **current coordinator snapshot, claim and parent** for scoped entries/SCOPED_ACTIVE, changes malformed timestamps and non-object coordinator to a handled \`ValueError\`, and repairs an expired-row test fixture that previously never reached an expired state.

**Remaining unresolved HIGH: stale decision / time-of-check vs time-of-use.** A Python \`acquire\`, \`owns\`, \`verify_pr\` or \`repair_integration.decide\` preflight cannot atomically authorize a *later* branch update or main merge against another GPT's live scoped claim. A genuine v2 writer and merge host must serialize the **actual write/merge action** with a single coordinator CAS/fence generation, require exact actor/task/branch/write-set/head identity and reject after an intervening coordinator ref update. Claiming scoped v2 after a released legacy slot must not race with old-inflight writes. Every legacy old-code process must first be stopped/drained and upgraded. During migration the only permitted live mode stays exclusive v1. **Never infer this HIGH issue is fixed from green CI or the review tool's check conclusion.**

Historical verification is not a live write permit. The hosted test harness can verify local deny decisions, not provider-verified concurrent GPT runs, active-run termination or crash recovery. A separate authenticated reviewer is still required before protected main integration. No authorization to turn on scoped v2 is granted here.
