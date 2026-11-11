# P0-D 企画室｜D18 10体ローカル図鑑ギャラリー

- **Game:** TRAP_RAIDERS (`p0d-siege-v19`)
- **Packet:** `P0D-D18-SESSION-GALLERY-TEN-20261112-05`
- **Owner lane:** `CHAT-PLANNING-D18-SESSION-GALLERY-20261112-05`
- **Status:** ORIGINAL SOURCE HANDOFF, opt-in, disabled demo; not part of S1 RC.
- **Delivery:** public plaintext source; no encryption, AES key, passwords or secret URLs.

## New behavior — actual Luau source

- Existing ten D18 original source-prototype identities from six categories shown in one independently authored **responsive local collector gallery**, with **10 separate lightweight 3D thumbnail stand-ins** in a `ViewportFrame` / `WorldModel`.
- Tap character card to inspect its ID, name, category, world and rarity; rotate preview 45° each tap; filter by six categories; star session favorites and show only favorites; explicit empty-state; close and destroy gallery.
- All ten are **free to preview** but do not imply any unlocking, ownership, availability in-game, save or market promise. Favorites live only in the GUI state for this session and do not persist.
- No combat effect, trade, server Remotes, data store, inventory authority, reward, pay-to-win, premium purchase, subscriptions or random loot-box mechanisms.

## Contents

`data/gallery.json` is the source for `src/D18GalleryCatalog.luau` (deterministically generated), `src/D18GalleryPreview.luau` constructs anchored non-colliding thumbnail parts only inside local ViewportFrames, `src/D18GalleryController.luau` creates the local GUI, `src/DisabledGalleryDemo.client.luau` is **OFF** by default. `tools/generate_catalog.py`, `tools/verify_pack.py`, `tests/test_gallery.py` and the immutable strict `BUILD_MANIFEST.json` provide reproducible evidence.

These ten thumbnail models are **not a replacement** for original full detailed D18 model packs and do **not** increase the canonical 3D source-model count: **10/72 (13.89%) remains unchanged**; 72/72 flagship editorial designs, 78/648 individually edited collector entries. See `docs/INTEGRATION.md` for exact source commits, opt-in mount, and genuine Roblox native/mobile/child QA that has *not* been done.

Safety: no changes to main, #220 exclusive RC, P0-A/B/C CAS/security, 5 scheduled automations, Roblox live publishing or spending. #220 integrator alone decides whether to include/skip; first release never blocked by optional gallery.
