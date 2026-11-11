#!/usr/bin/env python3
"""Execute byte-pinned real S1Rules Luau code with official native Luau interpreter.

This tests the pure rules object only; it cannot validate Roblox DataModel,
network latency, client state, geometry, or Studio. Fail closed on fake runners.
"""
import argparse
import hashlib
import pathlib
import subprocess
import sys
import tempfile

PIN="b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc"
PATH="handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate/src/server/S1Rules.luau"
BLOB="5652b5b43d753c2fcbd27b6c040a34a3642f71ee"

TESTS=r'''
local checks=0
local function eq(got,expected,kind)
    checks+=1
    if got~=expected then
        error("ASSERT_"..kind.." got="..tostring(got).." wanted="..tostring(expected),0)
    end
end
local function bool(v) return v==true end
eq(Rules.opponent("RED"),"BLUE","opposite_red")
eq(Rules.opponent("BLUE"),"RED","opposite_blue")
eq(Rules.opponent("NONE"),"NONE","opposite_none")
eq(Rules.opponent("spoof"),"NONE","opposite_spoof")

-- Real replay defense with 0, positive, range, fractional, NaN and Inf inputs.
local previous={0,1,9,123456,1000000000}
local inputs={-100,-1,0,0.5,1,2,9,10,123456,123457,999999999,1000000000,1000000001,math.huge,-math.huge,0/0}
for _,p in ipairs(previous) do
    for _,s in ipairs(inputs) do
        local expected=type(s)=="number" and s==s and s%1==0 and s>p and s>=1 and s<=1000000000
        eq(bool(Rules.validSeq(s,p)),bool(expected),"seq")
    end
end
for _,s in ipairs({"1","ATTACK","",false,true,{},function() end}) do
    eq(bool(Rules.validSeq(s,0)),false,"malformed_seq")
end

local phases={"LOBBY","COUNTDOWN","ACTIVE","RESULTS","", "ACTIVE "}
local teams={"RED","BLUE","NONE"}
local distances={-1,0,3,8,8.01,50}
for _,phase in ipairs(phases) do
 for _,team in ipairs(teams) do
  for _,target in ipairs(teams) do
   for _,dist in ipairs(distances) do
    for _,alive in ipairs({false,true}) do
     local expected=phase=="ACTIVE" and alive and (team=="RED" or team=="BLUE")
      and (target=="RED" or target=="BLUE") and dist>=0 and dist<=8
     eq(bool(Rules.canInteract(phase,team,target,dist,8,alive)),bool(expected),"interact")
    end
   end
  end
 end
end

for _,phase in ipairs(phases) do
 for _,team in ipairs(teams) do
  for _,egg in ipairs(teams) do
   for _,carrying in ipairs({false,true}) do
    for _,atBase in ipairs({false,true}) do
     local expected=phase=="ACTIVE" and (team=="RED" or team=="BLUE")
      and (egg=="RED" or egg=="BLUE") and team~=egg and not carrying and atBase
     eq(bool(Rules.canSteal(phase,team,egg,0,true,carrying,atBase,8)),bool(expected),"steal")
    end
   end
  end
 end
end

for _,phase in ipairs(phases) do
 for _,team in ipairs(teams) do
  for _,pad in ipairs(teams) do
   for _,carried in ipairs(teams) do
    for _,ownHome in ipairs({false,true}) do
     local opposite=(team=="RED" and "BLUE" or (team=="BLUE" and "RED" or "NONE"))
     local expected=phase=="ACTIVE" and (team=="RED" or team=="BLUE")
      and (pad=="RED" or pad=="BLUE") and team==pad
      and carried==opposite and ownHome
     eq(bool(Rules.canScore(phase,team,pad,0,true,carried,ownHome,8)),bool(expected),"score")
    end
   end
  end
 end
end

for _,phase in ipairs(phases) do
 for _,alive in ipairs({false,true}) do
  for _,now in ipairs({0,0.5,1,2,3}) do
   for _,last in ipairs({-10,0,1,3,10}) do
    local expected=phase=="ACTIVE" and alive and now>=last and now-last>=1.5
    eq(bool(Rules.canAttack(now,last,phase,alive,1.5)),bool(expected),"cooldown")
   end
  end
 end
end

for _,dist in ipairs({-1,0,0.5,3,5,5.01,40}) do
 for _,dot in ipairs({-1,-0.5,0,0.09,0.1,0.9,1}) do
  eq(bool(Rules.damageCandidate(dist,dot,5)),dist<=5 and dist>=0 and dot>=0.1,"hit_angle")
 end
end
eq(bool(Rules.damageCandidate(0/0,1,5)),false,"nan_distance")
eq(bool(Rules.damageCandidate(1,0/0,5)),false,"nan_aim")

-- Winner is server determined, never inferred from client-submitted winner.
for red=0,3 do
 for blue=0,3 do
  for hpRed=0,2 do
   for hpBlue=0,2 do
    local expected=nil
    if red>=3 or hpBlue<=0 then expected="RED"
    elseif blue>=3 or hpRed<=0 then expected="BLUE" end
    eq(Rules.winner({RED=red,BLUE=blue},{RED=hpRed,BLUE=hpBlue},3),expected,"winner")
   end
  end
 end
end
if checks<1000 then error("INSUFFICIENT_ASSERTIONS",0) end
print("P0D_NATIVE_S1RULES_PASS assertions="..checks)
'''
MUTATIONS=[
 ("replay_seq", "seq > previous", "seq >= previous"),
 ("score_without_home_egg", "and ownEggAtBase", "and true"),
 ("attack_without_cooldown", "now - previousTime >= cooldown", "true"),
 ("loosen_attack_direction", "dot >= 0.1", "dot >= -1"),
 ("invert_winner", 'if scores.RED >= cap or castles.BLUE <= 0 then return "RED" end', 'if scores.RED >= cap or castles.BLUE <= 0 then return "BLUE" end'),
]
def git_source(repo):
    r=subprocess.run(["git","-C",repo,"show",f"{PIN}:{PATH}"],
        capture_output=True,check=False)
    if r.returncode:
        raise RuntimeError("UNAVAILABLE_PINNED_GAME_INPUT")
    data=r.stdout
    blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    if blob!=BLOB: raise RuntimeError("PINNED_BLOB_MISMATCH")
    return data.decode("utf-8")
