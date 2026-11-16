# EGGRUMBLE P0D #470 — neutral horde spawn-throughput quality repair

SOURCE_WIP / DRAFT / NOT_RC / NOT_STUDIO_VERIFIED. This candidate owns **only** quality_gameplay/neutral_pacing/**; the existing 7-role, field, battle, castle, enemy, item, lobby, score, art and RC authors retain their scopes.

## Verified source gap and measurable goal

Author #482's actual EGGRUMBLE_SwarmCombat.luau uses SPAWN_BATCH = 5, SPAWN_TICK = .18, LIMIT = 110. Absolute theoretical spawn throughput ceiling (without pauses) is 5/.18 = 27.78/s, or 25,000 in 15 minutes. OWNER's 30,000+ **real** neutral KOs in one 15 minute match requires 33.34/s plus enough players and real enemy deaths. Current ceiling cannot hit the target.

## Real candidate patch — no second horde implementation

EGGRUMBLE_NeutralSpawnPacing.luau is a pure server-side token-bucket spawn policy. It enables a nominal 40/s = 36k potential 15m supply, with 110 live cap, max eight per update, no deferred burst after cap/no targets/match end, strict match ID isolation, and a server-tick-pressure reduction to 26/s or 16/s. No fake kills, no score credit, no NPC models, no Remote, no Store, no new combat owner. It **does not** guarantee 30k real kills or mobile FPS: those demand Studio/Android trials and actual observed damage/deaths.

## Existing #482 author source-selective intake (not done by this isolated PR)

Only the existing Horde author may alter the existing SwarmCombat spawn *batch decision*. Keep their original Humanoid.Died KO credit, LOS, physics, neutral actor models, three-lane target selection, MatchRules, Game and other feature ownership. Example only (the author must provide immutable server match ID and measured server step time):

~~~luau
local NeutralSpawnPacing = require(script.Parent:WaitForChild("EGGRUMBLE_NeutralSpawnPacing"))
local planner = NeutralSpawnPacing.new(session.id)
local lastTick = os.clock()
-- inside the author's existing 0.18s loop, not another loop:
local now = os.clock()
local batch = NeutralSpawnPacing.step(planner, {
    matchId=session.id, phase=session.rules.phase, dt=now-lastTick,
    live=api.getAliveCount(), activeHeroes=#candidates, tickMs=serverMeasuredTickMs,
})
lastTick=now
for _=1,batch do -- original addEnemy(...) by original author only
end
~~~

Native source-only QA: python3 -m unittest discover -s quality_gameplay/neutral_pacing/tests -p 'test_contract.py' -v, then run tools/build_native_harness.py to execute the exact authored module plus actual Luau spec. No fake native pass. Merge disabled; source-selective import by #482 owner and authenticated #220 RC writer only after latest-HEAD, Rojo/source lock, both TEAM/BR, actual one+15 and two+14 client Studio tests, low-end Android fifteen-minute p50/p10 FPS evidence, #420/#470 and OWNER acceptance.

ROLLBACK: omit this planner from the original spawn loop and retain SPAWN_TICK=.18 / SPAWN_BATCH=5. No main push, normal merge, Publish, paid feature, or Windows operation. Official RC adoption = 0.
