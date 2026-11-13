--!strict
-- EGG RAID RUMBLE optional S2+: original fairness-first progression rules.
-- PURE server-owned policy; never another live Game/Remote/Datastore writer.
-- Match Focus (Lv1-3) resets; Player account (Lv1-50) and USED EQUIPPED
-- collectible mastery (Lv1-10) require a separately authorized persistent store.
-- No HP/damage/walkspeed buffs, no paid XP, no random rarity/loot authority.
local P = {}

P.PLAYER_MAX_LEVEL = 50
P.MASTERY_MAX_LEVEL = 10
P.XP_CAP_PER_ROUND = 150
P.MAX_RECORDED_ROUNDS = 4096
P.MATCH_COMPLETION_XP = 50
P.MIN_ELIGIBLE_SECONDS = 60
P.MAX_ELIGIBLE_SECONDS = 360

local EVENTS = {
    PICKUP    = {xp=10,focus=10,cap=2},
    DEPOSIT   = {xp=25,focus=20,cap=2},
    RECOVER   = {xp=20,focus=15,cap=1},
    ESCORT    = {xp=10,focus=8, cap=2},
    DEFEND    = {xp=10,focus=8, cap=2},
    EQUIP_USE = {xp=12,focus=10,cap=1},
}

local function integer(n)
    return type(n)=="number" and n==n and n%1==0 and n>=0 and n<100000000
end
local function stringId(s,maxLen)
    return type(s)=="string" and #s>0 and #s<=maxLen
end
local function modeOk(m)
    return m=="CLASSIC" or m=="SCORE"
end

function P.xpToNext(level)
    if not integer(level) or level<1 or level>=P.PLAYER_MAX_LEVEL then return 0 end
    return 60+40*(level-1)
end
function P.masteryToNext(level)
    if not integer(level) or level<1 or level>=P.MASTERY_MAX_LEVEL then return 0 end
    return 24+12*(level-1)
end
local function applyLevels(startLevel,rawXp,cap,threshold)
    local level=startLevel
    local xp=rawXp
    while level<cap do
        local need=threshold(level)
        if need<=0 or xp<need then break end
        xp-=need
        level+=1
    end
    if level>=cap then xp=0 end
    return level,xp
end
-- This object must ONLY be loaded/committed on a trusted game server.
-- Production: use DataStore UpdateAsync transaction, do not use this in-memory
-- model to claim persistence or prevent concurrent-server duplicates.
function P.newProfile(playerUserId)
    if not integer(playerUserId) or playerUserId<1 then return nil end
    return {
        playerUserId=playerUserId,
        level=1, xp=0,
        mastery={}, -- [server-validated collectible ID] = {level,xp}
        claimedRoundIds={}, -- never evict silently: fail-closed at capacity
        settledCount=0,
    }
end
-- Server should use unique JobId/round serial and validate owned+equipped
-- from the canonical inventory, never read item ownership from a client.
function P.newRound(roundId,playerUserId,gameMode,equippedItemId,ownedByPlayer)
    if not stringId(roundId,128) or not integer(playerUserId) or
        playerUserId<1 or not modeOk(gameMode) then return nil end
    if equippedItemId~=nil then
        if not stringId(equippedItemId,96) or ownedByPlayer~=true then return nil end
    end
    return {
        id=roundId,playerUserId=playerUserId,mode=gameMode,
        equippedItemId=equippedItemId,events={},counts={},
        activityXp=0,focusXp=0,masteryXp=0,
        objectiveEvents=0,acceptedActions=0,closed=false,
    }
end

function P.recordEvent(round,eventId,kind,serverConfirmed)
    if type(round)~="table" or round.closed==true or
        not stringId(eventId,96) or serverConfirmed~=true then return false end
    local rule=EVENTS[kind]
    if not rule then return false end
    -- Strictly dedup server-generated objective event ID within this round.
    if round.events[eventId]==true then return false end
    local count=round.counts[kind] or 0
    if count>=rule.cap or round.acceptedActions>=20 then return false end
    if kind=="EQUIP_USE" and round.equippedItemId==nil then return false end
    round.events[eventId]=true
    round.counts[kind]=count+1
    round.acceptedActions+=1
    round.activityXp+=rule.xp
    round.focusXp+=rule.focus
    if kind=="EQUIP_USE" then
        -- Real-use reward only when item was verified OWNED+EQUIPPED at start.
        round.masteryXp+=12
    else
        round.objectiveEvents+=1
    end
    return true
