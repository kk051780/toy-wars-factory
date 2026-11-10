# TRAP RAIDERS: five optional no-key clean-room source receipts

**Scope:** `TRAP_RAIDERS / p0d-siege-v19`. The five source references here are
**NEW independently authored replacements**. Their five historical encrypted
ZIPs have **NOT** been decrypted or recovered; `21/26` original sources remain
recovered, not `26/26`. This tool does not install or execute a Roblox game.

Authoritative protocol: GitHub Issue #218 OWNER `PUBLIC_SOURCE_V1` and the
canonical fixed source-delivery verifier. Do not replace the original 21-packet
intake tool or change its result. The PC report in Issue #218 recorded
**21/21 original packs and 321 files received and SHA-verified on Windows**;
that milestone is separate from the five alternatives in this package.

This optional tool fetches the five clean-room source candidates from public
GitHub by **frozen 40-hex commit**, verifies the exact pinned manifest SHA256,
checks every declared source path, size and SHA256, rejects extra files,
symlinks and unsafe filenames, and stages verified files in a **new isolated**
folder with a separate `RECEIPT.json`. It uses no AES keys and no credentials.
The temporary bare Git folder is cleaned after staging, with a Windows-safe
read-only Git pack file removal fallback. The output folder is atomically
renamed into place, never overwritten or silently merged.

## Owner-controlled Windows Codex usage

From the directory containing `tools/verify_candidates.py` and `candidates.json`:

```powershell
python -m unittest discover -s tests -v
python tools/verify_candidates.py --output C:\Temp\TRAP_RAIDERS_FIVE_ALTERNATES
```

Optionally use `--packet P0D-D16-GLIDE-PERMISSION-CLEANROOM-20261110-01` to
fetch one candidate. Output parent must exist; output must not exist.
Python >=3.10 and Git required, public network access to GitHub required.
No network is used by ordinary unit tests (which use synthetic local Git repos).

**Do not run this from the live PC game checkout.** The program does not touch
`main`, Studio, existing sources, protected CAS locks, accounts or live Roblox.
The tool's successful receipt means **source transport only**.

## Precedence and next gate

1. Prefer any later exact-original historical source repack over a clean-room
   candidate; compare provenance and real current PC code. Select **at most ONE**
   implementation per feature (D14 seats, D16 scale, visual, clock, glide).
2. Keep D16 components disabled unless authoritative server event mapping,
   TTL, client display and anti-replay are reviewed. Avoid duplicate D08
   event choosers; do not trust client state.
3. Windows Codex verifies real Luau parse and Studio 2-client, mobile landscape,
   Play/Stop/save/normal close for each explicitly selected feature.
4. Never mark `STUDIO_QA_PASS` from this tool. No automatic merge, publish,
   purchases or changes to five Automations.
