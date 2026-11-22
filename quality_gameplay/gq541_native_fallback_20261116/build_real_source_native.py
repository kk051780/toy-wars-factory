#!/usr/bin/env python3
"""Execute the real immutable #541 source's target-selection Luau, not a Python model.

This only generates isolated native Luau tests. It does not write any Game/Swarm/
RC runtime source, does not claim Roblox-engine validation, and fails on drift.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
from pathlib import Path

COMPOSER_BLOB = "896aabf81113c02ac7a74909d579ffd20beb2b57"
POLICY_BLOB = "67982086cd548aeab9324c0a04689ca37f0d4828"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def extract(composer: Path) -> str:
    raw = composer.read_bytes()
    if blob(raw) != COMPOSER_BLOB:
        raise ValueError("RED_AUTHOR541_COMPOSER_DRIFT")
    tree = ast.parse(raw.decode("utf-8"))
    chunks = []
    for top in tree.body:
        if isinstance(top, ast.FunctionDef) and top.name == "patch":
            for node in ast.walk(top):
                if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
                    continue
                if not any(isinstance(t, ast.Name) and t.id == "b" for t in node.targets):
                    continue
                value = node.value.value
                if isinstance(value, str) and "-- Same existing Swarm tick" in value:
                    chunks.append(value)
    if len(chunks) != 1:
        raise ValueError("RED_AUTHOR541_SECTION_NOT_UNIQUE")
    section = chunks[0]
    start = section.index("      -- Same existing Swarm tick")
    stop = section.rfind("\n     end\n")
    if stop <= start:
        raise ValueError("RED_AUTHOR541_SECTION_TERMINATOR")
    body = section[start:stop] + "\n"
    must = (
        "Melee.ready(", "table.sort(eligible,", "meleeRays+=1",
        "if meleeLineClear(m,candidate.victim.root) then",
        "Melee.commit(", "candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)",
        "break -- One real hit per soldier swing."
    )
    if any(body.count(part) != 1 for part in must):
        raise ValueError("RED_AUTHOR541_MOVEMENT_CHANGED")
    if "nearest.humanoid:TakeDamage" in body:
        raise ValueError("RED_OLD_BUG_REINTRODUCED")
    return body

RUNTIME = r'''
local Melee=(function()
__POLICY__
end)()

local vectorMT={}
vectorMT.__sub=function(a,b)
    return setmetatable({x=a.x-b.x},vectorMT)
end
vectorMT.__index=function(a,k)
    if k=="Magnitude" then return math.abs(a.x) end
    return nil
end
local function vector(x) return setmetatable({x=x},vectorMT) end

local function newVictim(id,x,blocked,health)
    local hum={Health=health or 20,damage=0,id=id}
    function hum:TakeDamage(amount)
        self.damage+=amount
        self.Health-=amount
    end
    return {root={Position=vector(x), blocked=blocked or false},
            humanoid=hum}
end
local function newSoldier()
    return {PrimaryPart={Position=vector(0)}}
end

local function actualSourceTick(m, victims, meleeNow, meleeRays,
                                lastMeleeSwing,lastVictimHit,phase)
    local h={Health=10}
    local session={rules={phase=phase or "ACTIVE"}}
    local function meleeLineClear(_,target)
        return not target.blocked
    end
__REAL_AUTHOR541_MOVEMENT__
    return meleeRays
end

local function check(cond,label)
    if not cond then error("GQ541_NATIVE_FAIL "..label,2) end
end
'''

TESTS = r'''
do -- nearest victim on cooldown; second gets exactly one real 4 HP hit
    local n,f=newVictim("near",1,false),newVictim("far",2,false)
    local cd={[n.humanoid]=9.5}
    local used=actualSourceTick(newSoldier(),{n,f},10,0,{},cd)
    check(used==1 and n.humanoid.damage==0 and f.humanoid.damage==4,"cooldown_fallback")
    check(cd[n.humanoid]==9.5 and cd[f.humanoid]==10,"cd_commit_only_selected")
end
do -- wall in front, legal target behind; wall does not spend victim CD
    local a,b=newVictim("wall",1,true),newVictim("visible",2,false)
    local cd={}
    local used=actualSourceTick(newSoldier(),{a,b},10,0,{},cd)
    check(used==2 and a.humanoid.damage==0 and b.humanoid.damage==4,"wall_fallback")
    check(cd[a.humanoid]==nil and cd[b.humanoid]==10,"wall_no_cd_commit")
end
do -- stable equal-distance victim order
    local a,b=newVictim("first",2,false),newVictim("second",2,false)
    local used=actualSourceTick(newSoldier(),{a,b},10,0,{},{})
    check(used==1 and a.humanoid.damage==4 and b.humanoid.damage==0,"stable_tie_single_hit")
end
do -- dead closest ignored; soldier attack has no duplicate hit
    local a,b=newVictim("dead",1,false),newVictim("live",2,false)
    a.humanoid.Health=0
    local used=actualSourceTick(newSoldier(),{a,b},10,0,{},{})
    check(used==1 and a.humanoid.damage==0 and b.humanoid.damage==4,"dead_target_ignored")
end
do -- global 24 LOS rays across multiple soldiers during one shared tick
    local walls={}
    for i=1,40 do
        table.insert(walls,newVictim("blocked"..i,1+i/100,true))
    end
    local cd={}
    local used=actualSourceTick(newSoldier(),walls,10,0,{},cd)
    check(used==24,"global_los_cap")
    local nextTarget=newVictim("next",1,false)
    local used2=actualSourceTick(newSoldier(),{nextTarget},10,used,{},cd)
    check(used2==24 and nextTarget.humanoid.damage==0,"budget_shared_across_soldiers")
end
do -- soldier cooldown caps repeated swings
    local a=newVictim("one",1,false)
    local mob=newSoldier()
    local s,v={},{}
    local used=actualSourceTick(mob,{a},10,0,s,v)
    check(used==1 and a.humanoid.damage==4 and s[mob]==10,"first_swing")
    local used2=actualSourceTick(mob,{a},10.81,0,s,v)
    check(used2==0 and a.humanoid.damage==4,"soldier_cooldown")
    local used3=actualSourceTick(mob,{a},11.4,0,s,v)
    check(used3==1 and a.humanoid.damage==8,"soldier_boundary")
end
do -- phase gate: never hit after match ended
    local a=newVictim("inactive",1,false)
    local used=actualSourceTick(newSoldier(),{a},10,0,{},{},"FINISHED")
    check(used==0 and a.humanoid.damage==0,"finished_match")
end
do -- 0 rays remain, do not call LOS or deal damage
    local a=newVictim("cap",1,false)
    local used=actualSourceTick(newSoldier(),{a},10,24,{},{})
    check(used==24 and a.humanoid.damage==0,"zero_budget")
end
do -- victim CD still prevents repeat damage from another soldier
    local a=newVictim("shared",1,false)
    local cd={}
    local used=actualSourceTick(newSoldier(),{a},10,0,{},cd)
    local used2=actualSourceTick(newSoldier(),{a},10.3,used,{},cd)
    check(used==1 and used2==1 and a.humanoid.damage==4,"victim_global_cd")
end
print("GQ541_REAL_AUTHOR_NATIVE_TARGET_SELECTION_9_CASES_PASS")
'''

def build(composer: Path, policy_path: Path, out: Path, mutant: bool) -> None:
    policy_raw = policy_path.read_bytes()
    if blob(policy_raw) != POLICY_BLOB:
        raise ValueError("RED_AUTHOR533_MELEE_POLICY_DRIFT")
    body = extract(composer)
    if mutant:
        anchor = "if meleeLineClear(m,candidate.victim.root) then"
        if body.count(anchor) != 1:
            raise ValueError("RED_MUTANT_ANCHOR")
        # A realistic regression: stop after the first blocked LOS result.
        body = body.replace(anchor,
            "if not meleeLineClear(m,candidate.victim.root) then break end\n"
            "         " + anchor,1)
    source=RUNTIME.replace("__POLICY__",policy_raw.decode("utf-8"))
    source=source.replace("__REAL_AUTHOR541_MOVEMENT__",body)
    source+=TESTS
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(source,encoding="utf-8")
    print("NATIVE_REAL_AUTHOR541_SOURCE_LOCKED",out,len(source.encode("utf-8")),mutant)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--author-composer",type=Path,required=True)
    parser.add_argument("--policy",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--mutant",action="store_true")
    args=parser.parse_args()
    build(args.author_composer,args.policy,args.out,args.mutant)
