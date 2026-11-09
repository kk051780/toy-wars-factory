# TRAP RAIDERS P0-D D16 client visual-replica addon — encrypted handoff

This is **only a reference package** for the second D16 slice, `P0D-D16-VISUAL-REPLICA-20261110-02`. It is not the previous D16 pure FSM, not a replacement for the PC game's latest local source, not a Studio verification, and never a remote execution request.

## Immutable payload and verification
- Encrypted source file: `handoffs/TRAP_RAIDERS_D16_VISUAL_encrypted.json` on this isolated branch
- Game: `TRAP_RAIDERS`; work_id: `p0d-siege-v19`
- Expected private ZIP: `TRAP_RAIDERS_D16_VISUAL_REPLICA.zip`
- ZIP SHA256: `31a53ead53095152ac57d2b0ee49b49c37477c5341ef0bdd25c8c463fd911d7d`
- Manifest SHA256: `d24a42b3bce31dbef576c2e2977adce83f27185465499909cc846e48d6b9b343`
- AES ciphertext SHA256: `2aa07608f723432f84b0bc14cbd3bd1e3264db164eb577811d96d35e880f14b1`
- JSON file SHA256: `f121a2f14271a3c8b4d6a0d4d1886526c839aea285849b4cab0e3df172f979ea`
- 15 files plus BUILD_MANIFEST; 57/57 offline Python tests PASS (reference only); corrupted archive/manifest, path traversal and wrong decryption key are rejected
- **NOT TESTED**: Windows decrypt, actual Luau parse, real Roblox Studio, R6/R15 avatar visuals, mobile FPS, multiplayer, physical mobile, publish, revenue, GitHub P0-A protected source review.

## Function and compatibility
Existing first D16 pure server FSM: immutable `7242b32760327a527b868f5405d7782265388fe2`. This new addon contains pure client display policy, client-only translucent non-colliding replica renderer, optional guarded bootstrap and **server-only pure snapshot->TTL bridge**. Character originals are never physically resized or given abilities. The renderer limits ghost parts to 8 nearby players x 18 BaseParts with 90-stud visibility; actual visual performance must be verified in Studio.

**Critical clock mismatch resolved in contract**: earlier ScaleFxCore expiresAt is in server round-elapsed seconds. The new adapter must calculate remainingSeconds = expiresAt - serverRoundElapsedSeconds using the SAME authoritative server clock; client counts down relative to local os.clock(). Never compare raw expiresAt against client os.clock() or Unix time. It makes no new D08 event chooser, does no RemoteEvent send and does not take player-supplied damage or stats. Trusted server adapter and genuine PC paths still need to be implemented/verified by Codex, not by this packet.

## Owner-initiated Windows Codex restore
1. Get this JSON from **the exact immutable commit** linked from #218 after verification. Download the generic approved restore helper from `db734240f0157cc125b563656dbd09668226f3ab/tools/restore_handoff.py` or separately reviewed safer v43-A tool.
2. Obtain a fresh **D16-VISUAL addon-only** 256-bit key privately from OWNER; it is not on GitHub. Do not enter it in a checked-in command, PR, issue, CI, log or shell argument. Use the helper's `CHAT_CODEX_HANDOFF_KEY` local environment mechanism (if locally authorized).
3. Decrypt into a new empty sandbox path, compare restored ZIP SHA and BUILD_MANIFEST hashes **before** extraction, and rerun `python -m unittest discover -s tests -q` (expected 57). Stop on any mismatch.
4. Read current v37 PC CHECKPOINT/RESUME, full game/Place SHA and ownership before considering any integration. Respect v37 final QA -> v39-H1 -> v43-A -> later conflict review; this addon is optional and lower priority.
5. In a separately saved unpublished Studio test, inspect the Luau scripts/real game paths; verify replicated RoundId and server-owned event, 8-second TTL, two-team animations, respawn/leave/round-change cleanup, ghost parts noninteractive, R6/R15 and mobile FPS, no live Character properties modified. Record output, Play/Stop, save, normal Studio exit and PID disappearance. Do not pretend Python proves Studio functionality.

**Safety holds:** PUBLIC repo has only ciphertext and safe documentation, never commercial Luau/.rbxlx/plain ZIP/credentials. No main, merge, Roblox publish, paid upgrade, real payment, unauthorized P0-A CAS, automation changes or Studio control. #218 is the shared coordination board, #213 gameplay evidence and #217 safe cross-P0 handoff.
