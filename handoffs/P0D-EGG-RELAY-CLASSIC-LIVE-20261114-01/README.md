# EGG_RELAY_CLASSIC_V1 — real Game + mobile HUD patch candidate

This is **actual source-diff code** for the ONE existing authoritative Game/Remote, NOT a gameplay claim and NOT a second Game. Author policy: [P0D-EGG-RELAY-001](https://github.com/kk051780/toy-wars-factory/tree/d09a52a3b7ca1fe400e30370606d5751751a6941/handoffs/P0D-EGG-RELAY-PASS-POLICY-20261113-01).

## Visible behavior if #220 adopts

- An egg carrier in **classic one-egg mode** can use **🤝 Pass (H / touch)** to give the stolen egg to the closest nearby living teammate.
- Max 8 studs horizontally, 4 vertically, clear server raycast LOS; per-egg 12s cooldown.
- One canonical Game performs one no-yield transaction: previous owner loses the egg and its carried visual, receiving teammate gains it. Existing snapshots/waypoints update; neither score nor XP/HP/Store are granted.
- Server rejects cross-team, dead, restrained, farther-away, cooldown, stale epoch/egg-version/replayed request and forged target. Every pass rechecks the canonical owner.
- **5-egg mode remains disabled for relays** until original H2Score provides atomic transfer; not allowed to pretend classic eggOwners is the five-egg score ledger.

## Source contract

- PATCH_OPS.json contains 9 Game and 6 HUD unique-anchor replacements against the actual frozen B42 original Game/HUD. Game baseline blob: 21b866e801a53ba7ebd66132ae55fe28608750d6; HUD blob: ce6707dc1f833600e1c6913504d30911b24cb2a4.
- Before source handoff, all 15 anchor replacements applied once to the frozen source, original Game stayed one remote handler and original H2Score.deposit / classic deposit code remained. These are **static source checks only**.
- apply_relay.py can be invoked on a newly assembled *unpublished* working DIST **after current overlay and six-skill patch**; it refuses missing/duplicate anchors, a second policy module and a changed author policy blob.
- Appends module EggRelayPolicy.luau only; keeps one Game, one Remote and canonical existing seq. For source rollback, don't apply this patch in the next single RC build.

## QA and release boundary

**Executed:** source adapter generation and 12 static JS invariants on original B42 Game/HUD: PASS. **Not executed:** actual Python patch script, native Luau compile, full source-exact Rojo, Studio two clients, Android, first-time user FUN. This branch is SOURCE_CANDIDATE. Official RC adoption requires #220 sole writer, a reversible RC feature switch, same-current-HEAD build + negative QA. No main write/merge/Roblox publication/paid feature/extra cost.

## V2 compatibility fix and canonical RC55 CI

Original Game's `serverNow()` uses `workspace:GetServerTimeNow()` (2026 Unix epoch exceeds 1e9), while the unchanged isolated EggRelayPolicy validates `nowSec` with an absolute bound below 1e9. Feeding the epoch clock would **reject every normal pass**. Source adapter now obtains `os.clock()` in its own no-yield classic pass transaction and uses the **same server process clock** for per-egg cooldown and HUD remaining. This does not change the canonical match clock, Store, saved XP or five-egg score authority.

Workflow `.github/workflows/p0d-egg-relay-classic-rc55-candidate-ci.yml` has been added in this child feature branch to reconstruct exact successful RC56 HEAD `947cddb5351ba95b9b27597b9ec1828a8297cd66`, append only Game/HUD patch + one pure module, and check pinned native Luau/57-source Rojo embedded bytes. **Workflow result is not confirmed** merely by committing it. `QA_CLOCK_CI_RECEIPT.json` records 21/21 separate actual GitHub source-level checks, not native or engine proof. Official current RC remains unchanged.

**RC56 update (2026-11-14):** The official sole RC writer has already added saved BEAST evolution as the 56th script (CI 43504336646). This isolated branch's candidate workflow now pins its verified exact source SHA `947cddb5351ba95b9b27597b9ec1828a8297cd66`, applies `apply_saved_beast.py` after SavedPve and only then applies relay. Source count target is 56 → 57; rollback means simply omit relay source patch and retain official RC56. Actual new isolated CI outcome still unverified.
