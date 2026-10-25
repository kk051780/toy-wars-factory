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
