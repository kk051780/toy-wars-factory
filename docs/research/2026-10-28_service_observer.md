# Issue71: scoped read-only service observer after PR84

PR84 is independently merged. This new companion observes service lifecycle
metadata without replacing its GitHub collector or changing accepted modules.
The trusted host provides the already-connected GET and existing-task PEEK
capabilities. The observer derives the selected project's exact role task IDs
from immutable main manifest/policy and coordinator blob/epoch, then peeks each
role twice. It never lists arbitrary tasks or creates, updates, stops or starts
one. The host bridge allowlist must independently restrict repository endpoints
and the three task IDs. No credentials or authenticated workflows are added.

`observe(projects, binding, get, peek, clock)` returns only allowlisted metadata:
task ID, enablement, canonical run UUID, recorded status, aware lifecycle times,
current/previous result identity and fixed flags. It drops prompt, content_text,
chat references, unknown operation claims and provider exception text. Trace
digests cover the safe service projection, not secret-bearing report bodies.
The CLI `--request` contains only `projects` and `binding`; it emits GET/PEEK
requests and consumes responses through stdio. This is not origin authentication.
Callback/stdin output remains NOT_VERIFIED; synthetic tests remain
SYNTHETIC_TEST_ONLY. Only an external host trace of actual connected capability
calls through the exact source can establish LIVE_PROVIDER_VERIFIED for that
bounded execution. No replayable JSON document conveys authority.

An in-progress last_run commonly has a latest_result from the preceding run.
The observer preserves that distinction; it never treats the old report as the
current run's completion. Completed/failed/no_update/in_progress remain distinct.
Missing current results, failed self-reports, disabled services and inconsistent
lifecycle metadata do not become healthy-idle or start/recovery permission.
scheduled_for is intent and may be later than an early manual start; it is not
completion evidence. Actual start/result/completion order and freshness are
validated, with a trusted-host age bound (at most 48 hours) and a 120-second
collection window. Safe metadata must match on end rereads, and both mutable
Git refs must remain pinned. Expired holders stay occupied; no lease recovery
or takeover is performed.

Operation-error receipts are explicitly OPERATION_EVIDENCE_UNAVAILABLE. Service
prose mentioning BLOCKED_HOST_WRITE, a read-only404 or admin/push flags is not an
original denied-write response. The observer does not manufacture or induce a
write failure. It invokes the accepted v2 validator with absent full evidence;
that returns INDETERMINATE because exact PR/QA and original operation evidence
are not collected in this companion. It supplies no made-up placeholders and
grants no write/start/takeover/dispatch/merge/publish/spend authority.

Primary research actually opened again 2026-10-28 (JST):

- https://blog.jetbrains.com/research/2026/10/review-ai-generated/
  Publisher's research-team case on review trust calibration and presenting
  risk/confidence at the appropriate granularity. Exact publication/update date
  was not displayed in the retrieved page; the URL is in the 2026/10 archive.
  Apply its separation of high-level trust questions and detailed evidence to
  source identity, lifecycle metadata and missing operation receipts. This is
  design evidence, not proof of effectiveness in this repository.
- https://github.blog/ai-and-ml/github-copilot/reviewbench-an-open-benchmark-for-ai-code-review/
  Published 2026-10-05, update date unknown. Rechecked primary implementation
  case on independent, reproducible behavior evidence; not a new Oct27 article.
- https://docs.github.com/en/rest/actions/workflow-runs
  Publication/update date unknown. Provider run IDs and attempts are separate
  from lifecycle self-reports; this companion must not infer PR QA from prose.
- https://create.roblox.com/docs/performance-optimization/test-on-hardware
  Publication/update date unknown. Real hardware frame/memory/thermal and touch
  validation remains a separate unperformed experiment. No game changes here.

Acceptance remains staged: new source/tests and exact-head two-job CI, one
bounded live host observation, independent registered review/merge, then main
QA/handoff. Issue71 stays open for its remaining requirements. Permanent provider
integration, portable origin proof, actual host-error recovery, real cross-game
operation and P3 dispatch are not established. PR55 credential isolation and all
spend/Gemini/Roblox release holds remain in force.

- https://opensource.microsoft.com/blog/2026/10/19/introducing-scope-open-source-evaluation-for-ai-coding-agents/
  Published 2026-10-19, rechecked 2026-10-28 JST. The development team describes
  versioned configurations and recorded interaction traces, and cautions that one
  demo or CI pass is not repeated reliability. Apply safe run/identity traces and
  repeated validation; no Scope deployment, model calls or provider spending.
