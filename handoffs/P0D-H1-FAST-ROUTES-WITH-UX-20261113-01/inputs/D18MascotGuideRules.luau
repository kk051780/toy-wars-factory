--!strict
-- P0D-FUN-H1-001: DISPLAY-ONLY read of the already authoritative S1 snapshot.
-- Never creates or submits any game/egg/role/damage/reward authority.
local R={}
local PHASE={LOBBY=true,COUNTDOWN=true,ACTIVE=true,RESULTS=true}
local function int(v)
    return type(v)=="number" and v==v and v>=0 and v<=1000000000 and v%1==0
end
function R.accept(s, previousSerial, previousUpdate)
    if type(s)~="table" or s.kind~="SNAPSHOT" then return nil end
    if not int(s.serial) or type(previousSerial)~="number" or type(previousUpdate)~="number" then return nil end
    if s.serial < previousSerial then return nil end
    if s.team~="RED" and s.team~="BLUE" then return nil end
    if not PHASE[s.phase] then return nil end
    if type(s.carrying)~="string" or #s.carrying>64 then return nil end
    local update=s.updateId
    if update~=nil then
        if not int(update) or update<=previousUpdate then return nil end
    elseif previousUpdate>=0 then
        return nil -- A modern ordered stream cannot downgrade to legacy messages.
    end
    local enemy=if s.team=="RED" then "BLUE" else "RED"
    local carrying=(s.carrying~="")
    local destTeam=if carrying then s.team else enemy
    local objective=if carrying then "SCORE_PAD" else "EGG"
    return {
        serial=s.serial,updateId=update,team=s.team,phase=s.phase,
        carrying=carrying,enemy=enemy,destinationTeam=destTeam,
        objective=objective,partName=destTeam.."_"..objective
    }
end
return R
