# TRAP RAIDERS — Keyless handoff v2 (PUBLIC-safe tools and rules)

- `docs/KEYLESS_POLICY_V2.md`: all chats' delivery contract, two supported methods.
- `docs/CODEX_BOOTSTRAP.md`: one-time Windows recipient registration; no per-packet key exchange.
- `tools/keyless_handoff_v2.py`: recipient enrollment, encryption with owner public key, automated PC restore; contains **no keys**.
- `tools/build_migration_bundle.py`: make a PRIVATE bundle of mounted legacy source ZIPs; **never upload its output to PUBLIC GitHub**.
- `tools/verify_local_bundle.py`: read-only integrity verification of the bundle.
- `migration/CURRENT_ARTIFACTS_INDEX.json`: SHA catalog of available mounted source ZIPs. No source bytes.
- `tests/test_keyless_handoff_v2.py`: no-network deterministic safety and round-trip tests.

Status: tool implemented and tested, existing local ZIP bundle made separately, Windows recipient has **not** been enrolled, PUBLIC GitHub v2 sealed packages have **not** yet been generated. PC/Studio tests are not implied.
