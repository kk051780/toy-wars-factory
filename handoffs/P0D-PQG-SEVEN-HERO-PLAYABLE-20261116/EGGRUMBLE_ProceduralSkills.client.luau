--!strict
-- EGGRUMBLE V3: 7 distinct lightweight weapon/arm gestures using server-owned cast events.
-- Studio-only client presentation. No gameplay authority, damage, RemoteEvent or asset IDs.
-- R15 upgraded AnimationConstraint and legacy Motor6D are both supported.
-- Roblox Animator updates joints before PreSimulation: additive Transform here avoids C0 edits.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local localPlayer=Players.LocalPlayer
local MAX_ANIMATED_AVATARS=16
local MAX_VIEW_DISTANCE=130
local active:{[number]:any}={}
local listeners:{[number]:RBXScriptConnection}={}
local sequences:{[number]:number}={}
local DURATION={A=.26,B=.48,C=.82}
local function jointOf(character:Model,names:{string}):any
 for _,name in ipairs(names) do
  local found=character:FindFirstChild(name,true)
  if found and (found:IsA("AnimationConstraint") or found:IsA("Motor6D")) then
   return found
  end
 end
 return nil
end
local function joints(character:Model):any
 return {
  right=jointOf(character,{"RightShoulder","Right Shoulder"}),
  left=jointOf(character,{"LeftShoulder","Left Shoulder"}),
  waist=jointOf(character,{"Waist","RootJoint","Root"}),
 }
end
local function sameCFrame(a:CFrame,b:CFrame):boolean
 local delta=a:ToObjectSpace(b)
 local _,angle=delta:ToAxisAngle()
 return delta.Position.Magnitude<.005 and math.abs(angle)<.01
end
local function resetPose(record:any)
 for _,joint in pairs(record.joints) do
  if joint and joint.Parent then
   local last=record.lastApplied[joint]
   local delta=record.lastDelta[joint]
   -- If Roblox Animator has already replaced this pose, do NOT wipe that animation.
   if last and delta and sameCFrame(last,joint.Transform) then
    joint.Transform=joint.Transform*delta:Inverse()
   end
  end
 end
end
local function additive(record:any,joint:any,delta:CFrame)
 if not joint or not joint.Parent then return end
 local base=joint.Transform
 local last=record.lastApplied[joint]
 local previous=record.lastDelta[joint]
 -- When the animator is idle and leaves a previous procedural pose untouched,
 -- subtract our old delta before applying the new one; no accumulating arm twist.
 if last and previous and sameCFrame(last,base) then
  base=base*previous:Inverse()
 end
 joint.Transform=base*delta
 record.lastApplied[joint]=joint.Transform
 record.lastDelta[joint]=delta
end
local function readCast(player:Player)
 local signature=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 if type(signature)~="string" then return end
 local role,slot,sequence=string.match(signature,"^([A-Z]+):([ABC]):(%d+)$")
 if not role or not slot or not sequence then return end
 local seq=tonumber(sequence)
 if not seq or seq<=(sequences[player.UserId] or 0) then return end
 sequences[player.UserId]=seq
 local c=player.Character
 local hum=c and c:FindFirstChildOfClass("Humanoid")
 if not c or not hum or hum.Health<=0 then return end
 local count=0
 for _ in pairs(active) do count+=1 end
 if count>=MAX_ANIMATED_AVATARS and not active[player.UserId] then return end
 if active[player.UserId] then resetPose(active[player.UserId]) end
 active[player.UserId]={
  player=player,char=c,role=role,slot=slot,start=os.clock(),
  duration=DURATION[slot] or .3,joints=joints(c),
  lastApplied={},lastDelta={},
 }
end
local function watch(p:Player)
 local uid=p.UserId
 if listeners[uid] then return end
 listeners[uid]=p:GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature"):Connect(function()
  readCast(p)
 end)
 p.CharacterRemoving:Connect(function(character)
  local record=active[uid]
  if record and record.char==character then
   resetPose(record);active[uid]=nil
  end
 end)
