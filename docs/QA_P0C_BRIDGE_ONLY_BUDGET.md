# P0-C Codex budget policy — bridge only

OWNER decision (2026-11-08): Codex quota is limited. Codex is a Windows/Roblox Studio **bridge**, not the primary programmer or planner. ChatGPT+GitHub handle design, source coding, automated CI, independent reviews, shared CAS, state synchronization, metrics, and results.

Keep Codex calls short and rare:
- Invoke only for an actual Windows-only task such as listing current Studio instances/MCP state, inspecting a specific isolated Place, or a narrowly reviewed and owner-authorized Play/Stop test.
- Bundle all required PC observations into one limited handoff. Return a short GitHub Issue #204 receipt, then stop.
- Do not use Codex for long programming sessions, repeated QA already covered by GitHub Actions, CI reruns, installer work, exploratory loops, continuous monitoring, polling, or ordinary queue management.
- If bridge quota is exhausted, queue safely in GitHub; never silently purchase more capacity or bypass an authorization gate.
- This PR212 scanner is itself NOT a PC receiver deployment. No auto-start, scheduler, webhook or Windows runner is active. Successful output still says owner_authorized=false, codex_execution_authorized=false, may_run_commands=false. GitHub metadata and OWNER labels are not a signature or PC authorization.
- New scanner filters GitHub Issue #204 comments updated in the previous 11 minutes using the documented GitHub REST since parameter, avoiding all historical comments when total exceeds 500. If >500 recent changes, bounded scan fails closed.
- Duplicate currently valid work_id or nonce within one scan fails closed. Previously processed IDs/nonces provided by a real trusted ledger also fail closed; **this version does not have a persisted replay CAS**. Its output explicitly carries replay_history_verified=false; repeated CLI runs can display the same valid comment as a diagnostic but must never execute it.
- Repo is PUBLIC at this verification time: anonymous GitHub GET is allowed. If repo later becomes PRIVATE, an existing owner-authorized least-privilege read token may be used; access failure remains BLOCKED. No creation, printing or exfiltration of credentials.

Future true chat→PC→Codex execution requires a separately reviewed receiver and owner-authenticated signed intent, PC-side opt-in, durable idempotency and verified current coordinator/main SHA/Place scope. None is asserted implemented here. Main, merges, publishing, spending and blanket Windows privileges remain protected.
