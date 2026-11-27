--!strict
local Time = require(script.Parent:WaitForChild("TimePremiumRules"))
local Growth = {}

local LEVEL_ONE_SECONDS = 180
local ENERGY_CAP = 100
local ENERGY_PER_ACTIVE_SECOND = 4
local ACTION_ACTIVITY_SECONDS = 2
local MAX_SAMPLE_GAP = 1.5
local CAST_ENERGY = 30
local CAST_COOLDOWN = 15
local RANGE_BY_STAGE = table.freeze({6, 7, 8, 9, 10})
local LIMIT_BY_STAGE = table.freeze({2, 3, 4, 5, 6})

type State = {
    round: number,
    activeSeconds: number,
    firstS4Activity: number?,
    energy: number,
    lastCast: number,
    actionAt: number?,
    character: Model?,
    sampledAt: number?,
    position: Vector3?,
}

local function finite(number: any): boolean
    return type(number) == "number" and number == number and math.abs(number) < math.huge
end

function Growth.insideArena(position: Vector3?): boolean
    return position~=nil and finite(position.X) and finite(position.Y) and finite(position.Z)
        and math.abs(position.X)<=130 and math.abs(position.Z)<=76 and position.Y>=-30
end

function Growth.new(round: number): State
    return {round=round,activeSeconds=0,energy=ENERGY_CAP,lastCast=-math.huge}
end

function Growth.pause(state: State)
    state.character=nil
    state.sampledAt=nil
    state.position=nil
    state.actionAt=nil
end

function Growth.hasCurrentSample(state: State, now: number, character: Model?): boolean
    local sampledAt=state.sampledAt
    return character~=nil and state.character==character and finite(now)
        and sampledAt~=nil and now>=sampledAt and now-sampledAt<=MAX_SAMPLE_GAP
end

-- Call only after the current Game has accepted a real objective or damage result.
function Growth.markAction(state: State, round: number, now: number, character: Model?)
    if state.round==round and Growth.hasCurrentSample(state,now,character) then
        state.actionAt=math.max(now,state.actionAt or now)
    end
end

function Growth.sample(state: State, round: number, now: number, character: Model?,
        position: Vector3?, walkSpeed: number)
    if state.round~=round then return end
    if character==nil or position==nil or not finite(now) or not finite(walkSpeed)
        or not Growth.insideArena(position) then
        Growth.pause(state)
        return
    end
    local previousAt, previous = state.sampledAt, state.position
    if state.character==character and previousAt~=nil and now<=previousAt then return end
    local sameCharacter=state.character==character
    if not sameCharacter then state.actionAt=nil end
    state.character=character
    state.sampledAt=now
    state.position=position
    if not sameCharacter or previousAt==nil or previous==nil then return end

    local dt=now-previousAt
    if dt>MAX_SAMPLE_GAP then
        state.actionAt=nil
        return
    end
    local dx,dz=position.X-previous.X,position.Z-previous.Z
    local displacement=math.sqrt(dx*dx+dz*dz)
    -- Do not count respawn or recovery teleports as movement.
    if displacement>math.clamp(walkSpeed,0,64)*dt+.75
        or math.abs(position.Y-previous.Y)>16*dt+3 then
        state.actionAt=nil
        return
    end
    local qualified=if displacement>=.24 then dt else 0
    if state.actionAt and state.actionAt<=now then
        -- Intersect the sample window with the server-confirmed activity window.
        local actionSeconds=math.max(0, math.min(now,state.actionAt+ACTION_ACTIVITY_SECONDS)
            -math.max(previousAt,state.actionAt))
        qualified=math.max(qualified,actionSeconds)
    end
    if qualified<=0 then return end

    state.activeSeconds+=qualified
    state.energy=math.min(ENERGY_CAP,state.energy+qualified*ENERGY_PER_ACTIVE_SECOND)
    if state.firstS4Activity==nil and state.activeSeconds>=LEVEL_ONE_SECONDS then
        state.firstS4Activity=LEVEL_ONE_SECONDS
    end
end

function Growth.stage(state: State): number
    local fraction=Time.naturalGrowth(state.activeSeconds,LEVEL_ONE_SECONDS,0,0)
    return math.floor((fraction or 0)*4)
end

function Growth.cooldown(state: State, now: number): number
    return math.max(0,math.ceil(state.lastCast+CAST_COOLDOWN-now))
end

-- Ownership, current avatar, phase and the user's role selection are checked by Game.
function Growth.tryHalfMoon(state: State, round: number, now: number): (number?, number?)
    if state.round~=round or not Growth.hasCurrentSample(state,now,state.character)
        or now-state.lastCast<CAST_COOLDOWN or state.energy<CAST_ENERGY then
        return nil,nil
    end
    local index=Growth.stage(state)+1
    state.energy-=CAST_ENERGY
    state.lastCast=now
    return RANGE_BY_STAGE[index], LIMIT_BY_STAGE[index]
end

return table.freeze(Growth)
