# D14 seat authority handoff QA gates

## Offline source checks performed by the author

- Python 3: `python -m unittest discover -s tests -v`
- Verify canonical `BUILD_MANIFEST.json` includes five source/docs files.
- Fixed-commit GitHub remote readback must match each file SHA256 and byte size.
- Source is original clean-room text (no third-party assets, personal records,
  license-restricted source, private keys, Lua remotes, sounds or Place files).
- No edits to old SeatReference encrypted JSON. No claim of exact recovery.

## Windows OWNER Codex (not yet performed)

- Snapshot latest real PC Place, source and CHECKPOINT/RESUME/QA manifest.
- Compare original SeatCore if actually recovered, decide ONE seat authority.
- Review integration contract with D14 RAFT/RIDER/CART and one server-approved
  occupant roster; do not trust a client-side boolean as the `server_...` gate.
- Parse Luau and test in isolated unpublished Studio. Reproduce 2-player join,
  duplicate seat rejection, driver leaving, disconnect/respawn, round reset,
  stale replay, player on another vehicle and actual Seat/Weld cleanup.
- Verify no unintended physics control, real server authority, mobile HUD,
  saved Place, re-open, normal Studio closure/PID lock disappearance.
- Add genuine PC metrics to #213/#218; until then mark Studio NOT_TESTED.

## Hard HOLD

No direct main writes, merges, Roblox publication, spending, key sharing,
protected CAS changes or double installation of two seat authorities.
