--!strict
-- EGGRUMBLE private V3: shared TEAM/BR neutral-model capacity.
-- One pure, server-only ledger; no NPC spawn, HIT, KO, Game, Remote or DataStore authority.
-- This is an OPTIONAL PROPOSAL, not wired to the original Swarm or official RC.
local Budget = {}
local MODES = {TEAM=true, BATTLE_ROYALE=true}

local function integer(n:number):boolean
 return type(n)=="number" and n==n and n%1==0 and n>0 and n<100000
end
local function other(mode:string):string
 assert(MODES[mode]==true,"invalid mode")
 return if mode=="TEAM" then "BATTLE_ROYALE" else "TEAM"
end

function Budget.new(globalLimit:number, perModeLimit:number, oppositeReserve:number)
 assert(integer(globalLimit) and integer(perModeLimit) and integer(oppositeReserve),"invalid integer budget")
 assert(globalLimit>=perModeLimit+oppositeReserve and globalLimit>=2*oppositeReserve,"reserve cannot fit")
 local state={
  limits={global=globalLimit,perMode=perModeLimit,reserve=oppositeReserve},
  active={TEAM=false,BATTLE_ROYALE=false},
  generation={TEAM=0,BATTLE_ROYALE=0},
  live={TEAM=0,BATTLE_ROYALE=0,total=0},
  serial=0,
  tickets={},
 }
 function state:begin(mode:string):number
  other(mode)
  assert(not self.active[mode] and self.live[mode]==0,"mode already active")
  self.generation[mode]+=1
  self.active[mode]=true
  return self.generation[mode]
 end
 function state:acquire(mode:string,epoch:number):(string?,string)
  local opposite=other(mode)
  if not self.active[mode] then return nil,"INACTIVE" end
  if epoch~=self.generation[mode] then return nil,"STALE_EPOCH" end
  if self.live[mode]>=self.limits.perMode then return nil,"MODE_CAP" end
  if self.live.total>=self.limits.global then return nil,"GLOBAL_CAP" end
  if self.active[opposite] then
   local required=math.max(0,self.limits.reserve-self.live[opposite])
   if self.limits.global-(self.live.total+1)<required then
    return nil,"OPPOSITE_RESERVE"
   end
  end
  self.serial+=1
  local ticket=mode..":"..tostring(epoch)..":"..tostring(self.serial)
  self.tickets[ticket]={mode=mode,epoch=epoch}
  self.live[mode]+=1
  self.live.total+=1
  return ticket,"OK"
 end
 function state:release(ticket:string):boolean
  local owner=self.tickets[ticket]
  if not owner then return false end
  self.tickets[ticket]=nil
  if not self.active[owner.mode] or self.generation[owner.mode]~=owner.epoch then return false end
  assert(self.live[owner.mode]>0 and self.live.total>0,"ledger underflow")
  self.live[owner.mode]-=1
  self.live.total-=1
  return true
 end
 function state:retire(mode:string,epoch:number):boolean
  other(mode)
  if not self.active[mode] or self.generation[mode]~=epoch then return false end
  for token,owner in pairs(self.tickets) do
   if owner.mode==mode and owner.epoch==epoch then self.tickets[token]=nil end
  end
  self.live.total-=self.live[mode]
  self.live[mode]=0
  self.active[mode]=false
  self.generation[mode]+=1
  return true
 end
 function state:snapshot():any
  return {
   TEAM=self.live.TEAM,BATTLE_ROYALE=self.live.BATTLE_ROYALE,
   total=self.live.total,global=self.limits.global,
   activeTEAM=self.active.TEAM,activeBR=self.active.BATTLE_ROYALE,
  }
 end
 return state
end
return Budget
