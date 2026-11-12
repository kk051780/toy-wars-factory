# TRAP RAIDERS — five-change full S1 code REVIEW, **not** release

**Game** `TRAP_RAIDERS`; **work_id** `p0d-siege-v19`; **release ID** `P0D-S1-KIDS-RC01`.
- Protected sole-official RC: `rc/p0d-s1-kids-rc01`, verified original main game source and host remain unchanged.
- This independent reviewer branch: `review/p0d-s1-v6-five-safe-ux-20261112-04`.
- Immutable base **full 37-source project**: `09e118c9af3a7f30c2763b956ab80c4056d2a09d`. It already contained three prior selected/disjoint child-UX variants (Japanese map, Guardian first minute, mobile Guardian right-side trap button).
- Actual official parent: `1263a03701211a652b99b91d2339575dc8104eff`.
- Complete playable-in-principle code source tree: **`releases/P0D_S1_KIDS_RC01/`** (Rojo `default.project.json`, source, manifest, QA). This preview has **not been physically played**.

## Exactly two additions atop the full 3-way UX review baseline

1. **S1 arena edge recovery:** complete Game.server Luau borrowed byte-identically from an independently delivered public original-derived source `db58d8cf0cfad9e74f892b090d4a376c1ddd3725`. Git blob `5e671bbda4d27532a4480a7645e4fab3cb3bccf3`. The new server check returns live RED/BLUE players who physically leave x ±130 or z ±76 (current map 250 × 142 with 5 studs margin), retaining y < -30 recovery. Before return, the existing authority drops stolen eggs, restores slowed movement, stops momentum, respawns at the player's own team spawn, and applies existing short invulnerability.
2. **D07 heartbeat fail-closed:** complete original-derived server S1CanonicalRoundHost Luau borrowed unchanged from public candidate `5205d6c88344e4299171d9a0d6eae031694a8667`. Git blob `1808fa630b13ad2be2dfdac188823957530b9086`. Unexpected nil+reason such as INACTIVE or REENTRANT_HEARTBEAT or any malformed non-table command immediately triggers existing boss stop, while valid nil,nil idle and table,nil remain permitted. Boss stays **OFF**.

The integration is 2 isolated full Luau source replacements + the updated 37-file `BUILD_MANIFEST.json`. The Git compare against the immutable 3-way review baseline must show **exactly these 3 changed release files**, and no protected RC/main changes:
`src/server/Game.server.luau`, `src/server/S1CanonicalRoundHost.luau`, `BUILD_MANIFEST.json`.

## Repeatable checks

Run from a clone on the immutable commit:

```sh
python3 handoffs/P0D-S1-FIVE-SAFE-UX-REVIEW-20261112-04/verify_five_review.py
python3 -m unittest discover -s releases/P0D_S1_KIDS_RC01/tests -p 'test_*.py' -v
```

The first source-only script verifies all **37** `BUILD_MANIFEST.json` entries by actual SHA256 and byte length and five selected Git blob originals, plus 12 structural/safety tests. It is **committed for later execution**; do not call it tested unless an actual run receipt exists. Native Luau parse/real Rojo build for **this combined five-source tree** and physical Roblox Studio 2client/mobile are also **NOT_TESTED**. Prior three-way UX build passed its own genuine native+Rojo CI at https://github.com/kk051780/toy-wars-factory/actions/runs/43207102745; that older result **must not be reused** as five-way native engine PASS.

Review eligibility: source SHA + compare exact, no hidden additional Game/event authority, no duplicate native Remote, no new DataStore, paid Roblox publish, or client-controlled teleport/damage. Critical real-Roblox negative QA includes carrying egg during teleport (no instant score), respawn immunity, Guardian slowed state cleanup, 2 players and disconnect edge cases, repeated escape near map bounds, D07 nil-error heartbeat fail-closed, and existing D07 visible warning/damage timing. Run actual Studio under OWNER-directed final batch only; no interim Codex.

**S1 official game progress last sole-integrator audit: 75/100**. New review project creates zero official release points by itself. `CHAT_RC_READY=NO`, `OWNER_RELEASE_APPROVAL=NO`, `STUDIO_NOT_TESTED`.

## Handoff
Sole `#220` integrator may INCLUDE_OR_SKIP **after revalidating current official RC SHA and original Game/Host blobs**. This branch only represents a source-only review of a complete isolated project. Do not auto-merge to official RC or main. No Roblox production publish, payments, PC Codex execution, P0-A/B/C security/CAS changes, or existing five Automation updates.
