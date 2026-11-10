# D07 original-source cross-package contract findings (2026-11-10)

**Evidence boundary:** Source contract assertions below come from the five immutable public original-source commits named in `../README.md`, read without changes. They are *static code findings*, not Roblox Lua execution, automatic Windows ingestion or live test results. Existing successful D07 rig-only test evidence and v43-A PC gameplay QA must be preserved independently.

## P0 — Canonical D08 event cannot be passed directly to `Combined:start`

- **D08 producer:** `CanonicalEventBridge.luau` constructs `envelope` using `matchId`, `stage`, `epoch`, `kind`, `subtype`, **`phase = event.event`**, **`validUntil = event.untilAt`**. The server adapter routes this value to `onBossActivate(e)`.
- **D07 consumer:** `GoroganCombinedRuntime:start(activation)` requires `activation.event == "ACTIVATE"`, `activation.kind == "BOSS"`, `activation.subtype == "GOROGAN"`, `activation.matchId`, `activation.untilAt`, and an authoritatively attested activation object; its stage is obtained by calling `deps.getStageId(roundId)`.
- **Result:** These shapes **do not match directly** (`phase` vs `event`; `validUntil` vs `untilAt`; `stage` vs trusted stage getter). A direct `onBossActivate=combined.start` is invalid. Also check that `validUntil` exists and is a real bounded deadline, rather than copying an assumed deadline or raw client data.
- **OWNER-PC action:** Write/inspect one narrowly scoped **server-only, fail-closed compatibility mapper** in the *actual PC integration checkout*, built from a genuine D08 callback and current RoundCoordinator snapshot. Bind the `isCanonicalActivation` callback to genuine server provenance, not a freely forgeable `"ACTIVATE"` string; derive stage and TTL from authoritative round state; mint the event ID on the server. No second event chooser or duplicate `onBossActivate` subscription. Test wrong round/epoch/stage/deadline and replay rejection before Studio enablement.

## P1 — Separate moving physical rig and static client-only visual may diverge

- `GoroganRigDriver` supports genuine physical `Humanoid:MoveTo` via `requestNavigation`.
- `GoroganVisualPrefab.create()` stores `rootPosition` at initial spawn; `Prefab.render()` repeatedly moves the client model to `handle.rootPosition + bob`. `GoroganVisualPolicy.apply()` handles only `START/STOMP/END` and never applies a server position update after `START`. `Combined` sends visual `START`, `STOMP`, `END`, not `MOVE`.
- **Result:** Client-only 3D shell **may remain near spawn while the authoritative rig walks**. Do not conflate the cosmetic ring with actual hit position.
- **OWNER-PC action:** Inspect current PC visual design first. Then decide whether the server rig alone should be visible (disable duplicated shell), or add a validated bounded/timestamped server visual pose stream **in a separate small integration adapter** with no player damage authority. Prove in Studio 2-client that boss appearance, 2-second warning center, safe-zone hit logic and LOS align while it moves and during low-detail render.

## P1 — Window attestation must be connected to DamageGate using the same instance

- `GoroganAttackReceiptWindow:openFromCoreResult()` accepts only genuine `STOMP_RESOLVE`-shaped command and creates short-lived `roundId/eventId/attackId/center` state. It provides `:attests()` and `:center()`, and must be closed even after exceptions.
- `GoroganDamageBoundary` requires `deps.isCanonicalAttackReceipt(...)` and `deps.getAttackCenter(...)`, independently revalidates genuine Humanoid, server round, safe zone, immunity and geometry before `Humanoid:TakeDamage`.
- `Combined` uses `receiptWindow:openFromCoreResult(...)`, calls the damage gate and closes the window. It does **not** automatically inject `deps.isCanonicalAttackReceipt` and `deps.getAttackCenter` into an independently created DamageGate.
- **OWNER-PC action:** Wire the **same one** window's `attests` and `center` as trusted gate callbacks in actual server-only dependency construction. Reject missing/expired/wrong attackId, stale round, duplicate hits and fake client Remote. Prove at most one authoritative hit of <=8 damage per target/attack using real Studio two-client logs.

## P1 — Replication dependency not implemented by the visual example

- `GoroganClientAdapter.client.luau` requires an approved `ReplicatedStorage.TRAP_BossVisualEvent` RemoteEvent and server-replicated player attributes `TRAP_ActiveMatchId` / `TRAP_ActiveStage`. The code explicitly does not create the remote or authenticate the incoming packet's original server producer.
- **OWNER-PC action:** Confirm actual source attribute/Remote naming and lifecycle; use only server-owned emission; no listener duplicated across rounds. Verify that missing bindings fail inactive, low-detail and reduced-motion display operate correctly, and client input cannot grant damage or event authority.

## P1 — Avoid activating both original AI runtimes

- The original `GoroganServerRuntime` instantiates `Core.new()` and issues movement, warning and damage callbacks.
- The later `GoroganCombinedRuntime` **also** instantiates `Core.new()` and drives the physical rig, receipt and damage gate.
- **OWNER-PC action:** Select a single reviewed server execution owner, preferably the combined adapter if appropriate to actual PC state; retain the other as library-only/reference. Never run both in the same round or duplicate D08 callbacks. The alternative clean-room AI is another **mutually exclusive** option, not an additional integration layer.

## Already aligned source contract — explicit `now` for rig navigation

- The combined adapter calls `driver:requestNavigation(cmd.position, cmd.reason, now)`; `GoroganRigDriver:requestNavigation(position,reason,now)` requires that time. The older `GoroganServerRuntime` two-argument callback is not proof the driver contract will work if installed in place of Combined.
- **OWNER-PC action:** Preserve the explicit server monotonic `now` binding. Validate PathfindingService real yield/revalidation/cleanup and Studio normal-exit behavior.

## Gate status

`KEYLESS_ORIGINAL_5_PACKAGE_STATIC_SOURCE_REVIEW = COMPLETE` for the findings above (pinned source read); `21-PACKET_WINDOWS_SOURCE_RECEIPT = NOT_OBSERVED`; `LUAU_NATIVE_PARSE = NOT_TESTED`; `D07_S1_2CLIENT_STUDIO_INTEGRATION = NOT_TESTED`; `MOBILE_PHYSICAL = NOT_TESTED`; `NORMAL_STUDIO_EXIT = NOT_TESTED`. Never upgrade one gate based on another gate's offline tests.
