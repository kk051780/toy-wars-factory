# P0-D / D15 Trap–Rescue reference packet (CHAT-LEAD)

- Game: `TRAP_RAIDERS`
- PC work ID: `p0d-siege-v19` (not a new PC game)
- Packet ID: `P0D-D15-TRAP-RESCUE-20261110-01`
- Scope: **D15 only** — trapper chain root, poison damage instructions, rescue, solo escape, anti-stunlock immunity, state cleanup.
- Source: pure Luau reference with Python oracle/tests; **NOT integrated into the Windows latest game or Roblox Studio**.
- Python offline unit/property/safety tests: **80/80 PASS**.
- ZIP SHA256 after decryption: `0043b59baffb8de487eb216505ef1bef6652b7147f30f7e9e824014727216cd1`
- Manifest SHA256 inside ZIP: `bd91ab5cd3132bd80d5c884a757b7822b65af4421b8d653cea682246177d35fb`
- ZIP manifest-listed files: 16 (+ `BUILD_MANIFEST.json`); ZIP 20,919 bytes.
- The `.json` in this folder is AES-256-GCM encrypted source; no key is included. **Never commit the plaintext ZIP/Luau/Place or key to PUBLIC GitHub.**
- The 256-bit decryption key was generated for this particular packet; obtain it from the OWNER's *private ChatGPT conversation* only.

## Windows Codex restore after OWNER direct instruction

1. Do not modify the current local Place. First verify current authentic PC `CHECKPOINT/RESUME/FEATURE_MATRIX/BUILD_MANIFEST` + original ZIP/Place SHA, and create isolated backups.
2. Download `TRAP_RAIDERS_D15_encrypted.json` from the **pinned commit** linked in this handoff. Review the safe restore tool from [v43-A hardened restore handoff](https://github.com/kk051780/toy-wars-factory/tree/d37eec1b653d060ae27568ddcd5f501da9662081) or use the matching common helper (first review its security) from [P0D cross-P0 protocol tools](https://github.com/kk051780/toy-wars-factory/tree/db734240f0157cc125b563656dbd09668226f3ab/tools).
3. Supply the key by private OWNER instruction as process-local `P0D_HANDOFF_KEY`; never put it in command history, CI, logs, a GitHub issue, or the repository. Use private/isolated output folder and fresh filename, check expected packet ID and AAD.
4. Restore to `TRAP_RAIDERS_D15_ChatLead.zip`. Confirm restored ZIP SHA256 exactly `0043b59baffb8de487eb216505ef1bef6652b7147f30f7e9e824014727216cd1`. Run `python tools/verify_packet.py <restored ZIP>` and `python -m unittest discover -s tests -q` after safe extraction.
5. Do **not integrate** before v37 final saved SHA PvP QA and prioritized v39/v43-A checkpoint review. D13 NPC siege behavior is another chat's feature and must not overlap.
6. In a private isolated Studio, integrate only one D15 subfeature after actual round manager/authenticated Player `OnServerEvent` and server-only combat conditions are audited. Do not trust client-supplied team, distance, alive, clock, target or damage. No Remote built into the pure core. Verify 2–3 clients/phone emulator/final game regression. Record QA and owner-only normal Studio close/PID.

## Scope limits and safety

This is **not** seven-job ultimate implementation, Studio asset or completed gameplay experience. It produces bounded `POISON_DAMAGE` instructions; only the game's server-owned combat adapter may actually apply them. It cannot change egg ownership, outcome, XP, Robux or DataStore. The code was not compiled by a Luau compiler and was not Play-tested.

No `main` changes, merge, Roblox publication, monetization, spending, P0-A/B/C shared writes or automatic Windows task.