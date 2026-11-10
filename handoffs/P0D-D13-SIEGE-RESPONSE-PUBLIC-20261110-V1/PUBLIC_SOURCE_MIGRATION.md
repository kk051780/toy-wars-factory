# P0-D source-only migration — P0D-D13-SIEGE-RESPONSE-PUBLIC-20261110-V1

- Game: `TRAP_RAIDERS` / `p0d-siege-v19`
- Old encrypted packet: `P0D-D13-SIEGE-RESPONSE-20261110-A`
- New public source packet: `P0D-D13-SIEGE-RESPONSE-PUBLIC-20261110-V1`
- Original source ZIP SHA256: `2caba203e55acf1afff12da90ac4dc4de64fcf8e4bafaded4ce8134f90f80ccb`
- Files from original archive: **9/9**, all individual content SHA256 and sizes matched before copying.
- The old `BUILD_MANIFEST.json` is preserved byte-for-byte as `docs/LEGACY_BUILD_MANIFEST.json`; the new root `BUILD_MANIFEST.json` is the **PUBLIC_SOURCE_V1** format.
- **No private AES key is required** to checkout this packet.
- Historical README/QA files may mention AES/private keys; those delivery instructions are **superseded** by P0-D `PUBLIC_SOURCE_V1` protocol in Issue #218.
- This is a source handoff, not a Windows Codex acceptance or Roblox Studio gameplay PASS. Luau adapter checks and protected main/merge/publish gates remain.
- Never publish credentials, player data, other games' nonpublic code or third-party unlicensed assets.
