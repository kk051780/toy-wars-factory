--!strict
local P=require("./EGGRUMBLE_BuilderPlacementPolicy")
local n=0
local function check(b)
 assert(b,"builder native policy assertion "..tostring(n+1))
 n+=1
end
check(P.LIFETIME==9)
check(P.MAX_PER_HERO==2)
check(P.MAX_PER_SESSION==12)
check(P.capacity(0,0))
check(P.capacity(11,1))
check(not P.capacity(12,1))
check(not P.capacity(2,2))
check(not P.capacity(-1,0))
check(not P.capacity(0,0/0))
check(P.cooldown("WALL",100,87))
check(not P.cooldown("WALL",100,88))
check(P.cooldown("BRIDGE",100,83))
check(not P.cooldown("BRIDGE",100,84))
check(not P.cooldown("INVALID",100,0))
check(not P.cooldown("WALL",0/0,0))
check(P.inField(0,0,445,525))
check(not P.inField(430,0,445,525))
check(not P.inField(0,510,445,525))
check(not P.inField(0/0,0,445,525))
check(P.support(3,4,4))
check(not P.support(0,9,4))
check(not P.support(9,4,4))
check(not P.support(0/0,4,4))
check(P.safeDistance(51))
check(not P.safeDistance(50.9))
check(not P.safeDistance(-1))
check(not P.safeDistance(0/0))
check(P.blocksPlacement(false,false,true)) -- body parts can be noncollidable
check(P.blocksPlacement(true,false,true))
check(P.blocksPlacement(true,false,false)) -- solid foreign wall
check(P.blocksPlacement(true,false,false)) -- foreign same-name floor rejected upstream
check(not P.blocksPlacement(false,false,false)) -- noncollidable decoration
check(not P.blocksPlacement(true,true,false)) -- own floor
check(P.blocksPlacement(nil,false,false)) -- fail closed on invalid CanCollide
check(P.blocksPlacement(nil,false,true))
check(not P.blocksPlacement(false,true,false))
print("GQ_BUILDER_NATIVE_POLICY_PASS assertions="..tostring(n))
