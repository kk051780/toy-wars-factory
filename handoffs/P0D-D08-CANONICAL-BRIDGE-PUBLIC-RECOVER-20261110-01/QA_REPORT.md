# D08 reference QA report

- **Scope**: old v40 single-event lifecycle to trustworthy server consumer adapter; NOT a new event chooser.
- Python regression and source-shape tests: **64/64 PASS** (Python independent behavior and static Luau contract tests + ZIP negative tests).
- ZIP file SHA/size and AES-256-GCM roundtrip: Manifest/ZIP SHA and AES roundtrip PASS; immutable IDs are in GitHub README and BUILD_MANIFEST.json.
- Luau actual parser / Windows Codex restore / Roblox Studio 2+ clients / mobile / normal Studio exit: **NOT_TESTED**.
- Real PC code/Place SHA: **UNVERIFIED_PC_LOCAL**. No hidden dependency accepted as PASS.
- S2/S4 legacy boss name: `RAIGALD` vs `LIGARDO`, default BLOCKED pending OWNER PC review.
- WEATHER requires a real approved runtime; default BLOCKED. Existing v40 weather catalog only a reference and not actual game weather effects.
