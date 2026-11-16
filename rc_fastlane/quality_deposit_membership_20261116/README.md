# GQ586 — Current TEAM/BR membership before own castle egg deposit

## Distinct defect / owner
Original #482 Host OwnEggDeposit prompt validates owner UserId but not current match membership.
A player returning in another mode can potentially touch old active own castle and deliver
old carried eggs. **Source-derived risk only; not a Studio-reproduced exploit.**

#537 owns UI refresh on successful deposit (preserved). #551 owns stale avatar Died,
#525 owns item pickup, #535 human combat, #580 AI takeover, #515 field egg drop,
#520 field pickup topology. This path owns **only** the existing OwnEggDeposit guard.

## Source patch
- Existing Host, exactly one callback: check owner ID, joined[player.UserId]==session.mode,
  sessions[session.mode]==session and rules availability *before* Rules.depositEggs.
- No new runtime Script/Host, no duplicate Rules, Score, Item, Remote, AI or
  Game authority. Total real V3 31, other 30 byte exact.
- Build source via select_deposit.py prepare against **current** selected RC31 project,
  verify real selected .rbxlx Script Name/Class/Source via verify.
- Reverse ONLY NEW -> OLD, current Host returns byte-for-byte; flags off by excluding selector.

## Acceptance
- [ ] PR same-HEAD 10 Python negative/mutation cases
- [ ] Native actual selected Luau callback scenarios: valid/other-mode/no membership/stale session/
      wrong owner/missing rules/dead castle/no egg
- [ ] 31/31 Native and true Rojo Source+Class exact
- [ ] #220 unique authenticated non-force expected-SHA CAS after current RC re-read
- [ ] New official V3 and legacy same-HEAD CI and Place/ZIP bytes
- [ ] Studio2client / Android15min / #420 ART+FUN / OWNER: NOT_TESTED

No main, arbitrary PR merge, Roblox publish, paid service or Windows operation.
Previous source author's personal ACK is not a blocker; RC safety checks remain mandatory.

## Source pin and concurrency
Initial PR base 39ab645c230208f8e3306821695d04fe8fa107c1; later official HEAD may include
#520 FIELD and #583 CastleRules. Never adopt this stale workflow wholesale.
The sole #220 writer must compose just this one Host guard on the **latest** selected 31,
run native/Rojo again, compare 30 other scripts, then authenticate expected-SHA CAS.
