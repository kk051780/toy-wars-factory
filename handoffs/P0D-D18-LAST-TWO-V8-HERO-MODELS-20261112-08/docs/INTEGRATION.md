# D18 v8 final two showcase models: optional source-only handoff

* Source pin: D18 canonical v8 hero designs commit `176bfc400ef6ec561b129a8163a0f4776e1b9ee4`.
* Distinct IDs: `TRCA-TR-063` **火輪跳ね台** (LEGENDARY/TR/火輪の熔炉) and `TRCA-WE-099` **遊園ホルン** (LEGENDARY/WE/夢菓子の遊園).
* These are cosmetic models with **no trap bounce, burn, combat horn, accuracy, reach, pay advantage, unlock, reward, server state or persistence**.
* This pack is **not** installed in S1. Gallery source `P0D-D18-STORY-REACTIONS-TEN-20261112-07` contains only the previous 10 original 3D models. Any future inclusion of the two requires a separately owned integration and independent native/static plus real mobile/Studio QA.

## Opt-in test in an unpublished Place

1. Import `ShowcaseCatalog.luau` and `ShowcaseFactory.luau` as sibling `ModuleScript`s inside a **local** testing folder. The demo is intentionally `ENABLED=false` and not wired to an actual Rojo game.
2. In an isolated local `WorldModel` underneath a `ViewportFrame`, call `require(ShowcaseFactory).Build(worldModel, "TRCA-TR-063", CFrame.new())`. This returns a `Model` and `nil` error on success.
3. Call `.SetPose(model, "idle" | "tap" | "win" | "loss")`, `.SetLod(model, true/false)`, `.GetStatus(model)`, and `.Destroy(model)` on close or replacement.
4. Test native Luau parse, all four visual reactions, readability at 48 px, near/far model counts, camera clipping, mobile input, device FPS, normal Studio exit, and memory/latency on actual Studio. None of these Studio/Roblox runtime gates has been performed in this packet.

Maximum previews created by this factory: 12. `SetLod` toggles visibility only, not Part allocation. Never mount in live workspace gameplay. Source uses pure primitive Parts, local textures none, sounds none, animation timers none, Remote events none.

**Acceptance rule:** strict PUBLIC_SOURCE_V1 no-key SHA/size manifest and offline tests are source-only. They do not imply Studio PASS, official S1 adoption, or public release. The sole S1 RC integrator #220 may INCLUDE_OR_SKIP. Do not delay the first S1 release for 648 collector content.
