--!strict
-- P0D-MULTI-EGG-SCORE-001: pure server-side REFERENCE rules for a future
-- optional score-match. NOT plugged into existing original Game.server.luau.
-- The server integration, if ever approved, must provide player identity,
-- trusted proximity, monotonic event sequence, round epoch and timing.
local M = {}

M.REGULATION = 240
M.OVERTIME = 30
M.EGGS = {"RED_1","RED_2","BLUE_1","BLUE_2","CENTRE_1"}
M.CAPTURE_ENEMY = 12
M.CAPTURE_NEUTRAL = 10
M.RECOVER_BONUS = 2

local function validTeam(team)
    return team == "RED" or team == "BLUE"
end
local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 1000000000
end
local function periodAndPoints(egg, state)
    if egg.place == "CARRIED" then
        local carrier = state.players[egg.holder]
        if carrier and validTeam(carrier.team) then
            if egg.owner == carrier.team then return carrier.team,30,1 end
            return carrier.team,10,1
        end
    elseif egg.place == "VAULT" then
        local team=egg.vault
        if validTeam(team) then
            if egg.owner == team then return team,20,1 end
            if egg.owner == "NEUTRAL" then return team,10,2 end
            return team,10,3
        end
    end
    return nil,0,0
end
local function ownerFor(name)
    if name == "CENTRE_1" then return "NEUTRAL" end
    if name == "RED_1" or name == "RED_2" then return "RED" end
    if name == "BLUE_1" or name == "BLUE_2" then return "BLUE" end
    return nil
end
local function lockEpoch(state,epoch)
    return type(state) == "table" and state.epoch == epoch and
        finite(epoch) and epoch >= 1 and epoch % 1 == 0
end

function M.new(epoch)
    if not finite(epoch) or epoch < 1 or epoch % 1 ~= 0 then return nil end
    local eggs={}
    for _,id in ipairs(M.EGGS) do
        local owner=ownerFor(id)
        eggs[id]={id=id,owner=owner,
            place=if owner=="NEUTRAL" then "NEST" else "VAULT",
            vault=if owner=="NEUTRAL" then nil else owner,
            holder=nil,elapsed=0,everEnemy=false,
            capturePaid={RED=false,BLUE=false},recoverPaid=false,
            overtimePickedBy=nil}
    end
    return {epoch=epoch,phase="ACTIVE",now=0,
        eggs=eggs,players={},scores={RED=0,BLUE=0},
        winner=nil,finishReason=nil}
end
function M.addPlayer(state,id,team,epoch)
    if not lockEpoch(state,epoch) or state.phase~="ACTIVE" then return false end
    if type(id)~="string" or #id<1 or #id>64 or not validTeam(team) then return false end
    if state.players[id] then return false end
    state.players[id]={team=team,seq=0,carrying=nil,alive=true}
    return true
end
local function changeEgg(egg,place,vault,holder)
    egg.place=place
    egg.vault=vault
    egg.holder=holder
    egg.elapsed=0 -- never carry a full earning period across custody changes
end
local function activeOrNeutralOvertime(state,egg)
    return state.phase=="ACTIVE" or
        (state.phase=="OVERTIME" and egg.owner=="NEUTRAL")
end

