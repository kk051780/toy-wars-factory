-- Server-only experimental physical rider mount bridge. DISABLED by default.
-- Only OWNER-PC Codex may enable after real Studio/SeatCore/character review.
-- No RemoteEvent subscriptions. All provider callbacks MUST be server canonical.
local Core = require(script.Parent.RiderMountPolicy)
local Adapter = {}
Adapter.__index = Adapter
local function safePart(x)
    return typeof(x)=="Instance" and x:IsA("BasePart") and x.Parent ~= nil
end
local function safeCharacter(x)
    if typeof(x)~="Instance" or not x:IsA("Model") or x.Parent==nil then return nil end
    local root=x:FindFirstChild("HumanoidRootPart")
    local humanoid=x:FindFirstChildOfClass("Humanoid")
    if not safePart(root) or humanoid==nil or humanoid.Health<=0 then return nil end
    return root,humanoid
end
function Adapter.new(roundId,vehicleId,vehicleType,provider)
    assert(type(provider)=="table" and type(provider.getTrustedSnapshot)=="function"
       and type(provider.getSeatPart)=="function" and type(provider.getCharacter)=="function")
    return setmetatable({enabled=false,core=Core.new(roundId,vehicleId,vehicleType),provider=provider,links={},closed=false},Adapter)
end
function Adapter:_detach(role)
    local link=self.links[role]
    if not link then return end
    self.links[role]=nil
    if link.weld and link.weld.Parent then link.weld:Destroy() end
    -- Do not unseat unrelated new character or remove someone else's constraint.
    local character=self.provider.getCharacter(link.userId,link.characterEpoch)
    if character == link.character then
        local _,humanoid=safeCharacter(character)
        if humanoid then humanoid.Sit=false end
    end
end
function Adapter:_attach(action)
    local character=self.provider.getCharacter(action.userId,action.characterEpoch)
    local root,humanoid=safeCharacter(character)
    local seat=self.provider.getSeatPart(self.core.vehicleId,action.role,action.seatEpoch)
    if not root or not safePart(seat) or not seat.Anchored then return false end
    -- Only trusted server-built seat mounts, not a client-provided CFrame or model.
    if (root.Position-seat.Position).Magnitude>Core.MAX_SEAT_DISTANCE_STUDS then return false end
    if seat.CanCollide then return false end
    local newWeld=Instance.new("WeldConstraint")
    newWeld.Name="P0D_D14_TemporaryRiderMount"
    -- Bounds are checked against genuine server seat part before moving character.
    root.CFrame=seat.CFrame * CFrame.new(0,2,0)
    newWeld.Part0=seat
    newWeld.Part1=root
    newWeld.Parent=seat
    humanoid.Sit=true
    self.links[action.role]={weld=newWeld,userId=action.userId,characterEpoch=action.characterEpoch,character=character}
    return true
end
function Adapter:sync(nowMs)
    if self.closed or not self.enabled then return {ok=false,reason="DISABLED_OR_CLOSED"} end
    local gotSnapshot,snapshot=pcall(self.provider.getTrustedSnapshot,self.core.vehicleId)
    if not gotSnapshot then snapshot=nil end
    local result=Core.update(self.core,snapshot,nowMs)
    if not result.ok then
        for _,action in ipairs(result.unmounts) do self:_detach(action.role) end
        -- Watchdog also detaches when the server snapshot stream expires.
        local guard=Core.watchdog(self.core,nowMs)
        for _,action in ipairs(guard.unmounts) do self:_detach(action.role) end
        return result
    end
    for _,action in ipairs(result.unmounts) do self:_detach(action.role) end
    for _,action in ipairs(result.mounts) do
        if action.role == "PASSENGER" and not self.links.DRIVER then
            Core.releaseFailedMount(self.core,action.role,action.userId,action.characterEpoch)
        elseif not self:_attach(action) then
            Core.releaseFailedMount(self.core,action.role,action.userId,action.characterEpoch)
            if action.role == "DRIVER" then
                -- Physical driver mount failure is terminal; never leave passenger welded alone.
                Core.close(self.core,"PHYSICAL_DRIVER_MOUNT_FAILED")
                self:_detach("DRIVER")
                self:_detach("PASSENGER")
                return {ok=false,reason="PHYSICAL_DRIVER_MOUNT_FAILED"}
            end
        end
    end
    return result
end
function Adapter:close()
    if self.closed then return end
    self.closed=true
    Core.close(self.core,"SHUTDOWN")
    self:_detach("DRIVER")
    self:_detach("PASSENGER")
end
return Adapter
