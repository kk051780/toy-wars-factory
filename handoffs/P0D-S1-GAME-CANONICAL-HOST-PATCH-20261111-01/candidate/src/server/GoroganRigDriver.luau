--!strict
-- Server-only physical rig and path navigator for ALREADY approved Gorogan AI.
-- Not an event chooser, client visual, Humanoid damage source, or drop-in Roblox patch.
local PathfindingService = game:GetService("PathfindingService")
local Driver = {}
Driver.__index = Driver
local MAX_LIFETIME=14
local MAX_NAV=20
local NAV_MIN_GAP=.75
local MAX_DIRECT_STEP=8
local MAX_LEASH=42
local MAX_WAYPOINTS=16
local function validId(x)
    return type(x)=="string" and #x>=1 and #x<=64 and x:match("^[%w_-]+$")~=nil
end
local function finite(x)
    return type(x)=="number" and x==x and x~=-math.huge and x~=math.huge
end
local function goodVector(v)
    return typeof(v)=="Vector3" and finite(v.X) and finite(v.Y) and finite(v.Z)
        and math.abs(v.X)<=2048 and v.Y>=-100 and v.Y<=700 and math.abs(v.Z)<=2048
end
local function nearXZ(a,b,r)
    local d=Vector2.new(a.X-b.X,a.Z-b.Z)
    return d:Dot(d)<=r*r
end
local function addPart(model, name, size, color, initialCFrame, canCollide)
    local part=Instance.new("Part")
    part.Name=name;part.Size=size;part.Color=color
    part.Anchored=true;part.CanCollide=canCollide;part.CanTouch=false;part.CastShadow=true
    part.CFrame=initialCFrame;part.Parent=model
    return part
end
local function motor(parent,name,from,to,c0,c1)
    local m=Instance.new("Motor6D")
    m.Name=name;m.Part0=from;m.Part1=to;m.C0=c0;m.C1=c1;m.Parent=parent
    return m
end
function Driver.new(deps)
    assert(type(deps)=="table" and deps.integrationApproved==true,
        "DISABLED_UNTIL_OWNER_PC_REVIEW")
    for _,name in ipairs({"currentRound","isEventActive","isValidStageAnchor","isSafeTerrain"}) do
        assert(type(deps[name])=="function",name)
    end
    assert(typeof(deps.serverOnlyFolder)=="Instance" and deps.serverOnlyFolder:IsA("Folder")
        and deps.serverOnlyFolder:IsDescendantOf(workspace),
        "SERVER_ONLY_PARENT_REQUIRED")
    local self=setmetatable({deps=deps,model=nil,humanoid=nil,root=nil,roundId=nil,
        eventId=nil,spawnAt=0,lastNav=-math.huge,navCount=0,busy=false,closed=true,seenRounds={},seenCount=0},Driver)
    return self
end
local function eventLive(self)
    return not self.closed and self.roundId~=nil and self.eventId~=nil
        and self.deps.currentRound()==self.roundId
        and self.deps.isEventActive(self.roundId,self.eventId)==true
end
local function teardown(self)
    self.closed=true;self.busy=false
    local rig=self.model;self.model=nil;self.humanoid=nil;self.root=nil
    self.roundId=nil;self.eventId=nil
    if rig then rig:Destroy() end
end
function Driver:stop(roundId,eventId)
    if self.closed then return false,"ALREADY_CLOSED" end
    if roundId~=self.roundId or eventId~=self.eventId then return false,"STALE_STOP" end
    teardown(self)
    return true,"STOPPED"
