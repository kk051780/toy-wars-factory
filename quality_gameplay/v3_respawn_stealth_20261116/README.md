# GQ-V3-ASSASSIN-RESPAWN-STEALTH-FENCE — source-only

Owner handoff: issue #470, scoped existing #218 request 6912633412.
Stacked on existing original author composite PR #484 (source SHA
`6b52eaf1f2725496277998fe0c5532b7a8fcaab5`).
Never replace existing #482/#484 Game/Combat/BotActors authority or create a second one.

## Actual game defect
The Assassin B skill stores `EGGRUMBLE_StealthUntil` on the Player.
`BotActors` reads that attribute to decide whether it can damage the player.
The original Host's `CharacterAdded` callback equips the new avatar without
clearing the old avatar's timed stealth. If the old avatar dies before expiry,
the new life inherits up to 3 seconds of stealth despite not casting it.

## One-hunk gameplay repair
In `EGGRUMBLE_LobbyCastleModesPreview.server.luau`, once the callback
verifies identical character, original joined mode, active round and surviving
personal castle, clear only `EGGRUMBLE_StealthUntil` immediately before
`SevenRoleCombat.equip`. No combat/VFX/field/castle/neutral/item/lobby
authority is duplicated and no unrelated session reset occurs.

## Tests and handoff
`python3 -m unittest discover -s quality_gameplay/v3_respawn_stealth_20261116 -v`
checks the exact source diff against the pinned original, current-life
guards, BotActors real hit, and negative mutations. One-line runtime change.
Rollback: remove the one-hunk replacement, restoring the pinned #484 Host byte
for byte. Entire DRAFT candidate may be dropped without changing official RC.

Status: `SOURCE_PATCHED`, CI pending. `CLAIM_SOFT_NOT_GRANTED`.
`FORMAL_RC_INTEGRATED=0`, `STUDIO_PROOF=UNKNOWN`,
`ANDROID_PROOF=UNKNOWN`, `OWNER_ACCEPTED=NO`.
For official RC only #220 authenticated scoped non-force CAS plus same-HEAD
source/native/Rojo/Place evidence; user waived per-author approvals, not
source safety, overlapping-scope verification, or authenticated RC access.
