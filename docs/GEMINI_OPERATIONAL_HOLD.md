# Operational incident hold — proposed, not deployed

The input/framing bound in PR #23 remains unproved. This change turns the
incident stop instruction into a literal workflow condition and closes the old
independent-review transport. It does not establish a financial cap or readiness
to invoke Gemini. All changes remain an unmerged draft.

## Two latent execution paths

1. The one-shot workflow watches `ops/GEMINI_TRIAL_APPROVED_FUTURE.json`.
   That file already records the consumed trial. Editing it could previously
   start another run: the workflow title and prose were not executable holds.
2. `tools/gemini_patch_gate.py --online` previously constructed a direct
   Google GenerateContent request. It did not share the proposed persistent
   developer/reviewer budget ledger. A synthetic injected transport reproduced
   one unreserved dispatch and a safe response; no real provider was contacted.

No additional actual charge or provider call was observed in this investigation.
The original 33.713 modeled AIC remains distinct from unverified provider billing.

## Proposed enforcement

- The authored frontmatter uses literal `if: ${{ false }}`. The pinned official
  compiler generates the hold before activation. The existing marker, variables,
  environment flags and key presence cannot satisfy a literal false condition.
- `scan_online` is a terminal compatibility entry point. The direct HTTP
  implementation was removed; there is no environment switch or injected
  transport that releases this hold. The CLI exits **2 (BLOCKED)** before reading
  patch content, a provider credential or selecting transport.
- Every CLI attempt first removes old `detection_result.json` and temporary
  verdict files. Failure to remove them is an error. An offline static PASS
  cannot preserve or emit an independent-model approval.
- Verdict schema checks remain available as a pure parser for synthetic/captured
  bytes. Their unit tests do not call a model or authorize safe outputs.

Removing the old direct HTTP implementation is intentional security reduction;
no gameplay feature or independent-review requirement was removed. A model
verdict is still required before safe outputs; the held CLI cannot produce it.

## Reproducible evidence

Ten new tests cover direct-call transport refusal, no credential/patch access,
stale verdict removal, offline PASS without approval, missing patch,
unremovable verdict, a real CLI subprocess with synthetic key/unlock flags,
authored/compiled holds, marker presence and rejection of a removed hold.
Existing static and verdict-schema tests are retained. The full Python suite
has 43 tests. Existing 64 Node and native Lua checks retain their original scope.

The offline QA workflow installs official `github/gh-aw` **v0.93.2** (tag observed
at commit `764fdc608e552558e4e15ffebec8e2953feb18d7`), recompiles the Markdown,
checks the held dependency graph and requires the resulting lock file to equal
the checked-in lock byte for byte. Compiling does not execute the workflow.
The compiler output is retained as an artifact, including on validation failure.

Source for supported frontmatter conditions:
https://github.github.com/gh-aw/reference/frontmatter/#conditional-execution-if

## Remaining scope and reopening

This proposal protects this revision after review/merge. It does not retrofit
historical workflow snapshots or disable GitHub's run-again control for old runs.
The consumed trial must not be rerun. No workflow was dispatched here.

Live inference remains blocked until an independently established complete input
bound, current pricing/quota, shared enforcement for both roles and fresh owner
inference consent exist. Reopening also requires a separately reviewed code
change: a marker or environment flag alone cannot release the incident hold.
The cap remains 10 AIC, recurring AI remains inactive, and no automatic merge or
Roblox publication is enabled. Studio, multiplayer and mobile remain NOT_RUN.
