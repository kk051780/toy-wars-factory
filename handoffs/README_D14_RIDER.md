# TRAP RAIDERS P0-D D14 Rider Attach safety — encrypted reference handoff

- game_id: `TRAP_RAIDERS`
- work_id: `p0d-siege-v19`
- packet_id: `P0D-D14-RIDER-ATTACH-SAFETY-20261110-04`
- feature_id: `D14` (additional subpacket; never count as an extra finished feature)
- ZIP SHA-256: `11b7bae8ce25d48e2ba813058583f3a882a4bf19890ca6e004a9e519647616fe`
- SHA manifest SHA-256: `b674aa84ccf9f247c591f06ba284fd2f8b7f86066f24341e772e65edfa5688a7`
- ZIP bytes: `16745` / ZIP entries: `14` (sources, tests, docs and BUILD_MANIFEST)
- Encrypted JSON SHA-256: `50e8fed1df2975015766951f4724db50458fdf367972d381c62ab227b49a5e74`
- AES-GCM ciphertext SHA-256: `ba3c27a3be5202c565cfcfe69d252948fb5b6a5954cd018c30468139968637d1`
- Offline Python unittest: **94/94 PASS** (60 behavior, 19 source-shape, 15 archive/integrity). Correct-key ZIP byte-exact restore PASS, wrong-key/tamper rejection PASS.
- Windows restore / genuine Luau parser / Roblox Studio / physical rider moving / 2-client / mobile / Studio exit: **NOT_TESTED**.

## One-time private restore (OWNER → Windows Codex)

This PUBLIC repository contains only ciphertext JSON and this safe README. The private source ZIP and AES-256-GCM key are NEVER placed on GitHub, CI, Issue, README or logs. Use the separately delivered per-packet 256-bit key in the OWNER's private ChatGPT conversation, provided to the Windows process as `CHAT_CODEX_HANDOFF_KEY`, never as CLI plaintext.

Download the **reviewed generic safe restorer** from immutable commit `d37eec1b653d060ae27568ddcd5f501da9662081` and verify it; in a trusted private directory:

```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D14_RIDER_encrypted.json --out TRAP_RAIDERS_D14_RIDER.zip --expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D14-RIDER-ATTACH-SAFETY-20261110-04 --expect-zip-sha256 11b7bae8ce25d48e2ba813058583f3a882a4bf19890ca6e004a9e519647616fe
Get-FileHash .\TRAP_RAIDERS_D14_RIDER.zip -Algorithm SHA256
```

Verify manifest/path SHA and examine all Luau source before extracting or integrating. Re-run `py -m unittest discover -s tests -q` from extracted source root: expected 94 tests. **Python/static QA != Luau compile != Roblox Studio test**.

## Pure server policy and experimental physics adapter

- `luau/RiderMountPolicy.luau` receives only trusted server-derived current epoch/roster/seat records. Max two occupants, DRIVER plus optional PASSENGER; stage S1/S2; server-issued fresh `issuedAtMs` within 350ms, strict monotonic `seq`, round + vehicle ID + `authorityEpoch`, exact `characterEpoch` and seat epoch, distance <=8 studs, no egg/snare/glide/rewind. Explicit quit/round change or invalid roster immediately detaches, and no refresh for 1500ms expires attachments.
- `luau/RiderMountServerAdapter.luau` contains a **default DISABLED** experimental server `WeldConstraint` bridge to a trusted anchored noncolliding seat mount. Caller must supply genuine `getTrustedSnapshot`, `getSeatPart`, `getCharacter` callbacks; no RemoteEvent can provide authority, no client-position or player-provided CFrame. On physical driver mount failure, detach both and close. This reference does **not** guarantee real 2-person riding, humanoid physics, replication, safe dismount on all R6/R15 rigs, or animation quality.

## Conflict and actual PC acceptance gate

Existing D14 code already belongs to other packets: original two-seat authority `0bcf39c22c583604d72ccac47d29fc9d87b7e662`; cart motion `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12` (old overlapping cart packet SUPERSEDED); raft water motion `027fd926a9d315a84f701086448fa5c1febc6697`; client visuals `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0`. **Do not overwrite those or implement a second seat ledger.**

The latest PC report #213 #6758211567 says v39 saved-Place 2client PASS; v43-A Windows restored and S1 2/3-client **scoped** PASS, but its final saved Place, 4-stage/7-job/mobile regression and owned Studio normal close were still pending in that report. OWNER's Codex should finish the newest genuine PC save/exit first, then inspect D14 original source/SeatCore and enable this in an *unpublished isolated Studio* only if all safety checks pass. Verify alive player response, driver/passenger, respawn, leave, seat swap, invalid epoch/replay, egg/trap/glide, no character freeze or weld leftovers, 2-client and physical mobile FPS; save/quit/check owned PID. Otherwise HOLD and keep bridge disabled.

No main direct push, merge, Roblox publish, real purchase, spending, unauthorized P0-A/B/C CAS or automated Windows execution.
