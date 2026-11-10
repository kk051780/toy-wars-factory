# QA

- Verify `python -m unittest discover -s tests -v` (local static/test ZIP only).
- Verify all seven original ZIP SHA-256 values against original Issue #218 deliveries.
- `scan` should only report exact historical originals; no decrypt or network.
- `stage` requires the exact SHA, safe paths, UTF-8 sources, no obvious secrets,
  no encrypted ZIP entry, no symlink and a new output directory.
- Windows Codex must still verify true gameplay source integrity and integration.
- This packet is a locator utility, **not** any of the seven original game packets.
- Actual source readback and Roblox Studio tests: NOT_TESTED.
