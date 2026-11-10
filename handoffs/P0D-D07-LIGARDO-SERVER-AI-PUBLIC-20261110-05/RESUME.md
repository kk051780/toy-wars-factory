# RESUME for OWNER Codex

**Scoped software delivered, not gameplay completion.** Packet `P0D-D07-LIGARDO-SERVER-AI-20261110-04` is independent from Gorogan's S1/S3 server AI, Ligardo's S2/S4 appearance, and D08/D12/D16 weather.

1. Reconcile PC's latest v39 local source and saved Place SHA with #213, #218. v39-H1 Windows scoped QA PASS exists; the game overall remains PARTIAL_NOT_READY. Don't overwrite newer PC work.
2. Verify encrypted ZIP against immutable GitHub commit, AES-GCM AAD/packet/work/ZIP SHA and internal SHA manifest using safe restore v2. Abort on mismatch or absent private owner key.
3. Inspect actual Luau syntax, round owner, team names, boss event literals and server damage API. Keep D07 event picker singleton and all Gorogan code unchanged.
4. Integrate Ligardo S2 only after source/QA gates and demonstrate two-client actual LOS/telegraph/attack tests. S4 after S2. Do not infer Studio PASS from tests in this ZIP.
5. Save new Place, source SHA, QA and checkpoint. Close only your own Studio normally and verify PID gone. GitHub P0-A gate HOLD -> no unauthorized pushes, no PUBLIC plaintext game assets.
