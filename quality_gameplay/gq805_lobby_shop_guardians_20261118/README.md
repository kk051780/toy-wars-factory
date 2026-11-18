# GQ805 - lobby shop, 7-role castle guardians, earned BP and optional Robux
Source-only, not plugged into playable official RC or real persistent MarketplaceService.

Specification: https://github.com/kk051780/toy-wars-factory/issues/805
Castle attack parent: https://github.com/kk051780/toy-wars-factory/issues/804

### Implemented candidate files
- `EGGRUMBLE_LobbyShopCatalog.luau`: 14 guardians with different personality, weapon, battle behavior, appearance/evolution tier plus weapon/ability/beast/castle/cosmetic items. All have BP acquisition path and proposed Robux product key (real ID deliberately nil). Starter guardian free, role-compatible.
- `EGGRUMBLE_MatchPointPolicy.luau`: server-verified finished-game BP award proposal, win 120, loss 60 plus bounded enemy KO/egg/castle contributions, one match-user unique receipt.
- `EGGRUMBLE_ShopTransactionPolicy.luau`: validates server-account-state for lobby-only BP purchase and returns atomic-store permit. Robux request remains NOT_CONFIGURED; **does not grant** or prompt. User requests cannot update a wallet directly.
- `EGGRUMBLE_LobbyShopView.client.luau`: real Roblox client-only GUI renderer, 6 categories, balance, item lists, labels, in-lobby purchase callback contract. No Remote or MarketplaceService; caller must supply a trusted server shop snapshot and existing authenticated callback.

### Integration required (not complete)
1. Original #482/#489/#487 castle/shop/items/result and #220 current canonical Host **remain single owner**. Never create parallel DataStore, ProcessReceipt, Game, inventory or wallet. Attach ShopView via existing lobby UX on entering the physical shop; confirm currency and item preview. Only existing server-authoritative economy validates user and persists BP balance with inventory in one transactional `UpdateAsync`.
2. Match Host verifies real result and caps awards. Check a globally unique `matchId:userId` and persist award once with balance. Loss earns nonzero BP on full participation, AFK/noshow never earn. Reconcile crash/rejoin/one-session stale proof.
3. Guardian purchase unlocks collection, not separate HP or slot growth. A purchased guardian must equip only one of two active castle slots, spawn from **existing** castle authority and respect #804 2-active/3-per-round. 7 role appearances and tier animations are spec, not finished rigged Studio assets yet. Use original #500 defense, do not duplicate tower/AI. Tier visuals from player mastery (1–9 / 10–24 / 25+) and never skip by payment.
4. Robux path only after valid actual product IDs/price configured in Roblox Creator Hub, proper age/regional policy, one `MarketplaceService.ProcessReceipt` dispatch, saved idempotent `PurchaseId` grant and rollback on failure. Game pass ownership and Developer Product receipts are distinct. No paid random items in first launch. If later introduced, disclose real numerical odds and use `PolicyService.ArePaidRandomItemsRestricted` even for Robux-purchasable currency.
5. Secure service-to-view event, shop open only in lobby, Android fit, item preview full 3D, no excessive permanent HUD. Same HEAD native+Rojo, exact previous-source OFF, #220 authenticated nonforce expected-SHA official RC CAS, Studio 2-client, Android15min, player fun.
STATUS: SOURCE_POLICY_NATIVE_CANDIDATE, runtime wiring=NO, actual purchases=NO, formal RC=NO, Studio=NOT_TESTED; no main/publish/paid.
