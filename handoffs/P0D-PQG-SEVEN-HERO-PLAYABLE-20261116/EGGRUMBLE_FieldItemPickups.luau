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
 local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_FieldItems";folder.Parent=session.world
 local lastUse:{[string]:number}={}
 local consumed:{[string]:boolean}={}
 local RESPAWN_SECONDS=35
 local active=true
 local function matchActive():boolean
  return active and folder.Parent~=nil and session.rules and session.rules.phase=="ACTIVE"
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
   local key=tostring(player.UserId)..":"..kind
   local now=os.clock()
   if now-(lastUse[key] or -100000)<def.cooldown then return end
   -- Server-authoritative single-use claim before applying any effect.
   consumed[id]=true;lastUse[key]=now
   prompt.Enabled=false
   if kind=="HEAL" then
    hum.Health=math.min(hum.MaxHealth,hum.Health+35)
   elseif kind=="DASH" then
    local previous=hum.WalkSpeed
    hum.WalkSpeed=math.max(previous,27)
    task.delay(5,function()
     if hum.Parent and hum.Health>0 and hum.WalkSpeed==math.max(previous,27) then
      hum.WalkSpeed=previous
     end
    end)
   else
    local char=player.Character
    if char then
     local force=Instance.new("ForceField")
     force.Name="EGGRUMBLE_ItemShield";force.Visible=true;force.Parent=char
     task.delay(4,function() if force.Parent then force:Destroy() end end)
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
