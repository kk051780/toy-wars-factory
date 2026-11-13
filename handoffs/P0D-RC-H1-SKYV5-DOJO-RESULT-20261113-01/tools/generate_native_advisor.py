#!/usr/bin/env python3
"""Run EXACT immutable original Advisor table logic, not a rewritten model."""
from pathlib import Path
import argparse,hashlib

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"src/NextStepAdvisor.luau"
raw=P.read_bytes()
digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
assert digest=="d212dae56b328d48bfed5dafa742caff9afe82c7",digest
source=raw.decode("utf8")
assert source.rstrip().endswith("return Advisor")
head=source.rstrip()[:-len("return Advisor")]

test=r'''
local n=0
local function eq(tag,got,want)
    n+=1
    if got~=want then
        error("P0D_ADVISOR_NATIVE_FAIL:"..tag.." got="..tostring(got).." want="..tostring(want))
    end
end
local function test(tag,match,progress,opt)
    local result=Advisor.build(match,progress,opt)
    n+=1
    assert(type(result)=="table" and result.readOnly==true,tag)
    return result
end
local nothing=test("nil inputs",nil,nil,nil)
eq("nil result is practice",nothing.result,"PRACTICE")
eq("nil never grants XP",nothing.eggsScored,0)
eq("no rescue claims from nil",nothing.rescues,0)
eq("nil uses installed H1 default",nothing.suggestedSkill,"beast")
eq("no selected six skills",nothing.action,"VIEW_TRAINING")
eq("seven second card",nothing.autoDismissSeconds,7)
eq("close allowed",nothing.dismissible,true)
local won=test("winner",{won=true,eggsScored=2,neutralDefeats=6,rescues=0},
              {skillLevels={beast=2,weapon=4}},{availableSkills={"beast","weapon"}})
eq("win",won.result,"WIN")
eq("real team score projected",won.eggsScored,2)
eq("H1 weakest skill",won.suggestedSkill,"beast")
eq("H1 proposed level",won.suggestedSkillLevel,2)
eq("no fake friend",won.friendBonusVisible,false)
local lost=test("loss",{won=false,eggsScored=1}, {skillLevels={beast=5,weapon=1}},nil)
eq("lose",lost.result,"LOSE")
eq("weapon is lowest",lost.suggestedSkill,"weapon")
local evolve=test("evolve",{won=true,eggsScored=4},
        {canEvolve=true,canHatch=true,skillLevels={beast=1,weapon=1}},nil)
eq("evolution priority",evolve.action,"VIEW_EVOLUTION")
eq("evolution says available",evolve.actionText,"進化の条件を達成！次の姿を見てみよう")
local hatch=test("only true server hatch readiness",{won=false},
        {canEvolve=false,canHatch=true,skillLevels={beast=2,weapon=2}},nil)
eq("hatch second priority",hatch.action,"VIEW_HATCH")
local allmax=test("maxed",{won=true},{skillLevels={beast=5,weapon=5}},nil)
eq("all mastered immediate replay",allmax.action,"PLAY_AGAIN")
eq("no recommendation skill at cap",allmax.suggestedSkill,nil)
local friend=test("server friend",{won=false},{skillLevels={beast=1,weapon=1}},
                  {availableSkills={"beast","weapon"},sameServerFriendBonus=true})
eq("server bool allows visible bonus",friend.friendBonusVisible,true)
local fake=test("invalid stats",{eggsScored=999,neutralDefeats=-10,rescues=math.huge},
      {skillLevels={beast=2.5,weapon=-3}},nil)
eq("score cap 100",fake.eggsScored,100)
eq("KO lower bounded 0",fake.neutralDefeats,0)
eq("rescue infinity fail closed",fake.rescues,0)
eq("invalid levels cannot reward level",fake.suggestedSkillLevel,0)
local nan=test("NaN",{eggsScored=0/0,neutralDefeats=math.huge,rescues=-math.huge},
      {skillLevels={beast=5,weapon=5}},nil)
eq("NaN egg",nan.eggsScored,0)
eq("Inf KO",nan.neutralDefeats,0)
eq("negative Inf rescue",nan.rescues,0)
local skill6=test("six requested only when explicitly provided",{won=false},
     {skillLevels={beast=5,weapon=5,magic=1}},
     {availableSkills={"beast","weapon","magic"}})
eq("six only when supplied",skill6.suggestedSkill,"magic")
eq("untrusted skill never displayed",Advisor.build(nil,{skillLevels={pet=1}},
   {availableSkills={"pet"}}).suggestedSkill,"beast")
assert(n>=30)
print("P0D_H1_RESULT_ADVISOR_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--write",required=True,type=Path)
    args=p.parse_args()
    args.write.parent.mkdir(parents=True,exist_ok=True)
    args.write.write_text(head+test,encoding="utf8")
    print("P0D_ADVISOR_NATIVE_TEST_REAL_SOURCE_GENERATED")
