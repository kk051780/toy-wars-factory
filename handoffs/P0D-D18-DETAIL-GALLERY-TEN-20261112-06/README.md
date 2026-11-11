# TRAP RAIDERS / D18 — 詳細3D 10体を実ソースで鑑賞するギャラリー

**Packet:** P0D-D18-DETAIL-GALLERY-TEN-20261112-06  
**Scope:** `TRAP_RAIDERS`, `p0d-siege-v19`; optional isolated **LOCAL-only** gallery, original full source parts not previous 94-part simplified stand-ins.

- Reuses **exact immutable original nine source Luau files** from five previously delivered packets, grouped under independent module folders so names like `ShowcaseCatalog` never collide; original generated gallery catalog 10 IDs also copied exactly.
- `D18DetailedGalleryPreview.luau` calls each genuine existing factory's `Build/SetPose/SetLod/GetStatus/Destroy`; accepts exactly the established 10 IDs; displays original 10 models (21/16/18/15/21/18/16/13/20/21 Parts, in canonical order).
- `D18GalleryController.luau` retains prior six categories, character selection, local-only session favorites, 45° manual rotation, child-friendly Japanese story and adds **four selectable reaction poses** plus **distant simplified LOD**.
- `ViewportFrame` and `WorldModel` only; stage child `Folder` satisfies original factory constraints. Replacing, rotating, changing pose/LOD, and closing cleans up **through factory.Destroy**, avoiding the old producer's strong `live` counter hitting limits.
- `default.project.json` maps all exact source modules to StarterPlayerScripts but demo `ENABLED=false` and has **no autorun**. Local-only source is a standalone **isolated test Place**, not #220 S1 RC patch; use optional `Gallery.mount(playerGui)` only with #220/OWNER consent.
- No reward, server event, remote, DataStore, shop, paid offer, owned inventory, combat effect, P2W, external asset or copied competitor assets. Preview is free; favorites are not saved; catalog does not grant items.

**Status:** original source bytes and offline tests verified. Roblox Studio real renderer/native Luau/mobile/FPS/2 clients/48px legibility/player preference are NOT_TESTED until final controlled RC QA. Whole S1 release percentage #220 only, not this pack; first release must not be delayed by optional collection content.

See `docs/INTEGRATION.md` and `docs/SOURCE_PROVENANCE.json` for exact source pins, install, guard, and rollback.
