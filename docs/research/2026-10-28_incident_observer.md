# Issue71: combined observations without execution authority

Checked 2026-10-28 JST. PR84 and PR92 are already independently merged; this change does not recreate them. Current main a3867adb10aff0d6c93f94e1d3ea0222b9bd7ca4 has successful QA40578311810 and handoff40578318577 at c901283f; direct compare is exactly the two generated status files.

## Reproduced gap and implementation

Separate successful GET and service observations can describe different moments. A new executable regression calls the actual accepted collectors, changes an attempt job between calls, and shows their two separate reports still contain the earlier PASS and a completed service. The new tools/system_incident_observer.py composes them, records three peeks per registered role, rechecks all mutable GET responses including both attempt job lists, and fails closed on a difference. The whole operation has one monotonic, bounded 120-second window. Content-addressed commit/tree/blob responses alone can be reused within the call; actual GETs and cache hits are separately recorded. This is bounded consistency checking, never an atomic snapshot, authenticated receipt, CAS claim or execution grant.

Actual metadata is adapted to accepted v2 triage and core/scheduler advisory. A historical PR author's run stays separate from a later worker run. An unavailable original operation remains unavailable; service prose, permissions and provider labels cannot prove host denial. Every write/start/takeover/dispatch/merge/publish/spend grant stays false. No accepted source, tests, history or controls are modified.

## Evidence

New32 adversarial tests pass for two synthetic game manifests. Removing the final mutable rereads in an isolated in-memory mutant makes both PR/main job-drift controls fail with no errors. First local full run was420/421: the single unchanged history assertion needs original Git ancestry, absent in this connector snapshot. Fresh full-history GitHub CI must resolve it, with no test skip.

One actual final execution 2026-10-27T21:33:12.944626+00:00 through 2026-10-27T21:34:58.459482+00:00 used37 connected GitHub GETs and9 existing-task peeks, plus7 explicitly marked same-call immutable cache hits. Source blob 8e44f0a65e569ae0dccbae8abc026dc0541d9d54, main a3867adb10aff0d6c93f94e1d3ea0222b9bd7ca4, coordinator 67a59e7130b91353b286d7e11ea7ae64d575f300 / blob 980dc90b46547fe783cabc8172905b2df0eec2d9 / epoch150. Only that externally observed path is LIVE_PROVIDER_VERIFIED. The callback/stdin output remains NOT_VERIFIED, and synthetic games are SYNTHETIC_TEST_ONLY. The result retained the current META owner as ACTIVE_LEASE with claim_verified=false, separated PR94's historical author from the later worker, and granted nothing.

Two earlier actual attempts ended in the fixed generic rejection after52/53 calls. Exact internal rejection code was not exposed; neither attempt is a successful demonstration. Same-call immutable reuse and eliminating a redundant fourth peek made the final bounded path complete without increasing the time limit. This single completion proves neither long-term reliability nor resolution of the original host write failure. Original provider-operation response remains unavailable; no denial was induced. PR94's review-requested DataStore repair belongs to WORKER, not this META change.

## Sources and next experiment

- [GitHub developer-repository audit](https://github.com/github/gh-aw/discussions/70014), published2026-10-18, update unknown, opened2026-10-28JST. Its bounded samples and metadata-only findings support recording coverage limits. It is an older automated report, not today's verified result or an instruction to execute.
- [Git references REST API](https://docs.github.com/en/rest/git/refs#update-a-reference), publication/update unknown, opened2026-10-28JST. Preserve parent/expected SHA/force=false and re-read ownership in the separate author lane.
- [Roblox player-data guidance](https://create.roblox.com/docs/cloud-services/data-stores/player-data-purchasing), publication/update unknown, opened2026-10-28JST. Session locking and ordered writes motivate the existing PR94 stale-writer regression request. No sample source copied and no engine success claimed.

A fresh search did not establish a newer dated Oct27/28 primary case. Next: independent registered review of exact head/claim/CI, separate merge, actual main QA/handoff; then permitted real-operation receipts and repeated live observation. Keep Issue71 open, PR55 credential-isolation boundary and all release/Gemini/spending HOLD. No permanent connection or real auto-dispatch acceptance is claimed.