end
function Driver:start(snapshot)
    if not self.closed then return false,"ALREADY_ACTIVE" end
    if type(snapshot)~="table" or not validId(snapshot.roundId) or not validId(snapshot.eventId)
        or (snapshot.stageId~="S1" and snapshot.stageId~="S3")
        or not goodVector(snapshot.groundPosition) or not finite(snapshot.now)
        or snapshot.now<0 or snapshot.now>1e12 or self.deps.currentRound()~=snapshot.roundId
        or self.deps.isEventActive(snapshot.roundId,snapshot.eventId)~=true
        or self.deps.isValidStageAnchor(snapshot.stageId,snapshot.groundPosition)~=true
        or self.deps.isSafeTerrain(snapshot.groundPosition)~=true
        or self.seenRounds[snapshot.roundId] or self.seenCount>=128 then
        return false,"INVALID_SERVER_ACTIVATION"
    end
    -- Build an R6-shaped animated physical rig. The previously delivered D07 client
    -- visual is a SEPARATE local display and must not be parented to this rig.
    local origin=snapshot.groundPosition+Vector3.new(0,5.5,0)
    local model=Instance.new("Model")
    model.Name="Gorogan_ServerRig"
    local stone=Color3.fromRGB(103,112,105)
    local root=addPart(model,"HumanoidRootPart",Vector3.new(2,2,1),stone,CFrame.new(origin),false)
    root.Transparency=1
    local torso=addPart(model,"Torso",Vector3.new(5,6,3),stone,CFrame.new(origin),true)
    local head=addPart(model,"Head",Vector3.new(3,3,3),stone,CFrame.new(origin+Vector3.new(0,4.5,0)),false)
    local la=addPart(model,"Left Arm",Vector3.new(2.5,6,2.5),stone,CFrame.new(origin+Vector3.new(-3.7,-.6,0)),false)
    local ra=addPart(model,"Right Arm",Vector3.new(2.7,6,2.7),stone,CFrame.new(origin+Vector3.new(3.7,-.6,0)),false)
    local ll=addPart(model,"Left Leg",Vector3.new(2.6,6,2.6),stone,CFrame.new(origin+Vector3.new(-1.4,-5.2,0)),true)
    local rl=addPart(model,"Right Leg",Vector3.new(2.6,6,2.6),stone,CFrame.new(origin+Vector3.new(1.4,-5.2,0)),true)
    motor(root,"RootJoint",root,torso,CFrame.new(),CFrame.new())
    motor(torso,"Neck",torso,head,CFrame.new(0,3,0),CFrame.new(0,-1.5,0))
    motor(torso,"Left Shoulder",torso,la,CFrame.new(-3,2,0),CFrame.new(0,2.6,0))
    motor(torso,"Right Shoulder",torso,ra,CFrame.new(3,2,0),CFrame.new(0,2.6,0))
    motor(torso,"Left Hip",torso,ll,CFrame.new(-1.4,-3,0),CFrame.new(0,2.2,0))
    motor(torso,"Right Hip",torso,rl,CFrame.new(1.4,-3,0),CFrame.new(0,2.2,0))
    local hum=Instance.new("Humanoid")
    hum.Name="Humanoid";hum.RigType=Enum.HumanoidRigType.R6
    hum.MaxHealth=180;hum.Health=180;hum.WalkSpeed=10;hum.JumpPower=0
    hum.BreakJointsOnDeath=false;hum.Parent=model
    model.PrimaryPart=root
    -- Parent after all joints are defined. Entire rig was anchored while assembled.
    model.Parent=self.deps.serverOnlyFolder
    model:PivotTo(CFrame.new(origin))
    for _,part in ipairs(model:GetDescendants()) do
        if part:IsA("BasePart") then part.Anchored=false end
    end
    local ok=pcall(function()root:SetNetworkOwner(nil)end)
    if not ok then model:Destroy();return false,"NETWORK_OWNER_NOT_SERVER" end
    self.model=model;self.humanoid=hum;self.root=root
    self.roundId=snapshot.roundId;self.eventId=snapshot.eventId
    self.spawnAt=snapshot.now;self.lastNav=-math.huge;self.navCount=0
    self.busy=false;self.closed=false
    self.seenRounds[snapshot.roundId]=true;self.seenCount+=1
    return true,"RIG_READY"
end
function Driver:getPosition()
    if not eventLive(self) or not self.root or not self.root.Parent then return nil end
    local p=self.root.Position
    if not goodVector(p) then return nil end
    return {x=p.X,y=p.Y,z=p.Z}
end
function Driver:requestNavigation(position,reason,now)
    if not eventLive(self) or not self.root or not self.humanoid
        or self.humanoid.Health<=0 then return false,"INACTIVE" end
    if not finite(now) or now<self.spawnAt or now-self.spawnAt>=MAX_LIFETIME
        or now<self.lastNav then return false,"INVALID_TIME" end
    if self.busy then return false,"BUSY" end
    if now-self.lastNav<NAV_MIN_GAP then return false,"RATE_LIMIT" end
    if self.navCount>=MAX_NAV then return false,"NAV_BUDGET" end
    if type(position)~="table" or not finite(position.x) or not finite(position.y)
        or not finite(position.z) then return false,"INVALID_POSITION" end
    if reason~="CHASE" and reason~="LEASH_RETURN" then return false,"INVALID_REASON" end
    local goal=Vector3.new(position.x,position.y,position.z)
    local here=self.root.Position
    if not goodVector(goal) or not nearXZ(here,goal,MAX_DIRECT_STEP+.1) and reason=="CHASE" then
        return false,"TOO_FAR"
    end
    if self.deps.isSafeTerrain(goal)~=true then return false,"UNSAFE_NAV_TARGET" end
    self.busy=true;self.navCount+=1;self.lastNav=now
    local thisRound,thisEvent=self.roundId,self.eventId
    -- ComputeAsync can yield. All authoritative identity/round checks must be repeated.
    local path=PathfindingService:CreatePath({AgentRadius=3,AgentHeight=10,
        AgentCanJump=false,WaypointSpacing=4})
    local ok=pcall(function()path:ComputeAsync(here,goal)end)
    local canUse=ok and path.Status==Enum.PathStatus.Success
    local waypoint=nil
    if canUse then
        local points=path:GetWaypoints()
        if #points>=2 and #points<=MAX_WAYPOINTS then waypoint=points[2].Position end
    end
    local stillValid=eventLive(self) and thisRound==self.roundId and thisEvent==self.eventId
        and self.humanoid~=nil and self.humanoid.Health>0
        and finite(now) and (self.deps.currentRound()==thisRound)
    self.busy=false
    if not stillValid then return false,"STALE_AFTER_YIELD" end
    if self.root==nil or not nearXZ(here,self.root.Position,MAX_DIRECT_STEP+2) then
        return false,"RIG_MOVED_DURING_PATH"
    end
    if not waypoint or not goodVector(waypoint) or not nearXZ(self.root.Position,waypoint,MAX_DIRECT_STEP+2)
        or self.deps.isSafeTerrain(waypoint)~=true then return false,"PATH_BLOCKED" end
    self.humanoid:MoveTo(waypoint)
    return true,"MOVE_TO_NEXT_WAYPOINT"
end
function Driver:checkLifetime(now)
    if self.closed then return false,"INACTIVE" end
    if not finite(now) or now<self.spawnAt then return false,"BAD_TIME" end
    if now-self.spawnAt>=MAX_LIFETIME or not eventLive(self)
        or not self.humanoid or self.humanoid.Health<=0 then
        teardown(self);return true,"CLEANED_UP"
    end
    return false,"ACTIVE"
end
return Driver
