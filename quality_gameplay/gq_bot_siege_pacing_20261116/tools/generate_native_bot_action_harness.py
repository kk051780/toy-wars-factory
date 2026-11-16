#!/usr/bin/env python3
"""Execute the REAL original-author BotActors siege clause in native Luau VM.

No hypothetical rewrites of the action branch: extract the exact PRIVATE-staged
source text, including the original Rules.damageCastle pcall.
"""
import argparse
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
MODULE = HERE / "EGGRUMBLE_BotSiegePacing.luau"

TESTS = r"""
local Pace=(function()
--MODULE--
end)()
local damageCalls=0
local failNext=false
local Rules={}
function Rules.damageCastle(state,targetId,attackerId,amount)
 if failNext then
  failNext=false
  error("injected authoritative damage failure")
 end
 damageCalls+=1
 local target=state.castles[targetId]
 assert(target.alive and state.castles[attackerId].alive)
 assert(amount==26 and targetId=="TARGET")
 target.hp=math.max(0,target.hp-amount)
 return {fallen=false,releasedEggIds={},damage=amount}
end
local SiegePacing=Pace
local SIEGE_INTERVAL=1.6
local function realBotSiegeBranch(session,id,enemy,now,lastSiege)
 local enemyLoc=nil
 --SOURCE_BRANCH--
end
local assertions=0
local function check(value,label)
 assertions+=1
 assert(value,label)
end
local function arena(mode)
 local roster={}
 for i=1,4 do
  roster["AI_"..i]={id="AI_"..i,team=if mode=="TEAM" then "RED" else nil,alive=true,isAI=true}
 end
 roster.TARGET={id="TARGET",team=if mode=="TEAM" then "BLUE" else nil,alive=true,isAI=false,hp=1000}
 return {mode=mode,rules={mode=mode,phase="ACTIVE",winner=nil,castles=roster}}
end
local function advance(session,now,cd)
 for i=1,4 do
  realBotSiegeBranch(session,"AI_"..i,session.rules.castles.TARGET,now,cd)
 end
end

local team=arena("TEAM")
local cd={}
advance(team,10,cd)
check(team.rules.castles.TARGET.hp==974,"only one of four bots hits castle")
check(damageCalls==1,"actual source damage exactly once")
advance(team,11,cd)
check(team.rules.castles.TARGET.hp==974,"four bots cannot burst during interval")
advance(team,16.99,cd)
check(team.rules.castles.TARGET.hp==974,"sub-seven interval")
advance(team,17,cd)
check(team.rules.castles.TARGET.hp==948,"second shared per-target strike")
check(damageCalls==2,"real Rules invoked twice")
local br=arena("BATTLE_ROYALE")
local brCd={}
advance(br,17,brCd)
check(br.rules.castles.TARGET.hp==974,"BR independent from TEAM")
check(team.rules.castles.TARGET.hp==948,"BR does not alter TEAM")
-- Force one permitted castle damage to throw. The ORIGINAL branch is used;
-- reservation must roll back so a different bot can hit in the same cycle.
failNext=true
local before=damageCalls
advance(team,24,cd)
check(damageCalls==before+1,"failure first attempt canceled then next bot hit")
check(team.rules.castles.TARGET.hp==922,"failure did not impose ghost seven-sec block")
check(not failNext,"fault actually injected")
advance(team,25,cd)
check(team.rules.castles.TARGET.hp==922,"successful retry still enforces shared budget")
team.rules.phase="FINISHED";team.rules.winner="RED"
advance(team,40,cd)
check(team.rules.castles.TARGET.hp==922,"no post-round damage")
local fresh=arena("TEAM")
advance(fresh,10,{})
check(fresh.rules.castles.TARGET.hp==974,"new session has clean siege budget")
local off=arena("TEAM")
off.gqBotSiegePacingEnabled=false
advance(off,10,{})
check(off.rules.castles.TARGET.hp==896,"flag OFF restores four bots' same-time damage")
check(off.rules.castles.TARGET.hp>0,"rollback has no HP corruption")
print("GQ_BOT_SIEGE_ACTUAL_AUTHOR_BRANCH_NATIVE_PASS",assertions)
"""


def main(src: Path, out: Path):
    s = src.read_text(encoding="utf-8")
    start_label = "elseif now-(lastSiege[id] or 0)>=SIEGE_INTERVAL and SiegePacing.allow(session,enemy.id,id,now) then"
    end_label = "\n          if session.refresh then session.refresh() end"
    assert s.count(start_label) == 1, "staged author action branch gate drift"
    i = s.index(start_label)
    j = s.index(end_label, i)
    clause = s[i:j]
    assert clause.count("Rules.damageCastle(session.rules,enemy.id,id,26)") == 1
    assert clause.count("SiegePacing.cancelFailed(session,enemy.id,id,now)") == 1
    assert clause.strip().endswith("end"), "incomplete branch"
    # Standalone IF is syntactically equivalent to the author's ELSIF branch.
    clause = clause.replace("elseif", "if", 1)
    module = MODULE.read_text(encoding="utf-8")
    assert module.count("return Pace") == 1
    output = TESTS.replace("--MODULE--", module).replace("--SOURCE_BRANCH--", clause)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    print("EXTRACTED_ACTUAL_AUTHOR_BOT_BRANCH_SHA256", hashlib.sha256(clause.encode()).hexdigest())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    main(a.source, a.out)
