--!strict
-- TRAP RAIDERS P0D: optional bridge to the byte-preserved D16 ORIGINAL ScaleFxCore.
-- PRECONDITIONS: OWNER-reviewed canonical D08 server callback identity, round and weather mapping.
-- Not an event chooser, Remote listener, appearance renderer, heartbeat, second scheduler, or hitbox edit.
-- Do NOT use with the D16 CLEANROOM core or weather gates V1/V2 (different API).
local Gate = {}
Gate.__index = Gate

local WEATHER = {WX01_METEOR=true,WX02_SMALL=true,WX03_CROWN=true,
    WX04_GLIDE=true,WX05_CLOCK=true}
local STAGE = {S1=true,S2=true,S3=true,S4=true}
local MAX_ROUNDS = 128
local MAX_ROSTER = 16
local function finite(n)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
        and n>=0 and n<=1e12
end
local function validId(s)
    return type(s)=="string" and #s>=1 and #s<=96
        and string.match(s,"^[%w_.-]+$")~=nil
end
local function call(fn,...)
    if type(fn)~="function" then return false,nil end
    local ok,val=pcall(fn,...)
    if not ok then return false,nil end
    return true,val
end
local function snapshotOf(readRound)
    local ok,s=call(readRound)
    if not ok or type(s)~="table" then return nil end
    if not validId(s.matchId) or not STAGE[s.stage] or not finite(s.now)
        or not finite(s.startedAt) or not finite(s.deadline)
        or s.deadline<=s.startedAt or s.now<s.startedAt
        or not finite(s.epoch) or s.epoch%1~=0 or s.epoch>1e6
        or type(s.active)~="boolean" then return nil end
    -- Freeze scalars: callback may yield or mutate a returned snapshot table.
    return {matchId=s.matchId,stage=s.stage,epoch=s.epoch,
        startedAt=s.startedAt,deadline=s.deadline,now=s.now,active=s.active}
end
local function sameRound(a,b)
    return a and b and a.matchId==b.matchId and a.stage==b.stage
        and a.epoch==b.epoch and a.startedAt==b.startedAt
        and a.deadline==b.deadline
end
local function validRoster(roster)
    if type(roster)~="table" or #roster<1 or #roster>MAX_ROSTER then return nil end
    local out,seen={},{}
    for i=1,#roster do
        local id=roster[i]
        if not validId(id) or seen[id] then return nil end
        seen[id]=true;out[i]=id
    end
    return out,seen
end
local function originalCore(core)
    if type(core)~="table" then return false end
    for _,name in ipairs({"new","begin","advance","leave","close","snapshot"}) do
        if type(core[name])~="function" then return false end
    end
    return true
end

function Gate.new(core, config)
    assert(originalCore(core),"D16_ORIGINAL_CORE_REQUIRED")
    assert(type(config)=="table", "SERVER_CONFIG_REQUIRED")
    for _,name in ipairs({"readRound","isCanonicalActivate","isCanonicalCleanup",
        "getTrustedRoster","chooseTrustedGiantActor","mintServerEventId"}) do
        assert(type(config[name])=="function", "TRUSTED_CALLBACK_REQUIRED_"..name)
    end
    local map={}
    if config.subtypeToOriginalKind~=nil then
        assert(type(config.subtypeToOriginalKind)=="table", "TRUSTED_SUBTYPE_MAP_REQUIRED")
        for sub,kind in pairs(config.subtypeToOriginalKind) do
            assert(WEATHER[sub] and (kind=="GIANT_ONE" or kind=="MINI_ALL"),
                "OWNER_REVIEWED_WEATHER_MAPPING_REQUIRED")
            map[sub]=kind
        end
    end
    return setmetatable({core=core,config=config, mapping=map,
        enabled=(config.enabled==true and config.ownerApproved==true),
        stopped=false,active=nil,pending=nil,busy=false,generation=0,
        seen={},seenCount=0,lastNow=0,reason=nil},Gate)
end

local function closeActive(self)
    local active=self.active
    self.active=nil
    if not active then return true end
    local ok,result=pcall(self.core.close,active.state,active.round.matchId)
    if not ok or result~=true then
        self.enabled=false;self.reason="CORE_CLOSE_FAILED"
        return false
    end
    return true
end

local function authentic(fn,envelope)
    local ok,good=call(fn,envelope)
    return ok and good==true
end

