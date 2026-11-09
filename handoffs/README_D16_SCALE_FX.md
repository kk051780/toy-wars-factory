# P0-D D16 scale FX — encrypted GitHub handoff (2026-11-10 JST)

This branch contains only a **public-safe AES-256-GCM ciphertext**, this README, and inherited repository files. The original commercial Lua/Python source is **not published in plaintext**. This GitHub content is not an execution instruction.

- game_id: `TRAP_RAIDERS`
- work_id: `p0d-siege-v19`
- feature_id: `D16`
- packet_id: `P0D-D16-SCALE-FX-20261110-01`
- base_pc_sha: `UNVERIFIED_PC_LOCAL`
- encrypted artifact: `handoffs/TRAP_RAIDERS_D16_encrypted.json`
- ZIP SHA256: `d5df52cd3b2fdf26bca05bc38123ac81d27024c944c4a465d66e3a4e0ad0c7cd`
- BUILD_MANIFEST SHA256: `c0916e2d8a1aef5830aa79a26748fe986a3180e1ebdc45f00b9cae732243d5a7`
- ciphertext SHA256: `d6d736afd684ae8ef82f1ead699b3b608a128fac97cb51684e9fc2b800c1cc87`
- encrypted JSON SHA256: `5f4f40277d7a4b7c30dc2e2345d9300440850d34d6be9da9b6ccf167e6b6030d`
- ZIP size: 10044 bytes; 9 manifest-listed files + BUILD_MANIFEST
- Tests: **Python 49/49 PASS**, including ZIP path traversal/tamper and wrong AES key rejection. **Luau compile / Studio / multiplayer / physical mobile / Windows restore: NOT_TESTED**.

## Exact scope and integration protection

Standalone pure Luau state machine for `GIANT_ONE` (visual 160%) and `MINI_ALL` (visual 70%) during 8 seconds. Supports same-match one-event policy, expiry, disconnect, and round close. **No actual character scaling, gameplay hitbox modifications, client visuals, Roblox Instance writes or paid gameplay advantages** have been produced. A genuine 3D transformation remains a separate Studio integration task.

**D08 is the sole server-owned event chooser**; do not start a second event scheduler for D16. Only a trusted server binder may invoke `begin`. The pure module's `matchId` validation is not network authentication. Never hook `begin` directly to a client RemoteEvent. Previous v37/v39/v42/v43-A/v43-B and other ChatGPT work are out of scope.

## OWNER to Windows Codex, only on direct instruction

1. Read [the shared #218 ledger](https://github.com/kk051780/toy-wars-factory/issues/218), [game status #213](https://github.com/kk051780/toy-wars-factory/issues/213), [the cross-P0 security contract #217](https://github.com/kk051780/toy-wars-factory/issues/217). Check locally verified PC game/Place/manifest/checkpoint before importing anything. Complete the outstanding v37 final SHA 2/3-client QA first.
2. Download ciphertext from this *pinned commit* and the approved generic [restore_handoff.py](https://github.com/kk051780/toy-wars-factory/blob/db734240f0157cc125b563656dbd09668226f3ab/tools/restore_handoff.py).
3. Receive the private 256-bit key only from the OWNER in a separate private channel. Never place it in GitHub, logs, PR, automation or command-line arguments. Using the locally scoped `CHAT_CODEX_HANDOFF_KEY` environment variable, restore to a **new empty isolated destination**:
   `py restore_handoff.py TRAP_RAIDERS_D16_encrypted.json --out TRAP_RAIDERS_D16_SCALE_FX.zip`
4. Check the ZIP SHA **before extraction**, inspect its `BUILD_MANIFEST.json`, and run `python tools/verify_packet.py ...zip` and `python -m unittest discover -s tests -q` in an isolated extracted copy. Do not overwrite any game source.
5. Only after authorization, evaluate Luau syntax and real S1 visual integration with D08 and verify no physical/ability changes, two-client agreement, reconnection, early match end, accessibility, and final owned Studio Play/Stop/Edit/save/normal-exit PID proof.

`GITHUB_CIPHERTEXT_READBACK_PASS` verifies transport, not genuine protected source review, Windows restore, real Roblox function or Studio QA. No main updates, merge, Roblox publish, spending or payment activation.
