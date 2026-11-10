# Verification gate for the clean-room source receipt

- Frozen registry must contain exactly 5 distinct old IDs and 5 distinct new IDs.
- All 5 must have full 40-hex source commit and 64-hex manifest digest.
- `git fetch` immutable pinned commit; `git ls-tree -z` rejects symlinks,
  submodules, hidden files, path traversal and unlisted source paths.
- Validate exact `BUILD_MANIFEST.json` byte SHA, declared source bytes and SHA,
  source file count/length, and `P0D_PUBLIC_SOURCE_V1` game/packet contract.
- Stage to an isolated previously nonexistent destination. Output folder
  `RECEIPT.json` only after successful verification, atomic rename.
- Windows read-only temporary `.pack` / `.idx` cleanup regression included.
- Unit tests use synthetic local Git repos and never touch public GitHub.
- This is NOT old encrypted ZIP original recovery, Windows real game
  integration, Luau parse, Studio multiplayer or mobile QA evidence.
- No edits to protected CAS/main/PR/other authors/game/Roblox production.
