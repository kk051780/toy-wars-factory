--!strict
-- P0-D D07: server-only *optional* composition of ALREADY DELIVERED cores.
-- Extract old GoroganServerAICore, GoroganRigDriver, GoroganDamageBoundary,
-- GoroganAttackReceiptWindow as siblings. No second event scheduler or Remote listener.
-- NOT ENABLED until PC Codex reviews true RoundCoordinator and callback provenance.
local Core = require(script.Parent.GoroganServerAICore)
local Combined = {}
Combined.__index = Combined

local MAX_ROSTER = 24
local function validId(v)
    return type(v) == "string" and #v >= 1 and #v <= 64
        and v:match("^[%w_%-]+$") ~= nil
end
local function finite(x)
    return type(x)=="number" and x==x and x~=math.huge and x~=-math.huge
end
local function goodPos(p)
    return type(p)=="table" and finite(p.x) and finite(p.y) and finite(p.z)
        and math.abs(p.x)<=2048 and p.y>=-100 and p.y<=700
        and math.abs(p.z)<=2048
end
local function vec3(p)
    return Vector3.new(p.x,p.y,p.z)
end
local REQUIRED={"isCanonicalActivation","isRoundActive","getCurrentRoundId",
    "getStageId","getNow","getGroundAnchor","getRoster","isLineOfSight",
    "broadcastVisual","mintServerEventId"}
local function callable(x)
    return type(x)=="function"
end
function Combined.new(deps)
    assert(type(deps)=="table" and deps.integrationApproved==true,
        "DISABLED_UNTIL_OWNER_PC_REVIEW")
    for _,key in ipairs(REQUIRED) do
        assert(callable(deps[key]),"MISSING_AUTHORIZED_CALLBACK_"..key)
    end
    for _,key in ipairs({"driver","damageGate","receiptWindow"}) do
        assert(type(deps[key])=="table","MISSING_SERVER_MODULE_"..key)
    end
    local driver,gate,window=deps.driver,deps.damageGate,deps.receiptWindow
    for _,fn in ipairs({"start","stop","getPosition","requestNavigation","checkLifetime"}) do
        assert(callable(driver[fn]),"DRIVER_CONTRACT_"..fn)
    end
    for _,fn in ipairs({"start","stop","applyServerDamage"}) do
        assert(callable(gate[fn]),"GATE_CONTRACT_"..fn)
    end
    for _,fn in ipairs({"openFromCoreResult","close","attests","center"}) do
        assert(callable(window[fn]),"WINDOW_CONTRACT_"..fn)
    end
    return setmetatable({deps=deps,core=Core.new(),active=nil,visualSeq=0,
        epoch=0,busy=false,lastAt=0,closed=false},Combined)
end
local function live(self,a)
    return self.active==a and self.deps.getCurrentRoundId()==a.roundId
        and self.deps.isRoundActive(a.roundId,a.eventId)==true
end
local function sendVisual(self,a,kind,position)
    self.visualSeq+=1
    self.deps.broadcastVisual({kind=kind,matchId=a.roundId,
        stageId=a.stageId,eventId=a.eventId,bossId="GOROGAN",
        seq=self.visualSeq,position=position})
end
local function finish(self,a,reason)
    if self.active~=a then return false,"NOT_ACTIVE" end
    -- Disarm first so a yielding callback cannot authorize another hit.
    self.active=nil
    self.epoch+=1
    self.deps.receiptWindow:close()
    -- Core might have ended itself on lifetime expiry; don't require a second stop.
    Core.stop(self.core,a.roundId,a.eventId)
    -- Stop regardless of individual callback failure; no fake success reports.
    local okRig=pcall(function() self.deps.driver:stop(a.roundId,a.eventId) end)
    local okGate=pcall(function() self.deps.damageGate:stop(a.roundId,a.eventId) end)
    local okVisual=pcall(function() sendVisual(self,a,"END",nil) end)
    if not (okRig and okGate and okVisual) then return false,"CLEANUP_CALLBACK_ERROR" end
    return true,reason or "STOPPED"
