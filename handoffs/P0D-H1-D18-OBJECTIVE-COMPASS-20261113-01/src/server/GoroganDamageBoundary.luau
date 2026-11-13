--!strict
-- Server-only final damage boundary for existing GoroganServerRuntime callback.
-- CLIENT REMOTES MUST NEVER DIRECTLY CALL THIS; call only on genuine stomp resolve.
local Players=game:GetService("Players")
local Gate={}
Gate.__index=Gate
local function id(v)
    return type(v)=="string" and #v>=1 and #v<=64 and v:match("^[%w_-]+$")~=nil
end
local function finite(n)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function d2(a,b)
    local d=Vector2.new(a.X-b.X,a.Z-b.Z)
    return d:Dot(d)
end
function Gate.new(deps)
    assert(type(deps)=="table" and deps.integrationApproved==true,
        "DISABLED_UNTIL_OWNER_PC_REVIEW")
    for _,k in ipairs({"isRealRoundEvent","resolvePlayerFromTrustedId",
        "isSafeZone","isDamageImmune","isActiveCombatant","getBossPosition","getAttackCenter",
        "isCanonicalAttackReceipt"}) do
        assert(type(deps[k])=="function",k)
    end
    local self=setmetatable({deps=deps,roundId=nil,eventId=nil,receipts={},total=0,
        active=false,seenRounds={},seenCount=0},Gate)
    return self
end
function Gate:start(roundId,eventId)
    if self.active or not id(roundId) or not id(eventId)
        or self.deps.isRealRoundEvent(roundId,eventId)~=true
        or self.seenRounds[roundId] or self.seenCount>=128 then
        return false,"INVALID_BEGIN"
    end
    self.roundId=roundId;self.eventId=eventId;self.receipts={};self.total=0
    self.active=true
    self.seenRounds[roundId]=true;self.seenCount+=1
    return true,"READY"
end
function Gate:stop(roundId,eventId)
    if not self.active or roundId~=self.roundId or eventId~=self.eventId then
        return false,"STALE_STOP"
    end
    self.active=false;self.receipts={};self.total=0
    self.roundId=nil;self.eventId=nil
    return true,"CLEARED"
end
function Gate:applyServerDamage(playerId,damage,attackId,roundId,eventId)
    if not self.active or roundId~=self.roundId or eventId~=self.eventId
        or self.deps.isRealRoundEvent(roundId,eventId)~=true
        or not id(playerId) or not finite(damage) or damage<=0 or damage>8
        or not finite(attackId) or attackId%1~=0 or attackId<1 or attackId>3 then
        return false,"INVALID_CONTEXT"
    end
    -- This must attest that Core STOMP_RESOLVE actually emitted the specific attack,
    -- not merely that the caller sent an attackId between 1 and 3.
    if self.deps.isCanonicalAttackReceipt(roundId,eventId,attackId)~=true then
        return false,"UNTRUSTED_ATTACK"
    end
    local key=tostring(attackId).."/"..playerId
    if self.receipts[key] then return false,"DUPLICATE_DAMAGE" end
    if self.total>=72 then return false,"BUDGET_EXHAUSTED" end
    local player=self.deps.resolvePlayerFromTrustedId(playerId)
    if typeof(player)~="Instance" or not player:IsA("Player")
        or player.Parent~=Players then return false,"INVALID_SERVER_PLAYER" end
    local character=player.Character
    local hum=character and character:FindFirstChildOfClass("Humanoid")
    local root=character and character:FindFirstChild("HumanoidRootPart")
    if not hum or hum.Health<=0 or not root or not root:IsA("BasePart")
        or self.deps.isSafeZone(player)~=false or self.deps.isDamageImmune(player)~=false
        or self.deps.isActiveCombatant(player,roundId)~=true then
        return false,"IMMUNE_OR_DEAD"
    end
    local center=self.deps.getAttackCenter(roundId,eventId,attackId)
    local boss=self.deps.getBossPosition(roundId,eventId)
    if typeof(center)~="Vector3" or typeof(boss)~="Vector3"
        or math.abs(root.Position.Y-center.Y)>7 or d2(root.Position,center)>49
        or (boss-center).Magnitude>12 then return false,"OUT_OF_RANGE" end
    -- True geometry raycast cannot be delegated to any client.
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances=self.deps.raycastIgnore or {}
    local origin=center+Vector3.new(0,2,0)
    local target=root.Position+Vector3.new(0,1,0)
    local direction=target-origin
    if direction.Magnitude>16 or direction.Magnitude<.01 then return false,"BAD_LOS_RANGE" end
    local hit=workspace:Raycast(origin,direction,params)
    if hit and not hit.Instance:IsDescendantOf(character) then
        return false,"BLOCKED_LOS"
    end
    -- Revalidate immediately before damage; attack receipt consumed once to prevent
    -- re-entrant / duplicate requests from damaging twice.
    if self.deps.isRealRoundEvent(roundId,eventId)~=true or hum.Health<=0
        or self.deps.isSafeZone(player)~=false or self.deps.isDamageImmune(player)~=false
        or self.deps.isActiveCombatant(player,roundId)~=true
        or character~=player.Character or math.abs(root.Position.Y-center.Y)>7
        or d2(root.Position,center)>49 then return false,"STALE_BEFORE_DAMAGE" end
    self.receipts[key]=true;self.total+=1
    hum:TakeDamage(damage)
    return true,"SERVER_HIT_APPLIED"
end
return Gate
