# Composite-specific QA and blockers — 2026-11-12 JST

## Confirmed source selection
The actual 30-file source-built FTUE + corrected D07/D08 spatial + lobby composite at `b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc` is reused, with exactly one executable HUD swap. The parent docs `docs/OFFLINE_TEST_LOG.txt` reflect prior parent evidence and are NOT this newly-created candidate's test log. See `docs/INTEGRATION_PROVENANCE.json` and the new full-source test.

## Must not claim
- Both D07/D08 enable and owner-review booleans in Game remain **false**. Presence of original modules is not live boss proof.
- No authenticated latest Windows PC saved Place readback, and no Studio 2-client/mobile, real asset/FPS/Roblox gameplay simulation, server physics or human playability test.
- This is **NOT** a writer takeover of #220, nor official release-ready RC. The independent QA owner must test the **exact new candidate SHA** and later the actual official RC SHA.
- No D11 neutral original, all 7 roles, D14 vehicles, D16 fully adopted scale/weather or D18 full game library are newly integrated by this HUD-only patch.
- No DataStore/paid catalog/wallet/real-user retention evidence is added.

## Review-only adoption path
Only #220 integration writer should select this patch after exact HUD hash preflight or a 3-way merge if a newer HUD exists. Preserve one ServerScript+Remote+HUD authority, re-run original/full-source Python + independent trace + native compile; OWNER directly requests *final only* Windows Studio QA.