end
function Combined:stop(roundId,eventId)
    local a=self.active
    if a==nil or a.roundId~=roundId or a.eventId~=eventId then
        return false,"STALE_STOP"
    end
    return finish(self,a,"STOPPED")
end
function Combined:start(activation)
    if self.active then return false,"ALREADY_ACTIVE" end
    -- Provenance is a genuine server-side object/canonical v40 emission, NOT a
    -- caller's string flag or a client-provided matching table.
    if type(activation)~="table" or activation.event~="ACTIVATE"
        or activation.kind~="BOSS" or activation.subtype~="GOROGAN"
        or not validId(activation.matchId)
        or self.deps.isCanonicalActivation(activation)~=true then
        return false,"NOT_CANONICAL_V40_ACTIVATE"
    end
    local roundId=activation.matchId
    local stage=self.deps.getStageId(roundId)
    if stage~="S1" and stage~="S3" then return false,"STAGE_BLOCKED" end
    if self.deps.getCurrentRoundId()~=roundId then return false,"ROUND_MISMATCH" end
    local now=self.deps.getNow()
    local endAt=activation.untilAt
    local eventId=self.deps.mintServerEventId(activation)
    local anchor=self.deps.getGroundAnchor(stage)
    if not finite(now) or now<0 or not finite(endAt)
        or endAt<=now or not validId(eventId)
        or typeof(anchor)~="Vector3" or not finite(anchor.X)
        or not finite(anchor.Y) or not finite(anchor.Z)
        or self.deps.isRoundActive(roundId,eventId)~=true then
        return false,"UNSAFE_ACTIVATION"
    end
    local ttl=math.min(14,endAt-now)
    if ttl<=2 then return false,"INSUFFICIENT_LIFETIME" end
    local snapshot={roundId=roundId,eventId=eventId,stageId=stage,
        groundPosition=anchor,now=now}
    -- The original physical driver requires a Vector3 ground position while
    -- old Core requires a plain {x,y,z} at the same server-owned anchor.
    local okRig,rigReason=self.deps.driver:start(snapshot)
    if not okRig then return false,"RIG_START_"..tostring(rigReason) end
    local okGate,gateReason=self.deps.damageGate:start(roundId,eventId)
    if not okGate then
        self.deps.driver:stop(roundId,eventId)
        return false,"DAMAGE_GATE_START_"..tostring(gateReason)
    end
    local okCore,coreMsg=Core.start(self.core,{roundId=roundId,eventId=eventId,
        stageId=stage,kind="BOSS",subtype="GOROGAN",now=now,
        endsAt=now+ttl,origin={x=anchor.X,y=anchor.Y,z=anchor.Z}})
    if not okCore then
        self.deps.damageGate:stop(roundId,eventId)
        self.deps.driver:stop(roundId,eventId)
        return false,"CORE_START_"..tostring(coreMsg)
    end
    self.epoch+=1
    self.visualSeq=0
    local a={roundId=roundId,eventId=eventId,stageId=stage,
        startedAt=now,endsAt=now+ttl}
    self.active=a
    self.lastAt=now
    local ok=pcall(function() sendVisual(self,a,"START",coreMsg.position) end)
    if not ok then
        finish(self,a,"VISUAL_START_FAILED")
        return false,"VISUAL_START_FAILED"
    end
    return true,"STARTED"
end
local function validFreshRoster(roster)
    if type(roster)~="table" or #roster>MAX_ROSTER then return false end
    local seen={}
    for _,p in ipairs(roster) do
        if type(p)~="table" or not validId(p.playerId) or seen[p.playerId]
            or (p.team~="BLUE" and p.team~="RED") or not goodPos(p.position)
            or type(p.alive)~="boolean" then
            return false
        end
        seen[p.playerId]=true
    end
    return true
