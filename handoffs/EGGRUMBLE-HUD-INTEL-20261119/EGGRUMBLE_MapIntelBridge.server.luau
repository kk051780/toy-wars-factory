--!nonstrict
-- Single server-only EGGRUMBLE map presenter: no combat, store, item or HP authority.
-- Sends only already-filtered map data through one-way map RemoteEvent.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Intel=require(script.Parent:WaitForChild("EGGRUMBLE_MapVisibilityPolicy"))
-- Read-only existing V2 policy ledger; this does not create another damage owner.
local InvulRuntime=require(script.Parent:WaitForChild("EGGRUMBLE_InvulRuntime"))
local NAME="EGGRUMBLE_MapIntelUpdate_V1"
local remote=ReplicatedStorage:FindFirstChild(NAME)
assert(remote==nil,"RED_DUPLICATE_MAP_REMOTE_OWNER")
remote=Instance.new("RemoteEvent")
remote.Name=NAME
remote.Parent=ReplicatedStorage
-- No OnServerEvent listener: the client cannot ask for targets or forge scan pulses.
local state={}
local scenes=workspace:WaitForChild("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW",30)
if not scenes then return end
local TICK=.9
local MAX_VISIBLE_CELLS=500
local MAX_MARKERS=30
local REALM={LAND=true,SEA=true,SKY=true}
local function rootOf(p)
 local ch=p.Character
 local hu=ch and ch:FindFirstChildOfClass("Humanoid")
 local root=ch and ch:FindFirstChild("HumanoidRootPart")
 if hu and root and hu.Health>0 then return root end
 return nil
end
local function ownScene(p)
 local mode=p:GetAttribute("EGGRUMBLE_QueuedMode")
 if mode~="TEAM" and mode~="BATTLE_ROYALE" then return nil,nil end
 local folder=scenes:FindFirstChild(mode.."_Arena")
 if folder and folder:IsA("Folder") then return mode,folder end
 return nil,nil
end
local function findCastles(arena)
 local castles={}
 for _,m in ipairs(arena:GetChildren()) do
  if m:IsA("Model") and string.sub(m.Name,1,7)=="Castle_" then
   local foundation=m:FindFirstChild("StandardFoundation")
   if foundation and foundation:IsA("BasePart") then
    -- The canonical Castle Host sets these side colors from its verified
    -- server roster; no client team claim is trusted. Unknown colors fail shut.
    local tint=foundation.Color
    local team=nil
    local function closeColor(a,b)
     return math.abs(a.R-b.R)<.02 and math.abs(a.G-b.G)<.02
       and math.abs(a.B-b.B)<.02
    end
    if closeColor(tint,Color3.fromRGB(207,92,86)) then team="RED"
    elseif closeColor(tint,Color3.fromRGB(87,146,218)) then team="BLUE" end
    table.insert(castles,{id=m.Name,kind="CASTLE",x=foundation.Position.X,
     z=foundation.Position.Z,layer="LAND",ownerId=string.sub(m.Name,8),
     team=team,sourceModel=m})
   end
  end
 end
 table.sort(castles,function(a,b)return a.id<b.id end)
 return castles
end
local function ownCastle(castles,p)
 local uid=tostring(p.UserId)
 for _,c in ipairs(castles) do
  if c.ownerId==uid then return c end
 end
 return nil
end
local function getRole(p)
 local role=p:GetAttribute("EGGRUMBLE_Role")
 if role=="WARRIOR" or role=="MAGE" or role=="NINJA"
    or role=="TRAPPER" or role=="BUILDER" or role=="BEAST"
    or role=="ZOMBIE" then return role end
 return "WARRIOR"
end
local function realmOf(p)
 if p:GetAttribute("EGGRUMBLE_RealmDepth")=="SUBSEA" then return "SEA" end
 local ch=p.Character
 local hu=ch and ch:FindFirstChildOfClass("Humanoid")
 local seat=hu and hu.SeatPart
 if seat and seat.Name=="PilotSeat" then
   local parent=seat.Parent
   if parent and (parent.Name:find("_SKY_") or parent.Name:find("_AIRSHIP_")
     or parent:GetAttribute("RealmKind")=="FIGHTER") then
      return "SKY"
   end
   if parent and (parent.Name:find("_SEA_") or parent.Name:find("_SEA_BEAST_")) then
      return "SEA"
   end
 end
 return "LAND"
end
local function los(a,b,aCharacter,bCharacter)
 local delta=b-a
 if delta.Magnitude>82 or delta.Magnitude<.01 then return false end
 local ray=RaycastParams.new()
 ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={aCharacter,bCharacter}
 ray.RespectCanCollide=true
 return workspace:Raycast(a,delta,ray)==nil
