# Scheduled reviewer replacement — guarded exact-time deployment
Date: 2026-10-25

**Problem:** existing flexible-schedule REVIEWER `6add4ea80d3881919da4ea2c1d5def88` repeatedly returned `no_update` without chat_ref/observable activity; the daily META also returned `no_update`. This is an observation, not a proven root cause.

**Independent bootstraps:** a short exact-time read-only diagnostic `6add69aaccd08191bbf511db2ac30a96` completed and read private GitHub; the longer exact-time reviewer candidate `6add6aaceb4c8191b1666fe15f97cd88` completed read-only run `83fae721-db38-832f-b6bc-b0274091c1ce` with a structured report. No merge, no write, no Roblox engine proof.

## Fail-closed rollout — one registered reviewer, never two

1. Confirm the candidate task is disabled and the old reviewer is not running, then pause the old reviewer. Do not pause the WORKER or META.
2. Verify this PR's exact-head offline/compile_hold CI and its diff. Integrate through a separate CONTROLLER lease; author may not self-approve.
3. While holding that same lease, update ONLY `authorized_tasks.REVIEWER` on the shared `twf-repair-coordinator` ref from the old task ID to `6add6aaceb4c8191b1666fe15f97cd88`, using expected-sha/force=false. Keep WORKER/META unchanged. Before any new REVIEWER writes, confirm current main config and coordinator IDs match.
4. Update the candidate's *live scheduled task prompt* to the repository's full reviewer prompt, including the current strict role/lock/head/CI/QA clauses. Set exact-time hourly cadence, enable the new task only after verifying the GitHub registration. Retire the old task while its authorizations are revoked.
5. Execute a bounded test: read the candidate run ID, confirm it claimed a REVIEWER lease with new registered task, reviewed a currently open worker PR, and either produced a concrete WAIT/REPAIR record or integrated a PR under the same exact-head rules. One successful read-only bootstrap **does not** complete this test. Do not count A08 (autonomous review/main integration) as verified until post-merge main QA passes.
6. If a step fails, keep both reviewers unable to write, record the blocker, safely release controller, and only retry after fixing the specific error. No action may bypass CI, independent author/reviewer identity, budgets, or Roblox release HOLD.

Preserve historical reviewer ID in append-only completed history and earlier evidence. Only current configuration, live state pointers and saved prompt change in this PR. It does NOT activate external Gemini/Copilot inference or publish Roblox.

This PR proposes configuration change; applying the live Automations task and shared ref cutover is a separate tracked operational step.