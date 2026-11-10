--!strict
-- Isolated server-only adapter for an existing true RoundCoordinator and
-- existing server-owned physical Humanoid rig. This script DOES NOT spawn a
-- rig, own the boss-roll, or subscribe to client Remotes. OFF by default.
local Core = require(script.Parent.GoroganServerAICore)
local Runtime = {}
Runtime.__index=Runtime
local function finite(n)
    return type(n)=="number" and n==n and n~=-math.huge and n~=math.huge
end
local function planar(a,b)
    local dx,dz=a.x-b.x,a.z-b.z
    return dx*dx+dz*dz
end
local REQUIRED={"getBossPosition","getRoster","isRoundActive","requestNavigation",
    "broadcastVisual","isLineOfSight","applyServerDamage","getStageId","isCanonicalBossActivation"}
function Runtime.new(deps)
    assert(type(deps)=="table" and deps.integrationApproved==true,
        "DISABLED_UNTIL_OWNER_PC_INTEGRATION")
    for _,name in ipairs(REQUIRED) do assert(type(deps[name])=="function",name) end
    local self=setmetatable({},Runtime)
    self.deps=deps
    self.core=Core.new()
    self.visualSeq=0
    return self
end
local function visual(self,kind,cmd)
    self.visualSeq+=1
    -- The previously shipped D07 visual packet expects seq and bossId.
    self.deps.broadcastVisual({kind=kind,bossId="GOROGAN",
        matchId=cmd.roundId,stageId=self.deps.getStageId(),
        eventId=cmd.eventId,seq=self.visualSeq,
        position=cmd.position or cmd.center})
end
function Runtime:start(canonicalActivation)
    -- ONLY an actual authoritative ChaosEventCore ACTIVATE can call this.
    -- The boolean gate below is an integration assertion, not proof of origin.
    if self.deps.isCanonicalBossActivation(canonicalActivation)~=true
        or self.deps.getStageId() ~= canonicalActivation.stageId
        or self.deps.isRoundActive(canonicalActivation.roundId,canonicalActivation.eventId)~=true then
        return false,"UNCERTIFIED_ACTIVATION"
    end
    local ok,cmd=Core.start(self.core,canonicalActivation)
    if ok then self.visualSeq=0; visual(self,"START",cmd) end
    return ok,cmd
end
function Runtime:stop(roundId,eventId)
    local cmd,err=Core.stop(self.core,roundId,eventId)
    if cmd then visual(self,"END",cmd) end
    return cmd,err
end
function Runtime:heartbeat(now,roundId,eventId)
    if self.deps.isRoundActive(roundId,eventId)~=true then
        return self:stop(roundId,eventId)
    end
    local bossPosition=self.deps.getBossPosition()
    local players=self.deps.getRoster() -- authoritative, no client snapshot
    local cmd,err=Core.tick(self.core,{now=now,roundId=roundId,eventId=eventId,
        bossPosition=bossPosition,players=players,matchActive=true})
    if not cmd then return nil,err end
    if cmd.kind=="MOVE" then
        -- Real navigation/pathfinding & ground probes stay in SERVER callback.
        self.deps.requestNavigation(cmd.position,cmd.reason)
    elseif cmd.kind=="STOMP_WARNING" then
        visual(self,"STOMP",{roundId=cmd.roundId,eventId=cmd.eventId,center=cmd.center})
    elseif cmd.kind=="STOMP_RESOLVE" then
        -- Reacquire fresh authoritative positions at the actual impact instant.
        -- No cached target/visual packet may directly apply damage.
        local fresh=self.deps.getRoster()
        if type(fresh)~="table" or #fresh>24 then return nil,"INVALID_FRESH_ROSTER" end
        local seen={}
        for _,p in ipairs(fresh) do
            if type(p)=="table" and type(p.playerId)=="string" and not seen[p.playerId] then
                seen[p.playerId]=true
                if p.alive==true and (p.team=="BLUE" or p.team=="RED")
                    and p.inSafeZone~=true and type(p.position)=="table" then
                    local v=p.position
                    if finite(v.x) and finite(v.y) and finite(v.z)
                        and math.abs(v.y-cmd.center.y)<=7
                        and planar(v,cmd.center)<=cmd.radius*cmd.radius
                        and self.deps.isLineOfSight(cmd.center,p)==true then
                        -- Callback must resolve true live Humanoid/UserId, re-check
                        -- round ownership and damage immunity, and cap further hits.
                        self.deps.applyServerDamage(p.playerId,cmd.damage,cmd.attackId,
                            roundId,eventId)
                    end
                end
            end
        end
    elseif cmd.kind=="END" then
        visual(self,"END",cmd)
    end
    return cmd,nil
end
return Runtime
