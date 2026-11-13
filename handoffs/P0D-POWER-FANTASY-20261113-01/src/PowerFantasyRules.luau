--!strict
-- EGG RAID RUMBLE: OPTIONAL server-only fair power-fantasy candidate.
-- A genuine earned Lv50 can overpower minions/bosses, gain PvP strength and
-- once-per-round awakening. Not installed into any existing Game or Remote.
-- Never accept level/mastery/charge from a client, store or paid item.
local Power = {}
Power.MAX_LEVEL = 50
Power.MAX_MASTERY = 10
Power.AWAKEN_LEVEL = 10
Power.AWAKEN_REQUIRED = 80
Power.TELEGRAPH_SECONDS = 2
Power.AWAKEN_SECONDS = 8
local ACT = {
    DEPOSIT={charge=45, cap=2},
    RECOVER={charge=35, cap=2},
    ESCORT={charge=20, cap=3},
    DEFEND={charge=20, cap=3},
    PICKUP={charge=10, cap=2},
}
local function validInt(n,lo,hi)
    return type(n)=="number" and n==n and n%1==0 and n>=lo and n<=hi
end
local function safeId(v,max)
    return type(v)=="string" and #v>=1 and #v<=max
end
local function frac(level,maxLevel)
    return (level-1)/(maxLevel-1)
end
local function min(a,b)
    return if a<b then a else b
end
function Power.makeRound(roundId,userId,accountLevel,itemMastery,gameMode)
    if not safeId(roundId,128) or not validInt(userId,1,99999999999) or
        not validInt(accountLevel,1,Power.MAX_LEVEL) or
        not validInt(itemMastery,1,Power.MAX_MASTERY) or
        (gameMode~="CLASSIC" and gameMode~="SCORE_5") then
        return nil,"INVALID_SERVER_PROFILE"
    end
    return {
        roundId=roundId,userId=userId,level=accountLevel,mastery=itemMastery,
        mode=gameMode,phase="ACTIVE",charge=0,counts={},seen={},
        awakeningUsed=false,awakeningStartsAt=nil,awakeningEndsAt=nil,
    }
end
function Power.recordObjective(state,eventId,kind,serverConfirmed)
    if type(state)~="table" or state.phase~="ACTIVE" or
        not safeId(eventId,96) or serverConfirmed~=true or state.seen[eventId] then
        return false,"INVALID_EVENT"
    end
    local cfg=ACT[kind]
    if not cfg then return false,"INVALID_EVENT_KIND" end
    if (state.counts[kind] or 0)>=cfg.cap then return false,"ACTION_CAP" end
    state.seen[eventId]=true
    state.counts[kind]=(state.counts[kind] or 0)+1
    state.charge=min(100,state.charge+cfg.charge)
    return true,state.charge
end
function Power.canAwaken(state,now,carryingEgg,serverConfirmed)
    if type(state)~="table" or state.phase~="ACTIVE" or
        not validInt(now,0,1000000000) or serverConfirmed~=true then
        return false,"NOT_ACTIVE"
    end
    if carryingEgg~=false then return false,"DROP_EGG_FIRST" end
    if state.level<Power.AWAKEN_LEVEL then return false,"UNLOCK_AT_LEVEL_10" end
    if state.awakeningUsed then return false,"ONE_PER_MATCH" end
    if state.charge<Power.AWAKEN_REQUIRED then return false,"MORE_OBJECTIVES_NEEDED" end
    return true,"READY"
end
-- Called only by original Game after validated authoritative action.
-- A visible 2s warning effect MUST be shown by a separately reviewed world adapter.
function Power.beginAwaken(state,now,carryingEgg,serverConfirmed)
    local yes,why=Power.canAwaken(state,now,carryingEgg,serverConfirmed)
    if not yes then return false,why end
    state.awakeningUsed=true
    state.charge=0
    state.awakeningStartsAt=now+Power.TELEGRAPH_SECONDS
    state.awakeningEndsAt=state.awakeningStartsAt+Power.AWAKEN_SECONDS
    return true,{telegraphStart=now,startsAt=state.awakeningStartsAt,
        endsAt=state.awakeningEndsAt,kind="AWAKENING",counterplay="LOS_AND_ESCAPE"}
end
function Power.isAwakened(state,now)
    return type(state)=="table" and validInt(now,0,1000000000) and
        type(state.awakeningStartsAt)=="number" and
        type(state.awakeningEndsAt)=="number" and
        state.phase=="ACTIVE" and now>=state.awakeningStartsAt and now<state.awakeningEndsAt
end
-- Multiplier is relative to a 1x common beginner at Lv1.
-- Character-vs-player, vs minions and vs boss are explicitly separated:
--  PvP: earned max +20% base offense, max +10% mastery but combined <=+25%.
--  PvP awaken: +15% temporary, explicit telegraph (<=1.40 total).
--  PvE minion: 1x -> 3x Lv scaling + mastery up to 0.30 and awaken +0.5;
--  PvE boss: 1x -> 1.5x + mastery up to .15, awaken +.2.
--  PvP health <=+20%; no attack against eggs or capture score modification.
function Power.combat(state,targetType,now)
    if type(state)~="table" or state.phase~="ACTIVE" or
        not validInt(state.level,1,50) or not validInt(state.mastery,1,10) or
        not validInt(now,0,1000000000) then return nil,"INVALID_STATE" end
    if targetType~="PLAYER" and targetType~="MINION" and targetType~="BOSS" then
        return nil,"INVALID_TARGET"
    end
    local lf=frac(state.level,50)
    local mf=frac(state.mastery,10)
    local awake=Power.isAwakened(state,now)
    local offense
    if targetType=="PLAYER" then
        offense=1+min(.25,.20*lf+.10*mf)+(awake and .15 or 0)
    elseif targetType=="MINION" then
        offense=1+2*lf+.30*mf+(awake and .50 or 0)
    else
        offense=1+.50*lf+.15*mf+(awake and .20 or 0)
    end
    local health=1+.20*lf
    return {
        damage=offense,health=health,awakening=awake,
        level=state.level,mastery=state.mastery,targetType=targetType,
        affectsEggScore=false,
        usableWhileCarryingEgg=false,
        canBuyPower=false,
    }
end
-- This is a *suggestion* to an authorized matchmaking owner, not actual server ranking.
function Power.suggestBracket(level)
    if not validInt(level,1,50) then return nil end
    if level<=10 then return "NOVICE" end
    if level<=30 then return "VETERAN" end
    return "LEGEND"
end
function Power.ultimate(level)
    if not validInt(level,1,50) then return nil end
    if level<10 then return {name="防御の構え",tier=0,damageMultiplier=1} end
    if level<30 then return {name="覚醒の一撃",tier=1,damageMultiplier=1} end
    if level<50 then return {name="幻獣の共鳴",tier=2,damageMultiplier=1} end
    return {name="天龍降臨",tier=3,damageMultiplier=1}
end
function Power.endRound(state)
    if type(state)~="table" or state.phase~="ACTIVE" then return false end
    state.phase="ENDED"
    state.charge=0
    state.awakeningStartsAt=nil
    state.awakeningEndsAt=nil
    return true
end
return Power
