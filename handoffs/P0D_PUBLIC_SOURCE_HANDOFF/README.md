# TRAP RAIDERS public-source handoff v1 — no per-chat keys

OWNER authorized making the first game's original code public. All new non-sensitive P0-D code packets go as **real plain Luau/Python text files** under a unique `handoffs/<packet>/` path on a separate GitHub branch, accompanied by `BUILD_MANIFEST.json`, tests and a fixed full commit SHA. No per-packet AES-GCM or ChatGPT→Codex private key handoff.

Read [the complete P0-D public-source protocol](docs/P0D_PUBLIC_SOURCE_HANDOFF_V1.md). An offline source-archive/credential guard lives at [tools/p0d_public_pack.py](tools/p0d_public_pack.py), with [35 Python tests](tests/test_p0d_public_pack.py).

The checker is not comprehensive credential detection and is **not** Roblox Studio certification; package authors must review all code before placing it on the public Internet. Only `TRAP_RAIDERS / p0d-siege-v19` is authorized. No `main` writes, merge, Roblox public release, monetization, expense, P0-A/B/C CAS changes or automation edits.
