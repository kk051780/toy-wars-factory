--!strict
-- EGGRUMBLE V3 / GQ: per-mode temporary server FX lease, NOT combat authority.
-- Existing SkillFX remains the only emitter. This partitions its GLOBAL 72-part cap.
-- Solo match borrows up to 60/72, reserving 12 for the other mode.
-- When both modes have live FX, cap NEW acquisitions to 36 per mode;
-- pre-existing solo parts decay naturally, while the second mode has 12 guaranteed headroom.
local Quota={}
function Quota.new(totalCap:number,reserve:number)
 assert(type(totalCap)=="number" and totalCap%1==0 and totalCap>=12)
 assert(type(reserve)=="number" and reserve%1==0 and reserve>=6 and reserve<totalCap/2)
 local q={
  total=totalCap,reserve=reserve,half=math.floor(totalCap/2),
  usage={TEAM=0,BATTLE_ROYALE=0},
  tickets={},nextTicket=0,
 }
 function q:canStart(arena:string,count:number):boolean
  local mode=if arena=="TEAM_Arena" or arena=="TEAM" then "TEAM" elseif arena=="BATTLE_ROYALE_Arena" or arena=="BATTLE_ROYALE" then "BATTLE_ROYALE" else nil
  if not mode or type(count)~="number" or count~=count or count%1~=0 or count<1 or count>6 then return false end
  local other=if mode=="TEAM" then "BATTLE_ROYALE" else "TEAM"
  local occupied=self.usage.TEAM+self.usage.BATTLE_ROYALE
  local allowance=if self.usage[other]>0 then self.half else self.total-self.reserve
  return self.usage[mode]+count<=allowance and occupied+count<=self.total
 end
 function q:acquire(arena:string):number?
  if not self:canStart(arena,1) then return nil end
  local mode=if arena=="TEAM_Arena" or arena=="TEAM" then "TEAM" else "BATTLE_ROYALE"
  self.nextTicket+=1
  local id=self.nextTicket
  self.tickets[id]=mode
  self.usage[mode]+=1
  return id
 end
 function q:release(id:number):boolean
  if type(id)~="number" then return false end
  local mode=self.tickets[id]
  if not mode then return false end
  self.tickets[id]=nil
  self.usage[mode]-=1
  return true
 end
 function q:snapshot()
  return {team=self.usage.TEAM,br=self.usage.BATTLE_ROYALE,
   total=self.usage.TEAM+self.usage.BATTLE_ROYALE}
 end
 return q
end
return Quota
