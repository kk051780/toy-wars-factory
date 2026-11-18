--!strict
-- BATTLE-765 lane8 / MAGE REVIVE. One additive V3 Host-owned teammate rescue layer.
-- Existing MAGE healing, 7-role Combat, HP, KO, Score, Store authority untouched.
-- Genuine lethal hits (HP == 0) keep normal death; no resurrection after Humanoid.Died.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Workspace=game:GetService("Workspace")
local Rescue={}
local DOWNED_HEALTH_FRACTION=.20
local DOWNED_SECONDS=60
local PROMPT_HOLD_SECONDS=3
local REVIVE_FRACTION=.35
local MAGE_COOLDOWN_SECONDS=40
local MAX_REVIVE_DISTANCE=14
type Entry={
 player:Player,character:Model,humanoid:Humanoid,session:any,role:string,
 downAt:number?,lastHP:number,downed:boolean,
 originalWalkSpeed:number,originalJumpPower:number,originalJumpHeight:number,
 originalAutoRotate:boolean,
 shield:ForceField?,prompt:ProximityPrompt?,label:BillboardGui?,
 tick:number,connections:{RBXScriptConnection},
}
local active:{[Player]:Entry}={}
local lastMageCast:{[any]:{[number]:number}}=setmetatable({}, {__mode="k"}) :: any

local function current(e:Entry):boolean
 local s=e.session
 local p=e.player
 if not p.Parent or p.Parent~=Players or not s.world or not s.world.Parent
  or s.rules.phase~="ACTIVE" or s.mode~="TEAM" then return false end
 if p.Character~=e.character or e.humanoid.Parent~=e.character
  or e.humanoid.Health<=0 or p:GetAttribute("EGGRUMBLE_Eliminated")==true
  or p:GetAttribute("EGGRUMBLE_QueuedMode")~=s.mode then return false end
 local castle=s.rules.castles[tostring(p.UserId)]
 return castle~=nil and castle.alive and castle.team~=nil
end
local function allyMage(s:any,target:Player,healer:Player):boolean
 if healer==target or healer.Parent~=Players
  or healer:GetAttribute("EGGRUMBLE_Role")~="MAGE"
  or healer:GetAttribute("EGGRUMBLE_QueuedMode")~="TEAM"
  or healer:GetAttribute("EGGRUMBLE_Eliminated")==true then return false end
 local ours=s.rules.castles[tostring(target.UserId)]
 local theirs=s.rules.castles[tostring(healer.UserId)]
 if not ours or not theirs or not ours.alive or not theirs.alive
  or ours.team~=theirs.team then return false end
 local c=healer.Character
 local h=c and c:FindFirstChildOfClass("Humanoid")
 return h~=nil and h.Health>0 and healer:GetAttribute("EGGRUMBLE_Downed")~=true
end
local function clearEffects(e:Entry)
 local p=e.player
 if active[p]~=e then return end
 p:SetAttribute("EGGRUMBLE_Downed",false)
 e.humanoid:SetAttribute("EGGRUMBLE_Downed",false)
 if e.shield then e.shield:Destroy();e.shield=nil end
 if e.prompt then e.prompt:Destroy();e.prompt=nil end
 if e.label then e.label:Destroy();e.label=nil end
 if e.humanoid.Parent==e.character and e.humanoid.Health>0 then
  e.humanoid.WalkSpeed=e.originalWalkSpeed
  e.humanoid.JumpPower=e.originalJumpPower
  e.humanoid.JumpHeight=e.originalJumpHeight
  e.humanoid.AutoRotate=e.originalAutoRotate
 end
 for _,container in ipairs({p:FindFirstChildOfClass("Backpack"),e.character}) do
  if container then
   for _,tool in ipairs(container:GetChildren()) do
    if tool:IsA("Tool") and string.sub(tool.Name,1,16)=="EGGRUMBLE_SKILL_" then
     tool.Enabled=true
    end
   end
  end
 end
 e.downed=false;e.downAt=nil
end
local function stop(p:Player)
 local e=active[p]
 if not e then return end
 clearEffects(e)
 active[p]=nil
 for _,c in ipairs(e.connections) do c:Disconnect() end
 table.clear(e.connections)
end
function Rescue.policy()
 return {threshold=DOWNED_HEALTH_FRACTION,window=DOWNED_SECONDS,
  hold=PROMPT_HOLD_SECONDS,heal=REVIVE_FRACTION,cooldown=MAGE_COOLDOWN_SECONDS}
end
local function rescue(e:Entry,healer:Player)
 if not e.downed or not current(e) or not allyMage(e.session,e.player,healer) then return end
 if not e.downAt or os.clock()-e.downAt>=DOWNED_SECONDS then return end
 local mine=healer.Character
 local root=mine and mine:FindFirstChild("HumanoidRootPart")
 local targetRoot=e.character:FindFirstChild("HumanoidRootPart")
 if not root or not root:IsA("BasePart") or not targetRoot or not targetRoot:IsA("BasePart")
  or (root.Position-targetRoot.Position).Magnitude>MAX_REVIVE_DISTANCE then return end
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={mine,e.character}
 params.RespectCanCollide=true
 local hit=Workspace:Raycast(root.Position,targetRoot.Position-root.Position,params)
 if hit then return end
 local now=os.clock()
 local cd=lastMageCast[e.session]
 if not cd then cd={};lastMageCast[e.session]=cd end
 if now-(cd[healer.UserId] or -1e9)<MAGE_COOLDOWN_SECONDS then return end
 cd[healer.UserId]=now
 clearEffects(e)
 if e.humanoid.Parent==e.character and e.humanoid.Health>0 then
  e.humanoid.Health=math.max(e.humanoid.Health,e.humanoid.MaxHealth*REVIVE_FRACTION)
  e.lastHP=e.humanoid.Health
 end
 healer:SetAttribute("EGGRUMBLE_MageLastReviveAt",now)
 e.player:SetAttribute("EGGRUMBLE_RevivedBy",healer.UserId)
