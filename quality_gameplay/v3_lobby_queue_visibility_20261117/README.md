# EGGRUMBLE V3: TEAM/BR queue progress on existing gate billboards

**Feature ID:** `GQ_V3_LOBBY_QUEUE_ETA_20261117`

## Distinct source-derived usability defect

The original V3 TEAM and BATTLE_ROYALE portals show static mode names. After an actual valid queue entry, the player cannot see how many users are waiting, whether solo play is supported, or how many seconds remain of the original 12-second start. This is *not* the earlier #544 stale-epoch timer correction, #539 existing board visibility/occlusion, #547 castle/egg board, or #341 old S1 READY gate. No other TEAM/BR countdown billboard source claimant found in open PR inspection at creation time.

## Smallest overlay

One existing `EGGRUMBLE_LobbyCastleModesPreview.server.luau` source is patched using a fail-closed selector. The two existing gate `BillboardGui > TextLabel` instances are reused, with zero new GUIs, controllers, Remotes, Game/Score/Store authority, Save, monetization, or paid source. Visual-only ticker reads the **existing** queue and epoch; the original single `task.delay(COUNTDOWN)` remains the only start authority.

Supported states: idle (solo supported), queued `count/16` and remaining seconds, match active, cancellation/switch, disconnection, and round cleanup. BOARD distance/LOS properties remain owned by #539.

## Source anchors / safe merge rule

- Original Host author #482 `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`.
- Official 31-script RC HEAD at authoring: `9466312436d9567db8bb464a57b664d133f6a6cf`, with existing #539, #544 semantics and #595 selected. This is an input reference, **not** an adoption claim.
- Apply **after** current canonical Host selections (#607 deposit guard if chosen) and current #539 board. Select only this Host delta and prove other 30 scripts byte-identical. Never merge the entire feature branch over newer RC.
- Inverse selected hunks recover the byte-exact current Host (not an old original version).
- RED: changed/multiple anchors, duplicate queue feedback, source/compile failure, replaced countdown authority, feature collision, failed same-HEAD Native31/Rojo31, or changed non-Host script.
- YELLOW: optional cosmetic text layout / low-powered Android readability; track and retest with OWNER Studio.
- No original author personal ACK required. **#220 is still the sole authenticated official RC/CAS writer**, who must check current official HEAD and perform fresh same-HEAD V3+S1 CI after adoption.

## Evidence and acceptance

The dedicated read-only PR workflow runs 15 Python regression/mutation tests, compiles both the original and patched server Host with pinned Luau, and uploads the exact Host source+receipt. These are **source-only** checks: cannot establish actual Roblox GUI rendering.

For official RC status, require a current-HEAD companion31 profile containing just this Host overlay, full source exact 31/31, official V3/S1 Actions success at that HEAD, ZIP/Place byte and SHA receipts, `#220` ACK, then Studio TEAM/BR join/cancel/switch/16 capacity, 1 human+15 AI, Android portrait display and OWNER FUN review. Until then: `PREP_ONLY`, `RC_ADOPTED=NO`, `STUDIO/ANDROID/FUN/OWNER=NOT_TESTED`.

Rollback: unselect only this text overlay and retain every previously adopted source, especially #539, #544, #595, and newer #607. Main/Publish/Payments/Windows and existing automation schedule remain unchanged.
