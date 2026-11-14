#!/usr/bin/env python3
"""Execute EXACT authored Bot.tryHumanHit function with Luau raycast mocks.

Tests target, wall, friendly, nearer enemy, nil-ray, range, cone, team, life.
This is native Luau semantics, not physical Roblox Studio raycasting.
"""
import argparse,re
from pathlib import Path

def generate(module:Path):
    s=module.read_text("utf8")
    header="function Bot.tryHumanHit(team,origin,look,reach,attackerCharacter)"
    assert s.count(header)==1,("HUMAN_HIT_FUNCTION_CHANGED",s.count(header))
    tail=s.split(header,1)[1]
    finish=re.search(r'(?m)^end\s*$',tail)
    assert finish, "HUMAN_HIT_END_MISSING"
    function=header+tail[:finish.end()]
    required=("workspace:Raycast(origin,delta,params)",
      "hit.Instance:IsDescendantOf(bot.model)",
      "FilterDescendantsInstances={attackerCharacter}",
      "closest=d", "bot.team~=team")
    for text in required:
        assert text in function,("LOS_GUARD_LOST",text)
    assert 'FilterDescendantsInstances={bot.model,folder,attackerCharacter}' not in function
    code=r'''-- Native authored Bot.tryHumanHit raycast/occlusion behavioral QA.
local function v(x)
    local data={x=x}
    return setmetatable(data,{
        __sub=function(a,b) return v(a.x-b.x) end,
        __index=function(t,k)
            if k=="Magnitude" then return math.abs(t.x) end
            if k=="Unit" then
                return v(t.x>=0 and 1 or -1)
            end
            if k=="Dot" then return function(self,other) return self.x*other.x end end
            return nil
        end
    })
end
local Enum={RaycastFilterType={Exclude="Exclude"}}
local RaycastParams={}
function RaycastParams.new() return {} end
local a={tag="TARGET"}
local other={tag="OTHER_ENEMY"}
local ally={tag="ALLY"}
local wall={tag="WALL"}
local attacker={tag="PLAYER"}
local bots={{model=a,team="BLUE",root={Position=v(5)},hum={Health=100}},
    {model=other,team="BLUE",root={Position=v(8)},hum={Health=100}},
    {model=ally,team="RED",root={Position=v(3)},hum={Health=100}}}
local active=true
local function alive(bot) return bot.hum.Health>0 end
local mode="target"
local rayCalls=0
local workspace={}
local function hit(owner)
    return {Instance={IsDescendantOf=function(self,model) return owner==model end}}
end
function workspace:Raycast(origin,delta,params)
    rayCalls+=1
    assert(params.FilterType=="Exclude")
    assert(#params.FilterDescendantsInstances==1,"MUST_ONLY_EXCLUDE_ATTACKER")
    assert(params.FilterDescendantsInstances[1]==attacker,"MUST_NOT_IGNORE_OTHER_BOTS")
    if mode=="target" then
        return hit(delta.x>=7 and other or a)
    elseif mode=="wall" then return hit(wall)
    elseif mode=="ally" then return hit(ally)
    elseif mode=="nearer_enemy" then return hit(delta.x>=7 and a or other)
    elseif mode=="none" then return nil
    end
    error("unknown mode")
end
local Bot={}
''';
    tests=r'''
-- 1: clear real ray against candidate should accept nearest valid bot.
mode="target"
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==bots[1],"TARGET_NOT_HIT")
-- 2: walls block the target.
mode="wall"
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==nil,"ATTACK_PASSES_THROUGH_WALL")
-- 3: allied bots act as physical blockers.
mode="ally"
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==nil,"ATTACK_PASSES_THROUGH_ALLY")
-- 4: an unintended nearer enemy blocks a farther target.
mode="nearer_enemy"
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==nil,"ATTACK_PASSES_THROUGH_BOT")
-- 5: a ray that did not hit a queryable physical torso cannot award damage.
mode="none"
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==nil,"NO_HIT_DAMAGE")
-- 6: angle and reach contract.
mode="target"
assert(Bot.tryHumanHit("RED",v(0),v(-1),9,attacker)==nil,"BACKWARDS_DAMAGE")
assert(Bot.tryHumanHit("RED",v(0),v(1),3,attacker)==nil,"EXCESS_REACH")
-- 7: team authority and alive status.
assert(Bot.tryHumanHit("BLUE",v(0),v(1),9,attacker)==nil,"FRIENDLY_FIRE")
bots[1].hum.Health=0
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==bots[2],"DEAD_TARGET_NOT_SKIPPED")
-- 8: cannot attack while no active bot match.
active=false
assert(Bot.tryHumanHit("RED",v(0),v(1),9,attacker)==nil,"INACTIVE_DAMAGE")
assert(rayCalls>4,"RAY_PATH_NOT_EXECUTED")
print("FB005_HUMAN_BOT_LOS_NATIVE_8_SCENARIOS_PASS")
'''
    return code+function+"\n"+tests

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--module",type=Path,required=True)
    p.add_argument("--emit",type=Path,required=True)
    a=p.parse_args()
    out=generate(a.module)
    a.emit.write_text(out,"utf8")
    print("FB005_HUMAN_BOT_LOS_EXTRACTED",len(out))
