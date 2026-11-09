# TRAP RAIDERS v39-H1 — encrypted ChatGPT handoff

**Distribution only: encrypted standalone reference code packet. No plaintext game source or Roblox Place is on GitHub.**

- Game: `TRAP_RAIDERS`
- Work ID: `p0d-siege-v19`
- Packet: `v39-h1-chatlead-ref-20261110`
- Source: ChatGPT standalone offline authoring, **not integrated into the latest local game**
- Offline tests: **50/50 Python PASS**
- ZIP SHA-256 after decryption: `7d3c5d5c947530cb1874e7ee7dcf55d712c5c8c3bf6f49e5c25de093a7bc349d`
- ZIP size: **17,743 bytes**
- Manifest-listed files: **16 + BUILD_MANIFEST.json**
- GitHub transport: **AES-256-GCM ciphertext** in `TRAP_RAIDERS_v39_handoff_encrypted.json`
- Security: the 256-bit decryption key is supplied **only in OWNER's private ChatGPT conversation**; it is **never** committed to GitHub.
- Full game source / .rbxlx / real player data: **NOT INCLUDED**.
- Studio QA, DataStore, multiplayer, mobile QA, v37 integration: **NOT TESTED**.
- Existing `main` and P0-A/B/C pipelines: **NOT MODIFIED**.

## Restore in Windows Codex

1. Obtain both files in this folder from the GitHub handoff branch: `TRAP_RAIDERS_v39_handoff_encrypted.json` and `restore_handoff.py`.
2. Ensure Python has the public `cryptography` library: `py -m pip install --user cryptography` (if absent).
3. Set `P0D_HANDOFF_KEY` for the current Python process from the OWNER's private chat. **Never print, log, commit or paste the key into GitHub.**
4. Run `py restore_handoff.py TRAP_RAIDERS_v39_handoff_encrypted.json --out TRAP_RAIDERS_v39_ChatLead.zip`.
5. Require `RESTORED_ZIP_SHA256` to match the value above. Then extract to an isolated working directory.
6. Run `python verify_packet.py TRAP_RAIDERS_v39_ChatLead.zip` and `python -m unittest discover -s tests -q`. Only the latter confirms **offline reference tests**, not Roblox Studio.

## Integration boundary

First finish v37 in the real Windows local `p0d-siege-v19` build. After actual QA, connect the server-only stamp core to **authentic** round finalization evidence. Do not accept client-supplied wins, IDs or actions. `sessionOnly=true` / `saved=false` must be visible. Rewards are free, non-persistent cosmetic previews, never purchased combat power.

This encrypted handoff does not authorize public source release, main merge, Roblox publish, payments, or additional spending. For future frictionless transfers, use an OWNER-authorized GitHub **private repository**; the currently linked repositories are public.
