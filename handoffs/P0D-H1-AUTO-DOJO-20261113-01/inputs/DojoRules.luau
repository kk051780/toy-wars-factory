--!strict
-- P0D private H1 two-lane auto dojo. ONE existing Game owns tick and PvE use.
-- This module is pure: no Players/Workspace/Remote/DataStore/monetization calls.
-- Progress is bounded SESSION ONLY; never claim saved levels from this source.
local Dojo = {}
Dojo.MAX_LEVEL = 5
Dojo.MAX_SECONDS_PER_SKILL = 180
Dojo.BASE_XP_PER_SECOND = 1
Dojo.FRIEND_XP_MULTIPLIER = 1.5
Dojo.PVE_BONUS_PER_LEVEL = 0.05
local LEVEL_COSTS = {10,15,20,25}
local VALID = {BEAST=true,WEAPON=true}
local function fresh()
    return {BEAST=0,WEAPON=0}
end
function Dojo.new()
    return {
        level={BEAST=1,WEAPON=1},xp=fresh(),trainedSeconds=fresh(),
        current="NONE",friendBonus=false,
    }
end
function Dojo.tick(state:any,kind:any,delta:any,friendPresent:any,allow:any): boolean
    if type(state)~="table" or allow~=true or VALID[kind]~=true
        or type(delta)~="number" or delta~=delta or delta<=0 or delta>1.5
        or type(state.level)~="table" or type(state.xp)~="table"
        or type(state.trainedSeconds)~="table" then return false end
    local level=state.level[kind]
    local seconds=state.trainedSeconds[kind]
    if type(level)~="number" or level%1~=0 or level<1 or level>Dojo.MAX_LEVEL
        or type(seconds)~="number" or seconds<0
        or seconds>=Dojo.MAX_SECONDS_PER_SKILL then return false end
    -- Credit ONLY server-measured time in a valid station; no offline farm.
    local credited=math.min(delta,Dojo.MAX_SECONDS_PER_SKILL-seconds)
    local multiplier=if friendPresent==true then Dojo.FRIEND_XP_MULTIPLIER else 1
    state.trainedSeconds[kind]=seconds+credited
    if level<Dojo.MAX_LEVEL then
        local xp=state.xp[kind]
        if type(xp)~="number" or xp<0 or xp~=xp then return false end
        xp+=credited*Dojo.BASE_XP_PER_SECOND*multiplier
        while level<Dojo.MAX_LEVEL do
            local cost=LEVEL_COSTS[level]
            if not cost or xp<cost then break end
            xp-=cost
            level+=1
        end
        if level>=Dojo.MAX_LEVEL then xp=0 end
        state.level[kind]=level
        state.xp[kind]=xp
    end
    state.current=kind
    state.friendBonus=(friendPresent==true)
    return true
end
function Dojo.pveDamageMultiplier(state:any,kind:any): number
    if type(state)~="table" or VALID[kind]~=true or type(state.level)~="table" then return 1 end
    local level=state.level[kind]
    if type(level)~="number" or level%1~=0 or level<1 or level>Dojo.MAX_LEVEL then return 1 end
    return 1+(level-1)*Dojo.PVE_BONUS_PER_LEVEL -- max 1.20, PvE only
end
function Dojo.view(state:any): any
    if type(state)~="table" or type(state.level)~="table"
        or type(state.xp)~="table" then
        return {active="NONE",beast=1,weapon=1,xp=0,need=10,friendBonus=false,
            beastPve=1,weaponPve=1,sessionOnly=true}
    end
    local kind=if VALID[state.current]==true then state.current else "NONE"
    local rawLevel=if kind~="NONE" then state.level[kind] else 1
    local level=if type(rawLevel)=="number" and rawLevel%1==0
        and rawLevel>=1 and rawLevel<=Dojo.MAX_LEVEL then rawLevel else 1
    local xp=if kind~="NONE" and type(state.xp[kind])=="number"
        and state.xp[kind]>=0 and state.xp[kind]<100 then math.floor(state.xp[kind]) else 0
    return {
        active=kind,
        beast=math.clamp(state.level.BEAST or 1,1,Dojo.MAX_LEVEL),
        weapon=math.clamp(state.level.WEAPON or 1,1,Dojo.MAX_LEVEL),
        xp=xp,
        need=LEVEL_COSTS[level] or 0,
        friendBonus=state.friendBonus==true,
        beastPve=Dojo.pveDamageMultiplier(state,"BEAST"),
        weaponPve=Dojo.pveDamageMultiplier(state,"WEAPON"),
        sessionOnly=true,
    }
end
return Dojo