end
local function applyDamage(self,a,cmd,epoch)
    local w=self.deps.receiptWindow
    local okOpen,why=w:openFromCoreResult(cmd,a.roundId,a.eventId)
    if not okOpen then return false,"UNATTESTED_CORE_STOMP_"..tostring(why) end
    -- Guaranteed closure even if a callback throws.
    local ok,reason=pcall(function()
        local fresh=self.deps.getRoster()
        if not validFreshRoster(fresh) then error("INVALID_FRESH_ROSTER") end
        for _,player in ipairs(fresh) do
            if epoch~=self.epoch or not live(self,a) then error("STALE_ROUND_DURING_DAMAGE") end
            if player.alive and player.inSafeZone~=true then
                local p=player.position
                local c=cmd.center
                local dx,dz=p.x-c.x,p.z-c.z
                if math.abs(p.y-c.y)<=7 and dx*dx+dz*dz<=cmd.radius*cmd.radius
                    and self.deps.isLineOfSight(c,player)==true then
                    -- DamageGate must independently revalidate Humanoid, safezone,
                    -- immunity, round and world raycast before TakeDamage.
                    self.deps.damageGate:applyServerDamage(player.playerId,
                        cmd.damage,cmd.attackId,a.roundId,a.eventId)
                end
            end
        end
    end)
    w:close()
    if not ok then return false,"DAMAGE_CALLBACK_FAILED" end
    return true,"DAMAGE_WINDOW_CLOSED"
end
function Combined:heartbeat()
    local a=self.active
    if not a then return nil,"INACTIVE" end
    if self.busy then return nil,"REENTRANT_HEARTBEAT" end
    self.busy=true
    local epoch=self.epoch
    local ok,result,err=pcall(function()
        local now=self.deps.getNow()
        if not finite(now) or now<self.lastAt then error("NON_MONOTONIC_CLOCK") end
        self.lastAt=now
        if not live(self,a) or now>=a.endsAt then
            finish(self,a,"ROUND_OR_BOSS_EXPIRED")
            return {kind="END"},nil
        end
        local expired=self.deps.driver:checkLifetime(now)
        if expired then
            finish(self,a,"PHYSICAL_RIG_EXPIRED")
            return {kind="END"},nil
        end
        local position=self.deps.driver:getPosition()
        if not goodPos(position) then error("MISSING_REAL_BOSS_POSITION") end
        local roster=self.deps.getRoster()
        if not validFreshRoster(roster) then error("INVALID_ROSTER") end
        local cmd,why=Core.tick(self.core,{now=now,roundId=a.roundId,
            eventId=a.eventId,bossPosition=position,players=roster,matchActive=true})
        if why then error("CORE_"..tostring(why)) end
        if not cmd then return nil,nil end
        if cmd.kind=="MOVE" then
            -- OLD runtime omitted time; new Driver requires this exact server time.
            self.deps.driver:requestNavigation(cmd.position,cmd.reason,now)
            if epoch~=self.epoch or not live(self,a) then error("STALE_PATH_YIELD") end
        elseif cmd.kind=="STOMP_WARNING" then
            sendVisual(self,a,"STOMP",cmd.center)
        elseif cmd.kind=="STOMP_RESOLVE" then
            local hitOk,whyHit=applyDamage(self,a,cmd,epoch)
            if not hitOk then error(whyHit) end
        elseif cmd.kind=="END" then
            finish(self,a,"AI_ENDED")
        else
            error("UNKNOWN_CORE_COMMAND")
        end
        return cmd,nil
    end)
    self.busy=false
    if not ok then
        -- Deliberately stop instead of claiming QA PASS or retrying possibly
        -- inconsistent physics/damage state. No automatic restart this round.
        if self.active==a then finish(self,a,"FAIL_CLOSED") end
        return nil,"HEARTBEAT_FAIL_CLOSED"
    end
    return result,err
end
return Combined
