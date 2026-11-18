--!strict
-- GQ822 V2 real-owner PRE-DAMAGE GATE, not a second HP or Combat writer.
-- Existing original owners still calculate damage and own :TakeDamage/KO/Score.
-- The only new authority here is match-bound free-role SKILL stance lifecycle;
-- rule engine source is immutable original #823 (NOT reimplemented).
local Players=game:GetService("Players")
local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_InvulnerabilityPolicy"))
local Runtime={}
local matchPolicies=setmetatable({}, {__mode="k"})
local bound=setmetatable({}, {__mode="k"})
local avatarSerial=0
local hitSerial=0

local function asBool(v:any):boolean
 return v==true
end
local function context(p:Player,r:any,now:number)
 local s=r.session
 local ch=p.Character
 local hum=ch and ch:FindFirstChildOfClass("Humanoid")
 local castle=s.rules and s.rules.castles and s.rules.castles[tostring(p.UserId)]
 local eggCount=castle and castle.heldEggs or 0
 local shieldUntil=p:GetAttribute("EGGRUMBLE_ShieldUntil") or 0
 local normalShield=(type(shieldUntil)=="number" and shieldUntil>now)
  or (ch and ch:FindFirstChildOfClass("ForceField")~=nil)
 return {
  epoch=s,playerId=p.UserId,avatarEpoch=r.avatar,
  role=r.role,now=now,phase=s.rules and s.rules.phase,
  mode=s.mode,serverCurrent=p.Parent==Players and ch==r.character
   and hum~=nil and hum.Health>0 and s.world~=nil and s.world.Parent~=nil
   and p:GetAttribute("EGGRUMBLE_QueuedMode")==s.mode,
  characterAlive=hum~=nil and hum.Health>0,
  roleVerified=p:GetAttribute("EGGRUMBLE_Role")==r.role,
  castleAlive=castle~=nil and castle.alive==true,
  downed=asBool(p:GetAttribute("EGGRUMBLE_Downed"))
   or (hum~=nil and asBool(hum:GetAttribute("EGGRUMBLE_Downed"))),
  eliminated=asBool(p:GetAttribute("EGGRUMBLE_Eliminated")),
  carryingEgg=(type(eggCount)=="number" and eggCount>0)
   or asBool(p:GetAttribute("EGGRUMBLE_CarryingEgg")),
  shieldActive=normalShield,
  itemOwned=false,weaponHeld=false,guardSucceeded=false,
 }
end
local function remove(p:Player)
 local r=bound[p]
 if not r then return end
 bound[p]=nil
 for _,c in ipairs(r.connections) do c:Disconnect() end
 if r.tool and r.tool.Parent then r.tool:Destroy() end
 if p.Parent then
  p:SetAttribute("EGGRUMBLE_InvulPhase","NONE")
  p:SetAttribute("EGGRUMBLE_InvulUntil",nil)
 end
end
function Runtime.attach(session:any,p:Player,role:string)
 if not session or not session.rules or not session.world or not session.world.Parent
  or not Policy.ROLES[role] then return end
 local ch=p.Character
 local hum=ch and ch:FindFirstChildOfClass("Humanoid")
 if not ch or not hum or hum.Health<=0 or p.Parent~=Players then return end
 local old=bound[p]
 if old and old.session==session and old.character==ch and old.role==role then return end
 remove(p)
 avatarSerial+=1
 local ledger=matchPolicies[session]
 if not ledger then
  ledger=Policy.newRound(session)
  matchPolicies[session]=ledger
 end
 local r={session=session,character=ch,role=role,avatar=avatarSerial,
  ledger=ledger,connections={},tool=nil}
 bound[p]=r
 local backpack=p:FindFirstChildOfClass("Backpack")
 if backpack then
  local tool=Instance.new("Tool")
  tool.Name="迎撃覚醒"
  tool.ToolTip="敵の攻撃を誘う 3秒の迎撃構え → 職別無敵覚醒"
  tool.RequiresHandle=false
  tool.CanBeDropped=false
  tool.Parent=backpack
  r.tool=tool
  table.insert(r.connections,tool.Activated:Connect(function()
   if bound[p]~=r or p.Character~=ch or tool.Parent~=ch then return end
   local now=os.clock()
   local ok,res=Policy.arm(ledger,context(p,r,now),"SKILL")
   if ok then
    p:SetAttribute("EGGRUMBLE_InvulPhase","ARMED")
    p:SetAttribute("EGGRUMBLE_InvulUntil",res.untilTime)
   end
  end))
 end
 table.insert(r.connections,p.CharacterRemoving:Connect(function(oldChar)
  if oldChar==ch then
   Policy.cancelAvatar(ledger,p.UserId)
   remove(p)
  end
 end))
 table.insert(r.connections,hum.Died:Connect(function()
  Policy.cancelAvatar(ledger,p.UserId)
  remove(p)
 end))
 table.insert(r.connections,session.world.Destroying:Connect(function()
  Policy.cancelAvatar(ledger,p.UserId)
  remove(p)
 end))
end

-- This function is called INSIDE the old owner's existing exact hit branch.
-- It returns a damage number only. The owner alone still applies :TakeDamage.
-- Calling it never generates a replacement HP writer, knockback or score.
function Runtime.filterDamage(victimHum:Humanoid,baseDamage:number,
 attackerKind:string,attackerId:any):number
 if type(baseDamage)~="number" or baseDamage~=baseDamage
  or baseDamage<=0 or baseDamage>=math.huge then return 0 end
 if not victimHum or not victimHum.Parent or victimHum.Health<=0 then return 0 end
 local victim=Players:GetPlayerFromCharacter(victimHum.Parent)
 if not victim then return baseDamage end -- NPC and neutral original damage intact.
 local r=bound[victim]
 if not r or r.character~=victimHum.Parent then return baseDamage end
 local now=os.clock()
 local c=context(victim,r,now)
 if not c.serverCurrent then return baseDamage end
 local kind=if attackerKind=="PLAYER" then "PLAYER"
  elseif attackerKind=="NEUTRAL" then "NEUTRAL"
  elseif attackerKind=="BOSS" then "BOSS" else "ENVIRONMENT"
 hitSerial+=1
 local event={
  serverVerified=true,hostile=kind~="ENVIRONMENT",
  damage=baseDamage,kind=kind,
  attackerId=tostring(attackerId or "WORLD_UNKNOWN"),
  attackId="GQ822_PREHIT_"..tostring(hitSerial),
 }
 local verdict=Policy.onIncomingDamage(r.ledger,c,event)
 if verdict.blocked then
  if verdict.awakened then
   victim:SetAttribute("EGGRUMBLE_InvulPhase","AWAKENED")
   victim:SetAttribute("EGGRUMBLE_InvulUntil",verdict.untilTime)
   -- Cosmetic-only cleanup; the policy epoch and current avatar are rechecked.
   task.delay(verdict.duration,function()
    if bound[victim]~=r then return end
    local snap=Policy.snapshot(r.ledger,context(victim,r,os.clock()))
    if snap.phase~="AWAKENED" then
     victim:SetAttribute("EGGRUMBLE_InvulPhase",snap.phase)
     victim:SetAttribute("EGGRUMBLE_InvulUntil",nil)
    end
   end)
  end
  return 0
 end
 return baseDamage
end
function Runtime.currentPolicySnapshot(p:Player)
 local r=bound[p]
 if not r then return {phase="NONE",remaining=0} end
 return Policy.snapshot(r.ledger,context(p,r,os.clock()))
end
return Runtime
