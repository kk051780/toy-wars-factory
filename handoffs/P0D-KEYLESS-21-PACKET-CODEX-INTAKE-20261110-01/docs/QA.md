# QA / source provenance

- All records must be based on 40-character immutable Git commit IDs in #218.
- This is an auxiliary no-key delivery tool, not a new gameplay reference.
- A new output directory is mandatory; the real PC source tree is not modified.
- Verify every source file is listed exactly once in the original packet's
  `BUILD_MANIFEST.json`, with the exact file size and SHA256; reject extraneous
  package-root files and symlink/mode anomalies.
- GitHub is treated as the original delivery source, **not proof that Studio
  integration occurred**. Preserve exact current OWNER PC revision before any
  one-by-one integration.
- Offline unittest is executable without internet; actual 21-pack fetch and
  verification, Windows Codex intake, Studio Play/Stop, 2-client, mobile,
  performance and normal Studio close: all **NOT_TESTED** until genuine results.
- No modification of another chat's claimed source packages, issue top policy,
  P0-A/B/C locks, main, merge, live Roblox publishing, or paid services.
