local function sample(state,now,p)
    SevenJobs.Growth.sample(state,state.round,now,p.Character,p.root.Position,19)
end

local Growth=SevenJobs.Growth
local clock=Growth.new(99)
local roleOwner=newPlayer(201,"RED")
sample(clock,100,roleOwner)
sample(clock,100.5,roleOwner)
assert(clock.activeSeconds==0 and Growth.stage(clock)==0)
Growth.markAction(clock,99,100.75,roleOwner.Character)
sample(clock,101,roleOwner)
assert(clock.activeSeconds==.25)
Growth.markAction(clock,98,101.25,roleOwner.Character)
sample(clock,101.5,roleOwner)
assert(clock.activeSeconds==.75)
local diedWith=clock.activeSeconds
Growth.pause(clock)
sample(clock,110,roleOwner)
assert(clock.activeSeconds==diedWith and clock.actionAt==nil)
local previousAvatar=roleOwner.Character
roleOwner.Character=Instance.new("Model")
sample(clock,110.5,roleOwner)
Growth.markAction(clock,99,110.75,previousAvatar)
sample(clock,111,roleOwner)
assert(clock.activeSeconds==diedWith and clock.actionAt==nil)
roleOwner.root.Position=Vector3.new(200,3,0)
sample(clock,111.5,roleOwner)
assert(clock.activeSeconds==diedWith)
roleOwner.root.Position=Vector3.new(200.6,3,0)
sample(clock,114,roleOwner)
assert(clock.activeSeconds==diedWith)
roleOwner.root.Position=Vector3.new(201.2,3,0)
sample(clock,114.5,roleOwner)
assert(clock.activeSeconds==diedWith and clock.sampledAt==nil)
roleOwner.root.Position=Vector3.new(125,3,0)
sample(clock,115,roleOwner)
assert(clock.activeSeconds==diedWith)
roleOwner.root.Position=Vector3.new(125.6,3,0)
sample(clock,115.5,roleOwner)
assert(clock.activeSeconds==diedWith+.5)
print("ROLE_GROWTH_ACTIVITY_AFK_RESPAWN_TELEPORT_EPOCH_PASS")

local walk=Growth.new(7)
local p=newPlayer(202,"BLUE")
sample(walk,0,p)
for i=1,360 do
    p.root.Position=Vector3.new((i%2)*.6,3,0)
    sample(walk,i*.5,p)
    assert(Growth.stage(walk)==math.floor(i/90))
end
assert(walk.firstS4Activity==180 and walk.activeSeconds==180 and walk.energy==100)
local r,c=Growth.tryHalfMoon(walk,7,180)
assert(r==10 and c==6 and walk.energy==70 and Growth.cooldown(walk,180)==15)
sample(walk,194.99,p)
assert(Growth.tryHalfMoon(walk,7,194.99)==nil and walk.energy==70)
sample(walk,195,p)
assert(Growth.tryHalfMoon(walk,7,195)==10 and walk.energy==40)
sample(walk,210,p)
assert(Growth.tryHalfMoon(walk,7,210)==10 and walk.energy==10)
sample(walk,225,p)
assert(Growth.tryHalfMoon(walk,7,225)==nil and walk.energy==10)
p.root.Position=Vector3.new(1.2,3,0)
sample(walk,225.5,p)
assert(walk.energy==12)
print("ROLE_GROWTH_S0_TO_S4_ENERGY_COOLDOWN_PASS")

local function targets(...)
    local group={}
    for _,distance in ipairs({...}) do table.insert(group,addNeutral(distance,64)) end
    horde.mobs=group
    return group
end
local function damageCount(group)
    local count=0
    for _,mob in ipairs(group) do if mob.hp<64 then count+=1 end end
    return count
end

sevenJobs[owner]="WARRIOR"
sevenJobLastChoose[owner]=99
local startup=targets(10)
cast(owner,1)
assert(snapshots[owner]==nil and startup[1].hp==64)
local combatClock=Growth.new(match.serial)
SevenJobs.GrowthStates[owner]=combatClock
time=100
local waiting=growthSnapshot(owner)
growthHud(waiting)
assert(waiting.roleHalfMoon and waiting.roleEnergy==nil and waiting.roleGrowthStage==nil)
assert(not jobCast.Active and jobCast.Text=="半月斬\n準備中")
sample(combatClock,time,owner)
local ready=growthSnapshot(owner)
growthHud(ready)
assert(ready.roleEnergy==100 and ready.roleGrowthStage==0 and jobCast.Active)
owner.root.Position=Vector3.new(131,3,0)
SevenJobs.markGrowthActivity(owner)
local outside=growthSnapshot(owner)
growthHud(outside)
assert(outside.roleEnergy==nil and not jobCast.Active)
cast(owner,2)
assert(snapshots[owner]==nil and combatClock.energy==100 and combatClock.actionAt==nil)
owner.root.Position=Vector3.new(0,3,0)
local start=targets(5.9,6,6.001,9)
cast(owner,3)
assert(snapshots[owner]==1 and damageCount(start)==2 and combatClock.energy==70)
assert(start[1].hp==24 and start[2].hp==24 and start[3].hp==64)
local cooling=growthSnapshot(owner)
growthHud(cooling)
assert(cooling.jobCooldown==15 and cooling.roleEnergy==70 and not jobCast.Active)
time=111
sample(combatClock,time,owner)
cast(owner,4)
assert(snapshots[owner]==1 and combatClock.energy==70)
for i=1,360 do
    time=111+i*.5
    owner.root.Position=Vector3.new((i%2)*.6,3,0)
    sample(combatClock,time,owner)
end
assert(Growth.stage(combatClock)==4 and combatClock.energy==100)
local finish=targets(5.9,6,6.001,8,8.9,10,9.999,10.001)
cast(owner,5)
assert(snapshots[owner]==2 and damageCount(finish)==6 and combatClock.energy==70)
assert(finish[6].hp==24 and finish[7].hp==64 and finish[8].hp==64)

match.serial=8
assert(SevenJobs.activeGrowth(owner)==nil)
match.serial=7
owner.attrs.P0D_LateJoinSpectator=true
owner.team="NONE"
assert(SevenJobs.activeGrowth(owner)==nil)
cast(owner,6)
assert(snapshots[owner]==2 and combatClock.energy==70)
owner.attrs.P0D_LateJoinSpectator=false
owner.team="RED"
time+=30
local legacy=targets(12.9,13.1)
SevenJobs.GrowthStates[owner]=nil
cast(owner,7)
assert(legacy[1].hp==64 and legacy[2].hp==64 and snapshots[owner]==2)
growthFlag=false
cast(owner,8)
assert(legacy[1].hp<64 and legacy[2].hp==64 and snapshots[owner]==3)
print("ROLE_GROWTH_REAL_GAME_SKILL_RANGE_CAP_SPECTATOR_LEGACY_PASS")
print("ROLE_GROWTH_SNAPSHOT_AVATAR_BOUNDS_AND_HUD_READINESS_PASS")
