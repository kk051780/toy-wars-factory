# Original source retransport without AES keys

- Game `TRAP_RAIDERS`, existing work `p0d-siege-v19`
- New `packet_id`: `P0D-D17-COSMETIC-CATALOG-LIBRARY-RECOVER-20261110-01`
- Old `packet_id`: `P0D-D17-COSMETIC-CATALOG-20261110-01`
- Original unencrypted owner Library ZIP: `TRAP_RAIDERS_D17_CosmeticCatalog.zip`
- Old ZIP SHA256: `abd8efebae089b40c6837ceccc9fc152b2309ffa6a5b01eaf2dba497bac7e065`
- Preserved 15 original manifest-listed file byte sequences exactly, SHA verified before public upload.
- Old transport manifest saved byte-exact in `docs/LEGACY_BUILD_MANIFEST.json`.
- Canonical delivery: `PUBLIC_SOURCE_V1`, GitHub independent branch pinned SHA; older AES instructions, seal/restore scripts remain historical only, **no secret key needed**.
- No change to game behavior; a packet source handoff does not prove Windows Codex intake or Studio QA. Main, merge, public Roblox release, purchases, real paid products and shared P0 protection are untouched.
- Source presence and SHA verification is separate from gameplay acceptance. PC must compare newest saved Place/real source and integrate at most one non-overlapping slice at a time.
