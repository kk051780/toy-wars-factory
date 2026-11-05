# A12: bounded runtime diagnostics, source proposal

Issue [114](https://github.com/kk051780/toy-wars-factory/issues/114), checked 2026-10-29 JST.
This is one registered META implementation. The local prototype described in
[comment6482136080](https://github.com/kk051780/toy-wars-factory/issues/114#issuecomment-6482136080)
informed the requirements, not source provenance: its downloadable code was not
available through GitHub. This module and its regressions were independently
authored under the new canonical META lease. Prototype checksums/30 local tests
are not this PR's CI or evidence of unattended operation.

## Actual call path and boundaries

`system_runtime_alerts.observe` calls the accepted
`system_provider_transport.observe(collector="incident")`, which executes the
accepted incident, service and GitHub collectors. No accepted file is changed.
The host supplies existing read-only GET and exact-task PEEK callbacks plus a
monotonic clock. The accepted transport projects service lifecycle metadata
before the collectors receive it; no service prose is interpreted as an error
receipt. The new classifier checks pinned project/repo/roles/coordinator,
current service snapshot, trace attribution, PR head/base, run/attempt and both
offline+compile_hold jobs again before producing bounded diagnostic output.

This is not credential isolation, an authenticated portable receipt or a new
monitoring service. Python callbacks and caller JSON cannot authenticate origin.
`classify` is explicitly pure and NOT_VERIFIED; so is `reconcile`, even when
checksums match. The `observe` path can be exercised by a trusted host, which
must separately record actual connected calls and code SHA. Fixture execution
is SYNTHETIC_TEST_ONLY. This authoring cycle does not claim a connected anomaly,
scheduled detection, alert delivery, recovery, continuous operation or A12 +5.

All authority flags remain false, including write/start/takeover/dispatch/
merge/publish/spend/safe-next-schedule. The code has no write, retry, task-start,
notification or scheduling callback. Saving its output is the host's separate
fenced operation. GitHub persistence alone is not notification delivery.

## Classification and provisional history

- completed + current matching result differs from failed/no_update and missing
  current result. A previous result cannot complete the current run.
- in_progress within its role's declared duration differs from an overrun.
  Scheduling intent is not a start timestamp. No second observer/worker is
  launched to repair any state.
- an active lease remains active; an expired unreleased lease only warns.
  Expiry never authorizes takeover, even if a service appears completed.
- CI uses the exact observed PR/main head, workflow run, attempt and two jobs.
  Success on another head cannot clear failure. For initial attempts, timeout
  means wall time since creation (including queue time). The accepted envelope
  lacks a rerun-specific start: a pending attempt >1 is INDETERMINATE, not a
  fabricated timeout based on the original run's creation time.
- 403/404, unknown errors, missing jobs, malformed data and ref/head movement
  produce CONNECTOR_UNAVAILABLE with cause INDETERMINATE. The new module cannot
  diagnose HOST_WRITE_DENIED: no original operation receipt is collected.

Thresholds are explicit per selected project's roles, not internal toy rules.
The proposed bounded initial values are 1800 seconds for each service's running
duration, 900 seconds for first-attempt CI queue+execution, 120 seconds maximum
observation age and 48 hours replay age. These are monitoring hypotheses, not
official platform limits or measured optimal SLAs. Existing 30-minute lease
policy is unchanged; daily cadence is not confused with a running duration.
No missed-schedule detector or provider history pagination is implemented here.

Service alert IDs use project/repo/role/task/current run and anomaly kind, so
unrelated main updates do not create duplicates. CI IDs additionally bind head,
run and attempt. `reconcile(previous,current)` returns a new provisional frame,
increments repeat count only on a later observation and rejects duplicates,
foreign projects/roles, forged grants/delivery/recovery and unsafe extra fields.
Prior JSON is not authenticated storage; a legitimate host must independently
retrieve/fence any saved baseline. Disappearance becomes only
UNVERIFIED_RECOVERY_CANDIDATE, `recovered=false`; unavailable/indeterminate
observations become RECOVERY_UNASSESSABLE. No disappearance grants permission.

## CLI

`python tools/system_runtime_alerts.py --request request.json` takes exactly
`projects`, `binding`, `thresholds`, `previous`. Binding is the existing incident
binding; previous is null for the first observation. Each stdout GET/PEEK request
expects the accepted transport's JSON response on stdin. The final line is
`{"result": ...}`. Only a trusted, separately scoped host may fulfill requests.
No token/credential is a CLI argument. Failures emit a generic allowlisted
diagnosis, without exception text, service chat bodies or arbitrary provider data.

## Tests and acceptance

39 new regressions run real accepted collectors over two synthetic game manifests,
not copied observer logic. They include stale/current run, exact role/task/CI,
mid-observation ref/jobs movement, active/expired lease, HTTP errors, false
attestation, duplicate/replayed alerts and unverified recovery. A source mutant
that removes the running-duration alarm must fail the focused negative controls.
All 510 accepted Python tests remain byte-identical. The local snapshot lacks
real historical Git ancestry for one existing handoff test; real GitHub CI with
full history is authoritative and must pass all 549 tests and both jobs.

After independent registered review and main QA/handoff, a later legitimate
scheduled cycle must demonstrate a real new anomaly, actionable deduplicated
GitHub evidence and subsequently independently verified recovery. Do not induce
a security failure or force another run. Until that proof, A12/A13 remain unmet.
Issue113/progress config/report/tests are outside this META change. PR112 is
already independently merged, and no owner transcription repair is repeated.

## Primary sources and game experiment handoff

All below opened 2026-10-29 JST. Publication/update date and retrieval differ.

- [GitHub evaluation case](https://github.blog/ai-and-ml/llms/how-to-evaluate-llms-before-production/),
  published 2026-08-25, update unavailable: representative errors and explicit
  offline/production boundaries matter. This is an older case freshly checked;
  no newer dated case was verified by this run's search. Adopt new adversarial
  regressions; do not transfer their commercial/security effect to this project.
- [GitHub attempt jobs API](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt),
  publication/update unavailable: run ID and attempt number identify a job list;
  Actions read access suffices. No credentials/permissions are changed here.
- [Roblox analytics](https://create.roblox.com/docs/production/game-design/analytics-essentials)
  and [Discovery](https://create.roblox.com/docs/discovery), dates unavailable:
  cohort/retention/engagement metrics are candidate measurements, not measured
  effects. Keep first-production/first-180-second abandonment and D1/D7 separate.
- [BIG Games Update99](https://www.biggames.io/post/pet-simulator-99-update-99),
  published 2026-10-24: collection/rewards are an actual developer mechanism,
  not proof of causal retention or an asset/source template to copy.
- [Community thread](https://devforum.roblox.com/t/50-of-players-leave-within-2-minutes/4946893)
  returned a JavaScript/bot wall. Body/date/claims NOT_VERIFIED_THIS_RUN; no
  snippet statistic is adopted as a player outcome.

Game alternatives remain backlog hypotheses: (1) clarify current three-unit
first-production loop, (2) differentiated visible support/collection role after
protected PR98 adoption, and NO_CHANGE. Success needs real first-session funnel
and D1/D7 measurements, rejection conditions and independent QA. 32/64px identity,
18/24-part trial targets and 20 units/side x4 factories are project experiments,
not official limits. Native Studio/multiplayer/mobile/visual/fun evidence is
NOT_RUN; no game implementation, publication or inference spend is added.
