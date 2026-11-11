# TRAP RAIDERS S1 — official-RC intake, no source overwrite

P0-D packet: `P0D-S1-RC-INTEGRATION-DIFF-PREFLIGHT-20261112-01`

This packet is a **manifest-only** integrity-preserving read-only integration intake checker. Frozen source comparison: initial official sole-integrator RC 15 files vs newest first-minute FTUE 30-file single-game candidate. Verified classification: 11 unchanged, 4 changed, 15 new, 0 deleted. Original 7-field manifest has extraneous `status` key, newest 6-field manifest is canonical. Actual official RC unchanged.

Use `docs/README_INTEGRATION.md` and `docs/OBSERVED_DIFF.json` with `tools/rc_intake_preflight.py`; see 25 deterministic Python negative/positive tests in `tests/test_rc_intake.py`.

No keys, encryption, secrets, CI spending, main/official RC write, merges, real Roblox Studio playback, purchases or public publishing. #220's existing exclusive CHAT-INTEGRATOR alone selects source and reports overall game completion using its evidence-based 100-point score. No developer authored overall percentage here.
