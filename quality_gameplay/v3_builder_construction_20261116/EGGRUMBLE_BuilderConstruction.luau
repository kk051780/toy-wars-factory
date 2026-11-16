--!strict
-- EGGRUMBLE V3: independent, server-only, default-OFF temporary wall/bridge.
-- #482 author owns Game/Combat; #220 alone owns formal RC integration.
-- No Remote, DataStore, score, damage, egg, or alternative Game introduced.
local Players=game:GetService("Players")
local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_BuilderPlacementPolicy"))
local Build={}
Build.DEFAULT_ENABLED=false
local bySession:{[any]:any}=setmetatable({},{__mode="k"})

local function getActor(session:any,p:Player):(Model?,BasePart?)
 if typeof(session)~="table" or typeof(session.rules)~="table"
  or session.rules.phase~="ACTIVE" or session.rules.winner~=nil
  or not session.world or not session.world.Parent then return nil,nil end
 if typeof(session.mode)~="string" or (session.mode~="TEAM" and session.mode~="BATTLE_ROYALE") then return nil,nil end
 if not p or p.Parent~=Players or Players:GetPlayerByUserId(p.UserId)~=p then return nil,nil end
 if p:GetAttribute("EGGRUMBLE_Role")~="BUILDER"
  or p:GetAttribute("EGGRUMBLE_Eliminated")==true
  or p:GetAttribute("EGGRUMBLE_QueuedMode")~=session.mode then return nil,nil end
 local owner=session.rules.castles and session.rules.castles[tostring(p.UserId)]
 if not owner or owner.isAI or not owner.alive or (owner.heldEggs or 0)>0 then return nil,nil end
 local present=false
 for _,entry in ipairs(session.roster or {}) do
  if tostring(entry.id)==tostring(p.UserId) and entry.isAI==false then present=true;break end
 end
 if not present then return nil,nil end
 -- Reuse the original #531 Host live-match identity fence. An old roster/castle
 -- can survive a same-mode rejoin; queued mode and role alone are insufficient.
 if typeof(session.isCurrentHuman)~="function" then return nil,nil end
 local membershipOK,currentHuman=pcall(session.isCurrentHuman,p)
 if not membershipOK or currentHuman~=true then return nil,nil end
 local char=p.Character
 local humanoid=char and char:FindFirstChildOfClass("Humanoid")
 local root=char and char:FindFirstChild("HumanoidRootPart")
 if not char or not humanoid or humanoid.Health<=0
  or not root or not root:IsA("BasePart") then return nil,nil end
 return char,root
end

local function fieldContains(session:any,pos:Vector3):boolean
 local field=session.world:FindFirstChild("TacticalBattlefield")
 if not field or not field:IsA("BasePart") then return false end
 local p=field.CFrame:PointToObjectSpace(pos)
 return Policy.inField(p.X,p.Z,field.Size.X/2,field.Size.Z/2)
end

local function groundAt(session:any,at:Vector3):(Vector3?,BasePart?)
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Include
 params.FilterDescendantsInstances={session.world}
 params.RespectCanCollide=true
 params.IgnoreWater=true
 local hit=workspace:Raycast(at+Vector3.new(0,16,0),Vector3.new(0,-50,0),params)
 if not hit or not hit.Instance:IsA("BasePart") or not hit.Instance.CanCollide then return nil,nil end
 local part=hit.Instance
 -- Do not build on players, castles, roofs, movable items or an existing temporary bridge.
 if part.Name~="TacticalBattlefield" and not part.Name:match("^TacticalRoute_")
  and part.Name~="ValleyOverlook" then return nil,nil end
 return hit.Position,part
end

local function exclusion(session:any,pos:Vector3):boolean
 for _,point in pairs(session.castleLocations or {}) do
  if typeof(point)=="Vector3" and not Policy.safeDistance((point-pos).Magnitude) then return true end
 end
 local params=OverlapParams.new()
 params.FilterType=Enum.RaycastFilterType.Include
 params.FilterDescendantsInstances={session.world}
 params.MaxParts=0
 for _,other in ipairs(workspace:GetPartBoundsInRadius(pos,14,params)) do
  local n=other.Name
  if n:find("Egg") or n:find("Gate") or n:find("Vault") or n:find("FieldItem")
   or n:find("DecorStation") or n:find("Released") or n:find("PORTAL") then return true end
 end
 return false
