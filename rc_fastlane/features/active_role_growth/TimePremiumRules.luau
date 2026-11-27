-- #219 V1.3: pure time-effect planning; existing Combat/Growth must own all state.
-- Never expose these functions to a Remote or trust client-supplied parameters.
-- Caller must atomically validate ownership, cast snapshot, CD/E, real distinct hit,
-- round and target identity, anti-farm, immunity, alive, and consume the one-effect receipt.
local M={}
local advance={6,10,15,20,30}
local rewind={5,10,15,20,30}
local duration={2,3,4,5,6}
local function finite(x) return type(x)=="number" and x==x and math.abs(x)<math.huge end
local function stage(s) return finite(s) and s==math.floor(s) and s>=0 and s<=4 end
local function growth(t,T,g0,credit)
    if not finite(t) or t<0 or not finite(T) or T<=0 or not finite(g0) or g0<0 or g0>1
        or not finite(credit) or credit<0 or credit>30 then return nil end
    if t+credit>=T then return 1 end
    return math.clamp(g0+(1-g0)*(t+credit)/T,g0,1)
end
M.naturalGrowth=growth
function M.planAdvance(s,t,T,g0,credit)
    if not stage(s) then return nil,"INVALID_STAGE" end
    local g=growth(t,T,g0,credit)
    if g==nil then return nil,"INVALID_GROWTH" end
    if g==1 then
        if s~=4 then return nil,"NO_CREDIT_ROOM" end
        return table.freeze({kind="GROUND_SPEED_REQUEST",duration=4,maxFraction=0.08})
    end
    local seconds=math.min(advance[s+1],30-credit,math.max(0,T-t-credit))
    if seconds<=0 then return nil,"NO_CREDIT_ROOM" end
    return table.freeze({kind="GROWTH_CREDIT_REQUEST",seconds=seconds})
end
-- All times must come from existing server clock; firstS4Activity is nil before first
-- arrival at S4, otherwise the active-time reading when first S4 was reached.
function M.planRewind(s,t,T,g0,credit,firstS4Activity,alreadyUsed)
    if not stage(s) then return nil,"INVALID_STAGE" end
    local g=growth(t,T,g0,credit)
    if g==nil or type(alreadyUsed)~="boolean" then return nil,"INVALID_GROWTH" end
    if alreadyUsed then return nil,"TARGET_ROUND_LIMIT" end
    if firstS4Activity~=nil and (not finite(firstS4Activity) or firstS4Activity<0 or firstS4Activity>t) then return nil,"INVALID_S4_HISTORY" end
    if (g==1 and firstS4Activity==nil) or (firstS4Activity~=nil and t-firstS4Activity<10) then return nil,"S4_PROTECTED" end
    if g<=g0 then return nil,"INITIAL_FLOOR" end
    return table.freeze({kind="REWIND_REQUEST",seconds=rewind[s+1],duration=duration[s+1],minTelegraph=0.8})
end
-- Call only for a previously accepted, still-current rewind receipt; caller clears
-- on death/round change and on first S4 arrival. No other state is returned or changed.
function M.effectiveGrowth(s,t,T,g0,credit,firstS4Activity,remaining)
    if not stage(s) or not finite(remaining) or remaining<0 or remaining>duration[s+1] then return nil end
    local g=growth(t,T,g0,credit)
    if g==nil then return nil end
    if firstS4Activity~=nil and (not finite(firstS4Activity) or firstS4Activity<0 or firstS4Activity>t) then return nil end
    if remaining==0 or (g==1 and firstS4Activity==nil) or (firstS4Activity~=nil and t-firstS4Activity<10) then return g end
    return math.max(g0,g-math.min((1-g0)*rewind[s+1]/T,0.25))
end
return table.freeze(M)
