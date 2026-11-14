# P0D-018 — enemy capture / teammate rescue (SOURCE-only Draft)
Authoring base: official RC66 `43543378f976374e2cac2d68b3136ac355d3191b`. This isolated feature supplies **actual Luau policy** and an 18-case native fixture, not a playable Game integration. The native fixture is NOT EXECUTED yet. The Python safety suite is static only. No official RC adoption progress is claimed.

Mechanic: TRAPPER may hold one opposing player for at most 4 seconds; teammate rescue within 7 studs, automatic expiry or round/leave cleanup. One active capture per team; cooldown 18 s; fail-closed on wrong phase, egg carrying, invulnerability, bad role, distance or LOS. All distances and LOS MUST be calculated server-side.

## Required for A -> B READY
- Integrate into the **existing sole Game** and its single Remote. Do not create another Game, Store, Remote, or scheduler. Game computes trustworthy team/role/LOS/range and owns immobilization/restoration.
- Add short in-world cage/rescue marker without blocking movement/camera. Restore role WalkSpeed after rescue, expiry, death, disconnect, respawn, or match end. Limit active waits and close all leaks.
- Use feature switch OFF to restore exact prior 66-source build and source-lock; native execution for the real module and Game binding; Rojo source-exact and same-head CI; Sourcery P0/P1 triage; new FEATURE_ID P0D-018 only.
- Only then make nonDraft `P0D_PREP_READY_V1` PR and request #220 sole RC writer review. Studio/Android/FUN still not tested.

This PR is not READY, not a second source authority, not 67/67 Game source and not public release. No main/RC direct writes, paid actions, Roblox publish or PC operation.
