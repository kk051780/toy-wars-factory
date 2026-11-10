# Original source retransport without AES keys

- Game `TRAP_RAIDERS`, existing work `p0d-siege-v19`
- New `packet_id`: `P0D-D15-TRAP-RESCUE-LIBRARY-RECOVER-20261110-01`
- Old `packet_id`: `P0D-D15-TRAP-RESCUE-20261110-01`
- Original unencrypted owner Library ZIP: `TRAP_RAIDERS_D15_ChatLead.zip`
- Old ZIP SHA256: `0043b59baffb8de487eb216505ef1bef6652b7147f30f7e9e824014727216cd1`
- Preserved 16 original manifest-listed file byte sequences exactly, SHA verified before public upload.
- Old transport manifest saved byte-exact in `docs/LEGACY_BUILD_MANIFEST.json`.
- Canonical delivery: `PUBLIC_SOURCE_V1`, GitHub independent branch pinned SHA; older AES instructions, seal/restore scripts remain historical only, **no secret key needed**.
- No change to game behavior; a packet source handoff does not prove Windows Codex intake or Studio QA. Main, merge, public Roblox release, purchases, real paid products and shared P0 protection are untouched.
- Source presence and SHA verification is separate from gameplay acceptance. PC must compare newest saved Place/real source and integrate at most one non-overlapping slice at a time.
