# Issue 71: scoped GET observation adapter

The new `tools/system_github_evidence.py` requests only scoped repository GETs
through a host-supplied capability. It has no HTTP/authentication client, token
argument, environment credential lookup, writer, task starter or retry launcher.
The host must supply the existing connected read-only GitHub capability; never
pass credentials to PR-controlled Python. Open PR55's credential-isolation work
is still unresolved; this change neither enables an authenticated workflow nor
changes its gates.

`collect(projects, binding, get, clock)` reloads the selected manifest and role
policy from pinned main blobs, verifies coordinator commit/tree/blob/epoch and
roles, same-repository open PR/branch/run, current exact-head QA attempt and both
jobs, main QA or directly compared status-only descendants, and rereads mutable
refs/PR/CI before returning. Source records contain safe GET URLs, observation
times and body digests, not response bodies, provider exception text or tokens.
At most 120 seconds are allowed for one observation. Fixed job names here are
the current offline/compile_hold QA contract; repositories with other contracts
are unsupported, not implicitly healthy. Game IDs, repositories, task IDs,
coordination branches and author branch prefixes are not hardcoded.

The stdio CLI (`--request` containing exactly `projects` and `binding`) emits GET
requests and reads `{status, body}` responses. It is a bridge, **not an origin
authenticator**. Its output always says `NOT_VERIFIED`; arbitrary JSON, a fake
Response object, a provider string or push/admin permission label cannot promote
it. Synthetic fixtures are `SYNTHETIC_TEST_ONLY`. A real host may separately record
`LIVE_PROVIDER_VERIFIED` only for a trace in which it actually invoked its connected
GitHub GET tool for the exact module/inputs and passed those results through this
code. Such a host record is not a portable signed receipt; replaying it grants
no authority. If that integration is unavailable or any GET is rejected, report
the specific missing boundary as `NOT_VERIFIED`.

`advisory` calls the existing core evaluator and P3 scheduler with the collected
observation. It deliberately leaves `live_read_claim=false` and every execution
grant false. The canonical triage output helper returns INDETERMINATE because this
GitHub collector does not fetch actual service records or operation-error receipts.
It must not fabricate completed service runs, host errors, or safe-to-start results.
The output can therefore suggest further investigation but cannot dispatch,
recover a lease, merge, publish or spend. One selected PR is observed; the complete
repository queue is not counted by this prototype.

Primary sources opened on 2026-10-27 (publication/update dates separate):

- GitHub workflow jobs REST documentation (date not stated):
  https://docs.github.com/en/rest/actions/workflow-jobs
  Specific run-attempt job endpoints prevent combining attempts; pagination and
  exact two-job cardinality are checked. No workflow metadata endpoint is needed:
  this connector rejects that endpoint, so use allowed run GETs, pinned workflow
  ID/path and the ordinary workflow blob in trusted main.
- GitHub Git tree REST documentation (date not stated):
  https://docs.github.com/en/rest/git/trees
  Require regular 100644 blobs and a complete tree, not author path claims.
- GitHub ReviewBench implementation-team case, published 2026-10-05:
  https://github.blog/ai-and-ml/github-copilot/reviewbench-an-open-benchmark-for-ai-code-review/
  Keep adversarial behavior, provenance and production outcomes distinct.
  Rechecked today; this is not a new October 27 release.
- Roblox hardware testing guidance (date not stated):
  https://create.roblox.com/docs/performance-optimization/test-on-hardware
  Real-device frame/memory/thermal and touch testing remain separate unperformed
  experiments; synthetic games do not prove engine, multiplayer, mobile or fun.
- Roblox update index, updated 2026-10-22:
  https://create.roblox.com/docs/updates/2026-10-19
  Read the actual dated index; no unexamined version-link details adopted.

Issue71 remains open until independent main adoption, post-main QA/handoff and
the required live evidence are all proven. This draft alone is not P2 acceptance
or real multi-game dispatch. Existing spend/Gemini/Roblox release holds remain.
