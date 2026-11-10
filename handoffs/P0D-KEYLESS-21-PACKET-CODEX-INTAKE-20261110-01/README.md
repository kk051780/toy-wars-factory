# P0D keyless Windows Codex intake of 21 recovered original packages

**Game:** `TRAP_RAIDERS` / `p0d-siege-v19`.

This is a GitHub-to-isolated-folder **read-and-verify** delivery utility, not game code,
not an AES decryptor, and not a Roblox Studio validation. It never writes to
`main`, the working game checkout, Roblox Studio, or a shared coordinator.

The input is the already publicly readable set of 21 separately recovered
original package commits described in [Issue #218](https://github.com/kk051780/toy-wars-factory/issues/218).
The tool makes a fresh temporary **bare Git** repository in the destination's
parent, fetches exact 40-character immutable Git commit IDs from the fixed public
repository, verifies all manifest-listed source files by SHA-256 and byte count,
rejects extra paths/symlinks and path traversal, and stages only
verified content into an exclusively created **new, previously nonexistent**
destination. A success receipt is written last, never into an existing path.

## Windows Codex invocation (only when OWNER directly authorizes PC use)

```powershell
python tools/verified_intake.py --output C:\Temp\TRAP_RAIDERS_KEYLESS_21
```

Optionally only one package:

```powershell
python tools/verified_intake.py --output C:\Temp\TRAP_RAIDERS_KEYLESS_ONE --packet P0D-D14-RAFT-WATER-PUBLIC-20261110-05
```

Requires Python 3.10+, Git installed, and network access to the public GitHub
repository; Git credentials are not required. No generic arbitrary URL input is
accepted. Output contains `packs/<packet>/...` and `RECEIPT.json`, and does not
include the temporary Git repository. An existing output path is **always refused**.
An invalid source, missing commit, malformed manifest, extra file, SHA mismatch or
network failure returns `BLOCKED`, never success. No network work is performed by
these offline unit tests.

## Integration gate

Local delivery SHA pass is **not** original ZIP provenance proof, independent
review, Windows game integration, Studio Play/Stop, two-client/mobile QA or
Studio normal exit. The original author reports linked in #218 are still required
for provenance. Save current Windows PC source/Place/CHECKPOINT first and let OWNER
Codex compare the actual source before deliberately integrating each package.
Do not dual-install historical D07 Gorogan AI and its optional clean-room fallback,
or duplicate v40 event scheduler/D08 bridge, or integrate incompatible D14 movement
and seat contracts at once. Preserve all P0-A/B/C CAS/authorization gates, no
unauthorized main/merge/Roblox publish/paid work.

The five still-unverified legacy source packets are listed in `packets.json` but
are **NOT** included in the 21 fetchable entries. D14 RAFT/RIDER recovered source
can be fetched; D14 SEATS and four D16 legacy packages remain separate tasks.
