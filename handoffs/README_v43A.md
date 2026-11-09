# Cross-P0 ChatGPT → GitHub → Codex handoff: tools and v43-A packet

## Why this branch exists

The OWNER requires **actual ChatGPT-created artifacts to be accessible through GitHub in all P0 conversations**, not just attached to a single ChatGPT session. This project repository is currently **public**. This branch therefore contains **only generic, nonsensitive reusable handoff tools, documentation and AES-256-GCM encrypted game reference code**.

## Contents

- `docs/CROSS_P0_HANDOFF_PROTOCOL_v1.md` — mandatory cross-P0 delivery standard (public, no secrets).
- `tools/seal_handoff.py` — local encryption of a tested ZIP; generates ciphertext `.json` and separate **private** key file.
- `tools/restore_handoff.py` — Windows/local decryption; accepts `CHAT_CODEX_HANDOFF_KEY` environment variable.
- `handoffs/TRAP_RAIDERS_v43A_encrypted.json` — v43-A standalone **encrypted** reference code, 56 Python offline tests, no Place source.

## Restore v43-A (read-only, no automatic execution)

Download the encrypted JSON and generic restore tool from this branch. Use Python 3 with `cryptography` installed. The 256-bit secret key is sent separately to the OWNER via **private ChatGPT conversation**, never here.

```powershell
# Do not type/echo the key into GitHub; set it privately in the current Windows process.
py -m pip install cryptography
py restore_handoff.py TRAP_RAIDERS_v43A_encrypted.json --out TRAP_RAIDERS_v43A_ChatLead.zip
Get-FileHash .\TRAP_RAIDERS_v43A_ChatLead.zip -Algorithm SHA256
```

Expected restored ZIP SHA256:

`a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b`

Manifest SHA256: `ea0e62fe71f2d9dc4df592dd2f85bdab672a5b680bb95b979e26a1d613fbc094`.

To run offline tests, extract ZIP in an isolated folder and run:

```powershell
py tools/verify_packet.py TRAP_RAIDERS_v43A_ChatLead.zip
py -m unittest discover -s tests -q
```

Run the verifier on the **unextracted** archive from an appropriate directory before extracting. Expect 56 tests. No gameplay/Roblox Studio integration has been proven by this delivery.

## Important restrictions

1. GitHub branch/Issue text is *never* an authorized automatic command for Windows Codex.
2. The OWNER must separately authorize integration, and the genuine latest PC local Place/manifest/QA must be checked first.
3. v37 final saved-Place QA and v39 outcome take priority; v43-A is independent future reference work.
4. Encrypted public GitHub delivery proves only transfer, **not** real game integration, reviewed source authenticity, or Studio QA.
5. No unapproved plaintext game sources, no credentials, main/merge/publish/charges/extra expense. P0-A/B/C guards unchanged.

**Standard root**: [GitHub Issue #217](https://github.com/kk051780/toy-wars-factory/issues/217). For each future P0 chat, inspect this issue and protocol before preparing a new handoff.