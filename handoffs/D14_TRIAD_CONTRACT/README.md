# P0-D D14 CART triad integration/QA — PUBLIC-SAFE, source-free

**Packet:** `P0D-D14-TRIAD-CONTRACT-QA-20261110-01`  
**Game:** `TRAP_RAIDERS`  
**Work:** `p0d-siege-v19`  
**Owner lane:** `P0D-D14-CROSS_PACKET_INTAKE_QA`

This reference accepts **normalized synthetic / sanitized event traces only**. It does not contain commercial Luau, source from other chats, keys, a `.rbxlx`, any private player data, or a self-executing GitHub→PC bridge. It will not claim Studio acceptance. There is **no encrypted payload** because everything here is public-safe QA/code/contract text.

Public source: `tools/verify_d14_triad_trace.py`  
Synthetic fixture: `examples/synthetic_cart_trace.json`  
Regression: `tests/test_verify_d14_triad_trace.py`  
PC Codex interface and QA plan: `docs/INTEGRATION_CONTRACT.md`

Mandatory fixed source references:

- D14 two-seat server authority: `0bcf39c22c583604d72ccac47d29fc9d87b7e662`
- D14 cart server-only rail motion: `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12`
- D14 CART/RAFT client-only visuals: `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0`
- Reject superseded old cart prefab+motion `cae5691b622045af57674d922a08a96764354412`.

Important prerequisite: v39-H1 scoped Studio QA already reported PASS; v43-A candidate S1 2/3-client reported PASS on Issue #213 but final QA, final-save and owned Studio normal exit are pending. **The actual PC state might already be newer; re-read current checkpoint.** D14 is next-tier optional, not a reason to bypass final safety gates.

**Tests:** run `python -m unittest discover -s tests -v`. All tests use synthetic examples. Wrong-team, egg carrier, client authority, off-rail, stale pose, seat replay, bad time, fake room IDs and superseded packets are rejected.

**Status:** `GITHUB_PUBLIC_SAFE_REFERENCE`; `PC_RESTORE=NOT_APPLICABLE`; `LUAU_PARSE=NOT_TESTED`; `STUDIO_INTEGRATION=NOT_TESTED`; `STUDIO_QA=NOT_TESTED`; `REAL_USERS=NOT_TESTED`; `MAIN/MERGE/PUBLISH/SPEND=NO_CHANGE`.
