--!strict
-- GQ800: original neutral model conversion eligibility and orders, PURE Luau.
-- Result is a permit for the existing Swarm/SevenRoleCombat singleton, NOT an actor or damage writer.
local M={}
local MAX_CHARMED=3
local MAX_COMBINED=4  -- Existing #582 three summoned + new charmed must share this budget.
local TTL=14
local STACK_WINDOW=5
local THRESHOLD=0.35
local RANGE=32
local VALID_ORDER={FOLLOW=true,GUARD=true,FOCUS=true}
local REQUIRED={BANNER_KNIGHT=2,TINY_SHIELD=2,SPIKE_BOAR=2,ACORN_IMP=2,
 SHY_WRAITH=2,ICE_SLIME=2,SPARK_GOBLIN=2,BABY_GOLEM=4}
local DUTY={BANNER_KNIGHT="DEFENDER",TINY_SHIELD="SHIELD",SPIKE_BOAR="CHARGER",
 ACORN_IMP="SCOUT",SHY_WRAITH="AMBUSH",ICE_SLIME="SLOW",
 SPARK_GOBLIN="SPARK",BABY_GOLEM="TANK"}
function M.new(epoch:string,ownerId:string):any
 assert(type(epoch)=="string" and #epoch>0)
 assert(type(ownerId)=="string" and #ownerId>0)
 return {epoch=epoch,ownerId=ownerId,active=true,stacks={},members={},order="FOLLOW",focusId=nil}
end
local function count(t:any):number
 local n=0 for _ in pairs(t) do n+=1 end return n
end
function M.retire(s:any):{any}
 local actions={}
 for id in pairs(s.members) do table.insert(actions,{kind="RELEASE",targetId=id}) end
 s.members={};s.stacks={};s.active=false;s.focusId=nil
 return actions
end
function M.order(s:any,kind:string,focusId:string?):boolean
 if not s.active or not VALID_ORDER[kind] then return false end
 if kind=="FOCUS" and (type(focusId)~="string" or focusId=="") then return false end
 s.order=kind
 s.focusId=if kind=="FOCUS" then focusId else nil
 return true
end
function M.seal(s:any,now:number,e:any):any
 -- ALL fields must be produced by server-owned attack+neutral model verification.
 if not s.active or type(e)~="table" or e.serverConfirmedHit~=true or e.role~="ZOMBIE" then return nil end
 if e.epoch~=s.epoch or e.ownerId~=s.ownerId or e.phase~="ACTIVE"
  or e.ownerAlive~=true or e.avatarCurrent~=true then return nil end
 if e.targetKind~="NEUTRAL" or e.targetAlive~=true or e.targetFriendly==true
  or e.isBoss==true or e.isPlayer==true or e.sameTeam==true then return nil end
 if e.inLineOfSight~=true or type(e.distance)~="number" or e.distance>RANGE or e.distance<0 then return nil end
 local id=e.targetId
 if type(id)~="string" or id=="" or type(e.species)~="string" then return nil end
 if not REQUIRED[e.species] or s.members[id] then return nil end
 if type(e.hpFraction)~="number" or e.hpFraction<0 or e.hpFraction>1 then return nil end
 local prev=s.stacks[id]
 local stacks=if prev and now-prev.at<=STACK_WINDOW then prev.n+1 else 1
 stacks=math.min(stacks,REQUIRED[e.species])
 s.stacks[id]={n=stacks,at=now}
 local needed=REQUIRED[e.species]
 if stacks<needed or e.hpFraction>THRESHOLD then
  return {kind="SEAL",targetId=id,stacks=stacks,required=needed,visibleSigil=true}
 end
 local summoned=math.max(0,math.floor(tonumber(e.existingSummoned) or 0))
 if count(s.members)>=MAX_CHARMED or count(s.members)+summoned>=MAX_COMBINED then
  return {kind="SEALED_BUT_FULL",targetId=id,stacks=stacks,required=needed}
 end
 s.stacks[id]=nil
 s.members[id]={species=e.species,expires=now+TTL,ownerId=s.ownerId,epoch=s.epoch}
 return {kind="CHARM",targetId=id,ownerId=s.ownerId,epoch=s.epoch,
  expires=now+TTL,duty=DUTY[e.species],order=s.order,serverApplyRequired=true}
end
function M.step(s:any,now:number,snapshot:any):{any}
 if not s.active then return {} end
 if type(snapshot)~="table" or snapshot.epoch~=s.epoch or snapshot.ownerId~=s.ownerId
  or snapshot.phase~="ACTIVE" or snapshot.ownerAlive~=true
  or snapshot.avatarCurrent~=true then return M.retire(s) end
 local actions={}
 for id,member in pairs(s.members) do
  local live=snapshot.neutrals and snapshot.neutrals[id]
  if now>=member.expires or not live or live.alive~=true or live.friendlyOwnerId~=s.ownerId
    or live.epoch~=s.epoch then
   s.members[id]=nil
   table.insert(actions,{kind="RELEASE",targetId=id})
  else
   -- Existing Swarm+ZOMBIE orders enforce pathing/LOS and authorize hits.
   table.insert(actions,{kind="ORDER",targetId=id,duty=DUTY[member.species],
    order=s.order,focusId=s.focusId,ownerId=s.ownerId})
  end
 end
 return actions
end
function M.isCharmed(s:any,id:string):boolean
 return s.active and s.members[id]~=nil
end
M.MAX_CHARMED=MAX_CHARMED
M.MAX_COMBINED=MAX_COMBINED
M.TTL_SECONDS=TTL
M.STACK_WINDOW_SECONDS=STACK_WINDOW
M.HP_THRESHOLD=THRESHOLD
return M
