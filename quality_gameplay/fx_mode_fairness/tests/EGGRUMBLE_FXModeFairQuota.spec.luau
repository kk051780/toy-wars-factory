local Q=require("../EGGRUMBLE_FXModeFairQuota")
local q=Q.new(72,12)
assert(q:canStart("TEAM_Arena",6))
assert(not q:canStart("bogus",1))
assert(not q:canStart("TEAM",0))
assert(not q:canStart("TEAM",7))
assert(not q:canStart("TEAM",0/0))
assert(q:acquire("INVALID")==nil)
local a={}
for i=1,60 do
 local id=q:acquire("TEAM_Arena")
 assert(type(id)=="number","solo part "..i)
 a[#a+1]=id
end
assert(q:acquire("TEAM")==nil and not q:canStart("TEAM",6),"cannot monopolize all 72")
assert(q:canStart("BATTLE_ROYALE_Arena",6),"reserved other-mode headroom")
local b={}
for i=1,12 do
 b[#b+1]=assert(q:acquire("BATTLE_ROYALE_Arena"))
end
assert(q:snapshot().total==72)
assert(q:acquire("BATTLE_ROYALE")==nil and q:acquire("TEAM")==nil)
assert(q:release(a[1]))
assert(not q:release(a[1]),"double release must not inflate budget")
assert(q:snapshot().team==59)
assert(q:acquire("TEAM")==nil,"two busy modes halve fresh per-mode quota")
for i=2,31 do assert(q:release(a[i])) end -- team drops to 29
assert(q:snapshot().team==29)
local brCount=q:snapshot().br
for i=brCount+1,36 do b[#b+1]=assert(q:acquire("BATTLE_ROYALE_Arena")) end
assert(q:snapshot().br==36 and q:snapshot().total==65)
assert(q:acquire("BATTLE_ROYALE")==nil,"busy-mode soft cap")
local teamNew={}
for i=30,36 do teamNew[#teamNew+1]=assert(q:acquire("TEAM_Arena")) end
assert(q:snapshot().total==72 and q:snapshot().team==36)
assert(q:acquire("TEAM")==nil and q:acquire("BATTLE_ROYALE")==nil)
for _,id in ipairs(b) do assert(q:release(id)) end
assert(q:snapshot().br==0 and q:snapshot().team==36)
for i=1,24 do teamNew[#teamNew+1]=assert(q:acquire("TEAM_Arena")) end
assert(q:snapshot().team==60)
for i=32,60 do assert(q:release(a[i])) end
for _,id in ipairs(teamNew) do assert(q:release(id)) end
assert(q:snapshot().total==0)
assert(not q:release(-1) and not q:release(10^9))
print("EGGRUMBLE_FX_MODE_FAIRNESS_NATIVE_PASS")
