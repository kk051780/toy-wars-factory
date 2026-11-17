--!strict
-- GQ8_BATTLE_HP_REGEN_20261118
-- Called ONLY by the existing single V3 Host after its existing SevenRoleCombat.equip().
-- This is NOT a second skill/healing/game/score/Remote owner.
-- Last-hit inference is from SERVER Humanoid.HealthChanged; clients never submit damage.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local Regen={}
-- Immutable upstream #773 policy, verified source blob 23ccf84f88b2cb2901af33a563ff535e82d7a78f.
-- No duplicate numeric policy is maintained in this runtime bridge.
local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_PassiveRegenPolicy"))
local STEP_SECONDS=.25
type Entry={
 humanoid:Humanoid,
 character:Model,
 session:any,
 player:Player,
 role:string,
 lastHealth:number,
 lastDamage:number,
 accumulator:number,
 connections:{RBXScriptConnection}
}
local active:{[Player]:Entry}={}

function Regen.maxHP(role:string):number?
 return Policy.initialMaxHP(role)
end
local function current(e:Entry):boolean
 local p=e.player
 local s=e.session
 if not p.Parent or p.Parent~=Players or p.Character~=e.character then return false end
 if not s.world or not s.world.Parent or s.rules.phase~="ACTIVE" then return false end
 if p:GetAttribute("EGGRUMBLE_QueuedMode")~=s.mode then return false end
 if p:GetAttribute("EGGRUMBLE_Role")~=e.role then return false end
 if p:GetAttribute("EGGRUMBLE_Eliminated")==true then return false end
 local castle=s.rules.castles[tostring(p.UserId)]
 if not castle or not castle.alive then return false end
 return e.humanoid.Parent==e.character and e.humanoid.Health>0
end
local function stop(p:Player)
 local e=active[p]
 if not e then return end
 active[p]=nil
 for _,c in ipairs(e.connections) do c:Disconnect() end
 table.clear(e.connections)
 -- No max HP reset when someone dies: existing original Host handles the round.
end
function Regen.attach(session:any,p:Player,role:string)
 if not Policy.initialMaxHP(role) or not p.Parent or not session or not session.world then return end
 local ch=p.Character
 local h=ch and ch:FindFirstChildOfClass("Humanoid")
 if not ch or not h or h.Health<=0 then return end
 local existing=active[p]
 if existing and existing.humanoid==h and existing.session==session and existing.role==role then return end
 stop(p)
 if session.rules.phase~="ACTIVE"
  or p:GetAttribute("EGGRUMBLE_QueuedMode")~=session.mode
  or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
 local castle=session.rules.castles[tostring(p.UserId)]
 if not castle or not castle.alive then return end
 -- One baseline write on first equip of this avatar in this exact round.
 -- Later ticks are ONLY the bounded passive heal, never new damage/KO.
 local max=Policy.initialMaxHP(role)
 if type(max)~="number" then return end
 h.MaxHealth=max
 h.Health=max
 local now=os.clock()
 local e:Entry={humanoid=h,character=ch,session=session,player=p,
  role=role,lastHealth=h.Health,lastDamage=now,accumulator=0,connections={}}
 active[p]=e
 table.insert(e.connections,h.HealthChanged:Connect(function(newHP)
  if active[p]~=e then return end
  -- Any server-authoritative damage, including PvP, boss, traps and DoT,
  -- interrupts regen without requiring a duplicate DamageOwner.
  e.lastDamage=Policy.observeHealth(e.lastHealth,newHP,os.clock(),e.lastDamage)
  e.lastHealth=newHP
 end))
 table.insert(e.connections,h.Died:Connect(function() stop(p) end))
 table.insert(e.connections,p.CharacterRemoving:Connect(function(oldCh)
  if oldCh==ch then stop(p) end
 end))
 table.insert(e.connections,session.world.Destroying:Connect(function() stop(p) end))
 table.insert(e.connections,RunService.Heartbeat:Connect(function(dt)
  if active[p]~=e then return end
  if not current(e) then stop(p);return end
  e.accumulator+=math.min(.25,math.max(dt,0))
  if e.accumulator<STEP_SECONDS then return end
  local elapsed=e.accumulator
  e.accumulator=0
  local health=h.Health
  local actualMax=h.MaxHealth
  local clock=os.clock()
  local burning=(h:GetAttribute("EGGRUMBLE_BurnUntil") or 0)>clock
   or (h:GetAttribute("EGGRUMBLE_DoTUntil") or 0)>clock
  local downed=(p:GetAttribute("EGGRUMBLE_Downed")==true)
   or (h:GetAttribute("EGGRUMBLE_Downed")==true)
  local delta=Policy.regenDelta(health,actualMax,clock,e.lastDamage,
   elapsed,true,true,burning,downed)
  if delta>0 then
   h.Health=math.min(actualMax,health+delta)
   e.lastHealth=h.Health
  end
 end))
end
function Regen.clear(p:Player)
 stop(p)
end
return Regen
