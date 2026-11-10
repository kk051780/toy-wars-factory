# Original source retransport without AES keys

- Game `TRAP_RAIDERS`, existing work `p0d-siege-v19`
- New `packet_id`: `P0D-D06-SESSION-STAMP-LIBRARY-RECOVER-20261110-01`
- Old `packet_id`: `v39-h1-chatlead-ref-20261110`
- Original unencrypted owner Library ZIP: `TRAP_RAIDERS_v39_ChatLead.zip`
- Old ZIP SHA256: `7d3c5d5c947530cb1874e7ee7dcf55d712c5c8c3bf6f49e5c25de093a7bc349d`
- Preserved 16 original manifest-listed file byte sequences exactly, SHA verified before public upload.
- Old transport manifest saved byte-exact in `docs/LEGACY_BUILD_MANIFEST.json`.
- Canonical delivery: `PUBLIC_SOURCE_V1`, GitHub independent branch pinned SHA; older AES instructions, seal/restore scripts remain historical only, **no secret key needed**.
- No change to game behavior; a packet source handoff does not prove Windows Codex intake or Studio QA. Main, merge, public Roblox release, purchases, real paid products and shared P0 protection are untouched.
- Source presence and SHA verification is separate from gameplay acceptance. PC must compare newest saved Place/real source and integrate at most one non-overlapping slice at a time.
