# EGGRUMBLE V3 — 15-minute non-overlapping deadline policy

**Status:** independent SOURCE-only DRAFT; no official RC adoption, game-engine QA, or OWNER approval. Scope is only `quality_gameplay/v3_match_deadline_20261116/`. Claim in #218 comment 6906555425 is SOFT, not a grant to write to original #482 or official RC.

## Real reproduced gap
The original #482 V3 uses `Rules.start(session.rules)` but only concludes the server round in `Rules.damageCastle -> concludeIfLast`. A single bot-stalled castle can keep both TEAM or BR `ACTIVE` indefinitely. The earlier independent #363 set `MatchSeconds=900` on a different RC game; do not graft its whole Game/HUD into V3.

## Behavior and owner integration
Pure native Luau `EGGRUMBLE_DeadlinePolicy.luau` checks the same authoritative `session.rules` and returns a one-off **DRAW on 900s** only if at least two sides remain; if the real castle rules already declared a winner, it refuses. Existing eggs/castles/KOs/scores are preserved. A draw is a timeout outcome, not a made-up capture win.

Existing **#482 GAME author only**: add sibling ModuleScript, bind one unique match/epoch ID and `os.clock()` startedAt right after `Rules.start`; while current `sessions[mode]==session` and `phase==ACTIVE`, call `Deadline.expire(session.rules,lease,os.clock(),id)` with a low-rate server timer, and on success invoke **existing** `session.refresh()` (which already calls ResultService and RoundReplay). Stop the timer when the session is disposed. Update existing ResultService wording (via original #487 result owner) to show **引き分け** for `winner="DRAW"`; no new HUD. Must use same source session, not a parallel Game. Verify TEAM+BR mode-specific identity, real 15-minute clock, non-spoofability, winner-before-timeout, disposal, and no forced replay. The 900s policy is proposed V3 behavior and requires product owner validation.

## Reproducible QA
`python -m unittest discover -s quality_gameplay/v3_match_deadline_20261116/tests` for Python structure/harness construction. Native real VM (not a Python simulation): compile the Luau source, then run:
```sh
python quality_gameplay/v3_match_deadline_20261116/tools/make_native_deadline_harness.py --out /tmp/eggrumble-deadline.luau
luau-compile /tmp/eggrumble-deadline.luau >/dev/null
luau /tmp/eggrumble-deadline.luau
```
No native compiler / Studio runtime is claimed until Actions verifies it.

## Rollback
Remove the optional sibling policy module and two minimal hooks from the original #482 host. Existing Game/Rule/Remote/egg/HP/ART/SCORE source must stay byte-exact. Only authenticated #220 may adopt into official RC using nonforce CAS and same-HEAD native/Rojo/Place verification. Not a new public Roblox release; no main, merge, publish or spending.
