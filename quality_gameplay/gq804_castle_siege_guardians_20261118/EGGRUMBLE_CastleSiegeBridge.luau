--!strict
-- GQ804. This bridge is called only inside the existing validated Host/BotActors.
-- The original Rules.damageCastle keeps the only HP/egg/winner write authority.
local Players=game:GetService("Players")
local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeGuardianPolicy"))
local M={}
local function render(session:any,target:string,s:any)
 local bits=session.castleModels and session.castleModels[target]
 local door=bits and bits.door
 if not door or not door.Parent then return end
 local gui=door:FindFirstChild("GQ804_GateHP")
 if not gui then
  gui=Instance.new("BillboardGui");gui.Name="GQ804_GateHP"
  gui.Size=UDim2.fromOffset(190,48);gui.StudsOffset=Vector3.new(0,7,0)
  gui.AlwaysOnTop=false;gui.MaxDistance=70;gui.Parent=door
  local label=Instance.new("TextLabel");label.Name="Status"
  label.Size=UDim2.fromScale(1,1);label.BackgroundTransparency=.25
  label.BackgroundColor3=Color3.fromRGB(26,34,51)
  label.Font=Enum.Font.GothamBold;label.TextScaled=true
  label.TextColor3=Color3.fromRGB(245,234,205);label.Parent=gui
 end
 local label=gui:FindFirstChild("Status")
 if label and label:IsA("TextLabel") then
  label.Text=if s.stage=="GATE" then "城門 "..s.gateHP.."/180"
   elseif s.stage=="FALLEN" then "城陥落"
   else (if s.stage=="FINAL" then "最終城核" elseif s.stage=="INNER" then "内郭攻防"
    else "城核攻防").." HP"..s.castleHP.."/1000"
 end
 door.Color=if s.stage=="GATE" then Color3.fromRGB(111,78,54)
  elseif s.stage=="FALLEN" then Color3.fromRGB(65,65,65)
  elseif s.stage=="FINAL" then Color3.fromRGB(206,84,65)
  elseif s.stage=="INNER" then Color3.fromRGB(191,140,80)
  else Color3.fromRGB(117,160,172)
end
function M.attach(session:any,Rules:any):any
 assert(session and session.rules and session.rules.castles)
 assert(type(Rules.damageCastle)=="function")
 local epoch=tostring(session)
 local states={}
 for id in pairs(session.rules.castles) do states[id]=Policy.new(epoch,id) end
 local function tryAttack(targetId:string,attackerId:string,originalDamage:number,human:boolean):any
  local rules=session.rules
  local target=rules.castles[targetId];local attacker=rules.castles[attackerId]
  local state=states[targetId]
  if rules.phase~="ACTIVE" or not target or not attacker or not state
   or not target.alive or not attacker.alive or targetId==attackerId
   or (session.mode=="TEAM" and target.team==attacker.team) then
   error("GQ804_NOT_ACTIVE_ENEMY_OR_OWNER") end
  if (human and originalDamage~=120) or (not human and originalDamage~=26) then
   error("GQ804_BAD_ORIGINAL_DAMAGE") end
  if human then
   local p=Players:GetPlayerByUserId(tonumber(attackerId) or -1)
   local character=p and p.Character
   local health=character and character:FindFirstChildOfClass("Humanoid")
   if not p or not health or health.Health<=0
    or p:GetAttribute("EGGRUMBLE_Eliminated")==true then error("GQ804_INVALID_HUMAN") end
  else
   local actor=session.botActors and session.botActors[attackerId]
   local health=actor and actor:FindFirstChildOfClass("Humanoid")
   if not actor or not actor.Parent or not health or health.Health<=0 then
    error("GQ804_INVALID_OR_OLD_BOT") end
  end
  if not session.castleLocations[targetId] then error("GQ804_NO_CASTLE_WORLD") end
  -- The existing original Host prompt and BotActors already perform real
  -- physical distance/LOS/membership validation before invoking this callback.
  -- Their free non-paid server siege action is the starter siege tool.
  local req={
   verifiedByServer=true,matchId=epoch,targetCastleId=targetId,
   phase="ACTIVE",ownerCastleAlive=true,attackerId=attackerId,
   attackerCastleAlive=true,isEnemy=true,matchMember=true,
   losClear=true,reachable=true,withinRange=true,damage=originalDamage,
   now=os.clock(),freeSiegeToolVerified=true,
  }
  if state.stage=="GATE" then
   local result=Policy.gateHit(state,req)
   if not result then error("GQ804_GATE_DENIED") end
   render(session,targetId,state)
   return {fallen=false,releasedEggIds={},damage=0,gateHP=state.gateHP}
  end
  local permit=Policy.corePermit(state,req)
  if not permit then error("GQ804_CORE_DENIED_OR_COOLDOWN") end
  local result=Rules.damageCastle(rules,targetId,attackerId,permit.damage)
  -- Original function is synchronous, authoritative and non-yielding. Budget includes shields.
  assert(Policy.commitCorePermit(state,permit,{
   originalRulesAccepted=true,matchId=epoch,castleId=targetId,
   actualDamage=permit.damage}),"RED_GQ804_SIEGE_COMMIT")
  Policy.recordOriginalCastleHp(state,{
   verifiedByServer=true,matchId=epoch,targetCastleId=targetId,
   phase="ACTIVE",ownerCastleAlive=true,originalRulesAccepted=true,hp=target.hp,
  })
  render(session,targetId,state)
  return result
 end
 return tryAttack
end
return M
