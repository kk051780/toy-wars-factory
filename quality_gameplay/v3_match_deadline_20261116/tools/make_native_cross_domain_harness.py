#!/usr/bin/env python3
"""Execute original #482 CastleMatchRules + #487 ScoreBalance + #499 DeadlinePolicy
inside the actual native Luau VM. Original source files are not edited.
"""
from pathlib import Path
import argparse

TESTS=r"""
local assertions=0
local function check(ok,message)
 assertions+=1
 assert(ok,message)
end
local teamRoster=Rules.makeRoster("TEAM",{"101","102"},2)
local team=Rules.new("TEAM",teamRoster,24)
Rules.start(team)
check(team.phase=="ACTIVE","team must begin ACTIVE")
local before=Rules.auditEggConservation(team)
check(before.valid,"initial physical egg conservation")
check(before.total==30,"2 castles x3 and 24 field eggs")
Rules.takeEggs(team,"101",1,"102")
check(team.castles["101"].heldEggs==1,"real egg steal")
Rules.depositEggs(team,"101",1)
check(team.castles["101"].heldEggs==0,"real egg delivered")
check(team.castles["102"].vaultEggs==2,"enemy physical vault lost one")
check(Rules.auditEggConservation(team).valid,"egg conservation after steal and deposit")
local lease=Deadline.new(42,"TEAM:roundA")
local ok,reason=Deadline.expire(team,lease,941,"TEAM:roundA")
check(ok==false and reason=="BEFORE_DEADLINE","deadline not premature")
check(team.phase=="ACTIVE","preserve combat until deadline")
ok,reason=Deadline.expire(team,lease,942,"TEAM:roundA")
check(ok==true and reason=="TIME_LIMIT_DRAW","timed game completes")
check(team.phase=="FINISHED" and team.winner=="DRAW","timed TEAM ends DRAW")
check(Rules.auditEggConservation(team).valid,"time limit must not delete eggs")
check(team.castles["101"].alive and team.castles["102"].alive,"no invented castle death")
local result=Results.build(team,{["101"]=4,["102"]=1})
check(result.winner=="DRAW" and #result.rows==2,"score recognizes DRAW")
local matched=false
for _,row in ipairs(result.rows) do
 check(row.won==false,"draw must not earn WIN+500")
 if row.id=="101" then
  check(row.securedSteals==1 and row.deposited==1,"genuine raid scoring preserved")
  matched=true
 end
end
check(matched,"owner A ranking retained")
ok,reason=Deadline.expire(team,lease,943,"TEAM:roundA")
check(ok==false and reason=="ALREADY_APPLIED","replayed timer no mutation")
local royale=Rules.new("BATTLE_ROYALE",Rules.makeRoster("BATTLE_ROYALE",{"201","202"},2),24)
Rules.start(royale)
local lr=Deadline.new(5,"BR:roundA")
ok,reason=Deadline.expire(royale,lr,905,"BR:roundA")
check(ok and royale.winner=="DRAW","BR timeout is non-fabricated draw")
check(Rules.auditEggConservation(royale).valid,"BR egg conservation")
for _,row in ipairs(Results.build(royale,{["201"]=2}).rows) do
 check(row.won==false,"BR draw must not reward win")
end
local legit=Rules.new("TEAM",teamRoster,24)
Rules.start(legit)
for _=1,4 do Rules.damageCastle(legit,"102","101",250) end
check(legit.phase=="FINISHED" and legit.winner=="RED","real castle victory unchanged")
ok,reason=Deadline.expire(legit,Deadline.new(0,"TEAM:final"),900,"TEAM:final")
check(ok==false and reason=="ALREADY_FINISHED","winner never overwritten")
for _,row in ipairs(Results.build(legit,{}).rows) do
 if row.id=="101" then check(row.won and row.score>=700,"genuine winner retains 500-point bonus") end
end
print("EGGRUMBLE_V3_REAL_RULES_SCORE_DEADLINE_NATIVE_PASS "..assertions)
"""

def embed(name,source):
    text=source.read_text(encoding="utf-8").rstrip()
    assert text.endswith({"Rules":"return M","Results":"return Results","Deadline":"return Deadline"}[name])
    return "local "+name+"=(function()\n"+text+"\nend)()\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rules",required=True,type=Path)
    p.add_argument("--score",required=True,type=Path)
    p.add_argument("--policy",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    output=(embed("Rules",a.rules)+embed("Results",a.score)+embed("Deadline",a.policy)+TESTS)
    dest=a.out
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(output,encoding="utf-8")

if __name__=="__main__":
    main()
