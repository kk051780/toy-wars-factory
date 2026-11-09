# Public-safe P0-D intake audit tools

This artifact contains **no game source, no decrypted ZIP, no Roblox Place, no key**.

- `docs/P0D_INTAKE_REGISTRY.json`: 12 immutable encrypted-P0D packet metadata records; PC candidate source SHA is a comparison reference only.
- `tools/p0d_intake_audit.py`: deterministic offline validator and opt-in pinned public ciphertext/README network readback.
- `tests/test_p0d_intake_audit.py`: 23 tests covering duplicates, malicious paths, status inflation, dependency cycles, missing secrets, spoofed IDs, modified blob bytes and safe output creation.
- `docs/P0D_CODEX_INTAKE_BRIEF.md`: Windows Codex's bounded verification gates and integration order.

Running the tool **does not decrypt** any packet. For the first real PC task, v37 final Studio QA remains top priority. All encrypted packets are hold until OWNER-authorized PC restore and Studio QA.
