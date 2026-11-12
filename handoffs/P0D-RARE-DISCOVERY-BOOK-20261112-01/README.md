# TRAP RAIDERS — レア幻獣「発見ずかん」＆2人Studio観測場（独立・実装ソース）

Owner Issue #236, parent #232, master World Field #222, product #219. Optional **S2+** only. Do NOT integrate into sole S1 release #220 or D18 collectible canon without additional review. This handoff is keyless original source and CI evidence.

## Actually implemented
- `src/RareDiscoveryBook.luau`: **pure server-owned** per-session four-entry notebook (`0/4`→`4/4`) for the four original animated rare fantasy creatures. No repeat credit, no stale/NaN serial, no cross-player state, no D18 collection ID, no saving, XP, eggs or currency. A new player connection starts at 0/4.
- `src/RareDiscoveryHUD.luau`: **actual** Roblox `ScreenGui` source with 4 Japanese rows and live updated title, separate per player, on-screen readable on mobile, no client Remote and no buttons to tell server what was found.
- `src/RareDiscoveryQAPlan.luau`: **deterministic PRIVATE QA ONLY** observation schedule. Exactly four 26-second windows (~104 seconds) at four safe stands near central grassy hub. Each creature is temporarily visible up to 23 seconds, and the real prompt becomes available after a 2-second cue. **This MUST NOT be described as the product's true 12% random spawn policy.**
- `src/RareDiscoveryStudio.server.luau`: disabled by default; only owner may locally enable an unpublished backed-up Studio test copy. Reuses **unchanged** `RareRealmScene` and `RareRealmCatalog` from #230 and `RareEncounterPolicy` and `RareEncounterModels` from #232, after verifying SHA exact. One server-owned animated creature globally. Real physical `HumanoidRootPart` check, live Player presence, `Humanoid.Health>0`, no anchored player, server-side distance ≤14 studs, prompt Enabled + 2–23 seconds window, event serial and same-player duplicate checks. Independent per-user ScreenGui updates; only a 2-client real server run can log `TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4`. Disconnect destroys that user's notebook. Impossible >80 stud/sec movement temporarily blocks click to avoid mistaking instant teleport for walking. No reward, RemoteEvent, DataStore, or webhook.
- No source edits to frozen previous four worlds or moving models. No changes to main/RC, Roblox publishing, paid items, D18 canon, Windows PC or other automation.

## Important fact separation
- Running genuine Luau native CLI against an *engine mock* proves the original notebook/UI logic executes with external Roblox object doubles; it **does not** prove a real Studio avatar, touches, or mobile FPS.
- Rojo 7.7.1 .rbxlx **really packages 8 unchanged/exact original Luau sources** into a review-only Place. It starts with `ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false`, so it does not create a scene unless the owner explicitly enables a **disposable nonproduction copy**.
- The deterministic four-creature schedule is an **observation bench**, not a real-world loot-drop rate. Original rare encounters in #232 have a separate source-only *configured test* 12% chance per 45-second window. Neither has been measured as actual Roblox player drop odds.

## OWNER protected final real Studio QA plan — NOT performed by this Chat
1. Backup the Windows PC Studio Place, leave actual S1 first-release RC **untouched**. Download the **immutable** GitHub Actions review-only `.rbxlx` binary and verify SHA256 with CI receipt.
2. Open a **new unpublished test Place**, not official S1. In a **local disposable copy only** change `ENABLE_RARE_DISCOVERY_STUDIO_BOOK=false` to `true`; never push an enabled variant.
3. In Studio Test mode, Start **2 actual clients**. Each must see a separate right-side `発見ずかん 0/4` panel. At the green hub, observe four different moving creatures one by one (around four 26-second slots). Physically approach, click/tap the genuine Roblox ProximityPrompt; both clients should independently progress `1/4`, `2/4`, `3/4`, `4/4`.
4. Check server output `RARE_DISCOVERY_REAL_STUDIO_WITNESS`: only after two **different** valid live players each physically trigger all four prompts can `TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4 status=PASS` appear. Bad-distance/offline/dead/instant teleported player should be rejected. Trying the same monster twice does not increase the book. Disconnect/rejoin resets only own book to `0/4`.
5. Test on a **real phone** separately. Observe the right-side HUD not covering the native player movement/action controls, text legibility for kids, touch prompt operability, FPS/loading/streaming, root motion near moving creature, camera comfort, safe falls, and disconnect/rejoin. Screen-record with actual Studio build/device/server logs for owner QA.
6. This is not production D18 collection. Even with a genuine Studio PASS, official S1 completion/release status and World Field parent percentage change only after their authorized maintainers accept real evidence. The 12% opportunity and 0-reward policy remain independent design choices.
7. Stop Roblox Studio cleanly, never click Publish, never merge this branch into main/official RC or enable monetization without separate owner action.

## QA and proof
Actions job A: genuine pinned upstream Luau CLI, original `RareDiscoveryBook`, `RareDiscoveryQAPlan`, `RareDiscoveryHUD` code executed against test-only **external Roblox engine** doubles with two independent PlayerGui graphs; eight deliberately broken **original source** mutations must be rejected. Python source contract tests and strict full SHA256 of all packet files.
Actions job B: genuine pinned Rojo 7.7.1 creates a real `.rbxlx`, source text at all 8 embedded script paths must exactly match the previous pinned originals/new SHA256, and corrupt source/unsafe authorizations must be rejected. Neither job proves actual Roblox Studio device QA.

No images/videos or player revenue/retention evidence were captured; all such future claims remain NOT_TESTED.
