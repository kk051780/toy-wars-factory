# D14 / D16 legacy original ZIP locator (no key)

This **does not decrypt AES** and does not republish game code. It finds and
checks exact historical *original plaintext ZIP bytes* on the OWNER's PC.
Only seven D14/D16 old packets identified in #218 are in scope.

Read-only discovery:

```powershell
python tools/original_zip_locator.py scan C:\Path\To\Your\Saved\Archives
```

Once a matching unencrypted source ZIP is found, stage into a NEW empty path:

```powershell
python tools/original_zip_locator.py stage --zip C:\Path\To\ExactOriginal.zip --packet P0D-D16-GLIDE-AUTH-20261110-04 --output C:\Temp\P0D-D16-GLIDE-AUTH-SAFE-STAGE
```

This command **never** uploads to GitHub or changes the PC game. The author or
Codex must manually inspect content/license/secrets, follow the sole canonical
`P0D_PUBLIC_SOURCE_HANDOFF_V1.md` from commit
`b519a17a3152613666822b7d9660742f93a739b7`, run its package build and
verify, commit to a dedicated branch, and compare **all** files at full fixed
40-digit commit SHA. The legacy ZIP gets a NEW packet ID; no key required.

Results labeled `ORIGINAL_SOURCE_ZIP_VERIFIED` are LOCAL ONLY, not completed
GitHub handoff. `STAGED_UNPUBLISHED_SOURCE` is also not Studio acceptance.
If no exact ZIP is found, mark blocked; never claim an encrypted JSON is usable
as plaintext, guess keys, or substitute unrelated game code as original.

Do not touch `main`, existing branches, Codex PC source, Roblox live release,
paid items, credentials, P0-A/B/C controls, or the five existing Automations.