end
local function down(e:Entry)
 if e.downed or not current(e) then return end
 local canHelp=false
 for _,candidate in ipairs(Players:GetPlayers()) do
  if allyMage(e.session,e.player,candidate) then canHelp=true;break end
 end
 if not canHelp then return end -- solo/mage-less team never gets unfair 60s incapacitation.
 local root=e.character:FindFirstChild("HumanoidRootPart")
 if not root or not root:IsA("BasePart") then return end
 e.downed=true;e.downAt=os.clock()
 e.player:SetAttribute("EGGRUMBLE_Downed",true)
 e.humanoid:SetAttribute("EGGRUMBLE_Downed",true)
 e.originalWalkSpeed=e.humanoid.WalkSpeed
 e.originalJumpPower=e.humanoid.JumpPower
 e.originalJumpHeight=e.humanoid.JumpHeight
 e.originalAutoRotate=e.humanoid.AutoRotate
 e.humanoid.WalkSpeed=0;e.humanoid.JumpPower=0
 e.humanoid.JumpHeight=0;e.humanoid.AutoRotate=false
 -- ForceField blocks existing server Humanoid:TakeDamage calls but NOT a
 -- direct Humanoid.Health=0. A true instant-kill therefore remains a kill.
 local shield=Instance.new("ForceField")
 shield.Name="EGGRUMBLE_DownedRescueShield"
 shield.Visible=false
 shield.Parent=e.character
 e.shield=shield
 for _,container in ipairs({e.player:FindFirstChildOfClass("Backpack"),e.character}) do
  if container then
   for _,tool in ipairs(container:GetChildren()) do
    if tool:IsA("Tool") and string.sub(tool.Name,1,16)=="EGGRUMBLE_SKILL_" then
     tool.Enabled=false
    end
   end
  end
 end
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="EGGRUMBLE_MageRevive"
 prompt.ObjectText="味方がダウン中"
 prompt.ActionText="魔法使いが蘇生"
 prompt.HoldDuration=PROMPT_HOLD_SECONDS
 prompt.MaxActivationDistance=12
 prompt.RequiresLineOfSight=true
 prompt.Parent=root
 e.prompt=prompt
 table.insert(e.connections,prompt.Triggered:Connect(function(healer:Player)
  if active[e.player]~=e then return end
  rescue(e,healer)
 end))
 local label=Instance.new("BillboardGui")
 label.Name="EGGRUMBLE_ReviveTell"
 label.Size=UDim2.fromOffset(135,32)
 label.StudsOffset=Vector3.new(0,3.8,0)
 label.MaxDistance=48
 label.AlwaysOnTop=false
 label.Parent=root
 local text=Instance.new("TextLabel")
 text.Name="Countdown"
 text.Size=UDim2.fromScale(1,1)
 text.BackgroundColor3=Color3.fromRGB(39,24,53)
 text.BackgroundTransparency=.30
 text.TextColor3=Color3.fromRGB(250,223,115)
 text.TextScaled=true;text.Font=Enum.Font.GothamBold
 text.Text="蘇生待機 60秒"
 text.Parent=label
 e.label=label
end
function Rescue.attach(session:any,p:Player,role:string)
 if not session or session.mode~="TEAM" or session.rules.phase~="ACTIVE"
  or not session.world or not session.world.Parent then return end
 local ch=p.Character
 local h=ch and ch:FindFirstChildOfClass("Humanoid")
 if not ch or not h or h.Health<=0 then return end
 local prev=active[p]
 if prev and prev.character==ch and prev.session==session then return end
 stop(p)
 local e:Entry={player=p,character=ch,humanoid=h,session=session,role=role,
  downAt=nil,lastHP=h.Health,downed=false,originalWalkSpeed=h.WalkSpeed,
  originalJumpPower=h.JumpPower,originalJumpHeight=h.JumpHeight,
  originalAutoRotate=h.AutoRotate,shield=nil,prompt=nil,label=nil,tick=0,
  connections={}}
 active[p]=e
 table.insert(e.connections,h.HealthChanged:Connect(function(newHP)
  if active[p]~=e then return end
  local previous=e.lastHP
  e.lastHP=newHP
  if not current(e) then return end
  if not e.downed and newHP>0 and newHP<previous
   and newHP<=h.MaxHealth*DOWNED_HEALTH_FRACTION then down(e) end
 end))
 table.insert(e.connections,h.Died:Connect(function() stop(p) end))
 table.insert(e.connections,p.CharacterRemoving:Connect(function(old)
  if old==ch then stop(p) end
 end))
 table.insert(e.connections,session.world.Destroying:Connect(function() stop(p) end))
 table.insert(e.connections,RunService.Heartbeat:Connect(function(dt)
  if active[p]~=e then return end
  if not current(e) then stop(p);return end
  if not e.downed or not e.downAt then return end
  local elapsed=os.clock()-e.downAt
  if elapsed>=DOWNED_SECONDS then
   clearEffects(e)
   if h.Parent==ch and h.Health>0 then h.Health=0 end
   stop(p)
   return
  end
  e.tick+=dt
  if e.tick>=1 then
   e.tick=0
   local label=e.label and e.label:FindFirstChild("Countdown")
   if label and label:IsA("TextLabel") then
    label.Text="蘇生待機 "..math.max(0,math.ceil(DOWNED_SECONDS-elapsed)).."秒"
   end
  end
 end))
end
function Rescue.clear(p:Player)
 stop(p)
end
return Rescue
