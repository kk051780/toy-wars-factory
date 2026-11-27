local function neutral(id,x,z,hp)
    local mob=addNeutral(x,hp or 64)
    mob.id=id
    mob.pos=Vector3.new(x,3,z)
    mob.home=mob.pos
    return mob
end
local function at(state,nextTime)
    time=nextTime
    SevenJobs.Growth.sample(state,match.serial,time,owner.Character,owner.root.Position,19)
end
local function castWater(seq)
    useSevenJob(owner,{action="JOB_SKILL",seq=seq,damage=1000,job="NECROMANCER",target=enemy})
end
local function close(a,b)
    return math.abs(a-b)<1e-6
end

local data=SevenJobs.Water
assert(data.id=="MAGE-041" and data.cd==12 and data.energy==30)
assert(table.concat(data.metrics[1].values,",")=="10,12,14,16,18")
assert(table.concat(data.metrics[2].values,",")=="1,1.2,1.4,1.6,2")
sevenJobs[owner]="MAGE"
sevenJobLastChoose[owner]=99
local state=SevenJobs.Growth.new(match.serial)
SevenJobs.GrowthStates[owner]=state
local first=neutral(4,9,0)
local far=neutral(6,10.01,0)
horde.mobs={far,first}
local view=growthSnapshot(owner)
growthHud(view)
assert(view.roleWaterBolt and view.roleEnergy==nil and not jobCast.Active and jobCast.Text=="水弾\n準備中")
castWater(1)
assert(snapshots[owner]==nil and first.hp==64 and state.energy==100)
at(state,100)
growthHud(growthSnapshot(owner))
assert(jobCast.Active and jobCast.Text=="水弾 S0\nQ  E100")
castWater(2)
assert(first.hp==48 and far.hp==64 and state.energy==70 and snapshots[owner]==1)
view=growthSnapshot(owner)
growthHud(view)
assert(view.jobCooldown==12 and view.roleWaterTarget==4 and close(view.roleWaterSeconds,1))
assert(not jobCast.Active and string.find(jobCast.Text,"水印 4",1,true)~=nil)
assert(first.waterMarks[owner] and not first.waterMarks[enemy] and far.waterMarks==nil)
assert(first.waterCue.Enabled and first.waterCue.Name=="WaterMarkStatus"
    and first.waterCue.AlwaysOnTop==false and string.find(first.waterText.Text,"水印 4",1,true))
assert(horde:waterStatus(owner,100.999)==4 and horde:waterStatus(owner,101)==nil)
horde:updateWaterCue(first,101)
assert(not first.waterCue.Enabled)
at(state,111.999)
castWater(3)
assert(snapshots[owner]==1 and state.energy==70)
first=neutral(5,10,0)
horde.mobs={first}
at(state,112)
castWater(4)
assert(snapshots[owner]==2 and first.hp==48 and state.energy==40)
print("ACTIVE_MAGE_041_REAL_Q_RANGE_12S_ENERGY_AND_WATER_EXPIRY_PASS")

local t=time
for i=1,180 do
    owner.root.Position=Vector3.new((i%2)*.6,3,0)
    at(state,t+i*.5)
end
assert(SevenJobs.Growth.stage(state)==2 and state.energy==100)
local direct=neutral(10,13,0)
local spreadA=neutral(11,13,2)
local spreadB=neutral(12,13,-2)
local spare=neutral(13,14,3)
local outOfRadius=neutral(14,20,2)
horde.mobs={spare,spreadB,outOfRadius,direct,spreadA}
castWater(5)
assert(direct.hp==48 and spreadA.hp==64 and spreadB.hp==64 and spare.hp==64)
assert(direct.waterMarks[owner].direct and spreadA.waterMarks[owner].direct==false
    and spreadB.waterMarks[owner].direct==false and not spare.waterMarks and not outOfRadius.waterMarks)
assert(close(direct.waterMarks[owner].expiry-time,1.4))
assert(close(spreadA.waterMarks[owner].expiry-time,1.4))
assert(spreadA.waterCue.Enabled and spreadB.waterCue.Enabled and not spare.waterCue)
assert(horde:waterStatus(owner,time)==10)
assert(Horde.damageNeutral(horde,direct,Vector3.new(1,0,0),0,40,time)==false and direct.hp==8)
assert(Horde.damageNeutral(horde,direct,Vector3.new(1,0,0),0,40,time)==true and direct.hp==0)
assert(direct.waterMarks==nil and not direct.waterCue.Enabled and horde:waterStatus(owner,time)==12)
print("ACTIVE_MAGE_041_STAGE2_MARK_ONLY_SPREAD_AND_NEUTRAL_LIFE_PASS")

t=time
for i=1,180 do
    owner.root.Position=Vector3.new((i%2)*.6,3,0)
    at(state,t+i*.5)
end
assert(SevenJobs.Growth.stage(state)==4 and state.energy==100)
local farShot=neutral(22,18,0)
local over=neutral(23,18.001,0)
horde.mobs={farShot,over}
wallX=4
castWater(6)
assert(farShot.hp==64 and not farShot.waterMarks and state.energy==70)
at(state,time+12)
wallX=nil
castWater(7)
assert(farShot.hp==48 and over.hp==64 and close(farShot.waterMarks[owner].expiry-time,2))
owner.Character=Instance.new("Model")
at(state,time+12)
owner.root.Position=Vector3.new(131,3,0)
view=growthSnapshot(owner)
growthHud(view)
assert(view.roleWaterBolt and view.roleEnergy==nil and not jobCast.Active)
local old=snapshots[owner]
castWater(8)
assert(snapshots[owner]==old and state.energy==40)
owner.root.Position=Vector3.new(0,3,0)
owner.attrs.P0D_LateJoinSpectator=true
owner.team="NONE"
castWater(9)
assert(snapshots[owner]==old and state.energy==40)
owner.attrs.P0D_LateJoinSpectator=false
owner.team="RED"
waterFlag=false
at(state,time+15)
local legacy=neutral(24,3,0)
horde.mobs={legacy}
castWater(10)
assert(snapshots[owner]==old+1 and legacy.hp<64 and legacy.waterMarks==nil)
assert(not growthSnapshot(owner).roleWaterBolt)
local bounced=neutral(25,10,0)
horde.mobs={bounced}
waterFlag=true
local previousCast=time
at(state,previousCast+.1)
local energy=state.energy
assert(growthSnapshot(owner).jobCooldown==12)
castWater(11)
assert(snapshots[owner]==old+1 and bounced.hp==64 and state.energy==energy)
at(state,previousCast+12)
castWater(12)
assert(snapshots[owner]==old+2 and bounced.hp==48 and state.energy==energy-30)
print("ACTIVE_MAGE_041_STAGE4_WALL_RANGE_ROLE_AND_LEGACY_FALLBACK_PASS")
