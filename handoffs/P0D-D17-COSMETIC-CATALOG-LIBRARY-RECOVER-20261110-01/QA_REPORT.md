# P0-D D17 Cosmetic Catalog QA (2026-11-10 JST)

- Python reference/model & transport tests: **67/67 PASS** (`python -m unittest discover -s tests -q`)
- Includes 2,000 randomized equip/preview/unequip/revoke events and 1,000 repeated preview attempts.
- Tested free starter, server-entitled items, future preview-only denies, malformed item IDs, whitelist, revocation, inactive and callback failure, cleanup, resource cap, zero purchase flags, zero combat stats, session-only metadata, malicious path, manifest corruption, encrypted key/tamper rejection.
- ZIP per-file hash/size and ZIP CRC tests will be independently verified before Github upload.
- `LUAU_COMPILE=NOT_TESTED`, `WINDOWS_OWNER_CODEX=NOT_TESTED`, `STUDIO_PLAY=NOT_TESTED`, `2CLIENT=NOT_TESTED`, `PHYSICAL_MOBILE=NOT_TESTED`, `REAL_PURCHASE=DISABLED`, `DATASTORE=NONE`.
- `GITHUB_CIPHERTEXT_READBACK` is recorded only after GitHub immutable commit fetch and exact byte comparison.
