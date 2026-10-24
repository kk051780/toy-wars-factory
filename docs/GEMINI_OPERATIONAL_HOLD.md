# Isolated Gemini stop and continuity correction — draft against main

This proposal can be reviewed directly against main. It contains the operational
stop from PR #24 and the continuity correction from PR #19, without the budget
runtime, proxy overlay, pricing profiles, tokenizer tooling or Docker candidates
from the stacked experimental branches. No game source or character changes.

## Behavior after a reviewed merge

- Gemini trial frontmatter contains literal `if: ${{ false }}`. Official gh-aw
  v0.93.2 generates `if: false` before pre-activation and `&& (false)` on activation.
  Updating the consumed approval marker or setting environment flags cannot
  release these conditions. No workflow dispatch or recurring AI trigger is added.
- The old reviewer direct HTTP implementation is removed. `scan_online` always
  rejects. The CLI's `--online` mode exits 2 (BLOCKED) before reading patch content,
  a provider credential or selecting transport. There is no environment unlock.
- Every scanner CLI attempt invalidates stale success and temporary verdict
  files. If cleanup fails, the attempt fails. Static offline PASS never emits
  or retains an independent-model approval. Verdict schema tests remain pure.
- Handoff generation preserves the checkpoint, approval scope and unmerged PR
  attribution. Full Git history prevents status-only commits being mistaken for
  new source work. A genuine shallow clone is rejected until unshallowed.

The independent-review requirement is retained: the held reviewer cannot produce
the model approval needed by safe outputs. Removing its unreserved HTTP code is
an intentional security reduction, not a reduction of gameplay or review gates.

## Validation required for this independent branch

The Python suite has 43 tests, including ten operational hold cases and four real
Git-history continuity cases. Native Lua parsing, 37 balance assertions, 4,000
stress cases, exact installer embedding/hashes and deterministic handoff remain
required. Official compiler regeneration must match the checked-in lock exactly.
No provider key is exposed to these QA jobs. Their GitHub token is read-only.

The 64 Node/container checks in PR #24 concern the separate budget candidate;
they are not represented as tests of code included in this independent branch.
Existing idle audit schedules and their financial proposal PR #12 are unchanged.

## Limits and decision

This remains an unmerged proposal. It does not retrofit historical workflow
snapshots or disable run-again controls for old runs. The consumed trial must not
be rerun. No model, cap, quota, billing, secret, access or Roblox release is changed.

Request-specific complete input/framing proof is still **BLOCKED**. See
GEMINI_INPUT_BOUND_REVIEW.md for the exact official SDK snapshots inspected.
An operational stop is not proof of a 10-AIC financial cap. Reopening inference
requires independently established bounds, shared live enforcement for developer
and reviewer, current pricing/quota, fresh owner inference consent and reviewed
code changes. Merging this stop would not authorize model invocation.

Source proposals and evidence remain open; this extracts their limited stop and
continuity changes without merging or closing other work. Studio, multiplayer
and mobile remain NOT_RUN.
