local Config=(function()
__CONFIG__
end)()
SevenJobs.Armament=(function()
__ARMAMENT__
end)()

local roles={}
local lastAttack={}
local packets={}
local reports={}
local damageGrowth=0
local joinedPlayers={}
function Players:GetPlayers() return joinedPlayers end
function SevenJobs.markGrowthActivity() damageGrowth+=1 end
local SavedPvePolicy={mergeWithEarned=function() return 1 end}
local Dojo={pveDamageMultiplier=function() return 1 end}
local dojoStates={}
local function earnedDamageMultiplier() return 1 end
local function savedPveMinionMultiplier() return 1 end
local function twinBondOnlyNeutralMobBonus() return 1 end
local EXPERIMENTAL_FIVE_EGG_MODE=false
local SoloTeamBots={tryHumanHit=function() return nil end}
function remote:FireClient(p,s)
    if s.kind=="P0D_ATTACK_RESULT" then
        assert(s.seq==lastSeq[p] and s.serial==match.serial)
        table.insert(packets,s)
    else
        table.insert(reports,s)
    end
end
map.teams={
    RED={core={Position=Vector3.new(-130,4,0)}},
    BLUE={core={Position=Vector3.new(130,4,0)}}
}
local function broadcast() end
local function stopRound() error("Unexpected castle break") end

__GAME_MAGE_OWNERSHIP__
__GAME_PICK__
__GAME_ATTACK__
local function mageTick(player)
__GAME_MAGE_TICK__
end

local function mob(x,z,hp)
    local neutral={hp=hp,maxHp=hp,home=Vector3.new(x,3,z),attackAt=0,model=Instance.new("Model"),
        elite=false,popup={},popupText={},body={},cue={}}
    neutral.pos=neutral.home
    neutral.model.Parent=horde.folder
    table.insert(horde.mobs,neutral)
    return neutral
end
local function arcCount()
    local result=0
    for _,item in ipairs(made) do
        if item.Parent==workspace and item.Name=="P0D_M1_HIT_ARC_MAGE" then
            assert(item.CanQuery==false and item.CanCollide==false and item.CanTouch==false)
            result+=1
        end
    end
    return result
end
local function tap(seq,wait)
    if wait then advance(wait) end
    applyAttack(owner,{action="ATTACK",seq=seq,damage=999999,target=enemy,origin=Vector3.new(100,0,100)})
end
local function hitIs(name)
    assert(packets[#packets].status=="HIT" and packets[#packets].target==name)
end
local function equipHand(character,name)
    local hand=Instance.new("Part")
    hand.Name=name
    hand.CFrame=CFrame.new(0,3,0)
    hand.Parent=character
end
local function verifyStaff(character)
    local model=assert(character:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT"))
    local pieces=0
    for _,piece in ipairs(model:GetChildren()) do
        assert(piece.CanCollide==false and piece.CanTouch==false and piece.CanQuery==false)
        pieces+=1
    end
    assert(pieces==4 and model:FindFirstChild("RuneStaff") and model:FindFirstChild("SpellOrb"))
    return model
end

equipHand(owner.Character,"RightHand")
match.phase="LOBBY"
selectSevenJob(owner,{action="JOB_PICK",seq=1,role="MAGE"})
assert(#reports==1 and sevenJobs[owner]=="MAGE" and SevenJobs.mageArmamentSelected(owner))
local staff=verifyStaff(owner.Character)
tap(2)
assert(#packets==0 and arcCount()==0)
match.phase="ACTIVE"
local one=mob(8,0,100)
tap(3)
hitIs("MINION")
assert(arcCount()==1 and one.hp==100-math.floor(Config.CombatDamage.RAIDER*.60))
assert(staff==verifyStaff(owner.Character))
tap(3,Config.AttackCooldown+.01)
assert(#packets==1 and arcCount()==0)
horde.mobs={}
local two={}
for i=1,10 do two[i]=mob(8,0,100) end
tap(4)
hitIs("MINION")
assert(arcCount()==2 and mobLastHits[owner]==6)
local once=0
for _,target in ipairs(two) do
    if target.hp<100 then
        once+=1
        assert(target.hp==100-math.floor(Config.CombatDamage.RAIDER*.60))
    end
end
assert(once==6,"duplicate neutral damage or cast cap")
horde.mobs={}
local three=mob(8,0,100)
tap(5,Config.AttackCooldown+.01)
hitIs("MINION")
assert(arcCount()==3 and three.hp<100 and mobLastHits[owner]==1 and damageGrowth==3 and #packets==3)
print("ACTIVE_MAGE_AUTHOR_COMBO_AND_EXACT_SINGLE_TARGET_CAP_PASS")

horde.mobs={}
wallX=4
local closed=mob(8,0,100)
tap(6,3)
assert(closed.hp==100 and arcCount()==0 and packets[#packets].status=="MISS")
local close=mob(2,0,100)
tap(7,Config.AttackCooldown+.01)
hitIs("MINION")
assert(close.hp<100 and closed.hp==100 and arcCount()==0)
wallX=nil
horde.mobs={}
local far=mob(19,0,100)
local near=mob(16,0,100)
tap(8,3)
hitIs("MINION")
assert(far.hp==100 and near.hp<100 and arcCount()==1)
print("ACTIVE_MAGE_ACTUAL_ROOT_WALL_RANGE_AND_CLOSE_CONTACT_PASS")

local oldAvatar=owner.Character
SevenJobs.clearMageArmament(owner,oldAvatar)
assert(not oldAvatar:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT"))
owner.Character=Instance.new("Model")
mageTick(owner)
assert(not owner.Character:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT"))
equipHand(owner.Character,"Right Arm")
mageTick(owner)
verifyStaff(owner.Character)
horde.mobs={}
mob(8,0,100)
tap(9,Config.AttackCooldown+.01)
assert(arcCount()==1)
verifyStaff(owner.Character)
mageFlag=false
mageTick(owner)
assert(not owner.Character:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT"))
horde.mobs={}
local flagOff=mob(8,0,100)
tap(10,Config.AttackCooldown+.01)
assert(arcCount()==0 and flagOff.hp==100-math.min(40,Config.CombatDamage.RAIDER))
mageFlag=true
mageTick(owner)
verifyStaff(owner.Character)
horde.mobs={}
mob(8,0,100)
tap(11,Config.AttackCooldown+.01)
assert(arcCount()==1,"runtime disabled Mage retained a stale combo stage")
match.phase="LOBBY"
advance(3)
selectSevenJob(owner,{action="JOB_PICK",seq=12,role="WARRIOR"})
assert(#reports==2 and not owner.Character:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT"))
match.phase="ACTIVE"
horde.mobs={}
local legacy=mob(8,0,100)
tap(13)
assert(legacy.hp==100-math.min(40,Config.CombatDamage.RAIDER) and arcCount()==0)
owner.team="NONE"
local before=#packets
tap(14,Config.AttackCooldown+.01)
assert(#packets==before)
print("ACTIVE_MAGE_STAFF_R6_R15_RESET_ROLE_GUARDS_AND_OTHER_ATTACK_PASS")
