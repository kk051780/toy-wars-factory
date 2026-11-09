# P0-D TRAP RAIDERS — D07 LIGARDO (S2/S4) client-only boss 3D reference

**Reference packet:** `P0D-D07-LIGARDO-VISUAL-20261110-03`  
**game_id:** `TRAP_RAIDERS`  
**work_id:** `p0d-siege-v19`  
**PC source SHA:** `UNVERIFIED_PC_LOCAL`

## Exactly what is in the encrypted ZIP

Original, private Luau reference of decorative S2/S4 lightning wyrm (3 modules) plus independent Python oracle and offline tests, QA/BRIEF/RESUME/manifest and archive verifier. One 14/18 anchored-Part *client-only* prefab per received legitimate boss event; static/decorative electric bars. State policy rejects replay/stale round/other stages or bosses and expires <=20 seconds. No external 3D assets, new event chooser, Roblox combat AI, damage, hitboxes, rewards, economy, real purchases, or 3D Studio execution.

**Offline Python unit / state / static / ZIP safety tests:** 82/82 PASS. **Local AES-256-GCM decrypt ZIP byte exact, tamper and wrong-key rejected:** PASS. These are not Luau compiler or Studio tests.

## Integrity evidence

- Encrypted file: `handoffs/TRAP_RAIDERS_D07_LIGARDO_encrypted.json` (PUBLIC-safe ciphertext only)
- Encrypted JSON SHA256: `34eeaf7a9e13d19d9b344d3af7908f1b5da79015c834d5a63b91b6d6ff410850`
- AES ciphertext SHA256: `4484f2100ad40875330c1f71d39a6b7441c1588705e367251c91625eb8e90aff`
- Restored ZIP SHA256: `e2ebc8dc2d6b3d410866aca4e41ad4a13dd00284f25f93c47b01bbc5327995dd`
- BUILD_MANIFEST.json SHA256: `4b5591b7b0a4d537ba1d294ca89d1e934debc88dce656f46ce07dd56a64458ed`
- ZIP size: 16,189 bytes; 12 source/test/brief files plus manifest.

## OWNER-directed Windows Codex intake (HOLD until prerequisites)

1. Latest actual PC `p0d-siege-v19` source/Place SHA and CHECKPOINT first, back up without overwriting. Confirm v37 final saved-Place 2/3-client QA, then v39-H1 (and the v43-A planned gate) before optional D07.
2. Download the ciphertext at this commit and the trusted `restore_handoff_safe.py` from pinned commit `d37eec1b653d060ae27568ddcd5f501da9662081`; independently verify both pinned inputs.
3. In a new OWNER-controlled private directory set `CHAT_CODEX_HANDOFF_KEY` from the owner's **private** message ONLY. Never print, commit, log or publish the key. Never automatically execute downloaded code. Example in an existing trusted workdir:

```powershell
python restore_handoff_safe.py TRAP_RAIDERS_D07_LIGARDO_encrypted.json --out TRAP_RAIDERS_D07_LIGARDO_VISUAL.zip --expect-work-id p0d-siege-v19 --expect-game-id TRAP_RAIDERS --expect-packet-id P0D-D07-LIGARDO-VISUAL-20261110-03 --expect-zip-sha256 e2ebc8dc2d6b3d410866aca4e41ad4a13dd00284f25f93c47b01bbc5327995dd
```

4. Read-only verify ZIP's manifest, paths and SHA, then inspect Luau modules before integrating into private unpublished Studio. Existing v40 single boss-event chooser must map its **actual server event spelling** to display-only `LIGARDO` on stages S2/S4; DO NOT assume a literal canonical event name or create a second chooser. Require genuine server-owned RemoteEvent/round + timestamp; server AI/combat must be independently authorized in a distinct packet.
5. Validate Luau syntax, 2-client boss visuals, warning lifecycle (visual only; no actual attack implication), low-graphics mobile, FPS, remote spam, Stage S1/S3 no-Ligardo, round-end cleanup, restored saved Place SHA. Stop→Edit→Save→normal Quit→verify owned Studio PID ends. Keep `NOT_TESTED` for unexecuted gates.

**Status:** `GITHUB_CIPHERTEXT_REFERENCE` after immutable commit readback; `WINDOWS_RESTORE=NOT_TESTED`; `LUAU_PARSE=NOT_TESTED`; `STUDIO_QA=NOT_TESTED`; `PC_BASE_SHA=UNVERIFIED_PC_LOCAL`. Issue comments are not remote execution commands.

**Safety:** PUBLIC repo has no plaintext commercial Luau, .rbxlx, ZIP or AES key. No main push, merge, Roblox publish, real Robux purchases, extra spend, or P0-A/B/C controls changed. Existing S1/S3 Gorogan visual/AI remains independently owned.
