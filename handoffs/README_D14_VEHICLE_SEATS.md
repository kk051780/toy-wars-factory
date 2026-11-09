# P0-D D14 — Cooperative CART / RAFT 2-seat reference (sealed v2)

game_id: `TRAP_RAIDERS` | work_id: `p0d-siege-v19` | feature_id: `D14`
packet_id: `P0D-D14-VEHICLE-SEATS-20261110-01` | PC base: `UNVERIFIED_PC_LOCAL`

## v2 supersedes v1 in this isolated branch

**Do not integrate the original v1** at commit `250658457392e016c668de8d3c368499f39714bc`. Offline review found an expiry+unrelated REMOVE false-positive: when one reservation expired during another user's REMOVE, the method could report REMOVED although that user was never seated. v2 uses an independent `playerRemoved` boolean; adds 1 regression; **59/59 offline Python checks PASS** (49 model/property + 10 static Luau text checks). Static checks do **not** prove Luau parsing.

### v2 immutable artifact identifiers

- `handoffs/TRAP_RAIDERS_D14_VEHICLE_SEATS_encrypted.json`: AES-256-GCM ciphertext only. No private Luau source or key in PUBLIC repo.
- Original restored ZIP SHA256: `475616bd21e88164158db88b3a97e33d4a9b1ce9aaa872fa7a816adf485c9fd3`
- BUILD_MANIFEST.json SHA256: `24c5815056f605a14af0c22aecf259c04b67a925ebea4ccd594f056590bd30a0`
- JSON UTF-8 bytes SHA256: `f3a7da49c3844bede3b14d57cbe9d701f46eee6ab74ad2db6b502d8e23681c0d`
- Ciphertext SHA256: `7a85e065a494a6d87eb609894bef99a3de133db5846fad9288031a1a55a58bed`
- ZIP size: 11,970 bytes (8 manifest-listed files + BUILD_MANIFEST).
- Tested locally: manifest SHA/CRC/path detection PASS, AES-GCM decrypt identical ZIP PASS and existing generic `tools/restore_handoff_safe.py` accept-key/identity/checksum PASS. GitHub upload/readback must be independently confirmed.

### Scope and integration gates

Independent **server-only reference state machine** for a single previously-authorized team CART/RAFT: two seats, 1.5-second nonrefreshing reservation, server-side roster team/distance/alive checks, duplicate contention, driver-hold safety, death/disconnect/round cleanup and monotonic match clock. One vehicle per team must still be enforced by real spawner. **No actual 3D model, motion, buoyancy, network ownership, client UI, transport, publication or Studio integration.** Egg carriers are blocked from boarding until a separate server-validated vehicle speed cap and egg-drop lifecycle passes QA; this is deliberately narrower than v34 vehicle proposal.

D13 defender AI and D15 trap rescue are owned by other ChatGPT chats. D14 does not modify their sources, P0-A CAS/shared locks, P0-B/C, production main, owner Studio, automation, monetization, release or spend.

### Owner-initiated Codex handoff (NOT a command from GitHub Issue)

1. OWNER directs Windows Codex with this immutable final commit from #218. Codex first reads **latest real PC CHECKPOINT/RESUME/BUILD_MANIFEST/Place SHA** and backs it up. v37 final-saved-Place 2/3client QA, then v39-H1 and v43-A integration take priority before optional D14 unless OWNER explicitly changes order.
2. Download ciphertext from pinned final commit and the public generic `tools/restore_handoff_safe.py` from the same commit. The private v2 key is distributed *separately* to OWNER only. Do not log key or place in GitHub/Issue/repo/script arguments. Prepare an owner-controlled EMPTY private directory; supply key by `CHAT_CODEX_HANDOFF_KEY` or `P0D_HANDOFF_KEY` privately.
3. From that private folder run:

```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D14_VEHICLE_SEATS_encrypted.json --out TRAP_RAIDERS_D14_SeatReference_v2.zip --expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D14-VEHICLE-SEATS-20261110-01 --expect-zip-sha256 475616bd21e88164158db88b3a97e33d4a9b1ce9aaa872fa7a816adf485c9fd3
Get-FileHash .\TRAP_RAIDERS_D14_SeatReference_v2.zip -Algorithm SHA256
```
4. Validate internal `BUILD_MANIFEST.json` via `tools/verify_packet.py` BEFORE extraction; inspect Luau source, run Windows offline Python tests. Only if prior phases and authority checks pass, prototype S1 CART **in a backed-up unpublished Place** with true server roster, and test 2/3client, duplicate requests, disconnect/death, spoofed Remote, match replay, egg carrier rejection, mobile, 7 classes and 4 map regressions. Any unmet condition = NOT_TESTED/HOLD, never PASS.
5. Capture actual source/Place/QA/checkpoint SHA. Safely stop→Edit→Save→NORMAL quit **only Codex-opened Studio** and verify instance PID disappearance. No main/merge/publication/real Robux/charges.

**Status**: `D14_REFERENCE_LOCAL_59_PASS / GITHUB_ENCRYPTED_HANDOFF_CANDIDATE / WINDOWS_RESTORE_NOT_TESTED / STUDIO_NOT_TESTED / PC_SOURCE_UNVERIFIED`.