end

local function sessionState(session:any):any
 local s=bySession[session]
 if not s then s={entries={},last={},serial=0};bySession[session]=s end
 return s
end
local function count(s:any,userId:number):(number,number)
 local total,own=0,0
 for id,entry in pairs(s.entries) do
  if not entry.part or not entry.part.Parent then
   s.entries[id]=nil
  else
   total+=1
   if entry.userId==userId then own+=1 end
  end
 end
 return total,own
end

-- Independent fallback when the original Game's closeRound hook has not been
-- connected yet. Only one heartbeat exists per real session, and only while
-- there are active constructs. It does NOT create a second Game/Remote/loop.
local function monitorSession(session:any,s:any):()
 if s.monitoring then return end
 s.monitoring=true
 local function tick()
  if bySession[session]~=s then return end
  if not session.world or not session.world.Parent or not session.rules
   or session.rules.phase~="ACTIVE" or session.rules.winner~=nil then
   -- The original author may also call clear(); both paths are idempotent.
   Build.clear(session)
   return
  end
  local total=count(s,-1)
  if total==0 then
   s.monitoring=false
   return
  end
  task.delay(0.25,tick)
 end
 task.delay(0.25,tick)
end

function Build.place(session:any,p:Player,kind:string,serverEnabled:boolean?):(boolean,string)
 -- This opt-in flag is passed ONLY by the original server-owned skill dispatcher.
 if serverEnabled~=true then return false,"FEATURE_OFF" end
 if kind~="WALL" and kind~="BRIDGE" then return false,"INVALID_KIND" end
 local char,root=getActor(session,p)
 if not char or not root then return false,"NOT_AUTHORIZED" end
 local s=sessionState(session)
 local total,own=count(s,p.UserId)
 if not Policy.capacity(total,own) then return false,"BUILD_CAP" end
 local now=os.clock()
 local key=tostring(p.UserId)..":"..kind
 if not Policy.cooldown(kind,now,s.last[key] or -100000) then return false,"COOLDOWN" end
 local forward=root.CFrame.LookVector
 local direction=Vector3.new(forward.X,0,forward.Z)
 if direction.Magnitude<0.15 then return false,"AIM_INVALID" end
 direction=direction.Unit
 local near=groundAt(session,root.Position+direction*7)
 local far=groundAt(session,root.Position+direction*(if kind=="WALL" then 12 else 24))
 if not near or not far then return false,"NO_SUPPORT" end
 if not Policy.support(near.Y,far.Y,root.Position.Y) then return false,"UNSAFE_SLOPE" end
 -- A bridge over intact grass is a useless platform, not a crossing.
 -- Validate the MIDPOINT in the same active arena, not a client-provided hit.
 -- Ground under a riverbed can be lower; an actual gap yields nil.
 if kind=="BRIDGE" then
  local middle=groundAt(session,root.Position+direction*15.5)
  if not Policy.bridgeGap(if middle then middle.Y else nil,math.min(near.Y,far.Y)) then
   return false,"NO_GAP"
  end
 end
 local center=(near+far)*0.5
 if not fieldContains(session,center) or not fieldContains(session,near)
  or not fieldContains(session,far) then return false,"FIELD_BOUNDS" end
 if exclusion(session,center) or exclusion(session,near) or exclusion(session,far) then
  return false,"OBJECTIVE_BLOCK"
 end
 local dims=if kind=="WALL" then Vector3.new(13,10,2.4) else Vector3.new(10,1.2,20)
 local cy=if kind=="WALL" then math.max(near.Y,far.Y)+dims.Y/2 else math.max(near.Y,far.Y)+0.7
 local at=Vector3.new(center.X,cy,center.Z)
 local cf=CFrame.lookAt(at,at+direction)
 -- No overlapping player models, solid obstacles, or other walls/bridges.
 local params=OverlapParams.new()
 -- Include characters parented to Workspace, not only the per-mode arena Folder.
 -- A server-owned Player character is normally NOT under session.world.
 params.FilterType=Enum.RaycastFilterType.Include
 params.FilterDescendantsInstances={workspace}
 params.MaxParts=0
 for _,other in ipairs(workspace:GetPartBoundsInBox(cf,dims+Vector3.new(1,1,1),params)) do
  -- Many Humanoid body parts are CanCollide=false; they must still block construction.
  local model=other:FindFirstAncestorOfClass("Model")
  local isHumanoid=model~=nil and model:FindFirstChildOfClass("Humanoid")~=nil
  -- Only the actual session floor/routes are exempt, never copied map objects.
  local isOwnGround=other:IsDescendantOf(session.world)
   and (other.Name=="TacticalBattlefield" or other.Name:match("^TacticalRoute_")~=nil)
  if Policy.blocksPlacement(other.CanCollide,isOwnGround,isHumanoid) then
   return false,if isHumanoid then "HUMANOID_OVERLAP" else "OBSTACLE_OR_CONSTRUCT"
  end
 end
 -- Nothing yields between the final capacity+world guards and creation.
 local part=Instance.new("Part")
 part.Name="EGGRUMBLE_BUILDER_"..kind
 part.Anchored=true;part.CanCollide=true;part.CanTouch=false;part.CanQuery=true
 part.Size=dims;part.CFrame=cf
 part.Material=if kind=="WALL" then Enum.Material.Slate else Enum.Material.WoodPlanks
 part.Color=if kind=="WALL" then Color3.fromRGB(116,133,150) else Color3.fromRGB(159,122,81)
 part:SetAttribute("EGGRUMBLE_Temporary",true)
 part:SetAttribute("EGGRUMBLE_ConstructOwner",p.UserId)
 part.Parent=session.world
 s.serial+=1
 local id=s.serial
 s.entries[id]={part=part,userId=p.UserId}
 s.last[key]=now
 task.delay(Policy.LIFETIME,function()
  local entry=s.entries[id]
  if entry then
   s.entries[id]=nil
   if entry.part and entry.part.Parent then entry.part:Destroy() end
  end
 end)
 monitorSession(session,s)
 return true,kind
