# GQ805 3D guild shop — additive gameplay showroom, no purchasing

Feature `GQ805_3D_SHOP_KIOSK_RUNTIME_20261118` / Owner #805 / #810 latest DRI / claim #218 comment 6980319997.

**What is new and not a duplicate of #808:** one Studio-only server Script produces a walk-up 3D guild shop near the existing lobby, with 14 visibly distinct miniature guardians (7 original role IDs × 2), seven signs, bounded parts, and a ProximityPrompt. One player-side LocalScript opens the **original #808 ShopView module** on the actual prompt event. Both scripts avoid creation of any new commerce/network/store/combat authority. There is no fake earning, owned item grant, Robux, paid random item, or payment UX.

**Existing source reuse—byte unchanged:** PR #808 pinned `5b829902e2d6de96db8def04dccff974157ae243`:
- `EGGRUMBLE_LobbyShopCatalog.luau` Git blob `f71eb575aacd61dd8ccb7719f7dae4caec5fedcd`
- `EGGRUMBLE_LobbyShopView.client.luau` Git blob `f3cf10c8b0256896e9d194844deda91039429ddc`
- Important: the View contains `return Shop`, and therefore must be **selected as a ModuleScript** named `EGGRUMBLE_LobbyShopView` in `ReplicatedStorage.GQ805Shop`, not run as a LocalScript (source text byte-identical; Luau class selection differs). Catalog must be selected there as ModuleScript. Both runtime scripts herein fail closed if originals are absent.

**Required actual source selection (not done by this PR):**
- `ServerScriptService/GQ805_LobbyGuildShop.server.luau` = this PR `GQ805_LobbyGuildShop.server.luau`
- `StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient.client.luau` = this PR `GQ805_ShopKioskClient.client.luau`
- `ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopCatalog.luau` = original #808 catalog ModuleScript
- `ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopView.luau` = original #808 view **ModuleScript** despite original .client filename.
- Select beside existing **#796 real41** rather than creating a second game/Host or replacing weather child #814. Proposed total 45 scripts, subject to actual composer/runtime source lock checks and superseding new parent heads. Requires authenticated #220 B nonforce fresh expectedSHA CAS, same-HEAD native/Rojo/off rollback, byte artifact. The script part budget is <70 private Studio pieces; no workspace.Gravity changes; no other attributes used as gameplay authority.
- OFF: omit only two new scripts and two reused #808 modules -> exact original real41. Main `rich51` unaffected.

**Status:** actual Luau source produced, runtime dependency contract documented; **formal RC adopted=NO**. Native CI is not equivalent to Roblox Studio/Android/FUN. True wallet, BP award, ownership persistence, guardian AI and Robux receipt all still require existing authorized Store/Result/Guardian owners. No writer authorization, game publication or purchase action by this candidate.