function M.event(state,epoch,id,seq,action,eggId,trustedNear)
    if not lockEpoch(state,epoch) then return false end
    local player=state.players[id]
    if not player or not player.alive or not validTeam(player.team) then return false end
    if not finite(seq) or seq%1~=0 or seq<=player.seq or seq>1000000000 then return false end
    -- A well-formed sequence is consumed even if the action fails. No stale
    -- replay may become valid AFTER the egg's state changes.
    player.seq=seq
    if state.phase~="ACTIVE" and state.phase~="OVERTIME" then return false end
    if type(eggId)~="string" then return false end
    local egg=state.eggs[eggId]
    if not egg or not activeOrNeutralOvertime(state,egg) then return false end
    if action=="PICK" then
        if trustedNear~=true or player.carrying~=nil then return false end
        if egg.place=="CARRIED" then return false end
        if egg.place~="VAULT" and egg.place~="NEST" and egg.place~="DROPPED" then
            return false
        end
        changeEgg(egg,"CARRIED",nil,id)
        player.carrying=eggId
        if egg.owner~="NEUTRAL" and egg.owner~=player.team then
            egg.everEnemy=true
        end
        if state.phase=="OVERTIME" and egg.owner=="NEUTRAL" then
            egg.overtimePickedBy=player.team
        end
        return true
    elseif action=="DROP" then
        if player.carrying~=eggId or egg.holder~=id then return false end
        changeEgg(egg,"DROPPED",nil,nil)
        player.carrying=nil
        return true
    elseif action=="DEPOSIT" then
        if trustedNear~=true or player.carrying~=eggId or egg.holder~=id then
            return false
        end
        local team=player.team
        if state.phase=="OVERTIME" then
            -- Only NEW possession of the central egg after minute 4 can break
            -- a tie. No passive score farming or other egg in overtime.
            if egg.owner~="NEUTRAL" or egg.overtimePickedBy~=team then return false end
            changeEgg(egg,"VAULT",team,nil)
            player.carrying=nil
            state.scores[team]+=M.CAPTURE_NEUTRAL
            state.winner=team;state.phase="FINISHED";state.finishReason="GOLDEN_CENTRE"
            return true
        end
        local firstCapture=egg.owner~=team and egg.capturePaid[team]~=true
        if egg.owner==team and egg.everEnemy and not egg.recoverPaid then
            state.scores[team]+=M.RECOVER_BONUS
            egg.recoverPaid=true
        elseif firstCapture then
            state.scores[team]+=if egg.owner=="NEUTRAL" then M.CAPTURE_NEUTRAL
                else M.CAPTURE_ENEMY
            egg.capturePaid[team]=true
        end
        changeEgg(egg,"VAULT",team,nil)
        player.carrying=nil
        return true
    end
    return false
end
function M.removePlayer(state,epoch,id)
    if not lockEpoch(state,epoch) then return false end
    local player=state.players[id]
    if not player or player.alive~=true then return false end
    player.alive=false
    if player.carrying then
        local egg=state.eggs[player.carrying]
        if egg and egg.holder==id then
            changeEgg(egg,"DROPPED",nil,nil)
        end
        player.carrying=nil
    end
    return true
end
function M.respawnPlayer(state,epoch,id)
    if not lockEpoch(state,epoch) then return false end
    local p=state.players[id]
    if not p or p.alive then return false end
    if state.phase~="ACTIVE" and state.phase~="OVERTIME" then return false end
    p.alive=true
    return true
end
local function accrue(state,seconds)
    if seconds<=0 then return end
    for _,egg in pairs(state.eggs) do
        local team,period,points=periodAndPoints(egg,state)
        if team then
            local total=egg.elapsed+seconds
            local ticks=math.floor(total/period)
            if ticks>0 then state.scores[team]+=ticks*points end
            egg.elapsed=total-ticks*period
        end
    end
end
function M.advance(state,epoch,newNow)
    if not lockEpoch(state,epoch) or not finite(newNow) or
        newNow<state.now or newNow%1~=0 or newNow>1000000 then return false end
    if state.phase=="FINISHED" then return false end
    if state.phase=="ACTIVE" then
        local untilReg=math.min(newNow,M.REGULATION)
        accrue(state,untilReg-state.now)
        state.now=untilReg
        if state.now==M.REGULATION then
            if state.scores.RED~=state.scores.BLUE then
                state.winner=if state.scores.RED>state.scores.BLUE then "RED" else "BLUE"
                state.finishReason="REGULATION"
                state.phase="FINISHED"
            else
                state.phase="OVERTIME"
                -- New central egg pickup is mandatory during overtime, never
                -- use an earlier held egg to win or create two holders.
                local egg=state.eggs.CENTRE_1
                if egg.holder then
                    local holder=state.players[egg.holder]
                    if holder then holder.carrying=nil end
                end
                changeEgg(egg,"NEST",nil,nil)
                egg.overtimePickedBy=nil
            end
        end
    end
    if state.phase=="OVERTIME" then
        state.now=math.min(newNow,M.REGULATION+M.OVERTIME)
        if state.now==M.REGULATION+M.OVERTIME then
            state.phase="FINISHED";state.winner="DRAW";state.finishReason="OVERTIME_DRAW"
        end
    end
    return true
end
return M
