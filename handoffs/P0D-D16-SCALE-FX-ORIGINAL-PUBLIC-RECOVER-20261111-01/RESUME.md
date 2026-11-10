# D16 isolated handoff resume
1. Reacquire P0D #218 ledger and compare owners/claims. Only use `P0D-D16-SCALE-FX-20261110-01`.
2. On OWNER's Windows Codex, check latest private `p0d-siege-v19` CHECKPOINT/Place/source SHA and protect local files. Do not assume current game is v37.
3. Restore this encrypted ZIP through pinned public helper with separately delivered private key. Verify ZIP SHA and `BUILD_MANIFEST.json` SHA for each file *before extraction* into new directory.
4. Re-run Python tests. Run native Luau parse & Studio acceptance only when authorized.
5. `ScaleFxCore` is pure/server-only; no FX visuals or physical scaling is implemented; D08 selected event is a dependency. Implement visual-only client FX *later* only after reviewing avatar safety and accessibility.
6. Do not replace D08 singleton scheduler. Do not modify core game/Studio outside OWNER's explicit request. main/merge/publish/payment HOLD.