end
local function entityMarkers(p,mode,arena,root,viewer)
 local result=findCastles(arena)
 local count=#result
 local selfHome=ownCastle(result,p)
 -- Server-authored, source-pinned castle foundation color is a read-only
 -- projection of the original Host's TEAM roster; unknown remains private.
 local pteam=selfHome and selfHome.team
 local ownTeam=mode=="BATTLE_ROYALE" and ("BR_"..p.UserId) or pteam
 if mode=="BATTLE_ROYALE" or (pteam=="RED" or pteam=="BLUE") then
  for _,other in ipairs(Players:GetPlayers()) do
   if other~=p and other:GetAttribute("EGGRUMBLE_QueuedMode")==mode then
    local otherCastle=ownCastle(result,other)
    local theirTeam=mode=="BATTLE_ROYALE" and ("BR_"..other.UserId)
      or (otherCastle and otherCastle.team)
    local eroot=rootOf(other)
    if theirTeam and eroot and count<MAX_MARKERS then
     local sameTeam=theirTeam==ownTeam
     local pos=eroot.Position
     local visible=los(root.Position+Vector3.new(0,2,0),
       pos+Vector3.new(0,2,0),p.Character,other.Character)
     table.insert(result,{
      id="P"..other.UserId,kind=sameTeam and "ALLY" or "ENEMY",
      x=pos.X,z=pos.Z,team=theirTeam,layer=realmOf(other),
      serverLineOfSight=visible,
      stealthed=(other:GetAttribute("EGGRUMBLE_StealthUntil") or 0)>os.clock(),
     })
     count+=1
     if not sameTeam and count<MAX_MARKERS then
      table.insert(result,{id="TRAIL_"..other.UserId,kind="ENEMY_TRAIL",
       x=pos.X,z=pos.Z,layer=realmOf(other),expiresAt=workspace:GetServerTimeNow()+2})
      count+=1
     end
    end
   end
  end
 end
 -- Real castle gates exist as the already-owned server Host model children.
 for _,castle in ipairs(findCastles(arena)) do
  if count>=MAX_MARKERS then break end
  local gate=castle.sourceModel:FindFirstChild("SiegeGate")
  if gate and gate:IsA("BasePart")
   and (gate.Position-root.Position).Magnitude<=200 then
   table.insert(result,{id="GATE_"..castle.id,kind="CASTLE_GATE",
    x=gate.Position.X,z=gate.Position.Z,layer="LAND"})
   count+=1
  end
 end
 -- Only the original Swarm-author's real tagged Humanoid actors are scanned.
 local horde=arena:FindFirstChild("NeutralHorde")
 if horde then
  for index,npc in ipairs(horde:GetChildren()) do
   if count>=MAX_MARKERS then break end
   if npc:IsA("Model") and npc:GetAttribute("EGGRUMBLE_Neutral")==true then
    local h=npc:FindFirstChildOfClass("Humanoid")
    local part=npc:FindFirstChild("HumanoidRootPart")
    if h and h.Health>0 and part and part:IsA("BasePart")
      and (part.Position-root.Position).Magnitude<210 then
     table.insert(result,{id="N_"..tostring(index),
      kind="NEUTRAL",x=part.Position.X,z=part.Position.Z,layer="LAND",
      serverLineOfSight=los(root.Position+Vector3.new(0,1.5,0),
        part.Position+Vector3.new(0,1.5,0),p.Character,npc)})
     count+=1
    end
   end
  end
 end
 -- Actual original field pickups; different roles can scout distinct items.
 local items=arena:FindFirstChild("EGGRUMBLE_FieldItems")
 if items then
  for _,part in ipairs(items:GetChildren()) do
   if count>=MAX_MARKERS then break end
   if part:IsA("BasePart") and (part.Position-root.Position).Magnitude<=210 then
    local kind=if part.Name:find("_SHIELD") then "MAGIC_TREASURE" else "RESOURCE"
    table.insert(result,{id=part.Name,kind=kind,x=part.Position.X,
      z=part.Position.Z,layer="LAND"})
    count+=1
   end
  end
 end
 -- Egg objectives require explored tiles: never preload their hidden coordinates.
 for _,part in ipairs(arena:GetChildren()) do
  if count>=MAX_MARKERS then break end
  if part:IsA("BasePart") and string.match(part.Name,"^FieldEgg_%d+$")
    and (part.Position-root.Position).Magnitude<=250 then
   table.insert(result,{id=part.Name,kind="EGG",
    x=part.Position.X,z=part.Position.Z,layer="LAND"})
   count+=1
  end
 end
 return result
