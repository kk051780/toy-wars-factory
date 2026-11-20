--!strict
local P=require("./EGGRUMBLE_PvPControlCuePolicy")
assert(P.ROLE_COUNT==7 and P.ELEMENT_COUNT==8)
local event={
 serverConfirmedHit=true,matchActive=true,epochCurrent=true,
 victimIsHuman=true,attackerIsHuman=true,sameTeam=false,
 spawnProtected=false,targetAlive=true,attackerAlive=true,
 uniqueHitId="round19/hit1",role="WARRIOR",element="FIRE",
 distanceStuds=25,visible=true,deviceTier="LOW",serverTimeSeconds=20,
 targetHardCCCount8s=0,targetHardCCSeconds8s=0,targetControlImmunityUntil=0,
}
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local elements={"FIRE","ICE","LIGHTNING","WATER","WIND","EARTH","DIVINE","CURSE"}
for _,role in ipairs(roles) do
 event.role=role
 for _,element in ipairs(elements) do
  event.element=element
  local c=P.select(event)
  assert(c and c.status and c.noGore and c.colorIndependent and c.particleBudget<=4)
  assert(c.role==role and c.element==element and c.applyDamageHere==false and c.existingDamageReceiptOnly)
  assert(c.durationSeconds<=2.5 and c.maxHorizontalImpulseStuds<=14)
 end
end
event.role="TRAPPER";event.element="WIND"
local normal=P.select(event)
assert(normal.status=="KNOCKBACK" and normal.fallRescueRequired and normal.hardControl)
event.targetHardCCCount8s=2
local capped=P.select(event)
assert(capped.status=="BRIEF_SLOW" and not capped.hardControl and capped.maxHorizontalImpulseStuds==0)
event.targetHardCCCount8s=0
event.targetHardCCSeconds8s=1.7
assert(P.select(event).status=="BRIEF_SLOW")
event.targetHardCCSeconds8s=0
event.targetControlImmunityUntil=100
assert(P.select(event).status=="BRIEF_SLOW")
event.targetControlImmunityUntil=0
event.element="ICE";assert(P.select(event).status=="FREEZE")
event.element="LIGHTNING";assert(P.select(event).durationSeconds<=0.55)
for _,k in ipairs({"serverConfirmedHit","matchActive","epochCurrent","victimIsHuman","attackerIsHuman","targetAlive","attackerAlive"}) do
 event[k]=false;assert(P.select(event)==nil,k);event[k]=true
end
event.sameTeam=true;assert(P.select(event)==nil);event.sameTeam=false
event.spawnProtected=true;assert(P.select(event)==nil);event.spawnProtected=false
event.uniqueHitId="";assert(P.select(event)==nil);event.uniqueHitId="round19/hit1"
event.role="HACK";assert(P.select(event)==nil);event.role="TRAPPER"
event.element="HACK";assert(P.select(event)==nil);event.element="WIND"
event.serverTimeSeconds=math.huge;assert(P.select(event)==nil);event.serverTimeSeconds=20
event.targetHardCCCount8s=-1;assert(P.select(event)==nil);event.targetHardCCCount8s=0
event.distanceStuds=101;assert(P.select(event)==nil);event.distanceStuds=25
event.distanceStuds=81;event.visible=false;assert(P.select(event)==nil)
print("GQ802_PVP_NATIVE_ROLE7_ELEMENT8_56_RECEIPTS_CC_ANTILOCK_PASS")
