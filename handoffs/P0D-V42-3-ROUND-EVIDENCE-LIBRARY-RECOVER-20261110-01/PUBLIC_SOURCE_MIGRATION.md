# Original source retransport without AES keys

- Game `TRAP_RAIDERS`, existing work `p0d-siege-v19`
- New `packet_id`: `P0D-V42-3-ROUND-EVIDENCE-LIBRARY-RECOVER-20261110-01`
- Old `packet_id`: `LEGACY_PACKET_ID_NOT_IN_MANIFEST`
- Original unencrypted owner Library ZIP: `TRAP_RAIDERS_v42_3.zip`
- Old ZIP SHA256: `48a38fc83bf0018fff1a8151d14f36b54058174d09c74445301a892fcf696713`
- Preserved 13 original manifest-listed file byte sequences exactly, SHA verified before public upload.
- Old transport manifest saved byte-exact in `docs/LEGACY_PACKET_MANIFEST.json`.
- Canonical delivery: `PUBLIC_SOURCE_V1`, GitHub independent branch pinned SHA; older AES instructions, seal/restore scripts remain historical only, **no secret key needed**.
- No change to game behavior; a packet source handoff does not prove Windows Codex intake or Studio QA. Main, merge, public Roblox release, purchases, real paid products and shared P0 protection are untouched.
- Source presence and SHA verification is separate from gameplay acceptance. PC must compare newest saved Place/real source and integrate at most one non-overlapping slice at a time.