function Gate:activate(envelope)
    if not self.enabled or self.stopped then return false,"DISABLED_DEFAULT" end
    if self.busy then return false,"REENTRANT_ACTIVATION" end
    if self.active then return false,"ALREADY_ACTIVE" end
    if type(envelope)~="table" or envelope.phase~="ACTIVATE"
        or envelope.kind~="WEATHER" or not WEATHER[envelope.subtype]
        or not validId(envelope.matchId) or not STAGE[envelope.stage]
        or not finite(envelope.epoch) or envelope.epoch%1~=0
        or not finite(envelope.validUntil) then return false,"INVALID_D08_ENVELOPE" end
    -- Capture scalar fields before any callback can yield or mutate its table.
    local fields={matchId=envelope.matchId,stage=envelope.stage,
        epoch=envelope.epoch,subtype=envelope.subtype,validUntil=envelope.validUntil}
    local function envelopeUnchanged()
        return envelope.matchId==fields.matchId and envelope.stage==fields.stage
            and envelope.epoch==fields.epoch and envelope.subtype==fields.subtype
            and envelope.validUntil==fields.validUntil
            and envelope.phase=="ACTIVATE" and envelope.kind=="WEATHER"
    end
    local kind=self.mapping[fields.subtype]
    if kind==nil then return false,"OWNER_MAPPING_NOT_APPROVED" end
    local initial=snapshotOf(self.config.readRound)
    if not initial or initial.active~=true or initial.now>=initial.deadline
        or initial.now>=envelope.validUntil
        or initial.matchId~=envelope.matchId or initial.stage~=envelope.stage
        or initial.epoch~=envelope.epoch or initial.now<self.lastNow then
        return false,"STALE_OR_INACTIVE_ROUND" end
    local key=initial.matchId..":"..tostring(initial.epoch)
    if self.seen[key] or self.seenCount>=MAX_ROUNDS then
        return false,"DUPLICATE_OR_ROUND_LIMIT" end
    -- Reserve a one-attempt receipt before any yielding trusted callback.
    self.seen[key]=true;self.seenCount+=1
    self.generation+=1
    local ticket=self.generation
    self.busy=true
    self.pending={matchId=initial.matchId,epoch=initial.epoch,stage=initial.stage}
    local function finish(ok,reason)
        self.busy=false
        if self.generation==ticket then self.pending=nil end
        return ok,reason
    end
    if not authentic(self.config.isCanonicalActivate,envelope) then
        return finish(false,"NOT_AUTHENTIC_D08_ENVELOPE")
    end
    local rosterOk, rosterRaw=call(self.config.getTrustedRoster,initial.matchId)
    if not rosterOk then return finish(false,"ROSTER_CALLBACK_FAILED") end
    local roster,seen=validRoster(rosterRaw)
    if not roster then return finish(false,"INVALID_TRUSTED_ROSTER") end
    local actor=nil
    if kind=="GIANT_ONE" then
        local actorOk,selected=call(self.config.chooseTrustedGiantActor,envelope,roster)
        if not actorOk or not validId(selected) or not seen[selected] then
            return finish(false,"INVALID_SERVER_ACTOR")
        end
        actor=selected
    end
    local eventOk,eventId=call(self.config.mintServerEventId,envelope)
    if not eventOk or not validId(eventId) then
        return finish(false,"INVALID_SERVER_EVENT_ID") end
    local fresh=snapshotOf(self.config.readRound)
    if not self.enabled or self.stopped or self.generation~=ticket
        or not fresh or not sameRound(initial,fresh) or fresh.active~=true
        or fresh.now<initial.now or fresh.now<self.lastNow
        or fresh.now>=fresh.deadline or fresh.now>=fields.validUntil
        or not envelopeUnchanged() then
        return finish(false,"REVOKED_OR_CHANGED_DURING_CALLBACK")
    end
    -- Second provenance check may itself yield: revalidate state *after* it.
    if not authentic(self.config.isCanonicalActivate,envelope) then
        return finish(false,"AUTHORITY_RECHECK_FAILED")
    end
    local final=snapshotOf(self.config.readRound)
    if not self.enabled or self.stopped or self.generation~=ticket
        or not final or not sameRound(initial,final) or final.active~=true
        or final.now<fresh.now or final.now<self.lastNow
        or final.now>=final.deadline or final.now>=fields.validUntil
        or not envelopeUnchanged() then
        return finish(false,"REVOKED_AFTER_PROVENANCE_RECHECK")
    end
    self.lastNow=final.now
    local created,state=pcall(self.core.new,initial.matchId)
    if not created or type(state)~="table" then
        self.enabled=false;self.reason="CORE_NEW_FAILED"
        return finish(false,"CORE_NEW_FAILED")
    end
    local invoked,ok,result=pcall(self.core.begin,state,initial.matchId,eventId,kind,
        actor,roster,final.now)
    if not invoked or ok~=true then
        self.enabled=false;self.reason="CORE_BEGIN_FAILED"
        return finish(false,"CORE_BEGIN_FAILED")
    end
    if self.generation~=ticket or not self.enabled or self.stopped then
        pcall(self.core.close,state,initial.matchId)
        return finish(false,"REVOKED_AFTER_BEGIN")
    end
    self.active={round=final,state=state,eventId=eventId,kind=kind,
        epoch=initial.epoch,eventValidUntil=fields.validUntil}
    return finish(true,result)
