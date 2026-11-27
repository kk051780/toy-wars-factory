local R=require("./TimePremiumRules")
local function near(a,b) assert(math.abs(a-b)<1e-9,tostring(a).." != "..tostring(b)) end
local function eq(a,b) assert(a==b,tostring(a).." != "..tostring(b)) end
for s=0,4 do
    local a=R.planAdvance(s,20,180,0,0)
    eq(a.kind,"GROWTH_CREDIT_REQUEST");eq(a.seconds,({6,10,15,20,30})[s+1])
    local w=R.planRewind(s,100,180,0,0,nil,false)
    eq(w.seconds,({5,10,15,20,30})[s+1]);eq(w.duration,s+2);eq(w.minTelegraph,0.8)
    assert(table.isfrozen(a) and table.isfrozen(w))
    for _,g0 in ipairs({0,0.3,0.8}) do
        for t=0,200 do
            local g=R.naturalGrowth(t,180,g0,0)
            local e=R.effectiveGrowth(s,t,180,g0,0,nil,s+2)
            assert(e<=g and e>=g0 and g-e<=0.25+1e-9)
            assert(math.floor(g*4)-math.floor(e*4)<=1)
            near(R.effectiveGrowth(s,t,180,g0,0,nil,0),g)
        end
    end
end
eq(R.planAdvance(4,100,180,0,29).seconds,1)
eq(R.planAdvance(4,178,180,0,0).seconds,2)
eq(R.planAdvance(4,120,180,0,30),nil)
local speed=R.planAdvance(4,180,180,0,0);eq(speed.kind,"GROUND_SPEED_REQUEST");eq(speed.duration,4);near(speed.maxFraction,0.08)
eq(R.planAdvance(3,180,180,0,0),nil)
near(R.naturalGrowth(150,180,0,20),170/180)
eq(R.planRewind(4,180,180,0,0,nil,false),nil)
eq(R.planRewind(4,189,180,0,0,180,false),nil)
eq(R.planRewind(4,190,180,0,0,180,true),nil)
assert(R.planRewind(4,190,180,0,0,180,false))
near(R.effectiveGrowth(4,190,180,0,0,180,6),5/6)
eq(R.effectiveGrowth(4,180,180,0,0,nil,6),1)
eq(R.effectiveGrowth(4,185,180,0,0,180,6),1)
eq(R.effectiveGrowth(4,190,180,0,0,180,0),1)
eq(R.planRewind(4,0,180,0.5,0,nil,false),nil)
for _,s in ipairs({-1,5,0.5,math.huge,0/0,"4"}) do
    eq(R.planAdvance(s,0,180,0,0),nil)
    eq(R.planRewind(s,100,180,0,0,nil,false),nil)
end
eq(R.naturalGrowth(0,0,0,0),nil)
eq(R.naturalGrowth(0,180,0,-1),nil)
eq(R.naturalGrowth(0,180,0,31),nil)
eq(R.planRewind(4,100,180,0,0,101,false),nil)
eq(R.planRewind(4,100,180,0,0,nil,nil),nil)
eq(R.effectiveGrowth(4,100,180,0,0,nil,7),nil)
print("TIME_PREMIUM_RULES_PASS: 2 effects, all 5 stages, 3015 growth cases")
