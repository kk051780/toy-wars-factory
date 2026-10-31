# TOY WARS FACTORY — Gemini / Antigravity provider bridge (pre-inference only)

**Canonical work:** Issue #170, TWF-PROVIDER-BRIDGE-ANTIGRAVITY-GEMINI-20261031.
**Status:** PREPARED_HOLD. Not a connected agent, new task or production scheduler.
**Security:** This candidate is not allowed to relax the October 24 Gemini SEVERE_HOLD.

## Current provider routes (verified 2026-10-31)

- Google deprecated individual Google AI Pro/Ultra sign-in to *legacy Gemini CLI* on 2026-06-18. Using old quota tables as proof of entitlement is incorrect. Official source: https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals
- Paid-account interactive developer route: **Antigravity CLI** in an owner-controlled local environment; first login is user interactive and not something ChatGPT can perform with its GitHub connector. Migration: https://www.antigravity.google/docs/gcli-migration
- Headless Actions/CI route: **Antigravity CLI with Gemini API key**, explicitly separate API billing/quota. Current Google instructions require setting modelProvider to gemini and exporting GEMINI_API_KEY, not merely setting an environment variable. https://antigravity.google/docs/install
- An alternative headless integration is Gemini API CLI, but that is a separate provider implementation and not authorized by this offline candidate. https://ai.google.dev/gemini-api/docs/cli
- Never copy an OAuth refresh token, browser session, Google sign-in credential or API key into an issue, chat, git tree, workflow source or handoff report. A GitHub Actions secret (if separately authorized) is distinct from the user's Gemini-app subscription.

## Offline bridge gate

The only code in this proposal is a standard-library *offline validator* at tools/system_gemini_bridge_preflight.py. It reads JSON from stdin; it does not read environment variables, secrets or network, and never triggers a CLI or inference. No installed provider extension or additional GitHub permission is needed to inspect this contract.

Example (sample contains no secrets, and its SHA is not independently authenticated):

    {
      "schema": 1,
      "work_id": "TWF-PROVIDER-BRIDGE-ANTIGRAVITY-GEMINI-20261031",
      "project_id": "toy-wars-factory",
      "repository": "kk051780/toy-wars-factory",
      "main_sha": "e5deff4d5681bca4823a3da0f848e01bc089ae6e",
      "route": "antigravity_account_interactive",
      "tool": "antigravity-cli",
      "runner": "owner_local",
      "planned_write_set": ["tools/system_gemini_bridge_preflight.py"],
      "gemini_severe_hold": true,
      "request_inference": false,
      "request_write": false,
      "owner_approved_new_inference": false,
      "provider_hard_budget_cap_verified": false,
      "provider_auth_status": "NOT_CONFIGURED",
      "subscription_pays_api_calls": false
    }

To preview without making any provider call:

    python tools/system_gemini_bridge_preflight.py < local-contract.json
    python -m unittest tests/test_system_gemini_bridge_preflight.py -v

To describe API-headless routing *without activating it*, change only route to gemini_api_headless and runner to github_actions. The tool remains antigravity-cli; this does not grant a credential, API request or paid allowance.

**The output is ALWAYS non-authorizing**, even for valid input. Positive validation does not prove current GitHub main, service run, actual billing, authenticated Google account, budget cap, exclusive coordinator CAS claim or independent reviewer. It cannot authorize writes, testing against Roblox, or a merge.

## Next separation-of-duty gates

1. Keep existing #16/#18 severe-hold root-cause and expense analysis separate; the 2026-10-24 test exhausted 12/12 turns and 12 minutes, generated **no PR**, and reported modeled 33.713 AIC vs configured 10. Billing was NOT VERIFIED.
2. Choose either a live interactive owner-controlled Antigravity worker (requires owner-side environment connection) or independently priced Gemini API-key headless Actions worker. Do not equate either with a ChatGPT worker or registered task identity.
3. Security reviewer verifies authenticated provider identity, locked repo/project and read/write scope, hard provider budget ceiling and bounded one-shot execution. Fresh owner consent is required for lifting the specific inference SEVERE_HOLD; ordinary engineering delegation does not override it.
4. Only after an approved policy migration, register distinct Gemini work queue ID with #123 intake. For now do **read-only analysis only**; existing coordinator is single-writer, and any future source write must follow genuine owner-specific CAS, separate branch and independent review.
5. Execute one tiny inference task only after #16/#18 gates are explicitly met and exact budget/termination evidence can be captured. Record GitHub Actions run ID, source diff, test result, distinct reviewer, measured expense, and maintain Roblox engine/publication holds.

**Not done:** External Gemini authentication, subscription verification, provider hard quota, Gemini actual inference/PR, unattended write authority, Roblox execution and release.

This artifact prepares the integration contract and its regression checks, not the runtime connector.
