# TRAP RAIDERS / P0-D D16 free-glide authority — encrypted ChatGPT handoff

**game_id:** `TRAP_RAIDERS` · **work_id:** `p0d-siege-v19` · **packet_id:** `P0D-D16-GLIDE-AUTH-20261110-04`.

The PUBLIC repository contains only **AES-256-GCM encrypted reference code** and this public-safe README. This packet does not implement actual Roblox gliding physics, avatar mesh, UI, animation, server integration or Studio QA. It is NOT a new game baseline or production command. The OWNER must directly authorize the Windows Codex integration.

## Fixed artifact proofs

- Ciphertext JSON: `handoffs/TRAP_RAIDERS_D16_GLIDE_encrypted.json`.
- Private original ZIP: `TRAP_RAIDERS_D16_GLIDE_AUTH.zip`, **11,550 bytes**, SHA-256 **`872e8f9ec5ef38535ee3b295bf301a612e2063835e85cae67ab87bb370aee2cc`**.
- ZIP manifest SHA-256 **`84c5dbed4948b8fcc9e0446250d50840b97897e88cb7f5180581faa20b4faa88`**.
- AES ciphertext SHA-256 **`406e35da49cc579ec506a362f83e959113506e2a5adba24b8c17c9a75493735c`**.
- JSON envelope raw bytes SHA-256 **`8d0a06babd848003f2b51fef44c6b04bdee672a1d64fd62a97c779c986b23691`**; expected Git blob SHA-1 **`5d34fdc5964fe5b4d9f7fde914e3ab3974c75d92`**.
- 9 source/doc/test files plus `BUILD_MANIFEST.json` = **10 ZIP entries**; offline Python tests **62/62 PASS**. Luau parser/compiler, Windows restore, real Studio/2-3 client and physical phone QA are **NOT_TESTED**.

## Boundary, gameplay and fairness

`GlidePermissionCore.luau` is a standalone, deterministic, server-side pure state machine. It accepts a **trusted server-supplied snapshot** of round/player status and emits `START` or `STOP` decisions. Max 5s glide, 25s cooldown **after** stopping, starts only while descending from 3-60 studs. All seven free jobs are eligible, no purchase/XP/permanent power buff. Egg carrier, D14 vehicle occupant, D15 snared player or D09 rewind user must be refused, including cancellation mid-glide. Monotonic round epoch and per-user command sequence reject old requests. Stop on landing/death/team change as the trusted game adapter implements. Output limits `target_horizontal_cap=18`, `target_descent_cap=-10` are **suggested contract values** to validate in real gameplay, not enforced velocities.

**Critical:** the reference module does not distinguish whether its input snapshot is genuine. Codex MUST derive `Player.UserId`, unique monotonic round epoch, clock, height, velocity, egg ownership, mounted/snare/rewind state and alive status **only from server authority**. The client may send solely an intent. Do not accept client-provided authority fields. If physical adapter cannot honor caps and stop requests on the server, do not enable gliding.

No direct changes to D08 weather scheduler, D12 meteor, D13 defenders, D14 vehicle seats, D15 traps, D17 metrics, existing D16 scale/clock-rain, protected P0-A/B/C, original PC Place or Roblox Studio.

## Windows Codex owner-controlled restoration

1. Verify freshest #218, #213, #217 and physical PC `CHECKPOINT`, `BUILD_MANIFEST`, Place/source SHA. Preserve newer PC work. Finish v37 final multiplayer QA before optional features. Integration queue is still v39-H1, v43-A, then further packets by compatibility and OWNER priority.
2. Fetch this ciphertext from the pinned GitHub commit and safe `tools/restore_handoff.py` from approved common protocol commit `db734240f0157cc125b563656dbd09668226f3ab`. Obtain unique 256-bit decryption key from OWNER in private chat. Never put key in GitHub, PR, Issue, CI, shell args or logs.
3. In a new, empty Windows working directory, set `CHAT_CODEX_HANDOFF_KEY` through a local private mechanism. Run `py restore_handoff.py TRAP_RAIDERS_D16_GLIDE_encrypted.json --out TRAP_RAIDERS_D16_GLIDE_AUTH.zip`, verify full ZIP SHA, safe paths/manifest SHA/each file SHA. Never unzip over current source.
4. Re-run `py -m unittest discover -s tests -p 'test_*.py' -q` (62 cases expected) and replay `GOLDEN_CASES.json` against the Luau module inside the unpublished Studio runtime. This verifies reference decisions only.
5. Make **separate physical adapter** with trusted server state, safe gravity/velocity and anti-Remote checks. Test S1-S4, seven jobs, egg pickup mid-glide, mounted/snared/rewind cancellation, rematch/round ID changes, 2/3-client and mobile touch/FPS. Require ordinary Play→Stop→Edit→save→normal exit of only Codex-owned Studio instance and verify PID disappearance.
6. Record genuine test results per stage and updated SHA to #213/#218. `GITHUB_CIPHERTEXT_READBACK_PASS` ≠ `WINDOWS_RESTORE_SHA_VERIFIED` ≠ `STUDIO_QA_PASS`. This packet is `REFERENCE_OFFLINE_PASS` only.

No main push, protected-branch merge, live Roblox publishing, real purchases, added spend or P0-A/C auth/CAS bypass.
