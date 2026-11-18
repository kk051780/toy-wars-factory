# GQ8 REALM STORM PHASE FENCE — 2026-11-18

**Feature ID:** `GQ8_REALM_STORM_PHASE_FENCE_20261118`. Scope: exactly one original #764 `EGGRUMBLE_RealmBattleCore` server source; not a new weather engine. No second Game/Host/Combat/Swarm/Store/Score writer.

## Verified code-level defect

Original #764 server schedules storm lightning with a 2s warning. If the weather phase changes THUNDER → CLEAR during the 2-second pending warning, the code does **not** cancel `state.pendingLightning`; the discharge guard uses the pending timestamp only. The old warning can trigger a lightning strike in clear weather, making the attack unfair and visually deceptive.

## Candidate repair

Using immutable source Git blob `1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1`, patch **only two anchors**: cancel pending warning when leaving THUNDER and require current weather THUNDER at discharge. Everything else remains byte-identical by inverse patch proof.

`apply.py --origin <PR764-original-Luau> --out <candidate.server.luau>` creates a patched real Luau script. `apply.py --project36 <genuine-Core36.project.json> --out <candidate36.project.json>` prepares the real source selector with **36 sources unchanged in count; only one changed**. It explicitly refuses a drifted author blob, unexpected source count, missing authority or overwrites.

## CI / admission

Native Luau compilation, actual author blob identity and six negative/positive Python tests run in dedicated PR Actions. Formal RC still requires #220 authenticated B writer to use a current-head derived source build, same-HEAD full native+Rojo class/source inspection and inverse OFF original Core36/31, protected source lock, non-force expected-SHA CAS. Do not infer Roblox Studio, Android, 2-client or owner fun acceptance from offline code tests. No Roblox publish and no main write.

**Rollback:** discard the new one-script replacement and select exact official unmodified Core36. Keep original31 available separately. Other eight domains have existing independent PR owners.