end
local function unwatch(p:Player)
 local uid=p.UserId
 local c=listeners[uid]
 if c then c:Disconnect();listeners[uid]=nil end
 local record=active[uid]
 if record then resetPose(record);active[uid]=nil end
 sequences[uid]=nil
end
for _,p in ipairs(Players:GetPlayers()) do watch(p) end
Players.PlayerAdded:Connect(watch)
Players.PlayerRemoving:Connect(unwatch)
local function rotate(role:string,slot:string,t:number):(CFrame,CFrame,CFrame)
 local pulse=math.sin(math.pi*math.clamp(t,0,1))
 local snap=math.sin(math.pi*math.min(1,t*1.8))
 local left=CFrame.new();local right=CFrame.new();local waist=CFrame.new()
 if role=="WARRIOR" then
  right=CFrame.Angles(-1.35*pulse,.3*snap,-.7*pulse)
  left=CFrame.Angles(-.25*pulse,0,.35*pulse)
  waist=CFrame.Angles(0,-.2*pulse,0)
 elseif role=="MAGE" then
  right=CFrame.Angles(-1.0*pulse,0,.35*pulse)
  left=CFrame.Angles(-.8*pulse,0,-.45*pulse)
 elseif role=="NINJA" then
  right=CFrame.Angles(-.92*pulse,0,-.85*snap)
  left=CFrame.Angles(-.65*pulse,0,.85*snap)
  waist=CFrame.Angles(0,.36*pulse,0)
 elseif role=="TRAPPER" then
  right=CFrame.Angles(-.8*pulse,0,-.5*pulse)
  left=CFrame.Angles(-.8*pulse,0,.5*pulse)
 elseif role=="BUILDER" then
  right=CFrame.Angles(-.9*pulse,.25*pulse,-.18*pulse)
  left=CFrame.Angles(-.3*pulse,-.1*pulse,.25*pulse)
 elseif role=="BEAST" then
  right=CFrame.Angles(-.8*pulse,0,-.5*snap)
  left=CFrame.Angles(-.7*pulse,0,.5*snap)
  waist=CFrame.Angles(.14*pulse,0,0)
 elseif role=="ZOMBIE" then
  right=CFrame.Angles(-.7*pulse,0,-.38*pulse)
  left=CFrame.Angles(-1.0*pulse,0,.3*pulse)
  waist=CFrame.Angles(0,-.16*pulse,0)
 end
 if slot=="B" then
  right=right*CFrame.Angles(-.25*pulse,0,0)
 elseif slot=="C" then
  right=right*CFrame.Angles(-.45*pulse,0,-.18*pulse)
  left=left*CFrame.Angles(-.55*pulse,0,.18*pulse)
 end
 return right,left,waist
end
local function nearby(character:Model):boolean
 local camera=workspace.CurrentCamera
 local pivot=character:FindFirstChild("HumanoidRootPart")::BasePart?
 if not camera or not pivot then return false end
 return (camera.CFrame.Position-pivot.Position).Magnitude<=MAX_VIEW_DISTANCE
end
-- Transform is nonreplicated; each observing client animates visible players from ONE
-- server-owned replicated signature, avoiding per-frame network or custom remote traffic.
RunService.PreSimulation:Connect(function(_dt)
 for uid,record in pairs(active) do
  local elapsed=os.clock()-record.start
  local character=record.char
  local hum=character and character:FindFirstChildOfClass("Humanoid")
  if not character or not character.Parent or not hum or hum.Health<=0
   or elapsed>=record.duration then
   resetPose(record)
   active[uid]=nil
  elseif nearby(character) then
   local r,l,w=rotate(record.role,record.slot,elapsed/record.duration)
   local js=record.joints
   additive(record,js.right,r)
   additive(record,js.left,l)
   additive(record,js.waist,w)
  end
 end
end)
localPlayer.AncestryChanged:Connect(function(_,parent)
 if parent then return end
 for _,p in ipairs(Players:GetPlayers()) do unwatch(p) end
end)
