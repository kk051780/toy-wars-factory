--!strict
local C=require("./EGGRUMBLE_LobbyShopCatalog")
assert(C.guardianCount()==14 and C.count()==24)
assert(#C.list("GUARDIAN")==14)
local roles={WARRIOR=0,MAGE=0,NINJA=0,TRAPPER=0,BUILDER=0,BEAST=0,ZOMBIE=0}
local seen={}
for _,entry in ipairs(C.list()) do
 assert(not seen[entry.id]);seen[entry.id]=true
 assert(type(entry.battlePoints)=="number" and entry.battlePoints>0)
 assert(entry.paidOnly==false and entry.robuxProductId==nil and entry.damageMultiplier==1)
 if entry.category=="GUARDIAN" then
  roles[entry.role]+=1
  assert(entry.personality and entry.weapon and entry.behavior and entry.cue)
  assert(entry.activeCastleCap==2 and entry.summonsPerMatchCap==3)
 end
end
for role,n in pairs(roles) do assert(n==2,role) end
assert(C.freeStarter()=="GUARD_SHIELD_KNIGHT")
local starter=C.get(C.freeStarter())
assert(starter and starter.battlePoints==200)
assert(C.canEquip(C.freeStarter(),"WARRIOR",1,{}))
assert(not C.canEquip("GUARD_WAR_BANNER","WARRIOR",1,{}))
assert(C.canEquip("GUARD_WAR_BANNER","WARRIOR",1,{GUARD_WAR_BANNER=true}))
assert(not C.canEquip("GUARD_WAR_BANNER","MAGE",1,{GUARD_WAR_BANNER=true}))
assert(C.tier(1).tier==1 and C.tier(10).tier==2 and C.tier(25).tier==3)
assert(C.tier(25).paidBonusHP==0 and C.tier(25).paidBonusDamage==0)
assert(C.MAX_GUARDIANS_ACTIVE==2 and C.MAX_GUARDIAN_SUMMONS_PER_MATCH==3)
assert(C.get("GUARD_SHIELD_KNIGHT").id=="GUARD_SHIELD_KNIGHT")
local item=C.get("GUARD_SHIELD_KNIGHT");item.battlePoints=999
assert(C.get("GUARD_SHIELD_KNIGHT").battlePoints==200)
print("GQ805_CATALOG_14_GUARDIANS_7_ROLES_FREE_PARITY_PASS")
