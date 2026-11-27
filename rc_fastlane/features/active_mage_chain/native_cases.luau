
local function neutral(id,x,z,hp)
    local mob=addNeutral(x,hp or 64)
    mob.id=id
    mob.pos=Vector3.new(x,3,z)
    mob.home=mob.pos
    return mob
end

local serial=0
local function use(action)
    serial+=1
    fireServer(owner,{action=action,seq=serial,damage=1000,stage=4,targets={enemy}})
end

local function sample(state)
    SevenJobs.Growth.sample(state,match.serial,time,owner.Character,owner.root.Position,19)
end

local function simulateStage(stage)
    match.phase="ACTIVE"
    match.serial+=1
    horde.round=match.serial
    sevenJobs[owner]="MAGE"
    sevenJobLastChoose[owner]=time
    local state=SevenJobs.Growth.new(match.serial)
    SevenJobs.GrowthStates[owner]=state
    state.activeSeconds=45*stage
    sample(state)
    assert(SevenJobs.Growth.stage(state)==stage)
    return state
end

local function visualCounts()
    local tell,hit,arcs=0,0,0
    for _,part in ipairs(made) do
        if part.Parent and part.Name=="P0D_MAGE_CHAIN_TELL" then tell+=1 end
        if part.Parent and part.Name=="P0D_MAGE_CHAIN_HIT" then
            hit+=1
            assert(part.CanQuery==false and part.CanTouch==false and part.CanCollide==false)
            for _,item in ipairs(made) do
                if item.Parent==part and item.ClassName=="Beam" then arcs+=1 end
            end
        end
    end
    return tell,hit,arcs
end

local config=SevenJobs.Chain
assert(config.cooldown==20 and config.energy==40)
assert(table.concat(config.hopByStage,",")=="4,5,6,7,8")
assert(table.concat(config.targetsByStage,",")=="1,2,3,4,5")
for stage=0,4 do
    local state=simulateStage(stage)
    local site={}
    for index=1,6 do
        site[index]=neutral(index,5,(index-1)*(stage+4))
    end
    horde.mobs=site
    use("MAGE_CHAIN")
    local tell,hit,arcs=visualCounts()
    assert(tell==1 and hit==0 and arcs==0 and state.energy==60)
    advance(config.tellSeconds-.001)
    assert(site[1].hp==64)
    -- Duplicate/replay and an action stamped just under the boundary cannot charge twice.
    fireServer(owner,{action="MAGE_CHAIN",seq=serial})
    use("MAGE_CHAIN")
    assert(state.energy==60)
    advance(.001)
    for index,mob in ipairs(site) do
        assert(mob.hp==(if index<=stage+1 then 48 else 64),("CHAIN_STAGE_TARGET_%d_%d"):format(stage,index))
    end
    tell,hit,arcs=visualCounts()
    assert(tell==0 and hit==1 and arcs==stage+1)
    assert(mobLastHits[owner]==stage+1)
    advance(.3)
    tell,hit,arcs=visualCounts()
    assert(tell==0 and hit==0 and arcs==0)
end
print("ACTIVE_MAGE_025_ALL_FIVE_HOP_LIMITS_CHARGE_ONE_AND_ARC_BUDGET_PASS")

local state=simulateStage(4)
local seed=neutral(10,5,0)
local through=neutral(11,5,6)
local far=neutral(12,5,-8.001)
local dead=neutral(13,5,-2)
dead.hp=0
horde.mobs={far,through,dead,seed}
wallZ=3
use("MAGE_CHAIN")
advance(.24)
assert(seed.hp==48 and through.hp==64 and far.hp==64 and dead.hp==0)
wallZ=nil
advance(.3)

state=simulateStage(1)
seed=neutral(15,5,0)
local hidden=neutral(16,5,3)
local visible=neutral(17,5,-4)
horde.mobs={hidden,seed,visible}
blockedCasterOnly=true
use("MAGE_CHAIN")
advance(.24)
assert(seed.hp==48 and hidden.hp==64 and visible.hp==48,"CORNER_COVER_AND_NEXT_VISIBLE_TARGET")
blockedCasterOnly=false
advance(.3)

state=simulateStage(4)
seed=neutral(20,5,0)
local duplicate=neutral(21,5,-2)
duplicate.model=seed.model
local real=neutral(22,5,3,16)
horde.mobs={duplicate,seed,real}
use("MAGE_CHAIN")
advance(.24)
assert(seed.hp==48 and duplicate.hp==64 and real.hp==0 and mobLastKOs[owner]==1)
advance(.3)

state=simulateStage(0)
seed=neutral(30,13.001,0)
horde.mobs={seed}
use("MAGE_CHAIN")
assert(state.energy==100)
seed=neutral(31,6,0)
horde.mobs={seed}
wallX=3
use("MAGE_CHAIN")
assert(state.energy==100)
wallX=nil
use("MAGE_CHAIN")
wallX=3
advance(.24)
assert(seed.hp==64)
wallX=nil
advance(.3)
print("ACTIVE_MAGE_025_SEED_RANGE_LINK_WALL_DUPLICATE_AND_ACTUAL_KO_PASS")

state=simulateStage(0)
seed=neutral(35,6,0)
horde.mobs={seed}
state.energy=69
use("JOB_SKILL")
use("MAGE_CHAIN")
assert(state.energy==39 and state.lastChain==nil and seed.hp==48,"INSUFFICIENT_SHARED_ENERGY")
advance(.3)

state=simulateStage(0)
seed=neutral(40,6,0)
horde.mobs={seed}
chainFlag=false
use("MAGE_CHAIN")
assert(state.energy==100)
chainFlag=true
carry[owner]="BLUE"
use("MAGE_CHAIN")
assert(state.energy==100)
carry[owner]=nil
slowed[owner]=true
use("MAGE_CHAIN")
assert(state.energy==100)
slowed[owner]=nil
use("MAGE_CHAIN")
local castTime=time
use("JOB_SKILL")
assert(state.energy==30 and seed.hp==48,"INDEPENDENT_WATER_COOLDOWN")
advance(.24)
assert(seed.hp==32 and state.energy==30)
assert(growthSnapshot(owner).roleChain and growthSnapshot(owner).roleChainCooldown==20)
time=castTime+19.999
sample(state)
state.energy=100
use("MAGE_CHAIN")
assert(state.energy==100)
time=castTime+20
sample(state)
use("MAGE_CHAIN")
assert(state.energy==60)
match.phase="RESULTS"
advance(.24)
assert(seed.hp==32)
advance(.3)

state=simulateStage(0)
seed=neutral(50,6,0)
horde.mobs={seed}
use("MAGE_CHAIN")
local savedCharacter=owner.Character
owner.Character=Instance.new("Model")
advance(.24)
assert(seed.hp==64)
owner.Character=savedCharacter
advance(.3)

state=simulateStage(0)
owner:SetAttribute("P0D_LateJoinSpectator",true)
use("MAGE_CHAIN")
assert(state.energy==100)
owner:SetAttribute("P0D_LateJoinSpectator",false)
sevenJobs[owner]="WARRIOR"
use("MAGE_CHAIN")
assert(state.energy==100)
print("ACTIVE_MAGE_025_SEPARATE_WATER_CD_STALE_LIFE_ROUND_AND_ROLE_PASS")
