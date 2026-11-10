# TRAP RAIDERS legacy progression/meteor ZIP source locator

**Supplemental to the existing `PUBLIC_SOURCE_V1` protocol. Not a new protocol, not a gameplay implementation.**

This tool covers **four historical chat-made source ZIPs missing from the 21-original-public-source receipt snapshot**, rather than D14/D16 (which are handled by an existing separate owner tool). The four filenames and expected original SHA-256 hashes are pinned in `tools/legacy_zip_locator.py` based on historical GitHub Issue #213 reports.

The owner ChatGPT Library contains filename/size *metadata* for all four, but reading their actual bytes failed in the current chat with `This Project file does not have an authorized raw-byte materialization path`. Therefore this packet **does not make old game source keyless**, prove original ZIP SHA, decrypt any AES, or grant Studio QA. `VERIFY` requires original ZIP bytes on an owner-controlled PC.

## Supersession and no-collision

`v42-prototype` → `v42.1-progress` → `v42.2-progress-ui` is **one progression lineage**. Import at most one approved current edition, normally v42.2. Never count all three as three independently installed gameplay systems; never duplicate `v40-v42 FairProgressionFallback` or session XP persistence.

`v43b-meteor` is a distinct weather reference, *not* an extra event scheduler. Its event activation must use the single existing D08 canonical event bridge/approved event chooser. No autonomous RNG event loop, HP writer, physical weather damage or real product publication.

## Run on owner Windows PC (no secret files)

```powershell
python tools/legacy_zip_locator.py scan --folder "C:\Path\To\Known\ChatDownloads"
python tools/legacy_zip_locator.py verify --zip "C:\Path\To\Known\ChatDownloads\TRAP_RAIDERS_v42_2.zip" --packet-id v42.2-progress-ui
python tools/legacy_zip_locator.py stage --zip "C:\Path\To\Known\ChatDownloads\TRAP_RAIDERS_v42_2.zip" --packet-id v42.2-progress-ui --output "C:\Path\To\NEW_EMPTY\v42_2_stage"
```

`stage` is a **new isolated directory only** and never touches existing PC source, Studio, main, CAS, cost settings or automations. If the SHA or ZIP safety gate fails, stop; do not guess missing passwords. If a ZIP is absent, its author should reissue an exact original public-source pack, or OWNER Windows Codex may independently reimplement it with a **different ID**, never claiming source identity.

Only after a source bundle is reviewed for third-party IP, secrets and source tests, use the existing fixed `P0D_PUBLIC_SOURCE_HANDOFF_V1` packaging CLI to create a **new uniquely named PUBLIC handoff branch** and verify *all* immutable GitHub files. This helper's SHA check is **not** that final delivery.

### Historical evidence

- v42 initial source ZIP: [Issue #213, 6737764879](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6737764879)
- v42.1 source ZIP: [Issue #213, 6738342174](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6738342174)
- v42.2 source ZIP: [Issue #213, 6738911441](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6738911441)
- v43-B source ZIP and AES GitHub envelope: [Issue #213, 6751793841](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6751793841)
- Canonical no-key game-code contract: [Issue #218](https://github.com/kk051780/toy-wars-factory/issues/218) top and fixed `b519a17a3152613666822b7d9660742f93a739b7`.

Scope: `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`. No changes to other owners' D14 seats or D16 originals, the existing 21-pack intake tool, P0-A/B/C locks, `main`, live Roblox, real charges, or scheduled tasks.
