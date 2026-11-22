-- Independent role-lifecycle diagnostic boundary. Original four fixtures remain unchanged.
-- Stationary Bot/Swarm jobs are explicitly parked. Their real start/takeover and
-- all Host/Guardian/Rules/Policy/Combat/regen bodies are still loaded unchanged.
-- No navmesh, physical movement, multiplayer or rendering evidence is claimed.
local diagnosticParked = {}
local diagnosticSpawn = task.spawn
task.spawn = function(fn, ...)
 local line = if type(fn) == 'function' then debug.info(fn, 'l') else -1
 local owner = sourceLabel(line)
 if owner == 'BotActors' or owner == 'SwarmCombat' then
  table.insert(diagnosticParked, {owner=owner,line=line,at=now,fn=fn,args=table.pack(...)})
  return coroutine.create(function() end)
 end
 return diagnosticSpawn(fn, ...)
end
local diagnosticGetService = game.GetService
game.GetService = function(self, name)
 if name == 'PathfindingService' then
  return {CreatePath=function() error('UNEXPECTED_NAVMESH_REQUEST_IN_ROLE_DIAGNOSTIC') end}
 end
 return diagnosticGetService(self, name)
end
local guardianBirths = {}
local diagnosticSetAttribute = methods.SetAttribute
function methods:SetAttribute(name, value)
 diagnosticSetAttribute(self, name, value)
 if name == 'EGGRUMBLE_GuardianRole' then
  local hum=self:FindFirstChildOfClass('Humanoid')
  local gear={}
  for _,child in ipairs(self:GetChildren()) do
   if string.sub(child.Name,1,10)=='Signature_' then table.insert(gear,child.Name) end
  end
  table.insert(guardianBirths, {model=self,owner=self:GetAttribute('EGGRUMBLE_GuardianOwner'),role=value,
   actorType=self.Name,isModel=self:IsA('Model'),maxHealth=hum and hum.MaxHealth,
   initialHealth=hum and hum.Health,gear=table.concat(gear,','),at=now})
 end
end

