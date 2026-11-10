# P0-D source-only migration — P0D-D14-CART-RAIL-PUBLIC-20261110-V1

- Game: `TRAP_RAIDERS` / `p0d-siege-v19`
- Old encrypted packet: `P0D-D14-CART-RAIL-MOTION-20261110-02B`
- New public source packet: `P0D-D14-CART-RAIL-PUBLIC-20261110-V1`
- Original source ZIP SHA256: `c38a1536095ce4d64a1691905caff0b055f75038e02354718333ad6a79d88fa5`
- Files from original archive: **11/11**, all individual content SHA256 and sizes matched before copying.
- The old `BUILD_MANIFEST.json` is preserved byte-for-byte as `docs/LEGACY_BUILD_MANIFEST.json`; the new root `BUILD_MANIFEST.json` is the **PUBLIC_SOURCE_V1** format.
- **No private AES key is required** to checkout this packet.
- Historical README/QA files may mention AES/private keys; those delivery instructions are **superseded** by P0-D `PUBLIC_SOURCE_V1` protocol in Issue #218.
- This is a source handoff, not a Windows Codex acceptance or Roblox Studio gameplay PASS. Luau adapter checks and protected main/merge/publish gates remain.
- Never publish credentials, player data, other games' nonpublic code or third-party unlicensed assets.
