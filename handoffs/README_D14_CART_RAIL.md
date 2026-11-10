# P0-D TRAP RAIDERS / D14 CART visual & rail-motion reference

**Game:** `TRAP_RAIDERS`  **Work:** `p0d-siege-v19`  **Packet:** `P0D-D14-CART-RAIL-MOTION-20261110-02`  **Date:** 2026-11-10 JST.

This is a **new isolated ChatGPT implementation**, NOT the cumulative Windows PC source and NOT Studio QA evidence. Public repository contains AES-256-GCM ciphertext only. The OWNER alone receives the private key and optional plaintext reference ZIP via private ChatGPT delivery.

### Separate feature slice (no collision)

D14 prior official packet `P0D-D14-VEHICLE-SEATS-20261110-01` at immutable commit `0bcf39c22c583604d72ccac47d29fc9d87b7e662` owns 2-person seat authorization. This packet does **not** modify that source. It adds **new visual cart body** (stock Roblox anchored, noncolliding `Part`s and two **visual** seat markers) and **pure deterministic one-leg-at-a-time server rail motion** with maximum 16stud/s, max 24 authored nodes and fail-closed stop for unmounted/unauthorized/dead/egg-carrying/snared drivers, stale round/team, replay, invalid dt and server round end. Integration adapter requires callbacks from canonical server state. There is no actual vehicle physics, real player rig/seat, buoyant raft, cart collision, damage, egg movement, paid feature or DataStore.

### QA / checksum facts

- **Python offline reference oracle + static Luau source checks:** 34/34 PASS; randomized 5000-step property exploration; `tools/verify_manifest.py` PASS.
- **AES-256-GCM:** local byte-identical restore PASS, wrong key/tamper rejection PASS.
- **Luau parse, Studio Play, 2client/3client, mobile, physical driving:** NOT_TESTED. Windows PC SHA/base: UNVERIFIED_PC_LOCAL.
- **Private ZIP**: 12,859 bytes, 11 source/test/doc files plus `BUILD_MANIFEST.json` (12 archive entries); SHA256 `740a1aac3be5c743e6220d0d2d5c42e66e523ba0d11c14648eac6cf0604b2695`.
- **Manifest file SHA256**: `ca0e1dc4b972e403a59cdbd05a0d896eb038e339d349367bba4e75ea1cb1117f`.
- **Ciphertext JSON SHA256**: `d1d5d819dfd80a1fbb306e88c1308932e8d228146a3931da61721dc057a38e03`.
- **Ciphertext bytes SHA256**: `d0745aec1420389a85c3a51cb31e4175bb5a3143b4ed2cf7646036cfac4aa7d9`.

### OWNER-direct Windows Codex intake — HOLD until existing core gates

1. Read latest #218 / #213 / #217; verify current PC CHECKPOINT and saved Place/source SHA. Preserve newer local sources.
2. First complete v39 saved-Place critical remaining 2client/reconnect QA; then v43-A neutral ownership safety integration per OWNER priorities. This D14 optional cart is a later and separate one-packet feature; NEVER auto-trigger it based on GitHub issue comments.
3. With OWNER-supplied secret key only through private OS environment variable `CHAT_CODEX_HANDOFF_KEY`, use previously audited `tools/restore_handoff_safe.py` from **fixed** `d37eec1b653d060ae27568ddcd5f501da9662081`, matching exact packet ID/game/work/ZIP SHA, fresh private destination, no overwrites. Do not log or upload key.
4. Validate ZIP/manifest/CRC/path, rerun Python tests, review Luau parser; then only in unpublished isolated Studio adapt to existing D14 real seat ledger and fixed canonical routes. Use 2/3-client attack, quit, team swap, egg carry, false Remote, max-speed/dt, collision, gate and mobile FPS tests. Stop/Edit/Save/Quit only this session's Studio PIDs.
5. Continue with other game source/replication only after manual OWNER sign-off; do not merge, publish, charge, write main or bypass P0-A/B/C protections.

Cross-project protected state, existing automations, main/merge/publish/paid APIs left unchanged.
