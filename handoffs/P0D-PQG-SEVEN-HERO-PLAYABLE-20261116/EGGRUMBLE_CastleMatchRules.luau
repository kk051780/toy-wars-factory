--!strict
-- EGGRUMBLE match rules V3, pure Luau source: NO Roblox DataStore, Publish, Remote or writes.
-- This is an isolated candidate module, not part of the active authoritative Game.
-- Integrate via #220 only after source-lock, native and Studio acceptance.
local M={}
M.MODE_TEAM="TEAM"
M.MODE_ROYALE="BATTLE_ROYALE"
M.CASTLE_HP=1000
M.EGGS_PER_CASTLE=3
M.DEFAULT_FIELD_EGGS=24
M.MAX_HERO_SLOTS=16
M.MAX_DEFENSE_SLOTS=3
M.DEFENSE_POINTS=10
M.MODULE_COST={HARDENED=5,REPAIR=5,TURRET=4,TRAP=3,SENSOR=2}
M.COSMETIC_COLORS={STONE=true,GOLD=true,CYAN=true,AMETHYST=true,FOREST=true}
M.MAX_HOUSE_PIECES=48

local function assertId(v:any)
 assert((type(v)=="string" or type(v)=="number") and tostring(v)~="","valid owner ID required")
end
local function castleOf(m:any,id:any):any
 local c=m.castles[tostring(id)]
 assert(c~=nil,"castle does not exist")
 return c
end
local function assertActive(m:any)
 assert(m.phase=="ACTIVE" and m.winner==nil,"match is not active")
