--!nonstrict
-- Single server-only EGGRUMBLE map presenter: no combat, store, item or HP authority.
-- Sends only already-filtered map data through one-way map RemoteEvent.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Intel=require(script.Parent:WaitForChild("EGGRUMBLE_MapVisibilityPolicy"))
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
    table.insert(castles,{id=m.Name,kind="CASTLE",x=foundation.Position.X,
     z=foundation.Position.Z,layer="LAND",ownerId=string.sub(m.Name,8)})
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
 -- Unknown TEAM affiliation is deliberately not interpreted as enemy.
 -- TEAM server authority must publish verified team attributes first.
 local pteam=p:GetAttribute("EGGRUMBLE_MapVerifiedTeam")
 local ownTeam=mode=="BATTLE_ROYALE" and ("BR_"..p.UserId) or pteam
 if mode=="BATTLE_ROYALE" or (pteam=="RED" or pteam=="BLUE") then
  for _,other in ipairs(Players:GetPlayers()) do
   if other~=p and other:GetAttribute("EGGRUMBLE_QueuedMode")==mode then
    local theirTeam=mode=="BATTLE_ROYALE" and ("BR_"..other.UserId)
      or other:GetAttribute("EGGRUMBLE_MapVerifiedTeam")
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
    end
   end
  end
 end
 -- Future realm actors / neutral sources must be validated by their owners
 -- before joining this list. Never infer unrevealed map coordinates locally.
 return result
end
local function send(p)
 local mode,arena=ownScene(p)
 local root=rootOf(p)
 if not mode or not root then
  state[p]=nil
  return
 end
 local castles=findCastles(arena)
 local home=ownCastle(castles,p)
 if not home then return end
 local s=state[p]
 if not s or s.arena~=arena or s.mode~=mode then
  -- Do not initialize while the user is still in the lobby.
  local dx=root.Position.X-home.x
  local dz=root.Position.Z-home.z
  if dx*dx+dz*dz>150*150 then return end
  s={mode=mode,arena=arena,explored=Intel.newExploration(home.x,home.z),
      lastX=root.Position.X,lastZ=root.Position.Z,lastLayer="LAND"}
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
 local viewer={playerId=tostring(p.UserId),team=mode=="BATTLE_ROYALE"
       and ("BR_"..p.UserId) or p:GetAttribute("EGGRUMBLE_MapVerifiedTeam"),
     role=getRole(p),x=x,z=z,layer=layer,explored=s.explored,serverVerified=true}
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
 local bounds=arena:FindFirstChild("TacticalBattlefield")
 local terrain=nil
 if bounds and bounds:IsA("BasePart") then
  terrain={x=bounds.Position.X,z=bounds.Position.Z,
   width=bounds.Size.X,depth=bounds.Size.Z}
 end
 remote:FireClient(p,{
   kind="MAP_INTEL",version=1,mode=mode,role=viewer.role,
   layer=layer,cell=Intel.CELL,terrain=terrain,
   ownCastle=home.id,
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
