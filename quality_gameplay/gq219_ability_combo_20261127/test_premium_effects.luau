local R=require("./PremiumEffectRules")
local function eq(a,b) assert(a==b,tostring(a).." != "..tostring(b)) end
local function near(a,b) assert(math.abs(a-b)<1e-8,tostring(a).." != "..tostring(b)) end
local function context(extra)
    local c={confirmedHit=true,consumed=false,active=true}
    for k,v in pairs(extra or {}) do c[k]=v end
    return c
end
local function plan(n,s,extra) return R.planAfterHit(string.format("PREMIUM-%03d",n),s,context(extra)) end
local count=0
for s=0,4 do
    local i=s+1
    for b=0,1000 do
        local p=R.reserveEcho(s,b)
        eq(p.main+p.reserved,b)
        eq(p.reserved,math.floor(b*({20,25,30,35,40})[i]/100))
        assert(table.isfrozen(p))
        eq(R.releaseEcho(s,b,p.delay-0.001,true,true,false,b),nil)
        eq(R.releaseEcho(s,b,p.delay,true,true,true,b),nil)
        eq(R.releaseEcho(s,b,p.delay,true,false,false,b),nil)
        eq(R.releaseEcho(s,b,p.delay,false,true,false,b),nil)
        local result=R.releaseEcho(s,b,p.delay,true,true,false,math.floor(b/10))
        if math.min(p.reserved,math.floor(b/10))==0 then eq(result,nil) else eq(result.maxDamage,math.min(p.reserved,math.floor(b/10)));eq(result.allowRecursive,false) end
        count+=1
    end
    local large=R.reserveEcho(s,9007199254740991);eq(large.main+large.reserved,9007199254740991)
    local ret={explicitReturn=true,selectionOpen=true,safeOrigin=true,canMove=true,carryingEgg=false,moveCap=99,distance=({4,6,8,10,12})[i]}
    eq(plan(4,s,ret).maxDistance,ret.distance)
    ret.carryingEgg=true;eq(plan(4,s,ret),nil);ret.carryingEgg=false;ret.distance+=0.01;eq(plan(4,s,ret),nil)
    local lift={targetKind="NEUTRAL",safeLanding=true,resistant=false,targetCap=2,liftCap=3}
    eq(plan(5,s,lift).maxTargets,math.min(i,2));eq(plan(5,s,lift).maxHeight,math.min(i+1,3))
    lift.resistant=true;eq(plan(5,s,lift),nil)
    eq(plan(5,s,{targetKind="PLAYER",legalPush=true}).noLift,true)
    eq(plan(5,s,{targetKind="BOSS",legalPush=true}),nil)
    local attrs={}
    for j=1,i do attrs[j]="ELEMENT_"..j end
    eq(R.replaceAttribute(s,attrs,attrs[i]).attribute,attrs[i])
    eq(R.replaceAttribute(s,attrs,"MISSING"),nil);attrs[i+1]="EXTRA";eq(R.replaceAttribute(s,attrs,attrs[1]),nil)
    eq(plan(7,s,{safeVisualPoint=true,decoyActive=false}).duration,({0.7,0.9,1.1,1.3,1.5})[i])
    eq(plan(7,s,{safeVisualPoint=true,decoyActive=true}),nil)
    local heal={healAllowed=true,maxHP=1000,hp=900,healedRoundFraction=0,healCap=1000}
    near(plan(8,s,heal).maxAmount,({10,15,20,25,30})[i])
    heal.healedRoundFraction=0.059;near(plan(8,s,heal).maxAmount,1)
    heal.healedRoundFraction=0.06;eq(plan(8,s,heal),nil)
    heal.healedRoundFraction=0;heal.hp=999.5;near(plan(8,s,heal).maxAmount,0.5)
    heal.hp=1000;eq(plan(8,s,heal),nil)
    heal.hp=0;eq(plan(8,s,heal),nil)
    local seal={targetKind="PLAYER",targetEligible=true,targetUsedThisRound=false}
    eq(plan(9,s,seal).duration,({1,1.5,2,2.5,3})[i])
    seal.targetUsedThisRound=true;eq(plan(9,s,seal),nil)
    local sc={eligibleOptionalEffect=true,protectedKind=false,sameMarkedSourceAndCaster=true,consumed=false,elapsed=0,amount=100,mitigationCap=0.1}
    near(R.sealMitigation(s,sc).maxReduction,10);sc.protectedKind=true;eq(R.sealMitigation(s,sc),nil)
    sc.protectedKind=false;sc.sameMarkedSourceAndCaster=false;eq(R.sealMitigation(s,sc),nil)
    sc.sameMarkedSourceAndCaster=true;sc.elapsed=({1,1.5,2,2.5,3})[i];eq(R.sealMitigation(s,sc),nil)
    local a={invincible=false,otherMitigation=false,mitigationCap=1}
    local armor=plan(10,s,a)
    near(armor.maxMitigation,({0.05,0.08,0.11,0.14,0.17})[i]);eq(armor.reflectDamage,0)
    a.invincible=true;eq(plan(10,s,a),nil)
    local ac={legitimateHit=true,frontal=true,invincible=false,otherMitigation=false,consumed=false,elapsed=0,amount=100,mitigationCap=1}
    near(R.armorMitigation(s,ac).maxReduction,({5,8,11,14,17})[i])
    ac.frontal=false;eq(R.armorMitigation(s,ac),nil)
    ac.frontal=true;ac.otherMitigation=true;eq(R.armorMitigation(s,ac),nil)
    ac.otherMitigation=false;ac.consumed=true;eq(R.armorMitigation(s,ac),nil)
    ac.consumed=false;ac.elapsed=armor.duration;eq(R.armorMitigation(s,ac),nil)
    local zone={safeFloor=true,zoneActive=false,mitigationCap=0.04,radiusCap=99}
    local z=plan(11,s,zone);eq(z.radius,i+2);near(z.duration,1.5+0.5*i);near(z.maxMitigation,0.04);eq(z.collision,false)
    zone.zoneActive=true;eq(plan(11,s,zone),nil)
    local swap={targetKind="NEUTRAL",targetAlive=true,resistant=false,bothPositionsSafe=true,canMove=true,carryingEgg=false,moveCap=99,distance=({3,4,5,6,8})[i]}
    eq(plan(12,s,swap).maxDistance,swap.distance)
    swap.targetAlive=false;eq(plan(12,s,swap),nil);swap.targetAlive=true
    swap.targetKind="PLAYER";eq(plan(12,s,swap),nil)
    for n=3,12 do
        eq(R.planAfterHit(string.format("PREMIUM-%03d",n),s,{confirmedHit=false,consumed=false,active=true}),nil)
        eq(R.planAfterHit(string.format("PREMIUM-%03d",n),s,{confirmedHit=true,consumed=true,active=true}),nil)
    end
end
for _,s in ipairs({-1,5,0.5,math.huge,0/0,"4"}) do
    eq(R.reserveEcho(s,100),nil);eq(R.replaceAttribute(s,{"A"},"A"),nil);eq(plan(7,s,{}),nil)
end
for _,b in ipairs({-1,0.1,math.huge,0/0,"100",9007199254740992}) do eq(R.reserveEcho(4,b),nil) end
eq(R.replaceAttribute(4,{"A","A"},"A"),nil)
eq(R.replaceAttribute(4,{[1]="A",other="B"},"A"),nil)
eq(plan(8,4,{healAllowed=true,maxHP=100,hp=1,healedRoundFraction=-1,healCap=100}),nil)
eq(plan(13,4,{}),nil)
print("PREMIUM_003_012_RULES_PASS: 10 effects, 50 stage definitions, "..count.." echo budget cases plus negative cases")
