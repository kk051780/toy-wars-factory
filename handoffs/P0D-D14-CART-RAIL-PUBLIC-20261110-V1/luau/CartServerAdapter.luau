-- Server-only opt-in adapter. Does NOT construct or own models; D14 CART/RAFT visual is other chat's lane.
-- A separate trusted renderer may subscribe to read-only canonical rail pose snapshots.
local Motion = require(script.Parent.CartMotionCore)
local Adapter = {}
Adapter.__index = Adapter
function Adapter.new(route, roundId, teamId, callbacks)
    assert(type(callbacks) == "table")
    assert(type(callbacks.driverFacts) == "function")
    assert(type(callbacks.tickFacts) == "function")
    local state, err = Motion.new(route, roundId, teamId)
    if not state then return nil, err end
    return setmetatable({route=route, state=state, callbacks=callbacks},Adapter)
end
function Adapter:advance(actorFromServerEvent)
    -- ONLY canonical invoking Player from an existing server Remote handler, not client payload.
    -- callbacks.driverFacts MUST check existing D14 seat ledger + server match, alive, egg, snare.
    local facts=self.callbacks.driverFacts(actorFromServerEvent,self.state.roundId,self.state.teamId)
    return Motion.requestNext(self.state,self.route,facts)
end
function Adapter:heartbeat(dt)
    local facts=self.callbacks.tickFacts(self.state.roundId,self.state.teamId)
    local position,status=Motion.step(self.state,self.route,dt,facts)
    -- Return a pure pose snapshot for the VISUAL lane, not a Model/Instance operation.
    local pose={routeId=self.state.routeId,roundId=self.state.roundId,
                teamId=self.state.teamId,leg=self.state.leg,progress=self.state.progress,
                moving=self.state.moving,position=position,direction=self.state.direction}
    return status,pose
end
function Adapter:stop()
    return Motion.stop(self.state)
end
function Adapter:close()
    return Motion.endRound(self.state)
end
return Adapter
