--!strict
-- EGGRUMBLE independent NEUTRAL BOSS telegraph lane.
-- Studio-only visual and server-side damage. Never modifies the existing swarm/bot/hero/RC writers.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local Boss={}
local function block(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3,collide:boolean):Part
 local p=Instance.new("Part");p.Name=name;p.Position=pos;p.Size=size;p.Anchored=true
 p.Material=Enum.Material.Slate;p.Color=color;p.CanCollide=collide;p.CanTouch=false;p.Parent=parent
 return p
end
function Boss.spawn(parent:Instance,at:Vector3,options:any?):any
 -- Optional V3 session callbacks. Legacy isolated preview keeps its original
 -- Boss.spawn(workspace, at) API, without new boss or character implementations.
 local function sessionActive():boolean
  return not options or not options.isMatchActive or options.isMatchActive()==true
 end
 local function authorized(player:Player):boolean
  return not options or not options.canEngage or options.canEngage(player)==true
 end
 assert(RunService:IsStudio(),"private neutral boss preview only")
 local model=Instance.new("Model");model.Name="NEUTRAL_BOSS_STONE_GIANT";model.Parent=parent
 local torso=block(model,"Torso",at+Vector3.new(0,9,0),Vector3.new(8,10,5),Color3.fromRGB(103,114,127),true)
 block(model,"Head",at+Vector3.new(0,17,0),Vector3.new(5,5,5),Color3.fromRGB(139,149,162),true)
 for side=-1,1,2 do
  block(model,"Arm",at+Vector3.new(side*6,9,0),Vector3.new(4,10,4),Color3.fromRGB(91,100,112),true)
  block(model,"Leg",at+Vector3.new(side*2,2.5,0),Vector3.new(3,5,4),Color3.fromRGB(79,91,105),true)
 end
 local eye=block(model,"CoreWeakpoint",at+Vector3.new(0,10,-2.7),Vector3.new(2.5,2.5,0.5),Color3.fromRGB(93,220,245),false)
 eye.Material=Enum.Material.Neon
 local ring=Instance.new("Part");ring.Name="GroundTelegraph";ring.Shape=Enum.PartType.Cylinder
 ring.Size=Vector3.new(0.15,22,22);ring.CFrame=CFrame.new(at+Vector3.new(0,0.14,0))*CFrame.Angles(0,0,math.rad(90))
 ring.Anchored=true;ring.CanCollide=false;ring.CanTouch=false;ring.Material=Enum.Material.Neon
 ring.Color=Color3.fromRGB(252,112,67);ring.Transparency=1;ring.Parent=model
 model.PrimaryPart=torso
 local health=900
 local active=true
 local cooldown=false
 local lastStrike:{[number]:number}={}
 local MIN_HIT_INTERVAL=.22
 local function damageFrom(player:Player,amount:number,fromAuthorizedSkill:boolean?):boolean
  if not active or not sessionActive() or not authorized(player)
   or type(amount)~="number" or amount~=amount or amount<1 or amount>100 then return false end
  local c=player.Character
  local h=c and c:FindFirstChildOfClass("Humanoid")
  local root=c and c:FindFirstChild("HumanoidRootPart")
  if not h or h.Health<=0 or not root or not root:IsA("BasePart") then return false end
  -- Server-side role skill may reach 36stud, while the original manual
  -- ProximityPrompt remains a close-range action. No client-trusted remotes.
  local maxReach=if fromAuthorizedSkill==true then 36 else 14
  if (root.Position-eye.Position).Magnitude>maxReach then return false end
  local params=RaycastParams.new()
  params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances={c,model}
  local ray=workspace:Raycast(root.Position,eye.Position-root.Position,params)
  if ray and ray.Instance.CanCollide then return false end
  local now=os.clock()
  if now-(lastStrike[player.UserId] or -1000)<MIN_HIT_INTERVAL then return false end
  lastStrike[player.UserId]=now
  health=math.max(0,health-amount)
  model:SetAttribute("EGGRUMBLE_BossHealth",health)
  eye.Color=if health<=300 then Color3.fromRGB(255,99,91) else Color3.fromRGB(93,220,245)
  if health<=0 then
   active=false
   if options and options.onDefeat then
    local callbackOK,callbackError=pcall(options.onDefeat,player)
    if not callbackOK then warn("[EGGRUMBLE BOSS] onDefeat callback error:",callbackError) end
   end
   ring:Destroy()
   model:Destroy()
  end
  return true
 end
 local hitPrompt=Instance.new("ProximityPrompt")
 hitPrompt.Name="PreviewAttack";hitPrompt.ActionText="コア攻撃";hitPrompt.ObjectText="石の巨人"
 hitPrompt.HoldDuration=0.15;hitPrompt.MaxActivationDistance=12;hitPrompt.RequiresLineOfSight=true
 hitPrompt.Parent=eye
 hitPrompt.Triggered:Connect(function(player) damageFrom(player,50) end)
 task.spawn(function()
  while active and model.Parent and sessionActive() do
   task.wait(5)
   if not active or not sessionActive() or cooldown then continue end
   cooldown=true
   -- Readable windup before damage; 2.0 s to dodge out of radius.
   ring.Transparency=0.35
   task.wait(2)
   if not active or not sessionActive() then break end
   ring.Transparency=0.85
   for _,player in ipairs(Players:GetPlayers()) do
    if not authorized(player) then continue end
    local c=player.Character
    local h=c and c:FindFirstChildOfClass("Humanoid")
    local root=c and c:FindFirstChild("HumanoidRootPart")
    if h and h.Health>0 and root and root:IsA("BasePart") then
     local d=Vector3.new(root.Position.X-at.X,0,root.Position.Z-at.Z).Magnitude
     if d<=11 and math.abs(root.Position.Y-at.Y)<=8 then
      -- Server-side radial attack only, no client-trusted damage remotes.
      h:TakeDamage(28)
     end
    end
   end
   ring.Transparency=1
   cooldown=false
  end
 end)
 return {model=model,weakpoint=eye,damageFrom=damageFrom,
  maxHealth=900,attackRadius=11,windup=2}
end
return Boss
