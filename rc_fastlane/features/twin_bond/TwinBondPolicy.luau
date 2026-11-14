--!nocheck
-- P0D Twin Bond V1 — server-only, session-only PvE helper.
-- The ONE original Game owns ALL horde health, egg, scores and rewards.
-- This ModuleScript never attacks, damages, stores, purchases or creates Remotes.
local Bond = {}
local MAX_DURATION = 180
local SWITCH_WAIT = 20
local SPECIES = {AWARIN=true,SANGORU=true,RAIKO=true,KUMONON=true}
local state = setmetatable({}, {__mode="k"})

local function finite(n)
    return type(n)=="number" and n==n and n>=0
        and n~=math.huge and n~=-math.huge
end

function Bond.select(player, speciesId, level, now)
    if not player or not SPECIES[speciesId]
        or type(level)~="number" or level~=math.floor(level)
        or level<2 or level>3 or not finite(now) then
        return false, "INVALID"
    end
    local old=state[player]
    if old and old.untilAt>now and old.species~=speciesId
        and now<old.switchAt then
        return false, "SWITCH_COOLDOWN"
    end
    local same = old and old.untilAt>now and old.species==speciesId
    state[player]={
        species=speciesId,level=level,
        -- A re-selection may upgrade Lv2->Lv3, never extend the 180s lease.
        untilAt=(if same then old.untilAt else now+MAX_DURATION),
        switchAt=(if same then old.switchAt else now+SWITCH_WAIT),
    }
    return true,speciesId
end

function Bond.snapshot(player, now)
    if not player or not finite(now) then return nil end
    local current=state[player]
    if not current or now>=current.untilAt then
        state[player]=nil
        return nil
    end
    return {species=current.species,level=current.level,endsAt=current.untilAt}
end

function Bond.pveMultiplier(player, now)
    local current=Bond.snapshot(player,now)
    if not current then return 1 end
    -- hard cap: 20% neutral monster damage bonus, no multiplier for players
    if current.level==3 then return 1.2 end
    return 1.1
end

function Bond.forget(player)
    if player then state[player]=nil end
end

function Bond.speciesCount() return 4 end
return Bond
