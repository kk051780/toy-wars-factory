# Trusted-system module maintenance candidate (Issue #72)

This PR is a trust-root policy change, authored by a fenced CONTROLLER, **not
a regular META-approved modification**. It cannot be approved by its author
or by passing its own untrusted checker.

## Admission
The trusted base checker may accept M on `tools/system_[A-Za-z0-9_]+.py`
only when the module is a 100644 ordinary Git blob already present in the
**trusted ancestor of origin/main** (commit ancestry checked, with no fallback
to PR-provided policy or author claims). A symlink, file solely on the PR
branch, traversal-like path, rename, deletion or other tool is rejected.

Any such maintenance PR **also** needs a brand-new
`tests/test_system_*.py` and a brand-new `history/Cxxxxx_*.json`.
Existing accepted regressions and history records are never modified.
Real claim task/run/branch/epoch/CI checks remain enforced separately through
the base-sourced `repair_control.py verify-pr` in bootstrap-quality.yml.
The reviewer remains separate, release and Gemini spending HOLD stay in place.

## Trust-root rollout
1. Examine the source / deny-case regressions in PR using exact head.
2. Confirm the test remains red when trusted base has no module or path is a
   symlink or malicious descendant, plus hundreds of status/path denials.
3. Obtain a **separate read-only trust-root audit** for this protected checker
   modification and an independent integration authorization with exact
   main/PR head, no author self-merge.
4. Only after trusted main has adopted this rule may a registered META author
   edit existing system_host_write_triage.py with a fresh regression, new
   history, exact-head CI and independent REVIEWER integration.
5. Verify legacy standalone CLI actually rejects failed/no_update. Do not
   call this issue complete until the CLI repair is merged and main QA passes.

This candidate does not add any new secrets, budgets, scheduler permissions,
automatic publisher, OAuth scopes, or tool paths beyond exact preexisting
`tools/system_*.py` implementation code.
