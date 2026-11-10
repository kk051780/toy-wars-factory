-- Optional server Model:PivotTo adapter. DISABLED until OWNER PC Codex verified source maps.
-- Does not create Seat/WeldConstraints or transport riders. Existing seats remain D14 owned.
local Core = require(script.Parent.RaftWaterMotionCore)
local Adapter = {}
Adapter.__index = Adapter

local function authorizedModel(model)
    if typeof(model) ~= "Instance" or not model:IsA("Model") or model.Parent==nil then return false end
    local count=0
    for _,part in ipairs(model:GetDescendants()) do
        if part:IsA("BasePart") then
            count+=1
            if not part.Anchored or part.CanCollide or part:IsA("Seat") or part:IsA("VehicleSeat") then return false end
            if count>32 then return false end
        end
    end
    return count>0
end

-- All hooks supplied by the PC original server, not untrusted client payload:
-- snapshot(roundId,driverId,seatEpoch) -> trusted facts table; waterCheck(x,z,stage,raftId)->bool
-- isAuthorizedDriver(raftId,driverId,seatEpoch)->bool; serverClockMs()->number.
function Adapter.new(core, model, hooks, enabled)
    if enabled~=true or type(hooks)~="table" or type(hooks.snapshot)~="function"
        or type(hooks.waterCheck)~="function" or type(hooks.isAuthorizedDriver)~="function"
        or type(hooks.serverClockMs)~="function" or not authorizedModel(model) then
        return nil,"DISABLED_OR_UNVERIFIED"
    end
    return setmetatable({core=core,model=model,hooks=hooks,stopped=false},Adapter),"READY"
end

function Adapter:move(roundId, driverId, seatEpoch, seq, throttle, steer)
    if self.stopped then return "STOPPED" end
    if not self.hooks.isAuthorizedDriver(self.core.raftId,driverId,seatEpoch) then
        return "DENY_DRIVER"
    end
    local serverTime=self.hooks.serverClockMs()
    local facts=self.hooks.snapshot(roundId,driverId,seatEpoch)
    local updated,result=Core.step(self.core,roundId,driverId,seatEpoch,seq,throttle,steer,
        serverTime,facts,self.hooks.waterCheck)
    self.core=updated
    if result=="MOVE_OK" then
        -- Position is computed only by server policy. No client-supplied CFrame accepted.
        self.model:PivotTo(CFrame.new(updated.x,updated.y,updated.z)*CFrame.Angles(0,updated.yaw,0))
    end
    return result
end

function Adapter:stop(roundId)
    self.core=select(1,Core.close(self.core,roundId))
    self.stopped=true
end
return Adapter
