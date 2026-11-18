# EGGRUMBLE Lobby Social/Trade continuation (2026-11-19)
FEATURE_ID: GQ8_LOBBY_SOCIAL_TRADE_20261119

## Scope and provenance
- Branch based on PR #826 immutable HEAD 271f6125ebe9031aa0ca1ed807c10ca417c695c1.
- Parent #826 true Real48 includes original Real44 gameplay + exact original #808 catalog/view + #816 read-only shop. Preserve all 48 bytes.
- 2 genuinely new source routes: ServerScriptService/GQ8_LobbySocialPlaza (studio-only visual 4 meetup markers, three trade category booths, two-player opt-in photo) and ReplicatedStorage/GQ8Trade/GQ8_TradePolicy (pure, unconnected barter proposal).
- Do not recreate any combat/Host/Store/ResultService/Swarm/guardians/shop/skill-match systems. No new Remote, DataStore, payment or inventory owner.
- ON = optional 50-source private Place. OFF = source-identical original 48-source Place, no new routes.

## Experience
Players meet at 4 identifiable areas, see weapon/beast/guardian showcase areas and can voluntarily trigger a two-player free photo effect. No persistent history, friends API, teleport, chat, shop payment or live trading is asserted.

## Safe trade implementation contract, for later existing Store integration
1. Server reads two trusted account inventories with active session locks, unique immutable item instance IDs and versions.
2. Users open a one-time tradeId. Ownership and item category/availability verified on the server. Both sides contribute at least one item (no one-sided gifts by default). Neither protected starter/equipped/bound item nor in-game Robux is traded.
3. Editing either offer clears all previous locks and confirmations. Both users lock, wait 5 seconds, then separately confirm the unchanged revision.
4. Policy returns an INTENT only. Actual authoritative ownership and wallet snapshots must be rechecked under the existing Store single writer; persist idempotent transaction intent journal and recover split/partial saves on reconnect before allowing possession changes. Do not rely on sequential two-player UpdateAsync calls as an atomic transaction.
5. Only existing Store, after durable settlement receipt, marks trade settled. On disconnect, stale lease, server failure or bad replay fail closed without item change; log tradeId and both user IDs. Add trade history, report/block controls, rate limits and child-access rules.
6. Avoid off-platform deals, paid/random trade exchanges, hidden-value pressure, false scarcity. Show distinct rarity visuals and item unique ID, with accessibility text. Existing purchased entitlements/trade restrictions remain owner-controlled; premium paid cosmetics default non-tradeable until explicit policy.

## Gap
This is a genuine private source implementation + native build target, NOT yet a working player-to-player inventory transfer: wallet, durable journal, real preview of owned inventory, trading screen, cross-server sessions, and Store ownership are not integrated. No Roblox production or author acceptance. Preserve ROJO/source-lock/rollback and #220 fresh expected-SHA CAS requirements. No main, Robux, Publish or formal RC writes in this PR.
