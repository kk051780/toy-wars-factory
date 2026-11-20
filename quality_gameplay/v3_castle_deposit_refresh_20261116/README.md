# GQ V3 — egg deposit must refresh its actual castle board

**Nonoverlapping quality gameplay slice:** GQ_V3_CASTLE_DEPOSIT_REFRESH_20261116.
**Current status:** ISOLATED_SOURCE_WIP / SOFT CLAIM NOT GRANTED / ORIGINAL AUTHOR ACK PENDING / NO OFFICIAL RC / NO STUDIO OR ANDROID EVIDENCE.

## Real source finding
Original existing game author/composite PR #484 exact commit `6b52eaf1f2725496277998fe0c5532b7a8fcaab5`; Host Git blob `c1ff23cd2883401d44d6fc47311bebcfd53eb1c6` in `handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_LobbyCastleModesPreview.server.luau`.
The physical castle board reads `castle.vaultEggs` in `session.refresh()`. The `prompt(deposit,...)` callback invokes `Rules.depositEggs` but lacks `session.refresh()`, so TEAM and BR castle labels remain stale after a legitimate egg delivery. Siege attack and vault theft already refresh. Fix is **the sole deposit callback**, preserving original Rules and other seven domain source byte-for-byte.

## Proposed author-selected hunk
```luau
if c.alive and c.heldEggs>0 then
 local ok=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)
 if ok then session.refresh() end
end
```
A failed transaction never reports a successful display update. This does not add an egg, alter score or grant buffs.

## How to validate without changing owner files
- `python3 -B -m unittest discover -v -s quality_gameplay/v3_castle_deposit_refresh_20261116/tests`
- `python3 quality_gameplay/v3_castle_deposit_refresh_20261116/compose.py --input OWNER_HOST.luau --output /tmp/Host_ON.luau`
- `python3 quality_gameplay/v3_castle_deposit_refresh_20261116/compose.py --input OWNER_HOST.luau --output /tmp/Host_OFF.luau --off`; byte-exact to original.
- GitHub Action separately checks the immutable author commit, pinned Git blob, syntactic compilation of each mapped real Luau, **seven** native calls to the source-extracted actual callback, and private Rojo Place script identity. No publish or RC write in workflow.

## Eight-domain nonoverlap / RC gates
- CHARACTER: seven roles unchanged.
- FIELD: field egg generation, geometry unchanged.
- BATTLE: attack and siege damage untouched.
- CASTLE: deposited egg `vaultEggs` is immediately visible after success; no HP/defense change.
- NEUTRAL: horde/boss untouched.
- ITEM: healing, DASH, SHIELD and mode guards untouched.
- LOBBY: source uses same server session for TEAM / BR and existing queue state.
- BALANCE: egg stock and ranking formulas unchanged.

Sole integration route: #218 explicit CLAIM_GRANTED, original #482/#484 owner ACK and head re-pin, existing composite source exactly once, #220 authenticated non-force RC CAS then same-head Native/Rojo/exact official Place/ZIP byte receipt, Roblox Studio 2-client, low-end Android 15 min, #420 ART/FUN and OWNER. A passing private CI is **not** RC adoption. Keep all missing evidence as NOT_TESTED, not PASS. Do not merge, modify main, publish, spend or touch protected RC from this branch.