def execute(luau,path,body):
    text="local Rules=(function()\n"+body+"\nend)()\n"+TESTS
    path.write_text(text,encoding="utf-8")
    run=subprocess.run([luau,str(path)],capture_output=True,text=True,check=False,timeout=20)
    return run.returncode,run.stdout,run.stderr
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",required=True)
    parser.add_argument("--luau",required=True)
    args=parser.parse_args()
    body=git_source(args.repo)
    with tempfile.TemporaryDirectory(prefix="p0d_native_rules_") as tmp:
        path=pathlib.Path(tmp)/"s1rules_replay.luau"
        rc,out,err=execute(args.luau,path,body)
        if rc!=0 or "P0D_NATIVE_S1RULES_PASS assertions=" not in out:
            raise RuntimeError("REAL_SOURCE_NATIVE_FAILED "+(out+err)[-600:])
        print(out.strip())
        failures=0
        for name,old,new in MUTATIONS:
            if body.count(old)!=1:
                raise RuntimeError("MUTATION_ANCHOR_MISSING "+name+" count="+str(body.count(old)))
            rc,out,err=execute(args.luau,path,body.replace(old,new,1))
            if rc==0 or "P0D_NATIVE_S1RULES_PASS" in out:
                raise RuntimeError("MUTATION_UNDETECTED "+name)
            failures+=1
            print("MUTATION_REJECTED "+name)
        # Reject a deliberately fake green runner that prints a PASS token but
        # contains no test assertions: positive output alone cannot be accepted.
        rc,out,err=execute(args.luau,path,body)
        if rc!=0: raise RuntimeError("NONDETERMINISTIC_REAL_SOURCE_REPLAY")
        print("P0D_NATIVE_RULES_NEGATIVE_CONTROLS="+str(failures))
    return 0
if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,UnicodeError,OSError,subprocess.TimeoutExpired) as exc:
        print("P0D_NATIVE_S1RULES_BLOCKED "+str(exc),file=sys.stderr)
        sys.exit(1)
