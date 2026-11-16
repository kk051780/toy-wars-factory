--!strict
-- Native Luau regression for the optional castle defense policy.
-- This test does NOT claim Roblox Studio physics / Android / official RC acceptance.
local P=require("../EGGRUMBLE_CastleDefensePolicy")
local n=0
local function check(cond:boolean,label:string)
 assert(cond,label)
 n+=1
end
local red={id="1",team="RED",alive=true,modules={"TURRET","TRAP","SENSOR"}}
local blue={id="2",team="BLUE",alive=true,modules={"TURRET"}}
local friend={id="3",team="RED",alive=true}
local dead={id="4",team="BLUE",alive=false}
check(P.TICK_SECONDS<=0.5,"bounded pulse step")
check(P.MAX_CASTLES==16,"mobile castle cap")
check(P.hasModule(red,"TURRET"),"registered turret")
check(P.hasModule(red,"TRAP"),"registered trap")
check(P.hasModule(red,"SENSOR"),"registered sensor")
check(not P.hasModule(blue,"TRAP"),"unbought trap cannot fire")
check(not P.hasModule(red,"UNKNOWN"),"unknown item cannot become a weapon")
check(P.canTarget("TEAM",red,blue),"enemy blue target")
check(P.canTarget("TEAM",blue,red),"enemy red target")
check(not P.canTarget("TEAM",red,friend),"allies must be safe")
check(not P.canTarget("TEAM",red,red),"owner safe")
check(not P.canTarget("TEAM",red,dead),"destroyed castle disarms player")
check(not P.canTarget("TEAM",red,{id="5",team=nil,alive=true}),"team missing")
check(not P.canTarget("TEAM",red,{id="5",team="RED",alive=true}),"friendly target")
check(P.canTarget("BATTLE_ROYALE",red,friend),"BR is individual combat")
check(not P.canTarget("BATTLE_ROYALE",red,red),"BR self safe")
check(not P.canTarget("UNKNOWN",red,blue),"unknown queue blocked")
check(P.mayActivate("TURRET","ACTIVE",20,nil,30,true),"first turret shot")
check(not P.mayActivate("TURRET","LOBBY",20,nil,10,true),"pre-round turret blocked")
check(not P.mayActivate("TURRET","FINISHED",20,nil,10,true),"post-round turret blocked")
check(not P.mayActivate("TURRET","ACTIVE",20,nil,36,true),"outside turret range")
check(not P.mayActivate("TURRET","ACTIVE",20,nil,30,false),"solid walls block turret")
check(not P.mayActivate("TURRET","ACTIVE",20,19,30,true),"turret cooldown")
check(P.mayActivate("TURRET","ACTIVE",22.5,20,30,true),"turret cooldown elapsed")
check(not P.mayActivate("TRAP","ACTIVE",20,nil,10,true),"trap only at entrance")
check(not P.mayActivate("TRAP","ACTIVE",20,nil,7,false),"trap cannot hit through walls")
check(P.mayActivate("TRAP","ACTIVE",20,nil,7,true),"physical trap trigger")
check(not P.mayActivate("TRAP","ACTIVE",26,20,7,true),"trap cooldown")
check(P.mayActivate("TRAP","ACTIVE",27,20,7,true),"trap rearms")
check(P.mayActivate("SENSOR","ACTIVE",20,nil,25,false),"sensor can reveal through walls")
check(not P.mayActivate("SENSOR","ACTIVE",20,nil,31,true),"sensor bounded reach")
check(not P.mayActivate("SENSOR","ACTIVE",20,19.5,25,true),"sensor bounded frequency")
check(not P.mayActivate("SENSOR","ACTIVE",0/0,nil,25,true),"nan time denied")
check(not P.mayActivate("SENSOR","ACTIVE",20,nil,0/0,true),"nan distance denied")
check(not P.mayActivate("SENSOR","ACTIVE",20,nil,-1,true),"negative distance denied")
check(not P.mayActivate("NONE","ACTIVE",20,nil,0,true),"unknown device denied")
print("EGGRUMBLE_CASTLE_DEFENSE_NATIVE_POLICY_PASS "..tostring(n))