end
function M.makeRoster(mode:string,humanIds:{any},maxSlots:number?):{any}
 assert(mode==M.MODE_TEAM or mode==M.MODE_ROYALE,"invalid game mode")
 local limit=maxSlots or M.MAX_HERO_SLOTS
 assert(type(limit)=="number" and limit%1==0 and limit>=2 and limit<=32,"invalid preview slot cap")
 assert(type(humanIds)=="table" and #humanIds>0 and #humanIds<=limit,"invalid human roster")
 local out={}
 local dedup={}
 for i,id in ipairs(humanIds) do
  assertId(id);local key=tostring(id)
  assert(not dedup[key],"duplicate player");dedup[key]=true
  table.insert(out,{id=key,isAI=false,team=if mode==M.MODE_TEAM then (if i%2==1 then "RED" else "BLUE") else nil})
 end
 local bot=1
 while #out<limit do
  local id="AI_"..tostring(bot);bot+=1
  if not dedup[id] then
   table.insert(out,{id=id,isAI=true,team=if mode==M.MODE_TEAM then (if #out%2==0 then "RED" else "BLUE") else nil})
  end
 end
 return out
end
function M.new(mode:string,roster:{any},initialFieldEggs:number?):any
 assert(mode==M.MODE_TEAM or mode==M.MODE_ROYALE,"invalid game mode")
 assert(#roster>=2 and #roster<=32,"invalid roster size")
 local m={
  mode=mode,phase="LOBBY",winner=nil,castles={},ids={},events={},
  fieldEggs=initialFieldEggs or M.DEFAULT_FIELD_EGGS, initialFieldEggs=initialFieldEggs or M.DEFAULT_FIELD_EGGS,
  fieldEggTokens={}, eggSerial=0,
  teamDeposits={RED=0,BLUE=0},teamSiegeTokens={RED=0,BLUE=0},
 }
 assert(type(m.fieldEggs)=="number" and m.fieldEggs>=0 and m.fieldEggs%1==0,"invalid egg count")
 -- A world egg is not just a global number: each collectible receives a single-use server ID.
 for i=1,m.fieldEggs do m.fieldEggTokens["FIELD_"..i]=true end
 local used={}
 local teams={RED=0,BLUE=0}
 for _,entry in ipairs(roster) do
  assertId(entry.id)
  local id=tostring(entry.id)
  assert(not used[id],"duplicate castle owner");used[id]=true
  local team=entry.team
  if mode==M.MODE_TEAM then
   assert(team=="RED" or team=="BLUE","invalid team")
   teams[team]+=1
  else
   assert(team==nil,"royale must not have teams")
  end
  m.castles[id]={
   id=id,team=team,isAI=entry.isAI==true,hp=M.CASTLE_HP,shield=0,
   repairCharge=0,defensePoints=0,modules={},alive=true,
   vaultEggs=M.EGGS_PER_CASTLE,heldEggs=0,depositedEggs=0,
   decoration="STONE",homePieces={},castleClass="STANDARD",
  }
  table.insert(m.ids,id)
 end
 if mode==M.MODE_TEAM then assert(teams.RED>0 and teams.BLUE>0,"both teams required") end
 return m
end
function M.loadDefense(m:any,id:any,modules:{string})
 assert(m.phase=="LOBBY","cannot alter defenses after match begins")
 local c=castleOf(m,id)
 assert(type(modules)=="table" and #modules<=M.MAX_DEFENSE_SLOTS,"too many module slots")
 local spent=0;local used={};local nextModules={}
 for _,name in ipairs(modules) do
  local cost=M.MODULE_COST[name]
  assert(cost~=nil and not used[name],"invalid or repeated defense module")
  used[name]=true;spent+=cost;table.insert(nextModules,name)
 end
 assert(spent<=M.DEFENSE_POINTS,"defense budget exceeded")
 -- Always same core HP, plot size, gate health, siege hitbox and max defense allowance.
 -- HARDENED and REPAIR are mutually exclusive to cap effective castle endurance at +5%.
 assert(not (used.HARDENED and used.REPAIR),"durability stacking forbidden")
 c.modules=nextModules;c.defensePoints=spent
 c.shield=if used.HARDENED then 50 else 0
 c.repairCharge=if used.REPAIR then 50 else 0
 return spent
end
function M.decorate(m:any,ownerId:any,actorId:any,color:string)
 local c=castleOf(m,ownerId)
 assert(c.id==tostring(actorId),"only castle owner may decorate")
 assert(M.COSMETIC_COLORS[color],"invalid cosmetic color")
 c.decoration=color
 return color
end
function M.placeHouseDecoration(m:any,ownerId:any,actorId:any,piece:any)
 local c=castleOf(m,ownerId)
 assert(c.id==tostring(actorId),"cannot edit another player's home")
 assert(m.phase~="ACTIVE","no layout editing mid-match")
 assert(#c.homePieces<M.MAX_HOUSE_PIECES,"house part cap reached")
 assert(type(piece)=="table" and type(piece.x)=="number" and type(piece.y)=="number" and type(piece.z)=="number","invalid piece")
 assert(math.abs(piece.x)<=24 and math.abs(piece.z)<=24 and piece.y>=0 and piece.y<=25,"outside decorative plot")
 assert(type(piece.kind)=="string" and ({ROOF=true,FLAG=true,GARDEN=true,WINDOW=true,STATUE=true})[piece.kind],"invalid piece type")
 table.insert(c.homePieces,{kind=piece.kind,x=piece.x,y=piece.y,z=piece.z,collidable=false,combatBonus=0})
 return #c.homePieces
end
function M.start(m:any)
 assert(m.phase=="LOBBY","already started")
 m.phase="ACTIVE"
 table.insert(m.events,{type="START",mode=m.mode})
end
local function concludeIfLast(m:any)
 local survivors={}
 for _,c in pairs(m.castles) do
  if c.alive then
   local key=if m.mode==M.MODE_TEAM then c.team else c.id
   survivors[key]=true
  end
 end
 local count=0;local last=nil
 for key,_ in pairs(survivors) do count+=1;last=key end
 if count<=1 then
  m.winner=last
  m.phase="FINISHED"
  table.insert(m.events,{type="WIN",winner=last})
 end
end
function M.damageCastle(m:any,targetId:any,attackerId:any,amount:number):any
 assertActive(m)
 local c=castleOf(m,targetId)
 local attacker=castleOf(m,attackerId)
 assert(c.alive and attacker.alive,"eliminated hero cannot attack")
 assert(c.id~=attacker.id,"cannot attack your own castle")
 assert(m.mode~=M.MODE_TEAM or c.team~=attacker.team,"friendly fire blocked")
 assert(type(amount)=="number" and amount==amount and amount>=1 and amount<=250,"invalid siege damage")
 -- Siege tokens are earned from real stolen eggs, not purchased. One token: +10% one attack.
 local multiplier=1
 if m.mode==M.MODE_TEAM then
  local tokens=m.teamSiegeTokens[attacker.team]
  if tokens>0 then m.teamSiegeTokens[attacker.team]=tokens-1;multiplier=1.1 end
 end
 local raw=math.floor(amount*multiplier)
 local blocked=math.min(c.shield,raw);c.shield-=blocked
 local lost=math.min(c.hp,raw-blocked);c.hp-=lost
 if c.hp<=500 and c.repairCharge>0 then
  c.hp=math.min(M.CASTLE_HP,c.hp+c.repairCharge);c.repairCharge=0
 end
 local released=0
 if c.hp<=0 then
  c.hp=0;c.alive=false
  released=c.vaultEggs+c.heldEggs
  m.fieldEggs+=released
  local releasedEggIds={}
  for i=1,released do
   m.eggSerial+=1
   local key="RELEASE_"..tostring(m.eggSerial)
   m.fieldEggTokens[key]=true
   table.insert(releasedEggIds,key)
  end
  c.vaultEggs=0;c.heldEggs=0
  m.lastReleasedEggIds=releasedEggIds
  table.insert(m.events,{type="CASTLE_FALL",owner=c.id,attacker=attacker.id,releasedEggs=released})
  concludeIfLast(m)
 end
 return {hp=c.hp,shield=c.shield,damage=lost,fallen=not c.alive,releasedEggs=released,
  releasedEggIds=if released>0 then m.lastReleasedEggIds else {},winner=m.winner}
end
function M.takeEggs(m:any,thiefId:any,quantity:number,fromCastleId:any?):any
 assertActive(m)
 local thief=castleOf(m,thiefId);assert(thief.alive,"eliminated hero cannot collect eggs")
 assert(type(quantity)=="number" and quantity%1==0 and quantity>=1 and quantity<=3,"invalid egg pickup")
 assert(thief.heldEggs+quantity<=3,"carrying capacity exceeded")
 if fromCastleId~=nil then
  local target=castleOf(m,fromCastleId)
  assert(target.alive and target.id~=thief.id,"invalid target")
  assert(m.mode~=M.MODE_TEAM or target.team~=thief.team,"cannot steal team eggs")
  assert(target.vaultEggs>=quantity,"not enough enemy eggs")
  target.vaultEggs-=quantity
 else
  error("field egg pickup must reference a unique server-issued egg ID; use M.takeFieldEgg")
 end
 thief.heldEggs+=quantity
 table.insert(m.events,{type="EGG_TAKEN",thief=thief.id,source=fromCastleId or "FIELD",quantity=quantity})
 return thief.heldEggs
end
function M.takeFieldEgg(m:any,actorId:any,eggId:string):number
 assertActive(m)
 local actor=castleOf(m,actorId)
 assert(actor.alive,"eliminated owner cannot pick up an egg")
 assert(type(eggId)=="string" and m.fieldEggTokens[eggId]==true,"egg is missing or already collected")
 assert(actor.heldEggs<3,"egg carrying limit exceeded")
 -- No yields here: spending the token and transferring a single egg is atomic.
 m.fieldEggTokens[eggId]=nil
 m.fieldEggs-=1
 actor.heldEggs+=1
 table.insert(m.events,{type="FIELD_EGG_TAKEN",owner=actor.id,eggId=eggId})
 return actor.heldEggs
end
function M.auditEggConservation(m:any):any
 local tokens=0
 for _,available in pairs(m.fieldEggTokens) do
  if available then tokens+=1 end
 end
 local inCastles=0;local carried=0
 for _,castle in pairs(m.castles) do
  inCastles+=castle.vaultEggs
  carried+=castle.heldEggs
 end
 local initial=M.EGGS_PER_CASTLE*#m.ids
  +(m.initialFieldEggs or M.DEFAULT_FIELD_EGGS)
 return {valid=tokens==m.fieldEggs and tokens+inCastles+carried==initial,
  tokens=tokens,fieldEggs=m.fieldEggs,inCastles=inCastles,carried=carried,total=initial}
end
function M.depositEggs(m:any,actorId:any,quantity:number):number
 assertActive(m)
 local c=castleOf(m,actorId)
 assert(c.alive and type(quantity)=="number" and quantity%1==0 and quantity>0 and quantity<=c.heldEggs,"invalid deposit")
 -- Deposited eggs are physically stored in this castle, not destroyed.
 -- Preserve the egg stock so an enemy can steal it back or release it on castle fall.
 c.heldEggs-=quantity;c.vaultEggs+=quantity;c.depositedEggs+=quantity
 if m.mode==M.MODE_TEAM then
  m.teamDeposits[c.team]+=quantity
  -- One optional siege token earned per delivered egg, capped so egg advantage stays bounded.
  m.teamSiegeTokens[c.team]=math.min(2,m.teamSiegeTokens[c.team]+quantity)
 end
 table.insert(m.events,{type="EGG_DEPOSIT",owner=c.id,quantity=quantity})
 return c.depositedEggs
end
function M.onCarrierEliminated(m:any,id:any)
 local c=castleOf(m,id)
 local dropped=c.heldEggs;c.heldEggs=0;m.fieldEggs+=dropped
 local ids={}
 for _=1,dropped do
  m.eggSerial+=1
  local eggId="CARRIER_DROP_"..tostring(m.eggSerial)
  m.fieldEggTokens[eggId]=true
  table.insert(ids,eggId)
 end
 if dropped>0 then table.insert(m.events,{type="EGG_DROP",owner=c.id,quantity=dropped}) end
 return dropped,ids
end
function M.summary(m:any):any
 local alive=0;local eggsInCastles=0
 for _,c in pairs(m.castles) do
  if c.alive then alive+=1;eggsInCastles+=c.vaultEggs end
 end
 return {mode=m.mode,phase=m.phase,winner=m.winner,aliveCastles=alive,
  fieldEggs=m.fieldEggs,eggsInCastles=eggsInCastles,teamDeposits=m.teamDeposits}
end
return M
