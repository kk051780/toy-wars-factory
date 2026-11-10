# Original source retransport without AES keys

- Game `TRAP_RAIDERS`, existing work `p0d-siege-v19`
- New `packet_id`: `P0D-D11-NEUTRAL-SKIRMISH-LIBRARY-RECOVER-20261110-01`
- Old `packet_id`: `v43A-neutral-skirmish-chatlead-20261110`
- Original unencrypted owner Library ZIP: `TRAP_RAIDERS_v43A_ChatLead.zip`
- Old ZIP SHA256: `a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b`
- Preserved 16 original manifest-listed file byte sequences exactly, SHA verified before public upload.
- Old transport manifest saved byte-exact in `docs/LEGACY_BUILD_MANIFEST.json`.
- Canonical delivery: `PUBLIC_SOURCE_V1`, GitHub independent branch pinned SHA; older AES instructions, seal/restore scripts remain historical only, **no secret key needed**.
- No change to game behavior; a packet source handoff does not prove Windows Codex intake or Studio QA. Main, merge, public Roblox release, purchases, real paid products and shared P0 protection are untouched.
- Source presence and SHA verification is separate from gameplay acceptance. PC must compare newest saved Place/real source and integrate at most one non-overlapping slice at a time.
