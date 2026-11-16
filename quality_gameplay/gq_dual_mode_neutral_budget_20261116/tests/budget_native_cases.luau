--!nonstrict
-- Append after the pure Budget module (without its terminal return Budget).
local b=Budget.new(128,96,32)
local eTeam=b:begin("TEAM")
local teamTokens={}
for i=1,96 do
 local token,why=b:acquire("TEAM",eTeam)
 assert(token and why=="OK","first TEAM acquisitions must succeed")
 teamTokens[i]=token
end
local rejected,why=b:acquire("TEAM",eTeam)
assert(not rejected and why=="MODE_CAP","TEAM must be capped even if BR inactive")
local eBR=b:begin("BATTLE_ROYALE")
local brTokens={}
for i=1,32 do
 local token,msg=b:acquire("BATTLE_ROYALE",eBR)
 assert(token and msg=="OK","second mode must get reserved headroom")
 brTokens[i]=token
end
local full,msg=b:acquire("BATTLE_ROYALE",eBR)
assert(not full and msg=="GLOBAL_CAP","both mode sum may not exceed global cap")
local s=b:snapshot()
assert(s.TEAM==96 and s.BATTLE_ROYALE==32 and s.total==128,"physical model cap")
assert(b:release(teamTokens[1])==true,"one real death releases exactly one permit")
assert(b:release(teamTokens[1])==false,"duplicate death must not double release")
local added,ok=b:acquire("BATTLE_ROYALE",eBR)
assert(added and ok=="OK","opposite mode can use actually freed capacity")
assert(b:retire("TEAM",eTeam),"first match retires its own live tickets")
assert(not b:release(teamTokens[2]),"stale death callback after teardown must be ignored")
assert(not b:retire("TEAM",eTeam),"stale teardown cannot affect new matches")
local eTeam2=b:begin("TEAM")
assert(eTeam2~=eTeam,"new match has a distinct generation")
local wrong,msg2=b:acquire("TEAM",eTeam)
assert(not wrong and msg2=="STALE_EPOCH","old callbacks cannot spawn in fresh match")
for i=34,96 do
 local tok,msg3=b:acquire("BATTLE_ROYALE",eBR)
 assert(tok and msg3=="OK","BR reaches its per-mode cap after TEAM retires")
end
local bAgain,msg4=b:acquire("BATTLE_ROYALE",eBR)
assert(not bAgain and msg4=="MODE_CAP")
local fresh={}
for i=1,32 do
 local tok,msg5=b:acquire("TEAM",eTeam2)
 assert(tok and msg5=="OK","new TEAM gets protected 32 seats")
 fresh[i]=tok
end
local noExtra=b:acquire("TEAM",eTeam2)
assert(not noExtra,"global cap remains enforced in both directions")
assert(b:retire("BATTLE_ROYALE",eBR),"BR retirement")
assert(not b:release(brTokens[1]),"BR delayed callback does not steal TEAM permit")
assert(b:snapshot().TEAM==32 and b:snapshot().BATTLE_ROYALE==0)
assert(b:retire("TEAM",eTeam2))
assert(b:snapshot().total==0)
local invalid=pcall(function() Budget.new(40,35,12) end)
assert(not invalid,"impossible shared reserve must fail closed")
invalid=pcall(function() b:begin("INVALID") end)
assert(not invalid,"unknown mode must be rejected")
print("GQ_DUAL_MODE_NEUTRAL_BUDGET_NATIVE_PASS")
