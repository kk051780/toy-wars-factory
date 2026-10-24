# Connected Gemini budget runtime — offline, blocked under the existing cap

This follow-up to PR #21 connects a dated public price snapshot and a host-owned
token-bound adapter to the reservation runner through a real local HTTP gateway.
A durable SQLite ledger shares the budget across developer and reviewer clients,
multiple workers and process restarts. The existing 10-AIC cap is unchanged.

## Verified public inputs

Reviewed on 2026-10-24, the official Standard text rates for Gemini 3.8 Flash are
$0.75 input and $3.75 output per million tokens through 2026-12-31. Output pricing
includes thinking. The model page publishes 1,048,576 input and 65,536 output
tokens. The snapshot has a short validity period and fails closed after expiry.
Rates are used to model AIC; they do not verify free-tier eligibility or bills.

- https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash
- https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- https://ai.google.dev/api/tokens

The CountTokens documentation includes an example with an input count of 10
before generation and 11 afterward. Therefore this candidate does not call
CountTokens or promote its result, client headers, character counts or an
invented safety multiplier into a strict input bound.

## Concrete preflight result

The current conservative adapter reserves **the entire documented input and
output limits**, even for a short request. Integer nanocredit arithmetic gives:

- Input: 78.6432 modeled AIC.
- Output: 24.576 modeled AIC.
- Total reservation: **103.2192 AIC**.
- Existing allowed cap: **10 AIC**.
- Result: `CREDIT_CAP_EXHAUSTED`, **zero forwarded calls**.

This is the reservation for this deliberately broad bounding method, **not a
price quote, expected request cost, bill or minimum amount needed to use Gemini**.
No cap is increased. A smaller request-specific bound still needs defensible
validation before a real trial could fit the current cap.

## Persistence and shared accounting

`persistent_credit_ledger.cjs` uses SQLite `BEGIN IMMEDIATE`, a shared budget
row and durable lease rows. Restarting does not reset spent credits or active
reservations. A different run identifier, budget or request limit cannot replace
the existing state. Unknown charges halt durably and retain their reservations.
The database stores counters and opaque lease IDs, not source, prompts or keys.

The offline gateway routes developer and reviewer test clients to that same
ledger. The original GitHub Gemini CLI workflow and Python security reviewer
are **not rerouted or enabled**; there is no live provider transport, credential
read or environment flag that authorizes live execution in this package.

## Container verification

`runtime/Dockerfile.offline` uses the exact API-proxy image digest identified
in the original trial. CI builds a local candidate image and runs the connected
regressions with Docker networking disabled, a read-only filesystem, a temporary
SQLite directory, dropped capabilities and no provider credentials. The build
context excludes Git metadata, credentials and unrelated files.

Nineteen connected tests cover exact price conversion, profile expiry, rejection
under the real 10-AIC configuration, shared developer/reviewer accounting,
restart persistence, unknown roles, request-limit claims, retained in-flight
leases, durable halt and simultaneous reservations in six separate workers.
Positive forwarding tests use explicit synthetic prices and loopback responses.
They are not live provider evidence.

The evidence artifact records the container image metadata and conservative
preflight at a clearly labeled simulation time. Tests pin that historical time
for reproducibility; the executable gateway checks current time normally and
refuses an expired price snapshot.

## Remaining blocker

Status: **OFFLINE_CONNECTION_TESTED; LIVE_TRIAL_BLOCKED**.

Before fresh inference approval, validate a materially smaller request-specific
token bound, recheck the dated profile and authoritative provider quota/billing,
and review routing for both real model clients through the same controls.
No consumed one-shot marker, recurring AI setting, merge behavior, release gate
or Roblox publication is changed by this candidate.
