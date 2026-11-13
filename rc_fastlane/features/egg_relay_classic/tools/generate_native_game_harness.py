#!/usr/bin/env python3
"""Generate deterministic NATIVE LUAU gameplay transaction tests from the REAL
assembled Game.server.luau function body and immutable original EggRelayPolicy.

Not Roblox engine simulation: services/instances/players are deterministic stubs.
The tested function is extracted byte-for-byte from the real 58-source Game body.
"""
from __future__ import annotations
import argparse
from pathlib import Path

PREFIX = r'''
--!strict
-- Native Luau gameplay code tests; DO NOT claim Roblox Studio engine execution.
local EggRelay=(function()
'''

# The stub block comes AFTER the imported author policy and BEFORE the
# extracted real two functions (the Studio-only switch and the Game handler).
STUB = r'''
local function v(x,y,z)
    return setmetatable({X=x,Y=y,Z=z}, {
        __sub=function(a,b) return v(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
    })
end
local isStudio=true
local serverFlag={Value=true,IsA=function(_,name) return name=="BoolValue" end}
local storage={
    FindFirstChild=function(_,name)
        assert(name=="P0D_RC_ENABLE_EGG_RELAY_CLASSIC")
        return serverFlag
    end
}
local RunService={IsStudio=function() return isStudio end}
local game={GetService=function(_,name)
    assert(name=="ServerStorage")
    return storage
end}
local Players={list={}}
function Players:GetPlayers() return self.list end
local workspace={blocked=false,raycasts=0}
function workspace:Raycast(origin,direction,params)
    assert(origin and direction and params)
    self.raycasts+=1
    return if self.blocked then {} else nil
end
local RaycastParams={new=function() return {} end}
local Enum={RaycastFilterType={Exclude="Exclude"}}
local Rules={validSeq=function(seq,last)
    return type(seq)=="number" and seq==seq and seq%1==0
        and seq>=1 and seq<=1000000 and seq>last
end}
local actor: any=nil
local receiver: any=nil
local carry: any={}
local match: any={}
local slowed: any={}
local lastSeq: any={}
local relayVersions: any={}
local relayLastAt: any={}
local relayAcceptedSeq: any={}
local EXPERIMENTAL_FIVE_EGG_MODE=false
local broadcasts=0
local removeVisuals=0
local giveVisuals=0
local function healthy(p)
    return p.alive,p.root,nil
end
local function getTeamName(p)
    return p.team
end
local function removeCarrierVisual(p)
    assert(p==actor)
    removeVisuals+=1
end
local function giveEggVisual(p)
    assert(p==receiver)
    giveVisuals+=1
end
local function broadcast()
    broadcasts+=1
end
'''

