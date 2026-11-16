--!strict
-- EGGRUMBLE isolated field-item slice; NOT connected to official RC or economy.
-- Writer scope: ITEM field pickup/consumption only; no castle, lobby, hero or AI edits.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Items={}
local DEFINITIONS={
 HEAL={label="回復薬",color=Color3.fromRGB(84,232,150),cooldown=15},
 DASH={label="疾風の羽",color=Color3.fromRGB(96,211,245),cooldown=18},
 SHIELD={label="守護の結晶",color=Color3.fromRGB(192,146,255),cooldown=22},
}
local function canUse(player:Player,session:any):boolean
 local roster=session and session.rules and session.rules.castles
 local castle=roster and roster[tostring(player.UserId)]
 return castle~=nil and castle.alive==true and session.rules.phase=="ACTIVE"
end
-- Read the authoritative match roster. Client attributes cannot grant egg-carrier immunity.
local function carryingEnemyEggs(player:Player,session:any):boolean
 local castles=session and session.rules and session.rules.castles
 local castle=castles and castles[tostring(player.UserId)]
 return castle~=nil and type(castle.heldEggs)=="number" and castle.heldEggs>0
end
local function characterState(player:Player):(Humanoid?,BasePart?)
 local c=player.Character
 if not c then return nil,nil end
 local h=c:FindFirstChildOfClass("Humanoid")
 local root=c:FindFirstChild("HumanoidRootPart")
 if not root or not root:IsA("BasePart") then return h,nil end
 return h,root
end
function Items.start(session:any,positions:{Vector3}):()
 assert(RunService:IsStudio(),"Field item preview is Studio-only")
 -- Reuse the original lobby/castle LOS + anti-spam authority in actual TEAM/BR.
 -- The item-only isolated preview has no mode and can keep running alone.
 local isV3Match=session and (session.mode=="TEAM" or session.mode=="BATTLE_ROYALE")
 local guardSource=script.Parent:FindFirstChild("EGGRUMBLE_InteractionGuard")
 local interactionGuard:any=if guardSource then require(guardSource) else nil
 if isV3Match then
  assert(interactionGuard and type(interactionGuard.allow)=="function",
   "V3 items require the original InteractionGuard server authority")
 end
 local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_FieldItems";folder.Parent=session.world
 local lastUse:{[string]:number}={}
 local consumed:{[string]:boolean}={}
 local RESPAWN_SECONDS=35
 local active=true
 local function matchActive():boolean
  return active and folder.Parent~=nil and session.rules and session.rules.phase=="ACTIVE"
 end
 -- A player can take eggs *after* activating a buff. Cancel that buff as soon as
 -- cargo is observed (<=0.25s), rather than only rejecting new pickups.
 -- The loop is bounded to one short-lived item effect and stops after the match.
 local function cancelBuffIfCarrier(player:Player,duration:number,undo:()->())
  task.spawn(function()
   for _=1,math.ceil(duration*4) do
    task.wait(.25)
    if not matchActive() or carryingEnemyEggs(player,session) then
     undo()
     return
    end
   end
  end)
 end
 local serial=0
 for i,pos in ipairs(positions) do
  local kind=({"HEAL","DASH","SHIELD"})[(i-1)%3+1]
  local def=DEFINITIONS[kind]
  serial+=1
  local id="ITEM_"..tostring(serial)
  local part=Instance.new("Part")
  part.Name=id.."_"..kind;part.Shape=Enum.PartType.Ball
  part.Size=Vector3.new(2.2,2.2,2.2)
  part.Material=Enum.Material.Neon;part.Color=def.color
  part.Anchored=true;part.CanCollide=false;part.Position=pos
  part.Parent=folder
  local prompt=Instance.new("ProximityPrompt")
  prompt.ActionText="拾って使う";prompt.ObjectText=def.label
  prompt.MaxActivationDistance=8;prompt.RequiresLineOfSight=true
  prompt.HoldDuration=.2;prompt.Parent=part
  prompt.Triggered:Connect(function(player:Player)
   if consumed[id] or not part.Parent or not part.CanQuery or not canUse(player,session) then return end
   local hum,root=characterState(player)
   if not hum or not root or hum.Health<=0 then return end
   if (root.Position-part.Position).Magnitude>10 then return end
   -- DASH/SHIELD must not turn an egg run into invulnerable high-speed escape.
   -- Rejected pickups stay visible and do NOT consume the item or cooldown.
   if kind~="HEAL" and carryingEnemyEggs(player,session) then return end
   local key=tostring(player.UserId)..":"..kind
   local now=os.clock()
   if now-(lastUse[key] or -100000)<def.cooldown then return end
   -- Client ProximityPrompt LOS is presentation, not server authorization:
   -- reuse the same wall/vertical/humanoid/rate gate as castle egg prompts.
   if isV3Match and not interactionGuard.allow(player,part,"拾う",part.Name) then return end
   -- Server-authoritative single-use claim before applying any effect.
   consumed[id]=true;lastUse[key]=now
   prompt.Enabled=false
   if kind=="HEAL" then
    hum.Health=math.min(hum.MaxHealth,hum.Health+35)
   elseif kind=="DASH" then
    local previous=hum.WalkSpeed
    -- Preserve the original speed-source contract for all existing ITEM tests.
    hum.WalkSpeed=math.max(previous,27)
    local boosted=hum.WalkSpeed
    local function restoreSpeed()
     -- Never stomp a subsequent skill's newer speed decision.
     if hum.Parent and hum.Health>0 and hum.WalkSpeed==boosted then
      hum.WalkSpeed=previous
     end
    end
    cancelBuffIfCarrier(player,5,restoreSpeed)
    task.delay(5,restoreSpeed)
   else
    local char=player.Character
    if char then
     local force=Instance.new("ForceField")
     force.Name="EGGRUMBLE_ItemShield";force.Visible=true;force.Parent=char
     local function clearShield() if force.Parent then force:Destroy() end end
     cancelBuffIfCarrier(player,4,clearShield)
     task.delay(4,clearShield)
    end
   end
   part.Transparency=1;part.CanQuery=false
   task.delay(RESPAWN_SECONDS,function()
    if not matchActive() or not part.Parent then return end
    consumed[id]=nil
    part.Transparency=0;part.CanQuery=true;prompt.Enabled=true
   end)
  end)
 end
 session.itemStop=function()
  active=false
  if folder.Parent then folder:Destroy() end
 end
end
return Items
