--!strict
-- Original owner concept #219: 5 eggs, score for possession and castle delivery.
-- Pure server-side rules only. No client requests, services, remotes, clocks, money.
local Rules = {}
local OWNERS = {R1="RED",R2="RED",B1="BLUE",B2="BLUE",N1="NEUTRAL"}
Rules.LENGTH_SECONDS = 240
Rules.SCORE_VERSION = "H2_LAB_20261113_V1"

local function team(t: any): boolean
    return t == "RED" or t == "BLUE"
end
local function uid(n: any): boolean
    return type(n) == "number" and n >= 1 and n < 10000000000000 and n % 1 == 0
end

function Rules.new()
    local eggs = {}
    for id, original in pairs(OWNERS) do
        eggs[id] = {
            id=id, owner=original,
            state=if original == "NEUTRAL" then "NEUTRAL" else "HOME",
            controller=if original == "NEUTRAL" then nil else original,
            holder=nil, transferSeq=0, heldSeconds=0,
            bonusClaimed={RED=false,BLUE=false},
            rescueClaimed=false, enemyTouched=false,
        }
    end
    return {active=true,now=0,scores={RED=0,BLUE=0},
        winner="",eggs=eggs,carryByPlayer={},events=0}
end

function Rules.pickup(m: any,id: any,playerId: any,playerTeam: any): (boolean,string)
    if type(m) ~= "table" or m.active ~= true then return false,"INACTIVE" end
    if type(id) ~= "string" or OWNERS[id] == nil
        or not uid(playerId) or not team(playerTeam) then return false,"INVALID" end
    if m.carryByPlayer[playerId] ~= nil then return false,"FULL_HANDS" end
    local egg=m.eggs[id]
    if egg.state == "CARRIED" then return false,"ALREADY_CARRIED" end
    if egg.state ~= "HOME" and egg.state ~= "VAULT"
        and egg.state ~= "DROPPED" and egg.state ~= "NEUTRAL" then
        return false,"BAD_STATE"
    end
    if egg.owner ~= "NEUTRAL" and playerTeam ~= egg.owner then
        egg.enemyTouched=true
    end
    egg.state="CARRIED"
    egg.controller=playerTeam
    egg.holder=playerId
    egg.heldSeconds=0
    egg.transferSeq+=1
    m.carryByPlayer[playerId]=id
    m.events+=1
    return true,"PICKUP"
end

function Rules.deposit(m: any,playerId: any,playerTeam: any): (boolean,string,number)
    if type(m) ~= "table" or m.active ~= true then return false,"INACTIVE",0 end
    if not uid(playerId) or not team(playerTeam) then return false,"INVALID",0 end
    local id=m.carryByPlayer[playerId]
    if id == nil then return false,"NO_EGG",0 end
    local egg=m.eggs[id]
    if egg.holder ~= playerId or egg.controller ~= playerTeam
        or egg.state ~= "CARRIED" then return false,"INVALID_CARRIER",0 end
    m.carryByPlayer[playerId]=nil
    egg.holder=nil
    egg.state="VAULT"
    egg.controller=playerTeam
    egg.heldSeconds=0
    egg.transferSeq+=1
    local bonus=0
    if egg.owner ~= playerTeam and egg.bonusClaimed[playerTeam] ~= true then
        bonus=if egg.owner == "NEUTRAL" then 10 else 12
        egg.bonusClaimed[playerTeam]=true
    elseif egg.owner == playerTeam and egg.enemyTouched
        and not egg.rescueClaimed then
        bonus=2
        egg.rescueClaimed=true
    end
    m.scores[playerTeam]+=bonus
    m.events+=1
    return true,"DEPOSIT",bonus
end

function Rules.drop(m: any,playerId: any): (boolean,string)
    if type(m) ~= "table" or m.active ~= true then return false,"INACTIVE" end
    if not uid(playerId) then return false,"INVALID" end
    local id=m.carryByPlayer[playerId]
    if id == nil then return false,"NO_EGG" end
    local egg=m.eggs[id]
    if egg.state ~= "CARRIED" or egg.holder ~= playerId then
        return false,"INVALID_CARRIER"
    end
    m.carryByPlayer[playerId]=nil
    egg.state="DROPPED"
    egg.controller=nil
    egg.holder=nil
    egg.transferSeq+=1
    egg.heldSeconds=0
    m.events+=1
    return true,"DROP"
end

local function accrual(e: any): (string?,number,number)
    if e.state == "CARRIED" then
        if e.controller == nil then return nil,0,0 end
        if e.owner == e.controller then return e.controller,30,1 end
        return e.controller,10,1
    elseif e.state == "HOME" or e.state == "VAULT" then
        if e.controller == nil then return nil,0,0 end
        if e.owner == e.controller then return e.controller,20,1 end
        if e.owner == "NEUTRAL" then return e.controller,10,2 end
        return e.controller,10,3
    end
    return nil,0,0
end

function Rules.advance(m: any,seconds: any): (boolean,string)
    if type(m) ~= "table" or m.active ~= true then return false,"INACTIVE" end
    if seconds ~= 1 then return false,"TICK_MUST_BE_ONE_SECOND" end
    m.now+=1
    for _,egg in pairs(m.eggs) do
        local owner,period,amount=accrual(egg)
        if owner ~= nil and period > 0 then
            egg.heldSeconds+=1
            if egg.heldSeconds >= period then
                egg.heldSeconds-=period
                m.scores[owner]+=amount
            end
        else
            egg.heldSeconds=0
        end
    end
    if m.now >= Rules.LENGTH_SECONDS then
        m.active=false
        if m.scores.RED == m.scores.BLUE then
            m.winner="DRAW"
        elseif m.scores.RED > m.scores.BLUE then
            m.winner="RED"
        else
            m.winner="BLUE"
        end
        m.carryByPlayer={}
    end
    return true,"TICK"
end

function Rules.assertConserved(m: any): boolean
    local c=0
    for id,original in pairs(OWNERS) do
        local e=m.eggs[id]
        if e == nil or e.id ~= id or e.owner ~= original then return false end
        if type(e.transferSeq) ~= "number" or e.transferSeq < 0
            or e.transferSeq % 1 ~= 0 then return false end
        if e.state == "CARRIED" then
            if not uid(e.holder) or not team(e.controller)
                or m.carryByPlayer[e.holder] ~= id then return false end
            c+=1
        elseif e.holder ~= nil then
            return false
        elseif e.state == "VAULT" or e.state == "HOME" then
            if not team(e.controller) then return false end
        elseif e.state == "DROPPED" or e.state == "NEUTRAL" then
            if e.controller ~= nil then return false end
        else
            return false
        end
    end
    local count=0
    for _,_ in pairs(m.carryByPlayer) do count+=1 end
    if count ~= c then return false end
    return true
end

return Rules
