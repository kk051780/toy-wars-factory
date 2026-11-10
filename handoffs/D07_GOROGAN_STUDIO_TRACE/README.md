# TRAP RAIDERS / P0-D D07 Gorogan S1 trace gate

`P0D-D07-GOROGAN-STUDIO-TRACE-GATE-20261110-01`

This is a **public-safe, source-free QA kit**, not a playable boss or integration patch. Existing Gorogan code is handled by other ChatGPT/Codex lanes. The package validates anonymous normalized **server** evidence for an isolated S1 boss combat run, and explicitly refuses to call its own output `Studio QA PASS`.

## Contents

- `tools/verify_gorogan_trace.py` — strict read-only JSON validator, no network/subprocess/Roblox access, rejects symlinks/duplicate keys/NaN/oversized JSON.
- `tools/verify_manifest.py` — SHA-256/size verification of published source files (does **not** authenticate who created a GitHub commit).
- `tools/build_example.py` — produces clearly labelled synthetic examples, no real source.
- `examples/synthetic_pass.json`, `examples/synthetic_duplicate_damage_fail.json` — deterministic positive/negative synthetic fixtures.
- `tests/test_verify_gorogan_trace.py`, `tests/test_manifest.py` — regression, fuzz and malicious input coverage.
- `docs/TRACE_CONTRACT.md`, `docs/CODEX_HANDOFF.md`, `QA_REPORT.md`, `RESUME.md` — contract and staged acceptance.
- `BUILD_MANIFEST.json` — SHA for every other file.

## Run locally

```shell
python tools/verify_manifest.py .
python -m unittest discover -s tests -q
python tools/verify_gorogan_trace.py examples/synthetic_pass.json --format json
python tools/verify_gorogan_trace.py examples/synthetic_duplicate_damage_fail.json --format json
```

The second trace must FAIL (exit 1) due to duplicated target damage in one attack. Successful source-free checks are **not evidence** that Roblox Studio has run; for real evidence the OWNER PC must confirm saved Place/source SHA, raw server Output, 2-client game screens, no false hits, and the owned Studio's normal close/PID disappearance.

**Safety:** No gameplay source, encryption keys, main/PR/Studio actions, Roblox publication, paid activity or P0-A/B/C lock changes. Designed to complement, not override, the separate D07 server/rig/visual code and D11/D14 QA tools.
