# P0-D CHAT_LEAD / v40-v41-v42 independent fallback reference

**DO NOT EXECUTE OR MERGE AUTOMATICALLY.** Encrypted GitHub source transport, not current Roblox game code.

This packet was authored during the OWNER-reported Codex quota limit and contains **new** pure Luau reference modules / offline Python tests for:

- v40 boss event lifecycle (Gorogan/Raigald) and 7s neutral boss direction.
- v41 exclusive normal/boss/weather selection (65/25/10), short weather duration, safety-limited two-second **position-only** rewind.
- v42 session-only, free cosmetics-only account XP Lv1-25 / seven-job mastery 0-5 fallback, caps104 XP/57 mastery per match and replay protection.

## Integrity and QA

- Packet ID: `v40-v41-v42-fallback-chatlead-20261110`
- Work ID: `p0d-siege-v19`
- Original unencrypted ZIP: `TRAP_RAIDERS_v40_v42_ChatLead.zip`, 25,927 bytes, 19 files plus `BUILD_MANIFEST.json`.
- ZIP SHA256: `05a85a7934f6ae1815c9dd50c81a3ff81c3f8e46c9051fe0f8fea1838b8ed9ec`
- ZIP manifest SHA256: `05ba760549d7dbc14b65f68ed40e45bae34820585c465588fe522d7eeda5168c`
- Encrypted JSON SHA256 (local file, including final newline): `ee0a030390dfdce3f58535c561a5fe4afe96df815d51d63bbe69d8831fcdfe6c`.
- Offline tests: **Python unittest 69/69 PASS**, `verify_packet.py` ZIP manifest SHA PASS, AES-256-GCM decrypt restoring byte-identical ZIP PASS.
- PC Windows restore / Luau compilation / Roblox Studio / multiplayer / physical mobile = **NOT_TESTED**. No claim of v40–v42 full gameplay integration.

## How to restore (OWNER direct instruction only)

1. Download `TRAP_RAIDERS_v40_v42_encrypted.json` from the same handoff directory.
2. Download the shared public-safe utility from [restore_handoff.py](https://github.com/kk051780/toy-wars-factory/blob/db734240f0157cc125b563656dbd09668226f3ab/tools/restore_handoff.py).
3. Install Python `cryptography` if necessary (free package, no paid API) and set environment variable `CHAT_CODEX_HANDOFF_KEY` privately. The 256-bit key was supplied to OWNER privately in ChatGPT; **never echo, commit, log, or paste it into GitHub**.
4. Run `py restore_handoff.py TRAP_RAIDERS_v40_v42_encrypted.json --out TRAP_RAIDERS_v40_v42_ChatLead.zip` and verify the SHA above before extraction.
5. Run `python tools/verify_packet.py TRAP_RAIDERS_v40_v42_ChatLead.zip` after unpacking `tools` to a safe isolated folder. Run `python -m unittest discover -s tests -q` inside the extracted packet.
6. Integrate one submodule at a time into the real PC local game only after v37 final QA and the prior v39/v43-A review gates are met.

## Dependency / compatibility warning

Historical **v42.2** (expected ZIP SHA `8b9fe213c5ef90d8d0ce47099df2f33af0472488848200944d7164ca416bb44f`) is **not included** and unavailable in the current workspace. The new fallback has a **different packet ID and SHA**. v42.3 `RoundEvidenceGate` is a separate addon, not included. Do not merge both XP ledgers or infer that the historical binary was recovered.

## Collaboration

- [Cross-P0 coordination / soft scope claim](https://github.com/kk051780/toy-wars-factory/issues/217#issuecomment-6751589528)
- [Safe GitHub distribution protocol](https://github.com/kk051780/toy-wars-factory/issues/217#issuecomment-6750892464)
- [P0-D game source/Studio QA channel](https://github.com/kk051780/toy-wars-factory/issues/213)

`PUBLIC` repo: no plaintext proprietary commercial source, .rbxlx, game assets or encryption keys. No unapproved merge/main/publish/real payment/spend. GitHub Issue comments do **not** auto-run Windows Codex.