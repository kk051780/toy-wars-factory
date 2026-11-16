# EGGRUMBLE V3 — character silhouette + flagship field artwork (isolated source candidate)

Owner scope: ART-SILHOUETTE-FIELD-20261116-A01. Shared non-overlap dispatch: [#218 comment 6903370952](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6903370952). Parent source is existing author [PR #482](https://github.com/kk051780/toy-wars-factory/pull/482), pinned at base commit e84ec789041f510293a3e8490f904692ff075bdc. This is a stacked **SOURCE-ONLY / Studio-private / DRAFT** candidate, not the authoritative RC.

## Real implemented source

1. **EGGRUMBLE_HeroSilhouetteArt.server.luau**: additive and reversible 3D art. Distinct seven-job outlines (武神 full war armor and crest; 魔法使い high collar/robe; 暗殺者 hood and crossed blades; 超能力者 angular energy fins; マッドサイエンティスト reactor and coat; 魔獣使い horns and hide; 呪術師 ritual crown and talismans). Applies to existing SevenHeroArena role statues and player rigs after P0DPreviewRole in the legacy standalone demo and EGGRUMBLE_SelectedRole / EGGRUMBLE_Role in the current V3 live job-selection flow. The existing seven lobby role stands also get separate, distinctive four-piece miniature heraldry. Also supplies a common two-team helmet/armor silhouette to the actual V3 animated AI actors. **The AI armor does not imply a role choice/skill**. Individual role-body cosmetic Parts cap at 13 per player or stand. **NEW**: all 7 roles now wield **distinct three-Part hand-welded visual weapons** (武神・大剣、魔法使い・水晶杖、暗殺者・双刃、超能力者・念動球、マッドサイエンティスト・機械砲、魔獣使い・角杖、呪術師・儀式の大鎌). Body+held weapon max = 16 decorative Parts per actual player, and original non-Handle A/B/C skill Tools remain authoritative; none are replaced. Current V3 lobby also has 7 class-specific miniature totems, capped at four Parts each.
2. **EGGRUMBLE_FlagshipFieldArt.server.luau**: decorations on the **existing** V3 TEAM/BR battlefield: 3 route-specific marker styles, 20 stylized timber/foliage clusters, 10 paired rock groups, one ruined-gate vista, and up to 11 dimensional cornice/gable/crest Parts on each individual castle. These are **decorative only**. At 16 castle roster (V3 assumption) planned budget is 16×11+24+80+20+4=304 cosmetic Parts, bounded by 320 per active arena. Two concurrent mode arenas can double the visible budget; device tests must validate.

3. **EGGRUMBLE_EncounterReadabilityArt.server.luau** (new, exclusive ART-A01): 24 small neutral foot-soldiers per arena get only two subtle armor pieces; **real Humanoid.Died**, not a fabricated KO counter, causes a short KO ring (maximum 8 simultaneous, only near live players). Up to 28 actual world/released eggs carry a removable metallic cradle and jewel. Existing castle vault/deposit stations get a color-coded marker (no changes to pickup prompt or stock), TEAM/BR lobby gates get distinct 3D silhouette frames, and five existing defense stands get colored top caps. Independently, the existing author item preview supports three visually distinct HEAL/DASH/SHIELD pickup ornament shapes (12-item cap, two Parts each), with all pickup effects and prompts remaining author-owned. No new ability, damage, loot spawning, score or UI. Most neutrals remain mechanically untouched; only a capped subset is ornamented.

**Art part budget**: existing field overlay <=320/arena + max 24×2 neutral + 28×2 egg + 12×2 pickup + 16×2 vault/deposit + 2×6 portals + 5 stand discs = **497 conservatively budgeted decorative Parts per arena**. Seven lobby role-miniatures add up to 28 additional noncolliding Parts outside the arena budget, plus at most 8 transient KO cue Parts shared across both modes. This is **not an FPS measurement**. Two simultaneous mode worlds can exceed one arena's budget; device testing and LOD will decide whether to lower limits further.

The style uses warm limestone, slate, fabric and subdued metals with team-readable heraldry. It deliberately avoids always-on nameplate UI, permanent particle/Tween loops, a sea of Neon shapes, unlicensed external assets and opaque blockers in doorways.

## Faster private Studio builds without modifying the original #482 project

Two separate Rojo project files were added inside this isolated directory. Use **only one at a time**:

- EGGRUMBLE_SEVEN_HERO_ART_STUDIO.project.json — original SevenHeroArena + costume/stand source.
- EGGRUMBLE_V3_ART_STUDIO.project.json — original CastleMatchRules/BotPathRouter/BotActors/SwarmCombat/LobbyCastleModesPreview plus the three art scripts.

Both resolve the original #482 sibling files by relative paths; they do not copy or override them. **Compatibility warning:** #482 has advanced beyond the A01 fork and added a required InteractionGuard ModuleScript. This candidate's V3 project reflects its **older pinned parent** and is NOT a runnable current-author build until the original author source-selectively ports the three art Scripts onto the latest #482 project, preserving its InteractionGuard and all other modules. Do not build a runtime match from this stale manifest and claim a pass. On a computer with a verified Rojo installation, build using the appropriate project to an **isolated private** .rbxlx and manually open it in Studio. Do not Publish, replace an OWNER place or silently mark the official RC as updated. Rojo/native build and Studio execution have **not** been performed here, so the project definitions remain unproven candidates.

## Current author source integration without any branch merge

The original V3 art JSON below is a historical, **stale** #482 snapshot and must not be used as current V3 playable evidence. The author now also requires InteractionGuard, SevenRoleCombat and MatchResultService modules. The new `tools/compose_current_v3_art.py` reads a separately checked-out **latest** original #482 V3 Rojo project and grafts only the three art-only Scripts into a *new* file, resolving every source path and validating sibling module imports. It never modifies parent gameplay, RC, or Git branches.

Example from a working directory containing both independent checkouts:

```sh
python3 art/handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116/tools/compose_current_v3_art.py \
  --author-project author/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_V3_STUDIO.project.json \
  --out scratch/EGGRUMBLE_V3_CURRENT_ART_STUDIO.project.json
```

The dedicated workflow additionally retrieves the parent author branch **read-only** and validates this newly generated source mapping against the latest author files. Passing that check is **not** a native Luau compile, a Rojo runtime build, Studio Play, or Android game quality approval.

The standalone item preview is also author-owned. In a **separate private Studio copy**, run its `EGGRUMBLE_FieldItemPreview` with `EGGRUMBLE_FieldItemPickups` and add `EGGRUMBLE_EncounterReadabilityArt` as a cosmetic sibling Script for the nine-item test. **Do not run the item preview together with a V3 game host.**

## Manual private Studio preview, NOT production integration

- Use a **separate private Studio copy**, not the published experience.
- For **7-character art**: install original #482 SevenHeroArena SERVER Script and add EGGRUMBLE_HeroSilhouetteArt as a second SERVER Script to ServerScriptService. Start Studio Play, select a class and inspect its distinctive stand / wearable silhouette. The art script is inert outside Studio.
- For **V3 field/bot art**: install the existing #482 V3 Rojo preview project and add all three art .server.luau files as sibling **Scripts** in ServerScriptService. Start Play, use TEAM or BR lobby portal, then inspect personal castles and paths; only the session's selected arena is built.
- Never run the three alternative #482 preview game scripts together. This art pack depends on source objects produced by those previews; by itself it cannot produce a match.
- For a true end-to-end integration, the original #482 author must review and explicitly wire these layers into the private V3 project, validate conflict-free SourceExact build, then #220's authenticated writer may consider RC intake. **Do not directly edit existing Game/HUD/Rules/BotActors/SwarmCombat/map collisions, fork a second RC, or merge the stacked draft.**
- **Rollback**: delete these three additive art Scripts and restart the test session. They add no persistence, network protocol, collision, Game/HP/egg/score/KO authority, terrain write, shop or paid feature.

## Quality / device acceptance contract

Source-level guardrails: Studio-only, noncolliding/untouchable/unqueryable cosmetic Parts, no local material/shadow heavy loops, per-role and per-arena bounds, existing physical path preserved. Dedicated source CI: .github/workflows/p0d-eggrumble-art-a01-source.yml. Static tests are in tests/test_art_source_contract.py; running them is not the same as running Roblox.

Art design intent: clearly different silhouette from 25–40 studs, appealing near-field armor, meaningful red/blue sides and strong castle approach silhouettes, 3 visible infiltration routes, no line-of-sight loss to the egg vault/gate. **Visual appearance still needs real Studio screenshots before claiming success**. Blocky primitives are a first physical pass, not proof of top-tier detailed mesh/animation design; additional authored mesh, motion and material iteration remains required.

Final #420 separate criteria: PC human art 4.5/5, Android art 4/5, lower-end Android 15-minute median ≥30fps/p10≥25fps, heat degradation ≤20%, crashes 0, first 3-minute fun ≥4/5, plus old/new PC and Android scene evidence. All are internal targets, not measured results. Until independent #420 and #470 plus real OWNER acceptance: **ART_NO_GO / PRODUCT_NO_GO / OWNER_ACCEPTED=0**.

This change does not create a new field or claim an operational 3,000×3,000 stud final environment. The current V3 preview remains a smaller gameplay scaffold. Future larger terrain, real MeshParts, animation and streaming must be owned by their original scope owners and verified on device.
