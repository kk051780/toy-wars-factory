# D14 Rider Attach safety QA (2026-11-10 JST)

- Pure Python reference tests: 60 functional tests, including 2,500 seeded transition steps and 300 invalid replay attempts.
- Source-shape/static Luau checks: 19; verify no remote subscription, default-disabled bridge and two-role cap (NOT compiler).
- ZIP safety/manifest negative tests: 15.
- Total OFFLINE_PASS: 94/94 via `python -m unittest discover -s tests -q`.
- ZIP SHA/size/CRC/manifest is checked read-only; AES-GCM decrypted private ZIP bytes match exactly; wrong key and altered ciphertext reject (packaging phase).
- Windows real source SHA: UNVERIFIED_PC_LOCAL; Windows restore: NOT_TESTED; Luau syntax/compiler: NOT_TESTED; Studio physical mounts, 2/3client, mobile, actual motor physics, Studio normal exit: NOT_TESTED.
- NOTE: Current policy cannot authenticate the caller itself; integration MUST derive its snapshot solely from genuine server-owned state. The disabled physical adapter's WeldConstraint behavior is **not** engine-proven.
