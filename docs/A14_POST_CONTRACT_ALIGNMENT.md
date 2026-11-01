# A14 — Roblox Cloud Luau POST / CAS contract alignment (protected draft)

This candidate is an **offline compatibility checker and mock-only POST transport**. It is not a deployable webhook, does not read credentials from the environment, never opens a network connection in CI, and cannot grant provider authorization from caller-controlled JSON.

## What is new

- `tools/twf_roblox_task_post_once.py`: fixed 30-second-script Cloud v2 Luau task-creation request generator. The POST transport requires an explicitly supplied opener, API key and per-process `LocalIntentFence`. It sends no traffic just by importing it, and has no unattended command-line entrypoint. A supplied fake transport can be used for tests. Neither opener nor simulated HTTP response is provider authentication. Per-process deduplication is **not distributed deduplication**.
- `tools/twf_a14_post_cas_contract.py`: **pure no-network** comparison of the unmerged PR #158 reservation proposal/readback shape, PR #175's pinned source/artifact/version plan, and the fixed POST request. No direct imports from those unmerged PRs. Matches the exact canonical PR #158 fingerprint logic, but does not itself reserve any intent or authorize POST.
- 73 offline Python test methods across four new `test_twf_*` files, and a pinned byte-identical Luau fixture `fixtures/twf_open_cloud_smoke.luau` from PR #175, SHA256 `fc343ede29c2466b0962689b183b5320d81122a807d65ad7f82e942a9268759d`.

## Running independently

`python3 -m unittest discover -s tests -p 'test_twf_*.py' -v`

The GitHub base offline workflow also discovers `test_*.py` tests. It does **not** run Roblox Studio or authenticated Roblox Cloud operations. No API token is included or used in these tests.

## Security holds (never bypass)

1. PR #158 is unmerged and has **two independently reported source defects**: an old caller-supplied clock can survive long CAS operations, and a one-parent commit does not prove its changed-file scope. Original PR #158 maintainer / independent security review must resolve both before trusted usage. A successful fixture matching the old schema does **not** constitute authentic GitHub CAS or authorization.
2. The CAS adapter's `post_authorized=False` / `may_post=False` and the POST transport's hard-coded `engine_verified=False` are intentional. No code here should be used by automated worker tasks or given a production API key. Cross-host dedup requires a legitimate external CAS host bound to original provider refs and unique owned intent; `LocalIntentFence` only guards concurrent objects in the **same process**.
3. A real, owner-controlled **private** Roblox Universe/Place, exact Saved version, independently authenticated scoped key and immutable reviewed source/artifact are not yet available. A mere matching path, fixture or API-shaped JSON is not provider evidence.
4. GitHub private repository branch protection / independent manual `controller/*` review remain separate trust-root blockers: Issue #59 / PR #60. Do not self-approve, merge, publish, spend, run external inference or switch the repository public.

## Original upstream sources, no edits to them

- PR #158: `tools/cloud_global_intent_fence.py`, original head `bb0ae321afa7f0d35d6ac7e69d5f5fdee04e69bc`
- PR #175: `tools/open_cloud_engine_preflight.py` and `tools/twf_open_cloud_smoke.luau`, original head `4222ac0d0c9e76c21f5f9fee44af8fb1edd1d2ac`
- Parent issue: #151, initial real main `e5deff4d5681bca4823a3da0f848e01bc089ae6e`.

**This standalone draft is a candidate for later independently reviewed assembly; it does not imply the unmerged parent PRs have been adopted into main.**
