# P0-D S1: two-defect D07/D08 corrective Luau overlay (keyless)

**SCOPE = ISOLATED SOURCE-ONLY CORRECTION, NOT FINAL RC.** Game TRAP_RAIDERS / p0d-siege-v19 / release P0D-S1-KIDS-RC01.

A new self-contained S1 server candidate from the single Game source author exists at pinned commit `4b66dd8a9b34a45cf12e58684e0e4372df3f8b07`. It includes original v40/D08/Gorogan code, patched Game/HUD, a real 16-unit Python source plan+receipt, and source-only CI. **The sole #220 RC branch remains at initial game `35d7d0525388e885aac8281eff2315a59831e0cf`.** There is no proven genuine Roblox boss run yet.

Two problems were independently located in the concrete source candidate, and this packet carries the **complete revised Luau modules** at their exact target paths:

1. `src/server/S1GoroganLiveBindings.luau` — The original candidate's `playerFromId()` accepts digits and positive `Player.UserId` only; the same module emits `tostring(player.UserId)` in the real server roster. Roblox Studio local test Players can have `-1`/`-2` IDs, so original D07 AI may choose a valid target that its damage gate then fails to resolve. This correction resolves exact identity against the actual server Players roster, accepts canonical negative IDs but rejects forged/zero-padded IDs, duplicate roster matches, absent or non-Player actors. It never accepts client-chosen target identifiers.
2. `src/server/S1CanonicalRoundHost.luau` — Original v40/D08 intentionally retires an event when the roll is NORMAL (0..64) or after boss CLEANUP. The original Host `tick()` continues polling the retired D08 bridge, converting expected `ROUND_REPLAY_DENIED` or Host.closed into a false `D08_FAILED` signal in Game. This correction verifies the D08 retired match+epoch and enabled/cleanup status, calls existing Host:stop once, then returns a stable `(true,"EVENT_FINISHED")` on later ticks of the **same authenticated ACTIVE round**. A changed round, unknown retirement, disabled bridge, failed native callback, or other error still fails closed.

**Important:** These are corrections to the two NEW S1 adapter modules ONLY. All original recovered v40/D08/AI/Rig/Gate/Receipt/Combined sources remain unchanged. No new event chooser, remote, HP writer, spawn/rig, main edit, unreviewed switch to ON, or actual Roblox Studio claim.

## Pinned provenance

- Upstream complete S1 source candidate: `4b66dd8a9b34a45cf12e58684e0e4372df3f8b07`
- Original Host Git blob SHA1 `db28bafed6372f9fb2d4fa53c433d046999b64e2`; patched exact blob recorded in `SOURCE_LOCK.json`
- Original D07 Binding Git blob SHA1 `db2a5d2ee5e655b2a9beffe33747cf1fba47c37e`; patched exact blob recorded in `SOURCE_LOCK.json`
- Original D08 bridge (UNCHANGED): `70dcc3b50129c288441452776360588184ca6c22`
- Original original v40 event Core (UNCHANGED): `3c40c7dd80e6ec134f3124b6a6a0f625951792f4`

## Acceptance for sole #220 CHAT-INTEGRATOR

1. Confirm current integration candidate includes the exact ORIGINAL two Git blobs noted above. If not, **do not blindly overwrite**; compare changes first.
2. Replace ONLY these two ModuleScripts on the integrator's isolated game source candidate, keeping parent/sibling paths and all 14 other source units intact. Avoid installing a second script or another Rojo mount.
3. Regenerate full 16-unit `P0D_CHAT_RELEASE_PLAN_V1` and `CHAT_RC_RECEIPT.json`, plus official strict 25-file-or-updated `P0D_PUBLIC_SOURCE_V1` manifest; do NOT reuse stale source plan/receipt or release marks. The supplied patch is not a fake final receipt.
4. Run the source-only regression `python -m unittest discover -s tests -v`, official source verifier, independent read-only static QA, and distinct native Luau/2-client/mobile Studio acceptance before release. The payload's offline 45/45 JS boundary checks are not actual Luau runs.
5. Verify native Studio negative test player IDs `-1,-2` can be chased and receive legitimate D07 stomp damage, but not in spawn/immune/blocked LOS; repeat v40 rolls `0,64,65,89,90,99`, round rollover and genuine terminal success vs actual fail/disabled. CURRENT CODE SHOULD REMAIN OFF until reviewed private Studio QA, then OWNER can choose opt-in.

**No launch, merge, main mutation, paid service, or Windows PC action is authorized by this handoff.**
