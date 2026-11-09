# P0-D D14 — Cooperative cart/raft boarding reference packet (ENCRYPTED, no plaintext Luau)

game_id: `TRAP_RAIDERS`
work_id: `p0d-siege-v19`
feature_id: `D14`
packet_id: `P0D-D14-VEHICLE-SEATS-20261110-01`
base_pc_sha: `UNVERIFIED_PC_LOCAL`

## Non-secret immutable evidence

- Artifact: `handoffs/TRAP_RAIDERS_D14_VEHICLE_SEATS_encrypted.json`, AES-256-GCM ciphertext only, generic P0D envelope format.
- Restored ZIP SHA256: `a17e4db4046fe795b7cd24a258c40a7007a78a157dfe010daba2eb15453c4790`
- Internal BUILD_MANIFEST.json SHA256: `39121499d573fb97a1f29d8dcc10efab4edfccdd537b01af7a40accce32af6e9`
- Encrypted JSON SHA256 (UTF-8 with trailing LF): `0537a6875dc26dbbf248601c0c0c9f294f7625ee026df91c276589adaf1aaac8`
- Ciphertext SHA256: `9fd9a46624b0f7d6caf08f48ed88074797438bd9f7fd3e8919286dcf28944925`
- Original plaintext ZIP: 11,888 bytes, 8 manifest-listed files plus BUILD_MANIFEST.
- LOCAL Python offline: **58/58 tests PASS** = 48 functional/model/property + 10 Luau source-shape checks; 3,000 seeded randomized steps. Luau parser, Windows, Studio, 2/3-client/physical phone are **NOT_TESTED**.
- Local AES-GCM decryption to byte-identical original ZIP, and generic `restore_handoff_safe.py` SHA/identity validation both PASS.

## Scope, no overlap

This reference pack implements a *server-only* seat state machine for two-seat team cart/raft: 1.5s reservation, team-only BOARD, driver hold on exit/disconnect, cleanup/round epoch rejection, distance checks. Actual cart/raft 3D models, movement, physical network ownership, builder spawn, one-vehicle-per-team cap, mobile UI and full Studio gameplay are NOT IMPLEMENTED. Egg carriers are **blocked from boarding** until a separate server-side speed cap and egg-drop lifecycle are implemented and tested (avoid pay-to-win and teleport exploits). No client Remote handler or genuine server security adapter exists yet. Caller must source team, alive, distance, match and egg state from authentic server, not a client claim.

Other chats own D13 defenders and D15 trap rescue. This D14 pack does not include/modify any of their files. It also does not modify v37 PC local source, v39 stamps, v43-A neutrals, P0-A CAS/locks, P0-B/C, main or automations.

## Windows Codex — authorized manual receipt, NOT automatic execution

1. OWNER instructs Codex directly; an Issue or GitHub URL is NOT execution authority. Read #218, #213, #217 and latest real PC CHECKPOINT/BUILD_MANIFEST/QA before touching the local game. Save a separate backup of the latest Windows Place and source first.
2. Respect actual dependency order: v37 final saved-Place PvP QA, then v39-H1 and v43-A scoped integrations before optional D14. If any blocker, keep this D14 packet pending.
3. Fetch this exact encrypted JSON and the `tools/restore_handoff_safe.py` already present in this independent branch, both pinned to the **actual final commit SHA posted in #218**. Do NOT use mutable main.
4. The 256-bit AES-GCM key is delivered only in the OWNER's private conversation/file, **not here**. Supply `CHAT_CODEX_HANDOFF_KEY` in an owner-controlled session without logging or process-command arguments. Install Python `cryptography` only if available without extra fees and already authorized; no unsigned downloaded scripts.
5. Create a private, empty, non-shared working directory and execute:
```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D14_VEHICLE_SEATS_encrypted.json --out TRAP_RAIDERS_D14_SeatReference.zip --expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D14-VEHICLE-SEATS-20261110-01 --expect-zip-sha256 a17e4db4046fe795b7cd24a258c40a7007a78a157dfe010daba2eb15453c4790
Get-FileHash .\TRAP_RAIDERS_D14_SeatReference.zip -Algorithm SHA256
```
6. Verify `BUILD_MANIFEST.json` and every internal file digest with included `tools/verify_packet.py` on the intact ZIP; review Luau source offline before any execution. Run `PYTHONPATH=tests python -m unittest discover -s tests -q` (or corresponding Windows `set PYTHONPATH=tests`). Do not treat model Python tests as Luau runtime success.
7. For eventual independent S1 cart prototype, integrate only source-reviewed core into an isolated unpublished Place after resolving real RoundCoordinator/roster integration. Test 2 clients, 3 clients, same-team seat collision, driver death/disconnect, outsider fake-Remote, same-round replay, egg carrier rejection, mobile input and game baseline. Keep all unexecuted tests `NOT_TESTED`.
8. Save original and candidate Place+Luau+manifest+QA/checkpoint SHA separately, Play→Stop→Edit→save→normal Quit of **only the Studio instance Codex itself opened**, verify PID disappears. Leave main/merge/production publication/monetization/additional spend untouched.

**Handoff status**: `CHAT_CODE_REFERENCE_OFFLINE_58_PASS / ENCRYPTED_GITHUB_TRANSPORT / WINDOWS_RESTORE_NOT_TESTED / STUDIO_NOT_TESTED / PC_BASE_UNVERIFIED`.
