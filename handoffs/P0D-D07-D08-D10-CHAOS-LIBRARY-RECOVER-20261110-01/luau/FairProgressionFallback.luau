--!strict
-- TRAP RAIDERS v42 FALLBACK (new packet, NOT the unavailable v42.2 archive).
-- Pure in-session reference. v42.2 external adapter must be compared before integration.
local Core = {}
local JOBS = {WARRIOR=true,NINJA=true,TRAPPER=true,ZOMBIE_MASTER=true,
    BEAST_TAMER=true,MAGE=true,BUILDER=true}
local MASTERY_THRESHOLDS={100,250,500,1000,2000}
local function finite(n): boolean
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function validId(s): boolean
    return type(s)=="string" and #s>0 and #s<=96 and string.match(s,"^[%w_%-]+$")~=nil
end
local function countAssists(types)
    if type(types)~="table" then return 0 end
    local n=0
    for _,k in ipairs({"DEFENSE","ESCORT","SUPPORT"}) do if types[k]==true then n+=1 end end
    return n
end
function Core.levelForXp(xp:number):number
    if not finite(xp) or xp<0 then return 1 end
    local level=1
    local nextXp=xp
    while level<25 do
        local needed=40+30*(level-1)
        if nextXp<needed then break end
        nextXp-=needed
        level+=1
    end
    return level
end
function Core.masteryForPoints(points:number):number
    if not finite(points) or points<0 then return 0 end
    local star=0
    for i,threshold in ipairs(MASTERY_THRESHOLDS) do
        if points>=threshold then star=i else break end
    end
    return star
end
function Core.new(matchScope:string)
    assert(validId(matchScope))
    return {scope=matchScope,users={},seen={},count=0}
end
-- Trusted caller ONLY: not an API for the client to claim win, XP, duration or assists.
function Core.finalize(s,ev)
    if type(ev)~="table" or not validId(ev.matchId) or ev.scope~=s.scope
       or type(ev.userId)~="number" or ev.userId<1 or ev.userId%1~=0
       or not JOBS[ev.job] or ev.serverRoundFinalized~=true
       or ev.rosterConfirmed~=true or not finite(ev.duration) or ev.duration<=0
       or not finite(ev.activeSeconds) or ev.activeSeconds<0 or ev.activeSeconds>ev.duration then
        return nil,"INVALID_SERVER_EVIDENCE"
    end
    local key=ev.matchId..":"..tostring(ev.userId)
    if s.seen[key] then return nil,"ALREADY_FINALIZED" end
    if s.count>=512 then return nil,"LEDGER_FULL" end
    -- Record no-reward matches too: replaying a later forged version must not pay out.
    s.seen[key]=true
    s.count+=1
    local profile=s.users[ev.userId] or {totalXp=0,mastery={}}
    local activeRequirement=math.min(15,ev.duration*0.3)
    local eligible=ev.activeSeconds>=activeRequirement and ev.meaningfulActionConfirmed==true
    local xp=0
    local mastery=0
    if eligible then
        xp=45+(ev.won==true and 20 or 0)+(ev.eggDelivered==true and 15 or 0)
            +8*countAssists(ev.assistTypes)
        xp=math.min(104,xp)
        mastery=20+(ev.won==true and 15 or 0)+(ev.eggDelivered==true and 10 or 0)
            +4*countAssists(ev.assistTypes)
        mastery=math.min(57,mastery)
    end
    profile.totalXp+=xp
    profile.mastery[ev.job]=(profile.mastery[ev.job] or 0)+mastery
    s.users[ev.userId]=profile
    return {xpAwarded=xp,masteryAwarded=mastery,totalXp=profile.totalXp,
        level=Core.levelForXp(profile.totalXp),jobMastery=Core.masteryForPoints(profile.mastery[ev.job]),
        sessionOnly=true,saved=false,combatStatsChanged=false},"FINALIZED"
end
return Core