end
local function send(p)
 local mode,arena=ownScene(p)
 local root=rootOf(p)
 if not mode or not root then
  if state[p] then remote:FireClient(p,{kind="MAP_RESET",version=1}) end
  state[p]=nil
  return
 end
 local castles=findCastles(arena)
 local home=ownCastle(castles,p)
 if not home then
  if state[p] then remote:FireClient(p,{kind="MAP_RESET",version=1}) end
  state[p]=nil
  return
 end
 local s=state[p]
 if not s or s.arena~=arena or s.mode~=mode then
  -- Do not initialize while the user is still in the lobby.
  local dx=root.Position.X-home.x
  local dz=root.Position.Z-home.z
  if dx*dx+dz*dz>150*150 then return end
  s={mode=mode,arena=arena,explored=Intel.newExploration(home.x,home.z),
      lastX=root.Position.X,lastZ=root.Position.Z,lastLayer="LAND",
      mapStartTime=workspace:GetServerTimeNow()}
  state[p]=s
 end
 local x,z=root.Position.X,root.Position.Z
 local step=(x-s.lastX)^2+(z-s.lastZ)^2
 if step<=225*225 then
   Intel.reveal(s.explored,x,z,36)
   s.lastX=x;s.lastZ=z
 end
 local n=0
 for _ in pairs(s.explored) do n+=1 end
 if n>MAX_VISIBLE_CELLS then
   -- A full map reveal is not a pretext to replicate unlimited data.
   -- Restart visible detail around the last server-confirmed position.
   s.explored=Intel.newExploration(x,z)
 end
 local layer=realmOf(p)
 local role=getRole(p)
 local team=mode=="BATTLE_ROYALE" and ("BR_"..p.UserId) or home.team
 local viewer={playerId=tostring(p.UserId),team=team,
     role=role,x=x,z=z,layer=layer,explored=s.explored,serverVerified=true}
 -- A free server-timed passive reconnaissance window (8s every 65s)
 -- is intentionally different from paid items or client-triggered scans.
 local since=workspace:GetServerTimeNow()-s.mapStartTime
 local pulseKind={
  WARRIOR="SIEGE_SENSE",MAGE="MAGIC_SENSE",NINJA="TRAIL_SENSE",
  TRAPPER="ENEMY_SENSE",BUILDER="RESOURCE_SENSE",
  BEAST="BEAST_SENSE",ZOMBIE="CURSE_SENSE",
 }
 if since>=20 and (since-20)%65<8 and pulseKind[role] then
  viewer.pulse={kind=pulseKind[role],
    expiresAt=workspace:GetServerTimeNow()+1.3,serverVerified=true}
 end
 local marks=entityMarkers(p,mode,arena,root,viewer)
 table.insert(marks,{id="SELF",kind="SELF",ownerId=tostring(p.UserId),
   x=x,z=z,layer=layer})
 local visible=Intel.project(viewer,marks,workspace:GetServerTimeNow())
 local public={}
 for _,m in ipairs(visible) do
  if #public>=MAX_MARKERS then break end
  table.insert(public,m)
 end
 local explored={}
 for key,value in pairs(s.explored) do
  if value and #explored<MAX_VISIBLE_CELLS then table.insert(explored,key) end
 end
 -- Direct original authoritative V2 snapshot corrects stale ARMED player attrs
 -- after expiry without modifying the original Combat/Invul damage ownership.
 local realDefense=InvulRuntime.currentPolicySnapshot(p)
 local verifiedStatuses={}
 local character=p.Character
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 if humanoid then
  local nowClock=os.clock() -- same authoritative server clock as original Combat
  for _,entry in ipairs({
     {"EGGRUMBLE_BurnUntil","炎上"},
     {"EGGRUMBLE_SlowExpiry","減速"},
     {"EGGRUMBLE_MarkedUntil","標的"}
  }) do
   local expiry=humanoid:GetAttribute(entry[1])
   if type(expiry)=="number" and expiry==expiry and expiry>nowClock then
    table.insert(verifiedStatuses,entry[2])
   end
  end
 end
 local phase=realDefense.phase
 if phase~="ARMED" and phase~="AWAKENED" then phase="NONE" end
 local remain=tonumber(realDefense.remaining) or 0
 remain=math.min(12,math.max(0,remain))
 local defense={phase=phase,remaining=remain,
   spent=type(realDefense.spent)=="number" and realDefense.spent or 0,
   role=viewer.role}
 local bounds=arena:FindFirstChild("TacticalBattlefield")
 local terrain=nil
 if bounds and bounds:IsA("BasePart") then
  terrain={x=bounds.Position.X,z=bounds.Position.Z,
   width=bounds.Size.X,depth=bounds.Size.Z}
 end
 remote:FireClient(p,{
   kind="MAP_INTEL",version=1,mode=mode,role=viewer.role,
   layer=layer,cell=Intel.CELL,terrain=terrain,
   ownCastle=home.id,scanActive=viewer.pulse~=nil,defense=defense,
   statuses=verifiedStatuses,
   x=x,z=z,explored=explored,markers=public,serverTick=workspace:GetServerTimeNow(),
  })
end
local elapsed=0
local connection
connection=RunService.Heartbeat:Connect(function(dt)
 elapsed+=dt
 if elapsed<TICK then return end
 elapsed=0
 for _,p in ipairs(Players:GetPlayers()) do
  local ok,reason=pcall(send,p)
  if not ok then
   warn("[GQ828 MAP] server projection YELLOW:",reason)
   state[p]=nil
  end
 end
end)
Players.PlayerRemoving:Connect(function(p)state[p]=nil end)