end

function Gate:cleanup(envelope)
    if type(envelope)~="table" or not validId(envelope.matchId)
        or not finite(envelope.epoch) or envelope.epoch%1~=0
        or not STAGE[envelope.stage]
        or not authentic(self.config.isCanonicalCleanup,envelope) then
        return false,"UNTRUSTED_CLEANUP" end
    local a=self.active
    local p=self.pending
    local matches=(a and a.round.matchId==envelope.matchId
        and a.round.epoch==envelope.epoch and a.round.stage==envelope.stage)
        or (p and p.matchId==envelope.matchId and p.epoch==envelope.epoch
            and p.stage==envelope.stage)
    if not matches then return false,"STALE_CLEANUP" end
    -- Invalidate even an activation suspended inside a trusted callback.
    self.generation+=1
    self.pending=nil
    local ok=closeActive(self)
    return ok, if ok then "CLOSED" else "CORE_CLOSE_FAILED"
end

function Gate:tick()
    if not self.enabled or self.stopped then return false,"DISABLED_DEFAULT" end
    local a=self.active
    if not a then return false,"NO_ACTIVE_EFFECT" end
    local ticket=self.generation
    local s=snapshotOf(self.config.readRound)
    if not self.enabled or self.stopped or self.generation~=ticket or self.active~=a
        or not s or not sameRound(s,a.round) or s.active~=true
        or s.now<a.round.now or s.now<self.lastNow
        or s.now>=s.deadline or s.now>=a.eventValidUntil then
        self.generation+=1
        closeActive(self)
        return false,"ROUND_INVALID_OR_EXPIRED" end
    self.lastNow=s.now
    local invoked,ok,status=pcall(self.core.advance,a.state,a.round.matchId,s.now)
    if not invoked or ok~=true then
        self.enabled=false;self.reason="CORE_ADVANCE_FAILED"
        closeActive(self)
        return false,"CORE_ADVANCE_FAILED"
    end
    if status~="ACTIVE" then
        closeActive(self)
        return true,"EFFECT_ENDED"
    end
    return true,"ACTIVE"
end

function Gate:leavePlayer(trustedPlayerId)
    if not self.enabled or not self.active or not validId(trustedPlayerId) then
        return false,"INVALID_TRUSTED_LEAVE" end
    -- Existing authorized server player-leave callback, never Remote-supplied IDs.
    local tickOk,tickStatus=self:tick()
    if not tickOk or tickStatus~="ACTIVE" then
        return false,"ROUND_OR_EFFECT_NOT_ACTIVE" end
    local a=self.active
    local invoked,ok,status=pcall(self.core.leave,a.state,a.round.matchId,trustedPlayerId)
    if not invoked or ok~=true then
        self.enabled=false;closeActive(self)
        return false,"CORE_LEAVE_FAILED"
    end
    if status~="ACTIVE" then closeActive(self) end
    return true,status
end

function Gate:snapshot()
    if not self.enabled or self.stopped or not self.active then return nil,"NO_ACTIVE_EFFECT" end
    local a=self.active
    local ticket=self.generation
    local r=snapshotOf(self.config.readRound)
    if not self.enabled or self.stopped or self.generation~=ticket or self.active~=a
        or not r or not sameRound(r,a.round) or r.active~=true
        or r.now<a.round.now or r.now<self.lastNow
        or r.now>=r.deadline or r.now>=a.eventValidUntil then
        self.generation+=1;closeActive(self)
        return nil,"ROUND_INVALID_OR_EXPIRED" end
    local ok,value,reason=pcall(self.core.snapshot,a.state,a.round.matchId)
    if not ok or type(value)~="table" then
        self.enabled=false;closeActive(self)
        return nil,"CORE_SNAPSHOT_FAILED" end
    -- Never expose stale ACTIVE visuals merely because the owner skipped a tick.
    if value.status~="ACTIVE" or not finite(value.expiresAt)
        or r.now>=value.expiresAt then
        closeActive(self)
        return nil,"EFFECT_EXPIRED_OR_INACTIVE" end
    self.lastNow=r.now
    -- Pure copied value. No player model/Remote/actual visual mutation here.
    local targets={}
    if type(value.targets)=="table" then
        for i,id in ipairs(value.targets) do targets[i]=id end
    end
    return {matchId=value.matchId,eventId=value.eventId,status=value.status,
        kind=value.kind,scaleMilli=value.scaleMilli,targets=targets,
        expiresAt=value.expiresAt},reason
end

function Gate:stop()
    self.stopped=true;self.enabled=false;self.reason="OWNER_STOP"
    self.generation+=1;self.pending=nil
    local ok=closeActive(self)
    return ok,if ok then "STOPPED" else "CORE_CLOSE_FAILED"
end
return Gate
