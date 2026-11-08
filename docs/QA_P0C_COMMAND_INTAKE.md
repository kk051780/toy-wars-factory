# P0-C read-only command intake (C1)
OWNER source: https://github.com/kk051780/toy-wars-factory/issues/204#issuecomment-6718344277

This isolated DRAFT is a pure, offline Python diagnostic: fixed JSON fields, bounded UTF-8 and TTL, duplicate key refusal, repo/host/main source pin, work-id replay refusal and only one action named PING_STATUS_READONLY.

Even VALID parsing is untrusted. All provider_authenticated, owner_authorized, host_authorized, codex_execution_authorized and may_run_commands outputs are always false. User-controlled GitHub comments/fields are not authority.

NOT PRESENT: Windows receiver/poller, verified owner consent/signature, GitHub source authentication, Codex/Studio tool call, local scheduler, auto-start, paid API, remote shell or host-side authorization. Do not infer deployment from a green CI.

C2 next: independent review of C1 and separate owner-approved opt-in read-only Windows receiver; require provider-authenticated source, host-bound one-time consent, expiry/nonce/replay checks, original #123 CAS, and real end-to-end request receipt. No PC modification or unsupervised execution before those gates.

Offline test: python3 -m unittest discover -s tests -p "test_system_p0c_command_intake.py" -v
