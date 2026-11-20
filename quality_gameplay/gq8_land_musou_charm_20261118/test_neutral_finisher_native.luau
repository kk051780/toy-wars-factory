--!strict
local P=require("./EGGRUMBLE_NeutralFinisherPolicy")
assert(P.ROLE_COUNT==7 and P.SPECIES_COUNT==8)
local ids=P.listSpecies()
assert(#ids==8 and ids[1]=="ACORN_IMP")
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local event={serverConfirmed=true,uniqueHitId="epoch-17-1",targetIsNeutral=true,isFriendly=false,
 matchActive=true,epochCurrent=true,role="WARRIOR",species="TINY_SHIELD",
 ko=false,element="FIRE",distanceStuds=10,visible=true,deviceTier="NORMAL",combo=12,ordinal=1}
for _,role in ipairs(roles) do
 event.role=role
 local hit=P.select(event)
 assert(hit and hit.kind=="HIT" and hit.cosmeticOnly and hit.comboAccent)
 event.ko=true
 local ko=P.select(event)
 assert(ko and ko.kind=="KO" and ko.noGore)
 event.ko=false
end
assert(P.species("SHY_WRAITH").friendRole=="AMBUSH")
event.role="ZOMBIE"; event.ko=true;event.deviceTier="LOW"
assert(P.select(event).particles<=4)
event.serverConfirmed=false;assert(P.select(event)==nil)
event.serverConfirmed=true;event.targetIsNeutral=false;assert(P.select(event)==nil)
event.targetIsNeutral=true;event.isFriendly=true;assert(P.select(event)==nil)
event.isFriendly=false;event.epochCurrent=false;assert(P.select(event)==nil)
event.epochCurrent=true;event.distanceStuds=101;assert(P.select(event)==nil)
event.distanceStuds=5;event.uniqueHitId="";assert(P.select(event)==nil)
print("GQ800_FINISHER_NATIVE_ROLE7_SPECIES8_RECEIPT_GATES_PASS")
