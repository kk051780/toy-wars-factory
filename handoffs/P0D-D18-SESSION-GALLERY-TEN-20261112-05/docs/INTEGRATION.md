# D18 Gallery — OPTIONAL local-only S1 showcase

`TRAP_RAIDERS / p0d-siege-v19` · studio #219 · independent packet `P0D-D18-SESSION-GALLERY-TEN-20261112-05`.

## What this source does

An actual **local Roblox screen** with a rotating `ViewportFrame` preview for **10 already-authored prototype character IDs**, Japanese captions, six-category filtering, card selection, star favorites during the open UI session, and close. Preview shapes are **new low-cost thumbnail stand-ins**, NOT exact renders/imports of the ten older full 3D source prototypes, and not ten additional accepted 3D characters. The 10 original D18 3D source models remain 10/72 = 13.89%; individual editorial card rewrites remain 78/648 = 12.04%.

**No game ownership or unlocking is displayed or inferred.** All ten are previewable without a purchase, and session favorites are lost when the GUI closes. No permanent favoriting, `DataStoreService`, `RemoteEvent`, trading, purchases, prompts, server authority, anti-cheat, XP, trap/weapon effects, rewards, or published content.

## How to use in an isolated test Place (only after owner/integrator review)

1. Copy `src/D18GalleryCatalog.luau`, `src/D18GalleryPreview.luau`, `src/D18GalleryController.luau` into **StarterPlayerScripts** as sibling `ModuleScript`s; copy `src/DisabledGalleryDemo.client.luau` as sibling `LocalScript`.
2. The demo begins with `local ENABLED = false` and intentionally does not run. Only in an isolated test Place and after explicit integration review, switch it to true.
3. Test 1 client: open gallery, each of seven tabs, ten card selections, 45° rotation, favorite and favorite-only filter, empty-state behavior, GUI close, repeat on respawn and changing mobile orientation.
4. Test native Luau compiler and genuine Roblox engine startup, multi-client interaction, 48px readability, long Japanese labels, controller focus, color perception, viewport fit, GPU/low-memory FPS, accessibility, and actual app behavior. **ALL NOT TESTED in this Chat source pack**.
5. If an existing official #220 RC entrypoint has a newer HUD/UI, **DO NOT** blindly copy this demo; only the sole #220 integrator may include/skip it after reconciling current client UI. Production adoption is optional and must not delay first S1 launch.

## Source provenance and rollback

| Character group | Frozen originating GitHub source | Galley geometry relation |
|---|---|---|
| BE-018 / ZO-054 | `b013f501e6af2b0f1f92ae6ba52e11b239918ac3` | Separate low-cost thumbnails, not original parts copied |
| BE-072 | `69c6ea5dac251bd4bc31d49d3738f6a6949305ee` | Separate thumbnail |
| SP-027 / VE-090 | `e17928f244fb2758bbc6f0d84a084de47d072335` | Separate thumbnails |
| TR-009 / WE-045 | `2c3bac3c6a24640205299175f289835d7de8c50b` | Separate thumbnails |
| SP-081 / VE-036 / ZO-108 | `bbecdf922de2d8b393c66a7bbb49a65e7aab6619` | Separate thumbnails |
| 72 canon designs | `176bfc400ef6ec561b129a8163a0f4776e1b9ee4` | IDs, proper display names, classes and rarity matched |

Rollback: remove four Gallery scripts and only the isolated GUI `D18LocalCollectionGallery`. Previous game content, map, network, ownership, D17, RC and source remain unchanged. `WorldModel` parts exist exclusively under the gallery `ViewportFrame`, not `workspace`.

## Evidence rules

`PUBLIC_SOURCE_V1` plaintext six-field `BUILD_MANIFEST.json`, actual generated catalog repeat-check and Python verification. A Python unit suite tests data shape, class/rarity, hard client-only boundaries, source contracts, negative tamper probes, and extracted ZIP. This is **not** a native Luau or Studio run, not 2-player/mobile performance, and not release approval. Complete **S1** release progress must be copied from #220's own audited gate or `UNKNOWN_PENDING_GATE_AUDIT`; source packet completeness must never be presented as game release completeness.
