# Issue71: scoped provider input transport

Checked2026-10-28 JST. PR95 has independently merged as d7d4bb8a2bd2b25bb6298946b56ce56b0944eaa0; main QA40594943961 and handoff40594944031 succeeded. Current main 55d9e0da77f0a9237cf2776432cf22f62b551283 differs only in generated status2 files. Issue72 is closed and its actual legacy guard remains present.

## One bounded change

Existing service collection correctly drops prose from its output, but the callback/stdin input still contains provider prompt, result text, chat references and arbitrary extra fields. New tools/system_provider_transport.py is an **opt-in** input adapter before accepted collectors. It binds one project to pinned main/coordinator refs and verified ordinary blobs, derives exact registered tasks, restricts GETs to the selected PR/run/attempt and discovered pinned resource graph, then uses the accepted lifecycle validator to project PEEK responses before forwarding them. A failed session closes, with64-call/16MB total/2MB response/120-second caps and no retry. Existing GitHub payloads and accepted behavioral validators are preserved.

This is an in-process Python adapter. The separately trusted host's actual connection remains the permission boundary. A malicious in-process caller can bypass a Python object; this is no sandbox, credential proxy, portable authentication receipt or PR55 solution. No token/header, network client, SDK/config/auth/workflow change or task control is introduced. Old CLIs are unchanged: only the new route applies this input minimization. A host must deliberately choose reviewed code and its own verified pins. All write/start/takeover/dispatch/merge/publish/spend grants remain false.

## Tests and real path

New31 tests pass for two synthetic games and actual accepted collector/planner code. Synthetic canaries prove that old raw input contains prompt/result text while accepted output is already safe; new input projection preserves the exact observation. Returning the unfiltered response in an isolated in-memory mutant makes two direct controls fail with0 errors. An initial3-test mutant also produced accepted PEEK_UNAVAILABLE from a callback assertion; no accepted test or code is changed. Local454 tests:453 pass,1 unchanged ancestry assertion needs real Git history; fresh GitHub CI must resolve it without skip.

Exact source blob d6bd8b106101a34c5eeb35c92a583bd8ccd8235f ran 2026-10-28T01:34:00.807325+00:00–2026-10-28T01:35:46.778545+00:00:37 actual connected GETs and9 existing registered-task peeks passed through the new transport and accepted joined observer. All9 peeks were reduced to allowlisted lifecycle metadata before the accepted collectors. The host observed this execution only as LIVE_PROVIDER_VERIFIED; stdin/callback/output remain NOT_VERIFIED, two synthetic games remain SYNTHETIC_TEST_ONLY. The output kept META160 ACTIVE_LEASE with claim_verified=false and the PR author's historical run separate from the current worker, with all grants false. No original operation error or permanent deployment was established. A prior3-GET read-only attempt during REVIEWER159 was rejected after the shared ref moved; it is not a success or a claim.

## Sources and next evidence

- [GitHub MCP configuration](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md), dates unavailable, opened2026-10-28: read-only capabilities and best-effort content filtering have distinct boundaries. No settings copied or changed.
- [MCP draft security guidance](https://modelcontextprotocol.io/docs/draft/tutorials/security/security_best_practices), dates unavailable, opened2026-10-28: minimize scope and do not pass tokens through. This module makes no auth/containment claim.
- [MCP-FSD primary paper](https://arxiv.org/html/2610.22301v1), published2026-10-15, opened2026-10-28: declared contracts are not process confinement. This is design evidence, not a vulnerability finding in Toy Wars. No newer dated Oct28 source was verified by the fresh search.
- [Roblox DataStore best practices](https://create.roblox.com/docs/cloud-services/data-stores/best-practices), dates unavailable, opened2026-10-28: ordered bounded retries and unknown write outcomes matter. The actual PR94 read/final-save failures are a WORKER repair, not a game change here; engine evidence is still absent.

CLI: python tools/system_provider_transport.py --request HOST_SELECTED_REQUEST.json. Request has projects, the accepted joined binding, and collector=incident or service. The bridge protocol offers only GET or exact registered PEEK requests; the external host must enforce its own read-only tool selection and never supply credentials. JSON values cannot authenticate themselves. Do not start tasks or write refs from collection.

Next: separate registered review of exact head/immutable claim/scope/CI/live boundary, then independent main integration and actual main QA/handoff. Keep Issue71 open and all spending, Gemini and release HOLD. New source availability is not global adoption of this route or product completion.
