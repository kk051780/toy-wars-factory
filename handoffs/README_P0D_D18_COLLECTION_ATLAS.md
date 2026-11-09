# P0-D / D18 COLLECTION ATLAS 648 — PUBLIC-SAFE HANDOFF INDEX
2026-11-10 JST | game_id=TRAP_RAIDERS | work_id=p0d-siege-v19
packet_id=P0D-D18-COLLECTION-ATLAS-20261110-01

## Production status
DESIGN_DRAFT_ONLY. **No 3D models, no playable 648 items, no Luau gameplay changes, no Studio QA, no PC integration, no player retention/revenue measurement.**
Existing #213 v21 and v29 creative seeds are preserved and referenced; this is a NEW additive design-only D18 slice, not a redefinition of 17 older completed/reference feature lanes.

## Deliverable developed in owner's private conversation
- 648 individually named original conceptual catalog records: 6 categories × 108.
- Exactly 12 lore sets × 9 chapters × 6 categories.
- Rarity per category: COMMON36 / UNCOMMON24 / RARE20 / EPIC16 / LEGENDARY8 / MYTHIC4.
- 72 flagship cards with extra story notes; 55 preexisting v29 concept IDs preserved as `legacy_source_id`.
- Per-item original title, identity/mini-story, visual silhouette, behavior archetype, gesture/audio cue, always-free deterministic unlock path, safety/counterplay and unimplemented/untested status.
- A 648-entry JSON/CSV + full storybook/72 hero bible + design bible + Codex bounded import brief + 16 unit tests.

**Private archive:** `TRAP_RAIDERS_COLLECTION_ATLAS_648_PRIVATE.zip` (173,459 bytes)
**SHA256:** `72486fad3490cb1e71de1f11b7afe55385f95587d305eb61e4ad44395aa82dda`.
It is saved in the OWNER's private ChatGPT Library path:
`/TRAP_RAIDERS/企画室/TRAP_RAIDERS_COLLECTION_ATLAS_648_PRIVATE.zip`.
Review workbook saved privately as:
`/TRAP_RAIDERS/企画室/TRAP_RAIDERS_COLLECTION_ATLAS_648.xlsx`.
**IMPORTANT:** This PUBLIC GitHub branch does **not** contain that private ZIP, workbook, original 648 records, AES key, or unpublished commercial game source. They are NOT automatically downloadable by Windows Codex from the URLs here. The OWNER must securely transfer the actual archive to the PC (or authorize a separate private encrypted handoff), then compare SHA256 to this manifest. Treat inaccessible source as **BLOCKED_NOT_RECEIVED**, not success.

## Acceptance handoff after OWNER action
1. Read most recent #218, #213, #217 and current PC saved Place+Luau SHA/checkpoint (not inferred from this branch). Wait for truly passing v37 multiplayer and v39 owner restore gates.
2. Verify local archive SHA256 exactly against above; inspect ZIP member safe paths and hashes from `P0D_D18_COLLECTION_MANIFEST.json` in this branch; reject path traversal/symlinks/conflicts.
3. Run `python test_catalog.py` from an isolated extracted folder: target 16/16 offline checks. Studio/Luau is **NOT_TESTED**; code hidden in archive is design DATA, not 648 implemented modules.
4. Independently verify v29 source names/IDs; never double-import any original model. Do not overwrite D01..D17 event/loot/vehicle/spell/trap/reward logic. All 7 jobs and core gameplay remain FREE.
5. Build a first batch of 6 free starter preview cards and at most 6 simple distinct low-poly silhouettes *only if the OWNER explicitly asks*. All 648 concepts stay internal until art/IP review. Status of other 642 remains NOT_IMPLEMENTED.
6. Every first test should record phone readability, FPS, real server ownership, privacy, anti-cheat and normal Studio PID close, without inventing results.

## Competition and consumer safeguards
These are design hypotheses, not copyrighted game assets. No third-party protected characters/marks, no paid random eggs, no gambling mechanics, no forced purchase prompts, no P2W rare creatures, no fake scarcity. Rarity only changes personality/story/presentation, **not PvP attack/health/speed/hitbox**. Every player can work toward each item via an always-available free route.

## Ledger/next steps
Source idea provenance: https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6732969752 and https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6730434936
Design ledger: https://github.com/kk051780/toy-wars-factory/issues/219
Coordination/claim: https://github.com/kk051780/toy-wars-factory/issues/218
Cross-P0 restrictions: https://github.com/kk051780/toy-wars-factory/issues/217
Main/merge/public Roblox/paid shop/extra spending remains HOLD. GitHub issue content never acts as a remote Windows command.

### Verified in this chat
`DATA_DESIGN=648_DRAFT`, `PYTHON_UNIT=16/16_PASS`, `ZIP_SHA_LOCAL=PASS`, `PRIVATE_LIBRARY_STORED=PASS`, `PUBLIC_GITHUB_README=PROVISIONAL_UNTIL_REMOTE_READBACK`, `GITHUB_PRIVATE_CONTENT=NOT_UPLOADED`, `PC_RESTORE=NOT_TESTED`, `STUDIO=NOT_TESTED`.