end
-- Add server-owned Tool input to the ORIGINAL role system. This is not a
-- second Game or Remote: the original Host calls this after HeroCombat.equip.
-- Preserves original BUILDER A/B/C skills, including its turret.
function Build.equip(session:any,p:Player,serverEnabled:boolean?,bridgeEnabled:boolean?):(boolean,string)
 if serverEnabled~=true then return false,"FEATURE_OFF" end
 local character=getActor(session,p)
 if not character then return false,"NOT_AUTHORIZED" end
 local backpack=p:FindFirstChildOfClass("Backpack")
 if not backpack then return false,"NO_BACKPACK" end
 local prefix="EGGRUMBLE_SKILL_CONSTRUCT_"
 -- Respawn/re-equip may be called twice. Never leave old callbacks/tools live.
 for _,container in ipairs({backpack,character}) do
  for _,tool in ipairs(container:GetChildren()) do
   if tool:IsA("Tool") and string.sub(tool.Name,1,#prefix)==prefix then
    tool:Destroy()
   end
  end
 end
 -- A bridge Tool is hidden until a real authored crossing is present.
 -- WALL-only is the safe private-RC default; no misleading unusable bridge button.
 local kinds=if bridgeEnabled==true then {"WALL","BRIDGE"} else {"WALL"}
 for _,kind in ipairs(kinds) do
  local tool=Instance.new("Tool")
  tool.Name=prefix..kind
  tool.ToolTip=if kind=="WALL" then "建築士｜防壁（9秒・再使用13秒）"
   else "建築士｜橋（真の溝のみ・9秒・再使用17秒）"
  tool.RequiresHandle=false
  tool.CanBeDropped=false
  local originalCharacter=character
  tool.Activated:Connect(function()
   -- Roblox's existing Tool/equip transport is the ONLY input. No client
   -- coordinates, new Remote, duplicate HP/damage/score/Store authority.
   if p.Character~=originalCharacter or tool.Parent~=originalCharacter then return end
   Build.place(session,p,kind,true)
  end)
  tool.Parent=backpack
 end
 return true,"TOOLS_READY"
end

function Build.clear(session:any):()
 local s=bySession[session]
 if not s then return end
 for id,entry in pairs(s.entries) do
  if entry.part and entry.part.Parent then entry.part:Destroy() end
  s.entries[id]=nil
 end
 bySession[session]=nil
end
return Build
