--!strict
local P=require("./EGGRUMBLE_CurseConversionPolicy")
local function hit(species:string,id:string,hp:number):any
 return {serverConfirmedHit=true,role="ZOMBIE",epoch="TEAM:7",ownerId="17",phase="ACTIVE",
  ownerAlive=true,avatarCurrent=true,targetKind="NEUTRAL",targetAlive=true,
  targetFriendly=false,isBoss=false,isPlayer=false,sameTeam=false,
  inLineOfSight=true,distance=8,targetId=id,species=species,hpFraction=hp,existingSummoned=0}
end
local s=P.new("TEAM:7","17")
local a=hit("TINY_SHIELD","instance-1",.25)
assert(P.seal(s,0,a).kind=="SEAL")
local charm=P.seal(s,1,a)
assert(charm.kind=="CHARM" and charm.duty=="SHIELD" and P.isCharmed(s,"instance-1"))
assert(P.seal(s,2,a)==nil)
assert(P.order(s,"GUARD",nil))
local snap={epoch="TEAM:7",ownerId="17",phase="ACTIVE",ownerAlive=true,avatarCurrent=true,
 neutrals={["instance-1"]={alive=true,friendlyOwnerId="17",epoch="TEAM:7"}}}
assert(P.step(s,3,snap)[1].kind=="ORDER")
assert(P.step(s,16,snap)[1].kind=="RELEASE" and not P.isCharmed(s,"instance-1"))
local b=hit("BABY_GOLEM","instance-2",.35)
for i=1,3 do assert(P.seal(s,20+i,b).kind=="SEAL") end
assert(P.seal(s,24,b).kind=="CHARM")
assert(not P.order(s,"FOCUS",""))
assert(P.order(s,"FOCUS","neutral-88"))
local stale={epoch="TEAM:8",ownerId="17",phase="ACTIVE",ownerAlive=true,avatarCurrent=true}
assert(P.step(s,25,stale)[1].kind=="RELEASE")
assert(not s.active)
local rejected={
 {"role","MAGE"},{"epoch","BR:7"},{"ownerId","someone"},{"targetKind","PLAYER"},
 {"targetFriendly",true},{"isBoss",true},{"isPlayer",true},{"inLineOfSight",false},
 {"avatarCurrent",false},{"ownerAlive",false},{"serverConfirmedHit",false},
 {"distance",33},{"hpFraction",1.2}
}
for _,pair in ipairs(rejected) do
 local fresh=P.new("TEAM:7","17")
 local x=hit("ICE_SLIME","instance-x",.25);x[pair[1]]=pair[2]
 assert(P.seal(fresh,1,x)==nil,pair[1])
end
local full=P.new("TEAM:7","17")
for i=1,3 do
 local e=hit("ACORN_IMP","n"..i,.20)
 assert(P.seal(full,2*i,e).kind=="SEAL")
 assert(P.seal(full,2*i+1,e).kind=="CHARM")
end
local extra=hit("ACORN_IMP","n4",.20)
assert(P.seal(full,8,extra).kind=="SEAL")
assert(P.seal(full,9,extra).kind=="SEALED_BUT_FULL")
local s4=P.new("TEAM:7","17")
local h=hit("SPARK_GOBLIN","alone",.2);h.existingSummoned=4
assert(P.seal(s4,1,h).kind=="SEAL")
assert(P.seal(s4,2,h).kind=="SEALED_BUT_FULL")
local exp=P.new("TEAM:7","17")
assert(P.seal(exp,1,hit("TINY_SHIELD","e",.2)).kind=="SEAL")
assert(P.seal(exp,7,hit("TINY_SHIELD","e",.2)).kind=="SEAL")
print("GQ800_CURSE_NATIVE_FRIENDLY_NEUTRAL_SESSION_LIMIT_TTL_PASS")
