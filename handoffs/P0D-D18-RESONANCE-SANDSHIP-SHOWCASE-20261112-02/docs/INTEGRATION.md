# Optional Studio acceptance (OWNER directly requests final RC QA only)

Keep the three Lua files as siblings in a standalone isolated unpublished Studio test. `ShowcaseCatalog` and `ShowcaseFactory` are ModuleScripts, `ShowcaseDemo` is a disabled Script by default. Do not edit the current source-built S1 Game/HUD/D07-D08/D11/D14/D17 or map. No Rojo live mounts or automatic world insertion in this handoff.

1. Verify all manifest bytes/hash and `python tools/generate_catalog.py --check`. Keep source pinned to immutable 40-digit delivery SHA.
2. At an authorized later final-assembly stage, compare real PC baseline, clone to an **isolated Place** and only then enable demo manually for controlled QA.
3. Confirm exactly 15 near/12 far visible pieces for SP027 and 21 near/15 far for VE090, no collisions/touches/queries, 16-model budget, pose and LOD idempotence, Model Destroy cleanup, no new Remote or replicated game authority.
4. Confirm on low-end mobile and 2-client emulator that geometry is correctly staged, silhouette at 48px, not blocking team/egg/BOSS UI, FPS, zero interference with player movement or objectives. Run negative tests for invalid IDs/poses/non-model instances.
5. All sales, game publish and monetization remain OFF. Actual real players/retention/revenue are UNKNOWN until after release and consent-appropriate measurement. The S1 single integration owner #220 alone chooses INCLUDE/SKIP; safest initial S1 choice is SKIP if uncertain.

Rollback: remove the three optional Luau files, leaving all S1 gameplay unchanged. This does NOT run Codex, create Studio apps, authorize ROBLOX publishing, or unlock purchases.
