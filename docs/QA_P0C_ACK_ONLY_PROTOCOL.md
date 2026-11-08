# P0-C / C3A — GitHub receipt ACK-only prototype

OWNER live receipt: https://github.com/kk051780/toy-wars-factory/issues/204#issuecomment-6720282498

This is a protected stacked DRAFT source candidate only. It does not modify the existing PR211/PR212, main, Windows service, Roblox Studio or Codex.

The goal is **Windows → GitHub result return without manual screenshots**. The prior Windows V2 test already proved ChatGPT→GitHub→Windows foreground PING, but did NOT prove result return.

Source: tools/system_p0c_ack_only.py. The pure make_ack_only() function validates a fresh, exact `PING_STATUS_READONLY` GitHub source comment using the existing parent validation and pinned main SHA. It builds a small deterministic P0C_READONLY_RECEIPT_ACK_V1 record with work_id, source_comment_id, source_body_sha256, fixed repo/issue and explicit all execution and host-attestation flags false.

The separate post_ack_only_once() function is a proof-of-concept *potential* GitHub Issue #204 comment POST. It requires both a caller-supplied explicit owner_opt_in=True **and** a pre-approved issues-write credential. It never acquires, loads from disk, creates, prints, embeds or stores a token. No arbitrary URL, redirect, shell command, Codex, Studio, local SQLite, service or auto-poll. One POST attempt, no retry; no background process. If permission is missing, it fails closed before transport.

**IMPORTANT:** This protocol is NOT approved for real Windows deployment. No PC credential is connected to this normal ChatGPT session. No real GitHub ACK POST was made from Windows. GitHub issue comments have no global exactly-once key and a failed response may follow a successful remote POST, so unattended retry is not permitted. GitHub author/app metadata do not cryptographically prove original OWNER PC authorization, and a completed POST is not host attestation. The owner must not paste secrets into chat, Issues or Windows scripts.

Tests: tests/test_system_p0c_ack_only.py uses fake transport and pinned 2026-11-08 live-PING fixtures; all offline. No effect on game code. The candidate is designed for independent reviewer evaluation, then a separate OWNER-approved least-privilege Windows identity/transport test. Windows is currently known to have PowerShell V2; availability of Python on the PC is unknown. This is a source protocol, not an end-user installer.

Codex remains a quota-limited bridge for actual Studio-only operations; no changes in the user-approved security gates. No merge, publish or additional charge.


## C3C security remediation (2026-11-08)
The source of a returned ACK must be the GitHub REST comment endpoint, never the untrusted caller-supplied comment dictionary. In the gated POST candidate, after explicit opt-in and approved token preflight but before POST, a fixed GitHub GET `fetch_comment_once(source_comment_id)` is now mandatory by default. The fetched GitHub comment must have the same ID and body as the caller-selected comment; strict `examine_comment` checks canonical source URLs, actor/app metadata and short TTL against the re-fetched record. Fetch failure, changed content or expired original message blocks before any POST. The injected `source_fetcher` exists only for offline fixture tests and must not be supplied by a real caller.
This strengthens source integrity but does NOT authenticate Windows host or original owner execution permission. It does NOT provide exactly-once POST, GitHub write-credential provenance or a Windows runtime. No new Windows GitHub credential was requested or used.
