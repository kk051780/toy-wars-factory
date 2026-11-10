# TRAP RAIDERS / Independent keyless D16 free-glide permission fallback

`game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, `packet_id=P0D-D16-GLIDE-PERMISSION-CLEANROOM-20261110-01`

This is **NEW clean-room original source**, not a decrypt or byte-preserving recovery of the old encrypted `P0D-D16-GLIDE-AUTH-20261110-04` at commit `c3de5d94eae25e566bdf29452ed1980dae35909d`. Owner historical ZIP SHA `872e8f9ec5ef38535ee3b295bf301a612e2063835e85cae67ab87bb370aee2cc` remains un-restored. Do **not** count this as a legacy migration. If owner/original author recovers original, have Codex compare and choose **one** policy implementation; NEVER install both.

## What is actually written

- `luau/GlidePermissionPolicy.luau`: pure server-side state machine; no Roblox APIs, physics, Player mutation, RemoteEvents, DataStore, UI or scheduler. It checks server user identity, round/monotonic clock/sequence, alive/team, descending 3–60 studs, and absence of carried egg, mount, snare, rewind. Max 5 seconds active, 25-second cooldown after stopping, reset safely across rounds. Max horizontal 18 and minimum downward -10 are **suggested constraints** returned to an approved physical adapter, not velocities enforced here.
- `tests/glide_oracle.py`, `tests/test_glide_oracle.py`: deterministic independent Python oracle/43 offline regressions including 1000 randomized scenario assertions.
- `docs/QA.md`: exact PC integration gate.

## Operational safety

- Default `config.enabled ~= true` blocks START. `snapshot` MUST be built solely from genuine server authoritative data; a client can express `START`/`STOP` intent only. A missing or invalid authority record returns a STOP decision, never START.
- **Important:** A STOP output is a command for the owner-reviewed server physical adapter to stop any actual glide movement instantly, even when returned state is unchanged for an invalid/stale snapshot. This module makes no promise of enforced descent/velocity caps without that adapter.
- Do not use purchase/XP/job level to grant superior movement. Keep all 7 free jobs equal.
- No changes to D16 CLOCK_RAIN alternate, D16 SCALE_FX author claim, D14 seats cleanroom, v40/D08 canonical events, original PC sources/Place or protected branches.

## Delivery / QA scope

`PUBLIC_SOURCE_V1`: actual plaintext source, tests and SHA manifest in a unique GitHub handoff branch. Fixed commit full source readback is transport integrity **only**, not a Luau parse/Studio/2-client/physical mobile QA PASS.

Owner Windows Codex: preserve the newest verified PC Place + CHECKPOINT + source SHA, fetch this immutable new source commit into an isolated folder, verify `BUILD_MANIFEST` with the canonical `p0d_public_pack.py`, review actual server adapter signatures and decide whether reference is needed. If accepted, integrate **only one** enabled glide policy and a separately tested server physics adapter in an unpublished copy. Test spawn, egg ownership change midflight, mount/snare/rewind abort, team change/round reset, replay, 2 clients, touch/low-end mobile and Roblox Studio normal exit. If not possible, HOLD this new module.

No main writes, PR merges, Roblox production release, purchases, extra spending or protected P0-A/B/C CAS changes.
