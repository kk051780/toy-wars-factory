local Blink=SevenJobs.Blink
assert(Blink.config.id=="NINJA-031" and Blink.config.cd==16 and Blink.config.energy==30)
assert(table.concat(Blink.config.metrics[1].values,",")=="5,7,9,11,13")
assert(table.concat(Blink.config.metrics[2].values,",")=="0.18,0.18,0.18,0.18,0.18")
local arena=Instance.new("Part")
arena.Name="GrassArena"
arena.Parent=map.model
arena.Position=Vector3.new(0,-3,0)
arena.Size=Vector3.new(250,4,142)
arena.Anchored=true
arena.CanCollide=true
function map.model:FindFirstChild(name) if name=="GrassArena" then return arena end end
local wall=nil
local lowOnly=false
local ground=true
local groundNormal=1
local occupied=false
local bodyHitDistance=nil
local paramsSeen
function workspace:Raycast(from,direction,params)
    paramsSeen=params
    if direction.Y<0 and from.Y+direction.Y<=-1 then
        if not ground then return nil end
        local position=Vector3.new(from.X,-1,from.Z)
        return {Position=position,Instance=arena,Normal=Vector3.new(0,groundNormal,0)}
    end
    if wall and (not lowOnly or from.Y<1.1) and from.X<wall and from.X+direction.X>=wall then
        return {Distance=(wall-from.X)/direction.X*direction.Magnitude,Instance=obstacle}
    end
    return nil
end
function workspace:GetPartBoundsInBox(_,_,args)
    assert(args.RespectCanCollide==true and args.FilterDescendantsInstances[1]==owner.Character)
    return if occupied then {obstacle} else {}
end
function workspace:Blockcast(_,size,direction,params)
    assert(size.X==3.2 and params.RespectCanCollide and direction.Magnitude>=3)
    return if bodyHitDistance then {Distance=bodyHitDistance,Instance=obstacle} else nil
end
local others={}
function Players:GetPlayers() return others end
local function place(x,y,z)
    local position=Vector3.new(x,y,z)
    owner.root.Position=position
    owner.root.CFrame=setmetatable({Position=position,LookVector=Vector3.new(1,0,0)},frameMT)
    owner.root.AssemblyLinearVelocity=Vector3.zero
end
local function near(a,b)
    return math.abs(a-b)<1e-6
end
local function sample(state)
    SevenJobs.Growth.sample(state,match.serial,time,owner.Character,owner.root.Position,19)
end
local function warnings()
    local count=0
    for _,part in ipairs(made) do
        if part.Parent==map.model and part.Name=="P0D_NINJA_BLINK_WARNING" then
            assert(part.CanCollide==false and part.CanQuery==false and part.CanTouch==false)
            count+=1
        end
    end
    return count
end
local function ninja(seq)
    useSevenJob(owner,{action="JOB_SKILL",seq=seq,position=Vector3.new(80,2,80),range=900})
end

place(0,2,0)
owner.hum={WalkSpeed=19,FloorMaterial=Enum.Material.SmoothPlastic}
sevenJobs[owner]="NINJA"
sevenJobLastChoose[owner]=99
local state=SevenJobs.Growth.new(match.serial)
SevenJobs.GrowthStates[owner]=state
growthHud(growthSnapshot(owner))
assert(not jobCast.Active and jobCast.Text=="瞬歩\n準備中")
ninja(1)
assert(warnings()==0 and state.energy==100)
sample(state)
growthHud(growthSnapshot(owner))
assert(jobCast.Active and jobCast.Text=="瞬歩 S0\nQ  E100")
owner.hum.SeatPart=obstacle
ninja(2)
growthHud(growthSnapshot(owner))
assert(not jobCast.Active and warnings()==0 and state.energy==100)
owner.hum.SeatPart=nil
owner.hum.FloorMaterial=Enum.Material.Air
ninja(3)
assert(warnings()==0 and state.energy==100)
owner.hum.FloorMaterial=Enum.Material.SmoothPlastic
ninja(4)
assert(warnings()==1 and state.energy==70 and growthSnapshot(owner).jobCooldown==16)
advance(.179)
assert(owner.root.CFrame.Position.X==0 and warnings()==1)
advance(.002)
assert(near(owner.root.CFrame.Position.X,5) and owner.root.CFrame.Position.Z==0 and warnings()==0)
assert(near(owner.root.AssemblyLinearVelocity.Magnitude,0) and paramsSeen.RespectCanCollide)
assert(snapshots[owner]==1 and state.actionAt~=nil)
ninja(4)
assert(snapshots[owner]==1 and warnings()==0 and state.energy==70)
print("ACTIVE_NINJA_031_AUTHENTIC_Q_018_TELL_MOVES_AND_CHARGES_ONCE_PASS")

