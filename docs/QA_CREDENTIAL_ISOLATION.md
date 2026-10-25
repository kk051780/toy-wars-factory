# QA credential isolation — prerequisite of Studio Autopilot P2

Existing bootstrap offline QA must not leak repository read credentials to code coming from an unreviewed pull request. This is independent from the withheld P2 authenticated evidence workflow.

The change: checkout always uses persist-credentials: false. GH_TOKEN is available only when installing pinned gh-aw compiler and when the isolated native Git fetch obtains the coordinator ref. The PR-provided `gh aw compile`, `tools/verify_gemini_hold.py`, Python/Lua tests and installer build run without any GH_TOKEN/GITHUB_TOKEN environment explicitly passed by the workflow.

The coordinator scope verification continues to execute trusted-base repair_control.py; the fetch uses the token only within a dedicated step, never writes it to .git/config. The generated files and release/Gemini hold checks remain active.

Limitations: GitHub Actions jobs can have implicit runner credentials, and a privileged actor can modify an unprotected private main workflow. This change reduces explicit credential exposure to PR code but is not an enforcement of private branch protection. P2 actual authenticated automation remains disabled pending authorized provider-enforced rules and independent source review.

Regressions: `python3 -m unittest discover -s tests -p 'test_ci_token_isolation.py' -v`; required main QA and independent review must pass for exact head.

## HTTP authentication correction after independent audit

The coordinator fetch now uses the official checkout-compatible Basic header
with a transient base64-encoded `x-access-token:<token>` user/password pair.
It is set via a per-command Git `-c http.https://github.com/.extraheader`
option, never a persisted configuration key. The temporary shell variable is
unset afterward and interactive prompts are disabled. No PR-controlled Python
receives that token. The earlier bearer form was not accepted as verified.

The current PR's branch does not trigger the auto-repair-only fetch condition;
the real auto-repair integration path needs separate observed CI proof. Offline
static regression success alone is not live network authentication evidence.

## Follow-up: fully separate untrusted test job from authenticated workflows

The prior PR auditor correctly rejected two remaining credentials paths. The
`pull_request` QA now **never mentions github.token or GH_TOKEN**. Its gh-aw
compiler is a SHA256-pinned, public v0.93.2 linux-amd64 release binary; no
GitHub credentials are provided to compiler installation or compilation.

Private coordinator state is now read exclusively by
`.github/workflows/trusted-coordinator-claim.yml` using `pull_request_target`.
That workflow is sourced from trusted **target main**, checks out only the
target main SHA, fetches PR HEAD only as Git *data*, never executes it, and
runs the coordinator claim validator from the BASE SHA with read-only token.
Factual success must be confirmed on an actual `auto/twf-game-repair-...` or
`auto/twf-system-review-...` PR after merging this feature; until then it is
not verified. The independent reviewer must require both trusted_claim and
ordinary offline/compile_hold exact-head checks for automatic repair PRs.

Important: `pull_request_target` gives access to base-repo privileges. Never
check out and execute PR code in that workflow, and do not add privileged
write operations. The private default branch is still not provider-protected
on GitHub Free; this boundary remains a blocker for P2 credentials/dispatch.
