-- Exact staged Roblox Luau bodies with a small, deterministic test scene.
local vectorMT={}
local Vector3={new=function(x,y,z) return setmetatable({X=x,Y=y,Z=z},vectorMT) end}
function vectorMT.__add(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
local Color3={fromRGB=function(...) return {...} end}
local Config=(function()
__ACTIVE_CONFIG__
end)()
local Rules=(function()
__ACTIVE_S1_RULES__
end)()
local WindRules=(function()
__ACTIVE_WIND_RULES__
end)()
local player={Character={}}
local now=100
local snapshots,rays=0,0
local match={phase="ACTIVE"}
local alive,studio,enabled,team=true,true,true,"BLUE"
local hum={WalkSpeed=15}
local root={Position=Vector3.new(2,5,-4)}
local roles={[player]="GUARDIAN"}
local sevenJobs={[player]="NINJA"}
local lastSeq,lastWind,windUntil,carry,slowed,windHighlight={},{},{},{},{},{}
local RunService={IsStudio=function() return studio end}
local ServerStorage={GetAttribute=function() return enabled end}
local function getTeamName() return team end
local function healthy() return alive,root,hum end
local function serverNow() return now end
local function broadcast() snapshots+=1 end
local RaycastParams={new=function() return {} end}
local Enum={RaycastFilterType={Exclude="Exclude"},HighlightDepthMode={Occluded="Occluded"}}
local Instance={new=function()
    return {Destroy=function(self) self.Parent=nil; self.destroyed=true end}
end}
local ground={Anchored=true,CanCollide=true,IsA=function(_,name) return name=="BasePart" end}
local floor={Normal={Y=1},Instance=ground}
local workspace={Raycast=function(_,from,delta,params)
    assert(from.Y==root.Position.Y+1 and delta.Y==-8 and params.FilterDescendantsInstances[1]==player.Character)
    rays+=1
    return floor
end}
__ACTIVE_STOP_WIND__
__ACTIVE_APPLY_WIND__
local function cleanup(now)
__ACTIVE_WIND_CLEANUP__
end

local trapButton,windButton,relayButton={},{},{}
local UDim2={new=function(x,dx,y,dy) return {x=x,dx=dx,y=y,dy=dy} end}
local function show(s,currentNetBound)
__ACTIVE_WIND_HUD__
end
local function intent(seq)
    applyWind(player,{action="WIND_BURST",seq=seq,role="RAIDER",speed=900,x=0,y=2,z=0})
end
local function view(role,job,carries,bound)
    show({phase=match.phase,role=role,job=job,jobStudioPvE=enabled and studio,
        carrying=if carries then "RED" else "",windCooldown=0,trapCooldown=0},bound)
end
if __IS_BASELINE__ then
    intent(1)
    view("GUARDIAN","NINJA",false,false)
    assert(snapshots==0 and hum.WalkSpeed==15 and windButton.Visible==false)
    roles[player]="RAIDER"
    intent(2)
    assert(snapshots==1 and hum.WalkSpeed==27)
    print("ACTIVE_WIND_BASELINE_NINJA_MISSING_LEGACY_RAIDER_PASS")
    return
end

intent(1)
assert(hum.WalkSpeed==27 and windUntil[player]==102.5 and lastWind[player]==100 and snapshots==1 and rays==1)
assert(windHighlight[player].Name=="S1_RAIDER_WIND_SERVER_TELL" and windHighlight[player].Parent==player.Character)
now=102.499
cleanup(now)
assert(hum.WalkSpeed==27)
local old=windHighlight[player]
now=102.5
cleanup(now)
assert(hum.WalkSpeed==15 and old.destroyed and windUntil[player]==nil)
now=117.999
intent(2)
assert(snapshots==1)
now=118
intent(2)
assert(snapshots==1)
intent(3)
assert(snapshots==2 and hum.WalkSpeed==27)
now=119
carry[player]="RED"
cleanup(now)
assert(hum.WalkSpeed==15)
carry[player]=nil
print("ACTIVE_WIND_NINJA_27_2P5_18_AND_REAL_CLEANUP_PASS")

now=140
local denied={
    {function() studio=false end,function() studio=true end},
    {function() enabled=false end,function() enabled=true end},
    {function() team="NONE" end,function() team="BLUE" end},
    {function() alive=false end,function() alive=true end},
    {function() match.phase="LOBBY" end,function() match.phase="ACTIVE" end},
    {function() carry[player]="BLUE" end,function() carry[player]=nil end},
    {function() slowed[player]=true end,function() slowed[player]=nil end},
    {function() sevenJobs[player]="MAGE" end,function() sevenJobs[player]="NINJA" end},
    {function() root.Position=Vector3.new(121,5,0) end,function() root.Position=Vector3.new(2,5,-4) end},
    {function() root.Position=Vector3.new(2,13,0) end,function() root.Position=Vector3.new(2,5,-4) end},
}
for i,arm in ipairs(denied) do
    arm[1]()
    intent(10+i)
    assert(snapshots==2 and hum.WalkSpeed==15)
    arm[2]()
end
assert(rays==2)
local hit=floor
local floors={
    {function() floor=nil end,function() floor=hit end},
    {function() floor.Normal.Y=.64 end,function() floor.Normal.Y=1 end},
    {function() ground.CanCollide=false end,function() ground.CanCollide=true end},
    {function() ground.Anchored=false end,function() ground.Anchored=true end},
}
for i,arm in ipairs(floors) do
    arm[1]()
    intent(30+i)
    assert(snapshots==2 and hum.WalkSpeed==15)
    arm[2]()
end
intent(34)
assert(snapshots==2 and rays==6)
print("ACTIVE_WIND_AUTHORITY_RANGE_FLOOR_AND_REPLAY_NEGATIVES_PASS")

view("GUARDIAN","NINJA",false,false)
assert(windButton.Visible and windButton.Active and trapButton.Visible and windButton.Position.dx==-265)
view("GUARDIAN","NINJA",true,false)
assert(not windButton.Visible and not windButton.Active)
view("GUARDIAN","NINJA",false,true)
assert(windButton.Visible and not windButton.Active)
view("GUARDIAN","MAGE",false,false)
assert(trapButton.Visible and not windButton.Visible)
view("RAIDER","MAGE",false,false)
assert(windButton.Visible and windButton.Active and not trapButton.Visible and windButton.Position.dx==-140)
studio=false
floor=nil
roles[player]="RAIDER"
intent(45)
assert(snapshots==3 and hum.WalkSpeed==27 and rays==6)
print("ACTIVE_WIND_DUAL_LAYOUT_AND_LEGACY_RAIDER_PASS")
