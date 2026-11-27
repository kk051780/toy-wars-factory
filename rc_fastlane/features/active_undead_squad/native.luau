-- The runner inserts the exact staged role rules, Game, squad and Horde damage bodies.
local vectorMethods={}
local vectorMT={}
function vectorMT.__index(v,key)
    if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
    if key=="Unit" then return v/v.Magnitude end
    return vectorMethods[key]
end
local Vector3={new=function(x,y,z)
    return setmetatable({X=x,Y=y,Z=z,kind="Vector3"},vectorMT)
end}
function vectorMT.__add(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function vectorMT.__sub(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
function vectorMT.__mul(a,n) return Vector3.new(a.X*n,a.Y*n,a.Z*n) end
function vectorMT.__div(a,n) return a*(1/n) end
function vectorMT.__unm(a) return a*(-1) end
function vectorMethods:Dot(b) return self.X*b.X+self.Y*b.Y+self.Z*b.Z end

local CFrame={
    new=function(p) return {Position=p} end,
    lookAt=function(p,to) return {Position=p,LookVector=(to-p).Unit} end,
}
local Color3={fromRGB=function(...) return {...} end}
local Enum={PartType={Block="Block",Ball="Ball"},RaycastFilterType={Exclude="Exclude"},
    Material={SmoothPlastic="SmoothPlastic"}}
local RaycastParams={new=function() return {} end}
local made={}
local Instance={}
function Instance.new(class)
    local item={ClassName=class,kind="Instance",Parent=nil}
    function item:Destroy() self.Parent=nil end
    function item:PivotTo(at) self.CFrame=at; self.moved=(self.moved or 0)+1 end
    function item:IsA(wanted) return wanted==self.ClassName or wanted=="BasePart" and self.ClassName=="Part" end
    function item:IsDescendantOf(ancestor)
        local p=self.Parent
        while p do if p==ancestor then return true end; p=p.Parent end
        return false
    end
    table.insert(made,item)
    return item
end
local nativeType=typeof
local function typeof(v)
    if type(v)=="table" and v.kind then return v.kind end
    return nativeType(v)
end

local time=100
local os={clock=function() return time end}
local pending={}
local function resume(thread)
    local ok,delay=coroutine.resume(thread)
    assert(ok,delay)
    if coroutine.status(thread)~="dead" then table.insert(pending,{thread=thread,due=time+delay}) end
end
local task={
    spawn=function(fn) resume(coroutine.create(fn)) end,
    wait=function(seconds) coroutine.yield(seconds) end,
    delay=function(seconds,fn)
        table.insert(pending,{thread=coroutine.create(fn),due=time+seconds})
    end,
}
local function advance(seconds)
    local finish=time+seconds
    while true do
        local index
        for i,e in ipairs(pending) do
            if e.due<=finish and (not index or e.due<pending[index].due) then index=i end
        end
        if not index then break end
        local event=table.remove(pending,index)
        time=math.max(time,event.due)
        resume(event.thread)
    end
    time=finish
end

local Players={}
local studio=true
local enabled=true
local RunService={IsStudio=function() return studio end}
local ServerStorage={GetAttribute=function() return enabled end}
local game={GetService=function(_,name)
    if name=="Players" then return Players end
    assert(name=="RunService",name)
    return RunService
end}
local map={model=Instance.new("Model")}
map.model.Parent=Instance.new("Folder")
local obstacle=Instance.new("Part")
local blocked=false
local wallX=nil
local workspace={Raycast=function(_,from,direction,_)
    local to=from+direction
    if blocked or wallX and (from.X<wallX)~=(to.X<wallX) then return {Instance=obstacle} end
    return nil
end}
local function horizontal(origin,target)
    local flat=Vector3.new(target.X-origin.X,0,target.Z-origin.Z)
    return (if flat.Magnitude>.001 then flat.Unit else Vector3.new(1,0,0)),flat.Magnitude
end
local function anchoredToWalkable(_,_,p) return p end
local Horde={}
local horde=setmetatable({round=1,folder=Instance.new("Folder"),mobs={},kills=0},{__index=Horde})
local Combat=(function()
__ACTIVE_COMBAT_RULES__
end)()
__ACTIVE_REAL_HORDE_HIT__

local Rules=(function()
__ACTIVE_S1_RULES__
end)()
local SevenJobs=(function()
__ACTIVE_SEVEN_JOBS_RULES__
end)()
SevenJobs.Undead=(function()
__ORIGINAL_UNDEAD_SQUAD__
end)()
local function newPlayer(id,team)
    local char=Instance.new("Model")
    char.Parent=map.model
    local root=Instance.new("Part")
    root.Parent=char
    root.Position=Vector3.new(0,3,0)
    root.CFrame={LookVector=Vector3.new(1,0,0)}
    local p={Parent=Players,team=team,Character=char,root=root,alive=true,UserId=id,attrs={}}
    function p:SetAttribute(key,value) self.attrs[key]=value end
    return p
end
local owner=newPlayer(101,"RED")
local enemy=newPlayer(102,"BLUE")
local function healthy(p) return p.alive,p.root end
local function getTeamName(p) return p.team end
local function serverNow() return time end
local match={phase="ACTIVE",serial=7}
local carry,slowed,lastSeq,sevenJobLastChoose,sevenJobLastUse={},{},{},{},{}
local sevenJobs={[owner]="NECROMANCER",[enemy]="NECROMANCER"}
local mobCombo,mobComboUntil,mobImpactSeq,mobLastHits,mobLastKOs,guideProgress={},{},{},{},{},{}
local First90Guide={mark=function() end}
local snapshots={}
local function snapshotFor(p) return {team=p.team} end
local remote={FireClient=function(_,p,s)
    assert(s.team==p.team)
    snapshots[p]=(snapshots[p] or 0)+1
end}
local function sevenJobFlash() end
__ACTIVE_REAL_GAME_SKILL__

local function addNeutral(x,hp)
    local m={hp=hp,maxHp=hp,home=Vector3.new(x,1.4,0),attackAt=0,model=Instance.new("Model"),
        elite=false,popup={},popupText={},body={},cue={}}
    m.pos=m.home
    m.model.Parent=horde.folder
    horde.mobs={m}
    return m
end
local function cast(p,seq)
    useSevenJob(p,{action="JOB_SKILL",seq=seq,job="WARRIOR",damage=2000})
end
local function scene(p)
    local folderName="P0D_UNDEAD_SQUAD_"..p.UserId
    local folders,bodies=0,0
    for _,item in ipairs(made) do
        if item.Name==folderName and item.Parent==map.model then folders+=1 end
        if item.Name and item.Name:match("^P0D_UNDEAD_SOLDIER_") and item.Parent
            and item.Parent.Name==folderName and item.Parent.Parent==map.model then
            assert(item.PrimaryPart.CanCollide==false and item.PrimaryPart.CanTouch==false
                and item.PrimaryPart.CanQuery==false)
            bodies+=1
        end
    end
    return folders,bodies
end
local function assertScene(p,expected)
    local folders,bodies=scene(p)
    assert(bodies==expected and folders==(if expected==0 then 0 else 1),
        ("expected %d bodies, got %d in %d folders"):format(expected,bodies,folders))
end

if __IS_BASELINE__ then
    local guard=addNeutral(5,60)
    cast(owner,1)
    assertScene(owner,0)
    assert(guard.hp==46 and snapshots[owner]==1)
    advance(1.61)
    assertScene(owner,0)
    assert(guard.hp==32)
    print("ACTIVE_UNDEAD_BASELINE_TWO_EFFECTS_NO_BODIES_PASS")
    return
end

local guard=addNeutral(5,30)
cast(owner,1)
assertScene(owner,3)
assert(owner.attrs.P0D_UndeadCommand=="ATTACK" and snapshots[owner]==1)
assert(guard.hp==16 and mobCombo[owner]==1)
advance(.21)
assert(guard.hp==0 and horde.kills==1 and mobLastKOs[owner]==1)
assert(mobCombo[enemy]==nil and snapshots[enemy]==nil)
advance(2)
assert(guard.hp==0 and horde.kills==1)
print("ACTIVE_UNDEAD_THREE_REAL_BODIES_OWNER_HP_KO_PASS")

cast(owner,1)
cast(owner,2)
assertScene(owner,3)
assert(snapshots[owner]==1 and owner.attrs.P0D_UndeadCommand=="ATTACK")
advance(16)
cast(owner,3)
assert(snapshots[owner]==2 and owner.attrs.P0D_UndeadCommand=="GUARD")
assertScene(owner,3)
advance(18.1)
cast(owner,4)
assert(snapshots[owner]==3 and owner.attrs.P0D_UndeadCommand=="FOLLOW")
assertScene(owner,3)
guard=addNeutral(5,45)
advance(3)
assert(guard.hp==45)
advance(9)
assertScene(owner,0)
assert(owner.attrs.P0D_UndeadCommand==nil)
print("ACTIVE_UNDEAD_COMMAND_COOLDOWN_FOLLOW_AND_CAP_PASS")

local nextSeq=10
local function freshCast()
    advance(19)
    nextSeq+=1
    cast(owner,nextSeq)
    assertScene(owner,3)
end
blocked=true
guard=addNeutral(6,45)
freshCast()
advance(2)
assert(guard.hp==45)
blocked=false
advance(1.7)
assert(guard.hp<45,"AUTHOR_CENTER_OVERLAP")
print("ACTIVE_UNDEAD_WALL_BLOCKS_AND_CLEARED_SPACE_HITS_PASS")
SevenJobs.Undead.clear(owner)
wallX=2
guard=addNeutral(6,64)
freshCast()
for _,item in ipairs(made) do
    if item.Name and item.Name:match("^P0D_UNDEAD_SOLDIER_") and item.Parent
        and item.Parent.Parent==map.model then assert(item.CFrame.Position.X<wallX) end
end
advance(.21)
assert(guard.hp==64,"SPAWN_CROSSED_BLOCKING_GATE")
wallX=nil
advance(2)
assert(guard.hp<64)
print("ACTIVE_UNDEAD_SPAWN_STAYS_ON_OWNER_SIDE_OF_GATE_PASS")

local oldContainer
for _,item in ipairs(made) do
    if item.Name=="P0D_UNDEAD_SQUAD_"..owner.UserId and item.Parent==map.model then oldContainer=item end
end
assert(oldContainer~=nil)
time+=48.01 -- The old task is due, but the next Remote can run first.
nextSeq+=1
cast(owner,nextSeq)
assert(oldContainer.Parent==nil and owner.attrs.P0D_UndeadCommand=="ATTACK")
assertScene(owner,3)
advance(.21)
assertScene(owner,3)
print("ACTIVE_UNDEAD_EXPIRED_RECAST_REPLACES_STALE_SQUAD_PASS")

local cases={
    {function() carry[owner]="BLUE" end,function() carry[owner]=nil end},
    {function() slowed[owner]=true end,function() slowed[owner]=nil end},
    {function() owner.alive=false end,function() owner.alive=true end},
    {function() owner.team="NONE" end,function() owner.team="RED" end},
    {function() studio=false end,function() studio=true end},
    {function() enabled=false end,function() enabled=true end},
    {function() match.phase="RESULTS" end,function() match.phase="ACTIVE" end},
    {function() owner.Parent=nil end,function() owner.Parent=Players end},
    {function() match.serial+=1 end,function() end},
    {function() sevenJobLastChoose[owner]=time end,function() end},
    {function() sevenJobs[owner]="WARRIOR" end,function() sevenJobs[owner]="NECROMANCER" end},
    {function() owner.Character=Instance.new("Model") end,function() end},
}
for _,c in ipairs(cases) do
    c[1]()
    local healthBefore=guard.hp
    advance(.21)
    assertScene(owner,0)
    assert(guard.hp==healthBefore)
    c[2]()
    freshCast()
end
SevenJobs.Undead.clear(owner)
assertScene(owner,0)
advance(1)
assertScene(owner,0)
print("ACTIVE_UNDEAD_12_BOUNDARIES_NO_STALE_DAMAGE_PASS")

local denied={
    {function() carry[owner]="BLUE" end,function() carry[owner]=nil end},
    {function() slowed[owner]=true end,function() slowed[owner]=nil end},
    {function() owner.alive=false end,function() owner.alive=true end},
    {function() owner.team="NONE" end,function() owner.team="RED" end},
    {function() studio=false end,function() studio=true end},
    {function() enabled=false end,function() enabled=true end},
    {function() match.phase="LOBBY" end,function() match.phase="ACTIVE" end},
}
advance(19)
local before=snapshots[owner]
for _,c in ipairs(denied) do
    c[1]()
    nextSeq+=1
    cast(owner,nextSeq)
    assertScene(owner,0)
    assert(snapshots[owner]==before)
    c[2]()
end
cast(owner,nextSeq)
assertScene(owner,0)
freshCast()
cast(enemy,1)
assertScene(enemy,3)
SevenJobs.Undead.clear(owner)
assertScene(enemy,3)
SevenJobs.Undead.clear(enemy)
assertScene(owner,0)
assertScene(enemy,0)
print("ACTIVE_UNDEAD_INVALID_CASTS_AND_OWNER_ISOLATION_PASS")