end
function P.focusLevel(round)
    if type(round)~="table" then return 1 end
    if round.focusXp>=60 then return 3 end
    if round.focusXp>=25 then return 2 end
    return 1
end
function P.previewXp(round,outcome,duration,confirmed)
    if type(round)~="table" or round.closed or confirmed~=true or
        not integer(duration) or duration<P.MIN_ELIGIBLE_SECONDS or
        duration>P.MAX_ELIGIBLE_SECONDS then return 0 end
    if outcome~="WIN" and outcome~="LOSS" and outcome~="DRAW" then return 0 end
    if round.objectiveEvents<1 then return 0 end -- no AFK or equip-only farm
    local resultBonus=if outcome=="WIN" then 15 elseif outcome=="DRAW" then 5 else 0
    return math.min(P.XP_CAP_PER_ROUND,P.MATCH_COMPLETION_XP+
        round.activityXp+resultBonus)
end
function P.commit(profile,round,outcome,duration,serverConfirmed)
    if type(profile)~="table" or type(round)~="table" or
        profile.playerUserId~=round.playerUserId or
        not integer(profile.settledCount) or profile.settledCount>=P.MAX_RECORDED_ROUNDS or
        not integer(profile.level) or profile.level<1 or
        profile.level>P.PLAYER_MAX_LEVEL or not integer(profile.xp) or
        type(profile.claimedRoundIds)~="table" or type(profile.mastery)~="table" or
        profile.claimedRoundIds[round.id]~=nil then return nil end
    local xp=P.previewXp(round,outcome,duration,serverConfirmed)
    if xp<=0 then return nil end
    local before=profile.level
    local nextLevel,nextXp=applyLevels(profile.level,profile.xp+xp,
        P.PLAYER_MAX_LEVEL,P.xpToNext)
    local oldMastery,newMastery=nil,nil
    if round.equippedItemId~=nil and round.masteryXp>0 then
        local old=profile.mastery[round.equippedItemId] or {level=1,xp=0}
        if type(old)~="table" or not integer(old.level) or old.level<1 or
            old.level>P.MASTERY_MAX_LEVEL or not integer(old.xp) then return nil end
        oldMastery=old.level
        local lv,remain=applyLevels(old.level,old.xp+round.masteryXp,
            P.MASTERY_MAX_LEVEL,P.masteryToNext)
        newMastery=lv
        profile.mastery[round.equippedItemId]={level=lv,xp=remain}
    end
    profile.level=nextLevel
    profile.xp=nextXp
    profile.claimedRoundIds[round.id]=true
    profile.settledCount+=1
    round.closed=true
    return {
        grantedXp=xp,accountLevelBefore=before,accountLevelAfter=nextLevel,
        focusLevel=P.focusLevel(round),masteryLevelBefore=oldMastery,
        masteryLevelAfter=newMastery,
        rewardKind="FAIR_PROGRESS_ONLY",
        gameplayStatsIncreased=false,
        requiresPaidPurchase=false,
    }
end
function P.playerMilestone(level)
    if not integer(level) then return nil end
    if level==2 then return "WELCOME_BANNER" end
    if level==5 then return "PERSONAL_NEST_DECOR" end
    if level==10 then return "TEAM_EMOTE" end
    if level==20 then return "MOUNT_TRAIL_COSMETIC" end
    if level==30 then return "CASTLE_FLAG_COSMETIC" end
    if level==50 then return "MASTER_AURA_COSMETIC" end
    return nil
end
function P.masteryMilestone(level)
    if level==3 then return "CREATURE_PALETTE" end
    if level==6 then return "ALTERNATE_ANIMATION" end
    if level==10 then return "MASTERY_TITLE" end
    return nil
end
-- A future SAME-STRENGTH sidegrade (scout vs guard etc.) needs role balancing,
-- real Studio tests, and one Game-owned server activation; this policy never
-- increases base stats or changes a collectible's actual gameplay power.
return P