SUFFIX = r'''
local caseCount=0
local function reset()
    isStudio=true
    serverFlag={Value=true,IsA=function(_,name) return name=="BoolValue" end}
    workspace.blocked=false
    workspace.raycasts=0
    broadcasts=0
    removeVisuals=0
    giveVisuals=0
    EXPERIMENTAL_FIVE_EGG_MODE=false
    actor={UserId=101,team="RED",alive=true,Character={},
        Parent=Players,root={Position=v(0,0,0)}}
    receiver={UserId=102,team="RED",alive=true,Character={},
        Parent=Players,root={Position=v(4,0,0)}}
    Players.list={actor,receiver}
    carry={[actor]="BLUE"}
    match={phase="ACTIVE",serial=7,eggOwners={BLUE=actor},
        scores={RED=0,BLUE=0},hp={RED=100,BLUE=100}}
    slowed={}
    lastSeq={[actor]=0,[receiver]=0}
    relayVersions={BLUE=1}
    relayLastAt={}
    relayAcceptedSeq={}
end
local function request(): any
    return {action="EGG_RELAY",seq=1,roundEpoch=7,
        eggId="BLUE",targetUserId=receiver.UserId,expectedTransferSeq=1}
end
local function runCase(label,configure,expected)
    reset()
    local p=request()
    configure(p)
    local preVersion=relayVersions.BLUE
    local preRelayAt=relayLastAt.BLUE
    applyClassicEggRelay(actor,p)
    local passed=(carry[actor]==nil and carry[receiver]=="BLUE"
        and match.eggOwners.BLUE==receiver)
    assert(passed==expected, label..": wrong transfer outcome")
    assert(match.scores.RED==0 and match.scores.BLUE==0,label..": score mutation")
    assert(match.hp.RED==100 and match.hp.BLUE==100,label..": HP mutation")
    if expected then
        assert(broadcasts==1 and removeVisuals==1 and giveVisuals==1,
            label..": missing original visual/broadcast")
        assert(relayVersions.BLUE==2 and relayAcceptedSeq[actor]==1,
            label..": missing version/anti-replay advance")
        assert(relayLastAt.BLUE~=nil,label..": missing 12s cooldown start")
    else
        assert(broadcasts==0 and removeVisuals==0 and giveVisuals==0,
            label..": unauthorized side effects")
        assert(relayVersions.BLUE==preVersion and relayLastAt.BLUE==preRelayAt,
            label..": unauthorized version/cooldown mutation")
    end
    caseCount+=1
end
runCase("valid same-team 4-stud no-wall pass",function(p) end,true)
runCase("at horizontal 8-stud boundary",function(p)
    receiver.root.Position=v(8,0,0)
end,true)
runCase("at vertical 4-stud boundary",function(p)
    receiver.root.Position=v(2,4,0)
end,true)
runCase("negative Studio fake user IDs still work",function(p)
    actor.UserId=-101
    receiver.UserId=-102
    p.targetUserId=-102
end,true)
runCase("wrong team",function(p) receiver.team="BLUE" end,false)
runCase("range too far",function(p) receiver.root.Position=v(8.01,0,0) end,false)
runCase("vertical too far",function(p) receiver.root.Position=v(3,4.01,0) end,false)
runCase("server raycast blocked by obstacle",function(p) workspace.blocked=true end,false)
runCase("dead actor",function(p) actor.alive=false end,false)
runCase("dead target",function(p) receiver.alive=false end,false)
runCase("actor stunned",function(p) slowed[actor]={} end,false)
runCase("recipient restrained",function(p) slowed[receiver]={} end,false)
runCase("target already carrying egg",function(p) carry[receiver]="RED" end,false)
runCase("actor lost live ownership",function(p) match.eggOwners.BLUE=nil end,false)
runCase("wrong egg ID",function(p) p.eggId="RED" end,false)
runCase("wrong recipient UserId",function(p) p.targetUserId=999 end,false)
runCase("stale round serial",function(p) p.roundEpoch=6 end,false)
runCase("stale transfer version",function(p) p.expectedTransferSeq=0 end,false)
runCase("replayed seq",function(p) lastSeq[actor]=1 end,false)
runCase("already accepted seq",function(p) relayAcceptedSeq[actor]=1 end,false)
runCase("cooldown below 12 sec",function(p) relayLastAt.BLUE=os.clock() end,false)
runCase("cooldown expired",function(p) relayLastAt.BLUE=os.clock()-13 end,true)
runCase("Studio missing flag is OFF",function(p) serverFlag=nil end,false)
runCase("Studio BoolValue false",function(p)
    serverFlag={Value=false,IsA=function(_,name) return name=="BoolValue" end}
end,false)
runCase("not Studio cannot pass",function(p) isStudio=false end,false)
runCase("five egg H2 never mutated",function(p)
    EXPERIMENTAL_FIVE_EGG_MODE=true
end,false)
runCase("lobby phase",function(p) match.phase="LOBBY" end,false)
runCase("missing target",function(p) receiver.Parent=nil end,false)
runCase("invalid infinite target ID",function(p) p.targetUserId=math.huge end,false)
runCase("duplicate relay version in invalid request",function(p)
    p.expectedTransferSeq=1.5
end,false)
-- Last: actual replay and re-pass after transfer, before cooldown.
reset()
applyClassicEggRelay(actor,request())
assert(carry[receiver]=="BLUE" and carry[actor]==nil)
local n=broadcasts
applyClassicEggRelay(actor,request())
assert(broadcasts==n and carry[receiver]=="BLUE","duplicate same carrier")
local reverse={action="EGG_RELAY",seq=1,roundEpoch=7,eggId="BLUE",
    targetUserId=actor.UserId,expectedTransferSeq=2}
applyClassicEggRelay(receiver,reverse)
assert(broadcasts==n and carry[receiver]=="BLUE","immediate bounce back cooldown")
caseCount+=1
print("P0D_EGG_RELAY_ACTUAL_GAME_NATIVE_31_CASES_PASS")
assert(caseCount==31,"EXPECTED_31_CASES: "..tostring(caseCount))
'''
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--policy",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    source=a.game.read_text(encoding="utf8")
    begin="local function applyClassicEggRelay(player: Player, data)"
    finish="\nremote.OnServerEvent:Connect("
    assert source.count(begin)==1
    i=source.index(begin)
    assert source.count(finish)==1
    j=source.index(finish,i)
    game_handler=source[i:j]
    assert "EggRelay.evaluate(world," in game_handler
    assert "match.eggOwners[egg]=target" in game_handler
    assert "carry[target]=egg" in game_handler
    assert "os.clock()" in game_handler
    toggle_begin="local function classicRelayEnabled(): boolean"
    toggle_end="\n-- Original Game owns ALL classic-mode"
    assert source.count(toggle_begin)==1
    si=source.index(toggle_begin)
    sj=source.index(toggle_end,si)
    switch=source[si:sj]
    assert "P0D_RC_ENABLE_EGG_RELAY_CLASSIC" in switch
    policy=a.policy.read_text(encoding="utf8")
    assert policy.count("function Relay.evaluate(world, request)")==1
    assert policy.rstrip().endswith("return Relay")
    assert "Relay.MIN_SECONDS_BETWEEN_PASSES = 12" in policy
    generated=PREFIX+policy+"\nend)()\n"+STUB+"\n"+switch+"\n"+game_handler+"\n"+SUFFIX
    assert "P0D_EGG_RELAY_ACTUAL_GAME_NATIVE_31_CASES_PASS" in generated
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(generated,encoding="utf8")
    print("P0D_RELAY_ACTUAL_GAME_FUNCTION_EXTRACTED_FROM_ASSEMBLED_REAL_RC_PASS")
if __name__=="__main__":
    main()
