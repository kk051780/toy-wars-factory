# D17 Privacy-first Engagement Metrics — encrypted reference handoff

Game: `TRAP_RAIDERS` / work: `p0d-siege-v19` / packet: `P0D-D17-PRIVACY-METRICS-20261110-A`. 2026-11-10 JST.

This is an **offline Python analytics oracle only**, not Roblox telemetry SDK, live production analytics, Lua, monetization, release or final QoE evidence. Inputs are limited to ephemeral session and round IDs, no account identifiers or personal information. No real sales or D1/D7 claims.

- Encrypted ZIP: `handoffs/TRAP_RAIDERS_D17_encrypted.json` / format `P0D_AES256_GCM_HANDOFF_V1`.
- Restored ZIP SHA256: `e7857702eec8c2b3a3bdc96c5aaedb6720c1f572e7ac138369bf6bfe2b832eb2`, 6159 bytes; manifest SHA256: `b341e8fe495b05dba78835751120ce34a65dee407cd95949fcbfb4fee3f0b2f5`, 7 files + manifest.
- Encrypted JSON SHA256: `9243cf0e9556e5054a5d5aa09013a6dd09f9bddca46cc9540148e59eb1a5f832`; ciphertext SHA256: `d64776451d8e1a45dbeca36cb9ba78a6844035e70548f9c8730daa8cdd1a5790`.
- Python unittest 25/25 PASS; AES-256-GCM bytes roundtrip/wrong key/tamper rejection and manifest integrity PASS.
- Windows restoration, Roblox Studio, real clients, physical mobile, production metrics, pricing, sales: **NOT_TESTED / UNKNOWN**.
- PC baseline: `UNVERIFIED_PC_LOCAL`. PUBLIC GitHub has no plaintext reference ZIP/secret key/game files.

## Future Codex intake (ONLY by OWNER direct instruction)

1. Check [#218 P0-D intake](https://github.com/kk051780/toy-wars-factory/issues/218), #213 and true Windows CHECKPOINT/Place SHA. v37 final QA and v39-H1 remain first.
2. Owner supplies private AES key separately (not GitHub or CI); restore the fixed envelope via audited safe tool at pinned commit `d37eec1b653d060ae27568ddcd5f501da9662081` with `--expect-work-id p0d-siege-v19 --expect-packet-id P0D-D17-PRIVACY-METRICS-20261110-A --expect-zip-sha256 e7857702eec8c2b3a3bdc96c5aaedb6720c1f572e7ac138369bf6bfe2b832eb2` into a brand-new trusted folder. If hash, identity or audit fails: HOLD.
3. Audit Python and unit tests, then decide whether to implement a legitimate **server-owned** Roblox telemetry adapter in isolated unpublished Studio. No client-side fake round-end/completion, no cross-day player tracking, and no actual analytics collection without lawful privacy controls and separate OWNER approval.
4. Keep all business outcome fields UNKNOWN until real authorized data. No Robux purchase activation, paywall, cloud logging, new bills, main/merge/publish/authorization bypass.

Scope D17 local engagement proof only; not market research or revenue measurement itself. Other D13-D16 chat-owned content untouched.

