# P2 — Verified-source GitHub metadata adapter

Studio Autopilot P1 accepts JSON observations only as untrusted diagnostics. P2 reads GitHub API directly with an ephemeral repository-scoped token. It still cannot dispatch, merge, publish, pay for models, or prove Roblox engine/player quality.

## Live evidence source

- A single project manifest selects repository, task IDs, and coordinator ref. The client is fixed to https://api.github.com/repos/OWNER/REPO/ and only performs GET requests. Redirects are blocked.
- Read exact main SHA, current check-runs and coordinator ref. Retrieve coordinator state at its immutable commit SHA. Task IDs must match author/reviewer/meta registered for the game.
- A numbered PR read checks head and base repo identities (forks are not yet allowed), exact head CI and stale-base status. Re-read main/ref/PR to catch concurrent mutations. Failure or data ambiguity stops the reader.
- Required checks are offline + compile_hold with completed/success and matching SHA. Missing, incomplete/ambiguous, stale or duplicated data cannot be promoted to a PASS.
- Even if observed fields PASS, execution.dispatch_allowed, merge_allowed, publish_allowed, spending_allowed are always false. This is a fact report, not authorization.

## GitHub Actions proof

The new workflow at .github/workflows/studio-autopilot-evidence.yml runs ONLY on push to main after separately reviewed merge. Its GITHUB_TOKEN has explicitly read-only contents/checks/pull-requests/actions read access; checkout persists no credentials. The nonsecret JSON artifact demonstrates that GitHub was actually accessed.

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
