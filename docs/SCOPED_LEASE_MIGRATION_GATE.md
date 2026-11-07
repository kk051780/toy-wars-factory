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
