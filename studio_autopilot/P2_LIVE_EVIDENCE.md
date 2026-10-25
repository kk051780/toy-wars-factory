# P2 — Verified-source GitHub metadata adapter

Studio Autopilot P1 accepts JSON observations only as untrusted diagnostics. P2 reads GitHub API directly with an ephemeral repository-scoped token. It still cannot dispatch, merge, publish, pay for models, or prove Roblox engine/player quality.

## Live evidence source

- A single project manifest selects repository, task IDs, and coordinator ref. The client is fixed to https://api.github.com/repos/OWNER/REPO/ and only performs GET requests. Redirects are blocked.
- Read exact main SHA, current check-runs and coordinator ref. Retrieve coordinator state at its immutable commit SHA. Task IDs must match author/reviewer/meta registered for the game.
- A numbered PR read checks head and base repo identities (forks are not yet allowed), exact head CI and stale-base status. Re-read main/ref/PR to catch concurrent mutations. Failure or data ambiguity stops the reader.
- Required checks are offline + compile_hold with completed/success and matching SHA. Missing, incomplete/ambiguous, stale or duplicated data cannot be promoted to a PASS.
- Even if observed fields PASS, execution.dispatch_allowed, merge_allowed, publish_allowed, spending_allowed are always false. This is a fact report, not authorization.

## GitHub Actions proof

The earlier GitHub Actions prototype was withdrawn before integration: the private main branch is not protected, so no P2-specific credentialed workflow will be installed. Source and offline evidence checks remain available, but a secure post-merge authenticated run is NOT yet established.

To collect metadata in an authorized GitHub Actions run, execute python3 -m studio_autopilot.github_evidence (no PR number needed for trusted main). The CLI requires GITHUB_TOKEN and GITHUB_REPOSITORY matching the manifest. An unbound game or foreign repo fails closed.

## Known limitations

- A generated status-only main commit may have no QA on its own SHA. The adapter reports HOLD_EXACT_HEAD_CHECKS rather than asserting prior QA applies.
- GitHub PR-triggered workflow checks can be associated with a synthetic merge commit rather than the head SHA. This adapter never silently promotes them.
- CI mocks prove negative controls, not Roblox runtime; workflow run artifact is needed to prove live GitHub access.
- A real future multi-game executor still needs per-game app installations, CAS lease, data isolation and explicitly scoped permissions.

Primary official references: https://docs.github.com/en/rest/checks/runs and https://docs.github.com/en/rest/pulls/pulls.

## Hardening after independent audit

An early PR-triggered proof (run 40163275777) read live data successfully but exposed a read-scoped token to unreviewed PR code. That first mechanism has been replaced: **the authenticated workflow runs only on main after an independently approved merge** and checks out its exact push SHA. No PR code receives a token in this workflow. GitHub Actions checks must have the pinned official App ID/slug and their details URLs must resolve to live Actions runs with the configured, reviewable workflow path, matching SHA and check suite. The trusted workflow origin is a per-project manifest property, not hardcoded to Toy Wars in the adapter. The original PR execution is historical evidence only, not accepted secure deployment.

## Check-run-to-job authenticity gate

The adapter now verifies each check-run ID against an actual Actions job API response. The job must belong to the checked run, have exactly the expected job name, source SHA, success status and check-run URL. A correct workflow URL with a nonexistent, foreign or misleading job ID cannot establish a PASS. The workflow's numeric ID is pinned per project manifest alongside its path and GitHub Actions App ID. No live snapshot authorizes dispatch.

## Audit-hardening follow-up: workflow content and event authority

For `offline` and `compile_hold` to be accepted, the QA workflow file at the
**exact checked commit** must have the independently reviewed Git blob SHA
recorded in the trusted project's `ci_provenance.workflow_blob_sha`. A new PR
that changes `.github/workflows/bootstrap-quality.yml` cannot use successful
checks created by the altered workflow as proof of the original QA contract.

PR checks must have event `pull_request`; current-main checks must have event
`push`. A PR-triggered success is not post-merge main QA.

The trust pin is reviewed baseline configuration and must **never** be supplied
from the unreviewed PR that it attempts to evaluate. This is a diagnostic
hardening step only; repository rulesets/branch protection and independent
review must still protect updates to both the manifest and QA workflow.
The current evidence API continues to return dispatch/merge/release = false.

## 2026-10-25 trust-boundary hold for private GitHub Free

The candidate PR can modify its manifest and its QA workflow simultaneously.
The read-only collector now compares the candidate declared workflow digest
against the Git blob on the separately observed target-main SHA before
accepting any PR QA. A double modification aborts the entire snapshot.

This is **not** equivalent to enforcing server-side main protection.
Unreviewed changes pushed directly by a privileged actor could still alter
main and the source used to interpret it. The credentialed workflow file
was intentionally omitted from the PR, and no new task executes this reader.

For a private repository, GitHub Pro/Team is required for enforced branch
protection/rulesets. Upgrading or making this commercial code public is
not authorized. After the owner explicitly approves a plan change, enforce
independent PR review, required checks, no unauthorized bypass, and confirm
the repository settings from an admin account before installing a separately
reviewed credentials workflow. Until then, P2 remains offline/advisory only.

Even if every metadata check returns PASS, dispatch, merge, spending and
Roblox publication remain false. The old authenticated PR demo is not
secure post-merge proof.
