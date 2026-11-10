# P0-D D07 — Gorogan combined server wiring encrypted handoff

Game `TRAP_RAIDERS`; work `p0d-siege-v19`.
Packet: **`P0D-D07-GOROGAN-COMBINED-WIRING-20261110-04`**.

This is a **new server-only optional orchestration adapter**. It reuses the existing v40 single boss decision core, D07 Gorogan AI, separate D07 physical R6 navigation + damage gate/attack receipt, and separate client-only visual packet. It does **not** add or replace a boss scheduler or duplicate the original AI, rig, damage gate, visual prefab or other chat's Ligardo. It does **not** update the owner's actual Roblox Place or Windows PC.

## What is implemented

- `GoroganCombinedRuntime.luau`: one canonical in-process v40 `ACTIVATE` creates an optional S1/S3 Gorogan event only after server identity/stage/round/ground validation. Driver receives `Vector3` ground anchor; old AI Core receives `{x,y,z}` and `endsAt<=now+14`.
- Supplies the authoritative `now` argument missing from the old AI Runtime `requestNavigation` callback; rejects reentrant heartbeats and stale PC server round after yielding pathfinding.
- For a real `Core.tick()->STOMP_RESOLVE`, opens a bounded one-tick receipt before calling the **existing** `GoroganDamageBoundary` and closes it even if callbacks error. Never passes dummy `isCanonicalAttackReceipt=true`.
- Explicitly disarms window, driver, Gate and client visuals after end/exception to avoid ghost attacks, double damage or stale NPC. Does not call `Humanoid:TakeDamage` directly.

## Exact prerequisites (separate immutable packs)

- v40 `ChaosEventCore`: commit `c0b0bf692410cb651893c38f1a453c93d9f8b3b5`.
- D07 `GoroganServerAICore`: commit `80483ad6543fd73dfaf8a21ecf7b58dc2eca75e1`.
- D07 `GoroganRigDriver`, `GoroganDamageBoundary`, `GoroganAttackReceiptWindow`: commit `e7801615c5b70346dfaec189f195a65f5b597ec9`.
- D07 client visual (separate no-damage Part model): commit `5128e288c7bd119a470c253a9792f4d829c569ec`.

**The latest verified PC report** [#213 #6758415195](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6758415195) established v43-A S1 scoped 2/3 client Studio QA pass, latest local saved Place SHA `a60ed5f7497ae0c3cbac717e32f2c62577c3ec3bef7eceb0b4b40f44b834e28f`, saved Place closed and separate local D07 dependency analysis. That report also says canonical `ChaosEventCore` was **not found** in the PC game. The OWNER PC integrator must establish ONE server-owned event chooser before enabling this. No second random scheduler and no overwrite of newer local source.

## QA and secure restore

- Original private source ZIP: **19,324 bytes**, SHA256: `0f676b2dd1408ff3d995975a8d6b18db783eea2a3b2a87708f9ebe954d5ad2b0`.
- `BUILD_MANIFEST.json` SHA256 `b2b472eedde1d6d0c119e41a8cce2e657313ee628d94c9120ed64961f3737896`; **13 files plus manifest**.
- Offline Python **83/83 PASS**, including a clean ZIP extraction rerun; exact ZIP/manifest read-only verification PASS. AES-256-GCM original ZIP roundtrip byte-exact, wrong key and tampered ciphertext rejected.
- Windows restore, true Luau compiler, real NPC pathfinding, actual humanoid hit, Studio 2/3 client, mobile and physical phone are **NOT_TESTED** in this handoff. Reference code is NOT a Studio PASS or permission to publish.

**Repository is PUBLIC.** It contains *only* this ciphertext JSON and this public-safe README, not the private ZIP, Luau source or AES key. OWNER receives the key only in the private ChatGPT conversation, then gives it directly to the Windows Codex using a private environment variable. Do not put key in command line, GitHub Issues, CI logs or automation settings. Review the generic safe restore tool at immutable commit `d37eec1b653d060ae27568ddcd5f501da9662081` and verify game/work/packet ID, AAD, ZIP SHA and all manifest entries. If the key or artifact is missing, HOLD; never fabricate source.

The PC Codex should first reopen the *actual latest saved* v43-A Place for a quick regression, read-only inspect canonical event/weather ownership and current RoundCoordinator, then—**only if this compatibility gate passes**—integrate this one optional module in an isolated unpublished S1 Place, test visual warning+safe one-hit, nonteleport R6 navigation, wall/immune exclusion, round reset/rematch, FPS and clean Studio exit. Other D07/Ligardo, D14, economy, D18, full boss game remain separate and untested.

No main direct write, merge, Roblox publication, real charge, spend, P0-A auth/CAS or P0-B/C gates change. This GitHub handoff does **not** auto-run Windows Codex.
