# TRAP RAIDERS | P0-D D17 Cosmetic Catalog (ChatGPT reference)

Packet `P0D-D17-COSMETIC-CATALOG-20261110-01`; game `TRAP_RAIDERS`, work `p0d-siege-v19`.

## Actual implementation
- Pure Luau `CosmeticCatalogCore.luau`; standalone Python model & tests.
- Five allowlisted *visual-only* items: 1 free starter banner, 2 entitlement-gated future earned cosmetic slots, and 2 explicitly preview-only samples.
- All users may see item previews; only `STARTER` and truly server-entitled items may equip. Future preview-only entries never equip even if a resolver erroneously returns `true`.
- State lives only in the server session; no purchases, paid prices, XP, stamps granting, DataStore, telemetry, sales analytics or actual 3D objects.
- Session max 256 selected players, fail-closed callback errors, dynamic entitlement revocation, disconnect/reset cleanup, max 12 visual particles in display metadata.
- Output does not contain user IDs or a combat stat mutation. Preview is static metadata; Client may **not** decide entitlement or item asset path.

## Dangerous boundary: NOT a ready-made Roblox Store
The server must construct `Catalog.new(ownedServerRosterFn, serverEntitlementResolverFn)` in a trusted server module; callbacks must NEVER come from a RemoteEvent/client table. Codex must wire free-session v39 Stamp reward thresholds from a **true round-finalization source**; never infer rewards based on a user-supplied JSON claim. `egg_glow_amber` / `lobby_plinth_jade` are merely suggested catalog placeholders; they do not automatically unlock at 3/6 stamps without a vetted server grant function.

## Conflict prevention
- Does NOT implement D17 analytics: separate earlier `P0D-D17-PRIVACY-METRICS-20261110-A` chat owns them.
- Does NOT modify D06 SessionStampCore, D10 XP/mastery, D04 HUD/lobby, D13–D16 or Roblox Studio.
- If existing v39/v42 cosmetics exist on PC, inventory source must remain single and shared; no duplicate rewards or permanent store powers.
- No marketplace API, ProductId, Robux price, dynamic asset IDs, external tracking or purchases.

## QA status
- Python reference oracle tests and security-envelope tests only; runs via `python -m unittest discover -s tests -q`.
- `python tools/verify_packet.py TRAP_RAIDERS_D17_CosmeticCatalog.zip` verifies per-file size/SHA, paths and CRC.
- Luau parser/Roblox Studio Play/2-client/actual UI/physical phone: **NOT_TESTED**.
- Current Windows PC base SHA: **UNVERIFIED_PC_LOCAL**.

## Codex acceptance order
Windows Codex should first finish v37 final SHA QA and v39 minimum integration. Then in an isolated unpublished Studio branch, add one **preview-only** card to existing lobby UI with no entitlement/equip, check iPhone landscape. Only then attach `equip` to server-entitlement if a truly trusted v39 grant API exists; test two players, forged itemId, spoofed claimed entitlement and session resets. Stop if no trusted ownership source.
