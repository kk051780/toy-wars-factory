# Gemini admission and budget candidate — offline only

The original trial used 12 calls without recording proxy-side credits for its
unpriced native Gemini model. This candidate fixes that admission path and
tests a separate reservation ledger before any new model invocation.

## Implemented correction

`tools/build_gemini_admission_overlay.py` verifies the exact original
v0.28.70 proxy Git blob and generates a two-file overlay. It does not modify
the upstream checkout, install a container, change the compiled workflow or
read credentials. Generated files have a SHA-256 manifest.

The patched proxy identifies native Gemini models from their URL, rejects a
conflicting body model, malformed or unsupported URLs and unpriced models,
then applies the original common guards. Errors are terminal and contain no
prompt, source code or credentials. Existing model-policy and credit-limit
rejections remain active. Other providers keep their original behavior.

## Reservation runner

`runtime/gemini_budget_guard.cjs` also supplies a candidate nonstreaming,
text-only bounded runner. It requires all of the following host dependencies:

- An explicitly approved model price profile with evidence. There are **no live
  approved profiles** in this proposal; test rates are synthetic fixtures.
- A host-owned, request-hash-bound upper-limit adapter covering every input
  token and all charged output, including thinking. No client token estimate
  or unsigned request header is accepted as a bound.
- An injected single-attempt transport. No provider transport is implemented.

Before generation it reserves the maximum modeled cost using integer
nanocredits. Active reservations count against the cap, so concurrent requests
cannot spend the same remaining budget. A complete, consistent response may
release unused reservation. Timeout, missing/invalid usage, model changes or
a bound violation halt the ledger and retain the reservation. No retry or
refund occurs for an uncertain charge. The shared request-count limit is also
terminal. Mutable input bytes and mutable catalog entries are copied first.

The runner currently rejects streaming, multiple candidates, tools, media,
context-cache references and other features without a verified cost contract.
It counts generated thinking tokens as output; response totals must agree.

Google documents pre-request token counting and separate thinking usage:
- https://ai.google.dev/api/tokens
- https://ai.google.dev/gemini-api/docs/generate-content/tokens

An API count alone is **not** treated here as a certified upper bound for every
possible billable provider operation. A real model's bound contract, exact
rates and provider-side quota still need independent validation.

## What is connected

The generated overlay hooks **native admission only** in the reviewed AWF
proxy. The reservation runner is tested separately with injected trusted bounds
and real loopback HTTP servers. It is **not connected to the Gemini CLI**.
Neither the overlay nor a new runtime image has been installed or deployed.
The old one-shot marker is unchanged; no inference is retriggered. The
independent patch/security review remains required and is not modified.

Thus, the original unpriced-model path now has a reproducible correction, but
this proposal does **not** prove a live financial ceiling or a zero bill.
The ledger is in-memory for one process. Sharing/persisting a budget across
workers and including the separate security-review API call are additional
requirements before any complete runtime spending cap can be claimed.

## Reproducible tests

```text
TWF_AWF_ROOT=/path/to/gh-aw-firewall-v0.28.70 node --test tests/gemini_budget_guard.test.cjs tests/gemini_admission_overlay.test.cjs
python3 tools/build_gemini_admission_overlay.py --upstream /path/to/gh-aw-firewall-v0.28.70 --output /outside/upstream/candidate
```

CI retrieves public upstream commit
`32c12e0099763dad77acef6c655cb12e58fe36e1`, checks 12 exact original blobs,
and executes 40 Node regressions. Original credit accounting and common guard
descriptors are real upstream code. Telemetry, unrelated guard states and
transport are isolated test doubles; the model-policy rejection control
demonstrates that an existing denial still blocks the request. There are no
external Gemini calls, and HTTP integration uses only 127.0.0.1.

Tests cover the original failure before patching, the correction after patching,
model substitution, wrong upstream revisions, single-request overbudget,
an exact cap, concurrent reservations, request-count exhaustion, thinking
costs, mutable input, uncertain charges and repeated attempts after stopping.
Twenty simultaneous unpriced requests produce zero loopback upstream calls;
a priced positive control produces one.

## Next deployment prerequisites

Review the candidate, connect a trusted upper-bound adapter and verified price
profile to a single-attempt proxy transport, and validate an actual candidate
container without exposing a provider key. Then verify authoritative provider
quota/billing and obtain fresh owner authorization before one real trial.
Recurring AI development, automatic merging and Roblox publication remain
unauthorized. PR #19 remains a separate unmerged prerequisite for continuity.