-- Exact donor-like body sweeps: low obstruction may be missed by the centre ray.
local origin=Vector3.new(0,2,0)
local forward=Vector3.new(1,0,0)
wall=8;lowOnly=true
local stopped=Blink.landing(arena,owner.Character,origin,forward,13)
assert(stopped and near(stopped.X,5))
wall=2
assert(Blink.landing(arena,owner.Character,origin,forward,13)==nil)
wall=nil
bodyHitDistance=2.8
assert(Blink.landing(arena,owner.Character,origin,forward,13)==nil)
bodyHitDistance=7.35
assert(near(assert(Blink.landing(arena,owner.Character,origin,forward,13)).X,7))
bodyHitDistance=nil
ground=false
assert(Blink.landing(arena,owner.Character,origin,forward,13)==nil)
ground=true;groundNormal=.40
assert(Blink.landing(arena,owner.Character,origin,forward,13)==nil)
groundNormal=1;occupied=true
assert(Blink.landing(arena,owner.Character,origin,forward,13)==nil)
occupied=false
assert(Blink.landing(arena,owner.Character,Vector3.new(118,2,0),forward,5)==nil)
local run=Vector3.new(6,0,6)
local pre=Blink.direction(forward,run,19,1)
local angled=Blink.direction(forward,run,19,2)
assert(pre==nil and angled and near(angled.Z,math.sin(math.rad(45))))
assert(Blink.direction(forward,run*10,19,4)==nil)
assert(Blink.direction(forward,Vector3.new(-6,0,1),19,4)==nil)
print("ACTIVE_NINJA_031_SAFE_SWEEP_FLOOR_OVERLAP_BOUNDS_AND_ANGLE_PASS")

local seq=4
local attempts={
    {function() carry[owner]="BLUE" end,function() carry[owner]=nil end},
    {function() slowed[owner]=true end,function() slowed[owner]=nil end},
    {function() owner.alive=false end,function() owner.alive=true end},
    {function() match.phase="RESULTS" end,function() match.phase="ACTIVE" end},
    {function() match.serial+=1 end,function() match.serial-=1 end},
    {function() owner.Character=Instance.new("Model") end,function() end},
    {function() blinkFlag=false end,function() blinkFlag=true end},
    {function() owner.hum.SeatPart=obstacle end,function() owner.hum.SeatPart=nil end},
    {function() owner.hum.FloorMaterial=Enum.Material.Air end,
        function() owner.hum.FloorMaterial=Enum.Material.SmoothPlastic end},
    {function() place(20,2,0) end,function() end},
    {function() place(0,2,3.8) end,function() end},
    {function() enemy.root.Position=Vector3.new(5,2,0);others={enemy} end,function() others={} end},
}
for _,case in ipairs(attempts) do
    advance(18)
    place(0,2,0)
    state.energy=100
    sample(state)
    seq+=1
    ninja(seq)
    assert(warnings()==1)
    case[1]()
    local expected=owner.root.CFrame.Position
    advance(.181)
    assert(warnings()==0 and (owner.root.CFrame.Position-expected).Magnitude==0)
    case[2]()
end
advance(18)
place(0,2,0)
state.activeSeconds=90
state.energy=100
sample(state)
local previousSnapshot=snapshots[owner]
owner.root.AssemblyLinearVelocity=Vector3.new(0,0,19)
growthHud(growthSnapshot(owner))
assert(not jobCast.Active)
seq+=1
ninja(seq)
assert(warnings()==0 and state.energy==100 and snapshots[owner]==previousSnapshot)
local angle=math.rad(55)
local diagonal=Vector3.new(math.cos(angle),0,math.sin(angle))
owner.root.AssemblyLinearVelocity=diagonal*19
growthHud(growthSnapshot(owner))
assert(jobCast.Active)
seq+=1
ninja(seq)
assert(warnings()==1 and state.energy==70)
advance(.179)
local walked=diagonal*.179*19
place(walked.X,2,walked.Z)
advance(.002)
assert(warnings()==0 and (owner.root.CFrame.Position-(Vector3.new(0,2,0)+walked+diagonal*9)).Magnitude<1e-6)

-- The previous legacy Ninja Q still shares this round's accepted-use fence.
advance(20)
place(0,2,0)
state.energy=100
sample(state)
blinkFlag=false
local prior=addNeutral(9,64)
local offAt=time
seq+=1
ninja(seq)
assert(prior.hp<64 and warnings()==0 and state.energy==100)
local offSnapshots=snapshots[owner]
blinkFlag=true
for _,seconds in ipairs({.1,15.999}) do
    time=offAt+seconds
    sample(state)
    seq+=1
    ninja(seq)
    assert(warnings()==0 and snapshots[owner]==offSnapshots and state.energy==100)
end
time=offAt+16
sample(state)
seq+=1
ninja(seq)
assert(warnings()==1 and snapshots[owner]==offSnapshots+1 and state.energy==70)
advance(.181)
assert(warnings()==0)
print("ACTIVE_NINJA_031_STALE_LIFE_EPOCH_CARRY_BOUND_AND_OCCUPIED_REJECT_PASS")
