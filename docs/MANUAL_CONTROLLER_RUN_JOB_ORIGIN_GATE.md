# PR166 original GitHub Actions run/job origin gate — independent review intake

This proposal adds `tools/manual_controller_run_origin_gate.py` to the existing
protected PR #166. It checks a claimant's non-authorizing
`reported_actions_origin_untrusted` fields against *separately supplied*
GitHub Actions original run and one-page job records.

The independent reviewer must fetch these records from its own authenticated
GitHub connection. User/author-supplied JSON or copied run/job records are not
trusted as provider attestation. Exact run ID, attempt=1, event
`workflow_dispatch`, workflow path, original repository numeric ID, current
accepted main head, actor/triggering actor, completed-success job and witness
step all must match. A green ordinary PR CI (`pull_request` event) is rejected.

This module provides a **pure compatibility check**, not its own GitHub network
transport, security signature, log attestation, provenance chronology or permission
to merge. It does not replace or automatically invoke the existing
`manual_controller_claim_witness.py` read-only claim checks.
It must be called by a genuinely independent authorized review workflow after
actual original run/job retrieval.

All returned authority fields remain `false`, even on success. No Github
write/probe dispatch, authorization escalation, Roblox engine action, Gemini call,
or merge performed by this module. Existing issue60 bootstrap hold and PR163
privileged write hold remain unaffected.

Native test: `python3 -m unittest discover -s tests -p 'test_*.py' -q`.
