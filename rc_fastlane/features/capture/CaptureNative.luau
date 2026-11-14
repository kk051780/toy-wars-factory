--!nocheck
-- Native Luau fixture: CI must inject real module as Capture (not yet executed).
local tests=0
local function check(ok,name) tests+=1 assert(ok,"CAPTURE_"..name) end
local a,b,target,other,friend={},{},{},{},{}
local s={now=100,epoch=7,phase="ACTIVE",role="TRAPPER",
    attackerTeam="RED",targetTeam="BLUE",attackerAlive=true,targetAlive=true,
    targetInvulnerable=false,attackerCarrying=false,targetCarrying=false,
    serverDistance=5,serverLineOfSight=true}
local function clone()
    local v={} for k,x in pairs(s) do v[k]=x end return v
end
check(Capture.status(target,100,7)==nil,"initial")
local x=clone() x.phase="LOBBY"
check(not Capture.begin(a,target,x),"lobby")
x=clone() x.role="RAIDER"
check(not Capture.begin(a,target,x),"role")
x=clone() x.targetTeam="RED"
check(not Capture.begin(a,target,x),"same_team")
x=clone() x.serverDistance=100
check(not Capture.begin(a,target,x),"range")
x=clone() x.serverLineOfSight=false
check(not Capture.begin(a,target,x),"los")
x=clone() x.targetInvulnerable=true
check(not Capture.begin(a,target,x),"invuln")
local ok,why=Capture.begin(a,target,clone())
check(ok and why=="CAPTURED","capture")
check(Capture.status(target,100,7).remaining==4,"four_seconds")
check(not Capture.begin(a,target,clone()),"no_extend")
check(not Capture.begin(b,other,clone()),"team_limit")
local rescue={now=101,epoch=7,phase="ACTIVE",rescuerAlive=true,
    targetAlive=true,rescuerTeam="BLUE",serverDistance=3}
check(Capture.rescue(friend,target,rescue),"teammate_rescued")
check(Capture.status(target,101,7)==nil,"rescue_clear")
check(not Capture.begin(a,target,clone()),"cooldown")
s.now=118
check(Capture.begin(a,target,clone()),"cooldown_boundary")
check(Capture.status(target,122,7)==nil,"expiry")
Capture.clearRound()
s.now=130
check(Capture.begin(a,target,clone()),"reset")
Capture.forget(a)
check(Capture.status(target,130,7)==nil,"leave_cleanup")
assert(tests==18,"EXPECTED_18_GOT_"..tostring(tests))
print("CAPTURE_NATIVE_18_PASS")
