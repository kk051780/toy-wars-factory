--!strict
-- One-tick attestations for a REAL GoroganServerAICore STOMP_RESOLVE output.
-- The existing GoroganServerRuntime MUST be reviewed and modified locally by
-- Codex to open() immediately after Core.tick and close() after damage delivery.
-- Never call open() from a client Remote/instance attribute/client packet.
local Window={}
local function finite(n)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
Window.__index=Window
local function id(s)
    return type(s)=="string" and #s>=1 and #s<=64 and s:match("^[%w_-]+$")~=nil
end
function Window.new()
    return setmetatable({active=nil},Window)
end
function Window:openFromCoreResult(cmd,roundId,eventId)
    if self.active~=nil or type(cmd)~="table" or cmd.kind~="STOMP_RESOLVE"
        or not id(roundId) or not id(eventId) or cmd.roundId~=roundId
        or cmd.eventId~=eventId or type(cmd.attackId)~="number"
        or cmd.attackId%1~=0 or cmd.attackId<1 or cmd.attackId>3
        or type(cmd.center)~="table" or not finite(cmd.center.x)
        or not finite(cmd.center.y) or not finite(cmd.center.z)
        or math.abs(cmd.center.x)>2048 or cmd.center.y<-100 or cmd.center.y>700
        or math.abs(cmd.center.z)>2048 then
        return false,"REJECTED_RECEIPT"
    end
    self.active={roundId=roundId,eventId=eventId,attackId=cmd.attackId,
        center=Vector3.new(cmd.center.x,cmd.center.y,cmd.center.z)}
    return true,"OPEN"
end
function Window:attests(roundId,eventId,attackId)
    local a=self.active
    return a~=nil and a.roundId==roundId and a.eventId==eventId
        and a.attackId==attackId
end
function Window:center(roundId,eventId,attackId)
    if not self:attests(roundId,eventId,attackId) then return nil end
    return self.active.center
end
function Window:close()
    self.active=nil
end
return Window
