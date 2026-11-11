# D18 6-family handoff (OFFLINE original source)

## Why this is distinct
This is an independent, optional `D18-COLLECTION-3D-BATCH-ARCHETYPE` lane. It neither adds to, nor replaces, the earlier twelve-character production-source gallery; those twelve original source packs remain frozen. New: six *different* original V7 editorial flagships, data schema, deterministic model Luau generator, six named 3D archetype templates, and next-54 canonical source queue.

Canonical owner atlas: `TRAP_RAIDERS_COLLECTION_ATLAS_648_v8.xlsx` (sheets `看板72`, `V7_看板12種`, `V8_看板72監査`). Pin the actual XLSX SHA256 in the JSON files; a copy of the spreadsheet is not needed for normal compile. The V8 audit tab's old 3D-NOT-STARTED statuses are editorial snapshots, **not live source status**. Current model count is assembled only from fixed previous 12 source receipts plus these six new prototypes. Verify against newest #219 soft-claims before assigning a future row.

## Reproducible authoring
1. Create or edit original character-specific shapes in `data/six_pilot_geometry.json`, preserving exactly three visible signature roles in far LOD. Do **not** substitute an unreviewed generic same-shape model for an editorially unique character.
2. Run `python tools/generate_catalog.py`, then `python tools/generate_catalog.py --check`.
3. Run `python -m unittest discover -s tests -v` and `python tools/verify_pack.py`. Add or modify a single canonical ID only on a **new isolated branch and claim** in Issue #219, not this frozen packet.
4. Optional standalone Rojo `default.project.json` creates disabled-by-default LOCAL showroom source; isolated, **not S1 main/RC**. Manual toggle only in separate unpublished Place after owner and #220 integrator review. The factory rejects non-WorldModel parenting; client code never calls server Remotes.

## Native Studio verification PENDING
- Native Luau parse/type check (not confirmed here), Roblox Studio opening, 6 near/far previews, 48px silhouette against storyboard, phone touch, camera framing and FPS/memory with a real device, two clients, cleanup on view close.
- `Demo.ENABLED=false` as authored. No server authority, no true collectibles, no damage, no unlock/reward/data store, no owner publish permit. #220 may `INCLUDE_OR_SKIP` during a future full RC integration; do not hold S1 first release for this.

## APIs
`Factory.Build(viewportWorldModel, canonicalId, originCFrame) -> model,error`; `Factory.SetPose(model, "idle"|"tap"|"win"|"loss")`; `Factory.SetLod(model, isFarBoolean)`; `Factory.SetYaw(model, 0|45|...|315)`; `Factory.GetStatus(model)`; `Factory.Destroy(model)`. `MAX_ACTIVE=12`, unique Part names, anchored noncolliding primitive parts only. At most 30 Parts per model near and 18 visible far; six prototypes in exact canonical ID list.

## Queue and parallelism
The remaining **54 are NOT implemented**. `data/next54_source_queue.json` contains six independent nine-ID lists, every row canonical ID/name/world/rarity and original silhouette hint. Ownership remains `NONE`. Every chat must read latest #219, claim an individual ID before 3D work, use a new folder/branch and immutable SHA, and never share a write path. Codex/owner should integrate only approved build packets, one at a time, after final gated QA. No background run, no automatic GitHub PR merger, no paid service.
