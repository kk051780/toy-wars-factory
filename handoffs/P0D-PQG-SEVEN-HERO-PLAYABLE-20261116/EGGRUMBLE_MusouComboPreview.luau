--!strict
-- EGGRUMBLE isolated BATTLE FEEL lane: server-owned combo, multi-target cone, lightweight VFX.
-- Standalone Studio only. No edits to canonical seven hero combat or RC.
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local Battle={}
local COMBO_DAMAGE={18,22,30}
local COMBO_RADIUS={8,9,12}
local COMBO_ANGLE={105,120,150}
local COMBO_WINDOW=1.25
local states:{[Player]:{step:number,expires:number,nextAt:number}}={}
local function getRig(player:Player):(Model?,Humanoid?,BasePart?)
 local c=player.Character
 local h=c and c:FindFirstChildOfClass("Humanoid")
 local root=c and c:FindFirstChild("HumanoidRootPart")
 if not h or h.Health<=0 or not root or not root:IsA("BasePart") then return nil,nil,nil end
 return c,h,root
end
local function inCone(root:BasePart,at:Vector3,angle:number):boolean
 local d=Vector3.new(at.X-root.Position.X,0,at.Z-root.Position.Z)
 if d.Magnitude<0.2 then return true end
 local f=Vector3.new(root.CFrame.LookVector.X,0,root.CFrame.LookVector.Z)
 if f.Magnitude<0.2 then return false end
 return f.Unit:Dot(d.Unit)>=math.cos(math.rad(angle/2))
end
local function impact(parent:Instance,root:BasePart,step:number):()
 local ring=Instance.new("Part")
 ring.Name="COMBO_IMPACT_"..step;ring.Shape=Enum.PartType.Ball
 ring.Size=Vector3.new(3,3,3);ring.Anchored=true;ring.CanCollide=false;ring.CanTouch=false
 ring.CanQuery=false;ring.Material=Enum.Material.Neon;ring.Transparency=.58
 ring.Color=if step==3 then Color3.fromRGB(255,190,64) else Color3.fromRGB(119,204,255)
 ring.CFrame=root.CFrame*CFrame.new(0,0,-5);ring.Parent=parent
 local tween=game:GetService("TweenService"):Create(ring,TweenInfo.new(.2),{
  Size=Vector3.new(COMBO_RADIUS[step]*1.6,COMBO_RADIUS[step]*1.6,COMBO_RADIUS[step]*1.6),Transparency=1})
 tween:Play();Debris:AddItem(ring,.28)
end
function Battle.attack(player:Player,targets:{Model},effectsParent:Instance):any
 assert(RunService:IsStudio(),"battle feel preview only")
 local character,hum,root=getRig(player)
 if not character or not hum or not root then return {ok=false,reason="NO_CHARACTER"} end
 local now=os.clock()
 local state=states[player] or {step=0,expires=0,nextAt=0}
 if now<state.nextAt then return {ok=false,reason="COOLDOWN"} end
 local step=if now>state.expires then 1 else state.step%3+1
 state.step=step;state.expires=now+COMBO_WINDOW
 state.nextAt=now+(if step==3 then 0.55 else 0.23)
 states[player]=state
 local count=0
 local used:{[Model]:boolean}={}
 for _,target in ipairs(targets) do
  if count>=12 then break end
  if target~=character and not used[target] and target:GetAttribute("EGGRUMBLE_NeutralTarget")==true then
   used[target]=true
   local h=target:FindFirstChildOfClass("Humanoid")
   local part=target:FindFirstChild("HumanoidRootPart")
   if h and h.Health>0 and part and part:IsA("BasePart") then
    local dist=(part.Position-root.Position).Magnitude
    if dist<=COMBO_RADIUS[step] and inCone(root,part.Position,COMBO_ANGLE[step]) then
     local params=RaycastParams.new()
     params.FilterType=Enum.RaycastFilterType.Exclude
     params.FilterDescendantsInstances={character,target}
     local ray=workspace:Raycast(root.Position,part.Position-root.Position,params)
     if not ray or not ray.Instance.CanCollide then
      h:TakeDamage(COMBO_DAMAGE[step]);count+=1
     end
    end
   end
  end
 end
 impact(effectsParent,root,step)
 player:SetAttribute("EGGRUMBLE_PreviewComboStep",step)
 player:SetAttribute("EGGRUMBLE_PreviewComboHits",count)
 return {ok=true,step=step,hits=count,damage=COMBO_DAMAGE[step]}
end
function Battle.clear(player:Player):()
 states[player]=nil
end
return Battle
