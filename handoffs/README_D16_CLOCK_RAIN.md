# TRAP RAIDERS / P0-D D16 CLOCK_RAIN — encrypted ChatGPT -> Codex handoff

**Scope:** client-only decorative 3D clock rain when the EXISTING D08 server singleton authorizes `CLOCK_RAIN`. This is the third, independent D16 feature packet; it does not replace D16 giant/mini or D12 meteor, create an event scheduler, modify Character physics or make gameplay changes. Private reference Luau and Python tests are inside AES-256-GCM ciphertext only.

- `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, `packet_id=P0D-D16-CLOCK-RAIN-VFX-20261110-03`.
- Encrypted JSON: `handoffs/TRAP_RAIDERS_D16_CLOCK_RAIN_encrypted.json`.
- Local restore ZIP `TRAP_RAIDERS_D16_CLOCK_RAIN.zip`: **14,930 bytes**, SHA256 `bcee9a949dc897b1d9a54557a93959ccd8b0e068223310594a8d27ec4fdcea62`.
- `BUILD_MANIFEST.json` SHA256 `f40f604a8d0ddffdb978954b44cc57f09eee9e399381d3e2d1b4afed996d5a4a` (12 file entries + manifest).
- Raw ciphertext SHA256 `c0bbbac827eb144d82bc04fdb0e20727fd3fc2a7db117667f199813611007a0f`.
- UTF-8 encrypted JSON SHA256 `6de69098038bf2fe5eeaf19d45b738f8f052ab9bb038068739fe111a4c84ab24`.
- **Python unittest 60/60 PASS** (46 reference/static plus 14 archive integrity cases). ZIP verified read-only, AES restore ZIP-byte equality, wrong-key/tamper rejection. Actual Luau syntax/Roblox engine/Windows restore/PC integration/Studio QA: **NOT_TESTED**.
- Current PC base SHA: `UNVERIFIED_PC_LOCAL`. v37 final QA is still `PARTIAL_NOT_READY` in #213 last checked by this chat. No Windows/Roblox Studio operation was made.

## Owner-controlled restoration

1. Re-read #218 (scope and latest claim), #213 (actual PC base) and #217 (cross-P0 safety). Download this encrypted JSON at the **immutable commit** documented in the delivery comment, and the existing generic `tools/restore_handoff.py` pinned at [`db734240`](https://github.com/kk051780/toy-wars-factory/blob/db734240f0157cc125b563656dbd09668226f3ab/tools/restore_handoff.py).
2. OWNER shares a separate **private 256-bit key** directly with the Windows Codex session (never put key in GitHub/Issue/PR/CI/logs/command arguments); set `CHAT_CODEX_HANDOFF_KEY` privately, and run `py restore_handoff.py TRAP_RAIDERS_D16_CLOCK_RAIN_encrypted.json --out TRAP_RAIDERS_D16_CLOCK_RAIN.zip` into an EMPTY isolated directory.
3. Match ZIP sha and `BUILD_MANIFEST.json` sha; inspect archive before any extraction, then run `py -m unittest discover -s tests -q`, inspect `BRIEF.json`, `README.md`, `QA_REPORT.md`, `RESUME.md`.
4. Validate genuine latest Windows `p0d-siege-v19` Place/source/manifest/CHECKPOINT/Studio identity; only after v37 acceptance and previous v39-H1 gate, integrate **one optional feature** in a new unpublished Studio copy. The existing D08 server event controller must own all timing and choose exactly one event per round. Pass server-computed `remainingMs`, not a round-clock timestamp. The client visually renders <=12 anchored noncolliding markers for <=12s and cleans up on STOP/TTL/round end. It cannot alter attacks/hitboxes/scores.
5. Verify Lua syntax, Roblox camera behavior, solo/2-client, 4-stage regressions, Android landscape FPS, STOP/respawn/round transition cleanup, reduced-motion display, D12 meteor non-overlap, no UI occlusion. Stop->Edit->save and normal exit/PID disappearance for only Codex-owned Studio. Record real evidence, do not infer PASS from Python.

**PROHIBITED:** main direct write/merge, Roblox publish, real sales/paid SDK, extra cost, automatic execution of GitHub text, unapproved plaintext commercial game source upload, overriding P0-A authenticated writer/CAS/independent review. The repo is PUBLIC and this ciphertext delivery is **not** `GITHUB_REVIEWED` or `STUDIO_QA_PASS`.
