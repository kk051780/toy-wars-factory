--!strict
-- Engine-independent, server-authoritative decorative eclipse timing.
-- Only colors of NONCOLLIDING ornaments change. No bridge doors or damage.
local Cycle = {}
Cycle.PERIOD_SECONDS = 30
Cycle.STATES = {"SUN", "MOON"}
function Cycle.phase(elapsed: number): string
    if type(elapsed)~="number" or elapsed~=elapsed or elapsed<0
       or elapsed==math.huge or elapsed==-math.huge then return "SUN" end
    if math.floor(elapsed/Cycle.PERIOD_SECONDS)%2==0 then return "SUN" end
    return "MOON"
end
function Cycle.validate(): (boolean,string)
    if Cycle.phase(0)~="SUN" or Cycle.phase(30)~="MOON"
       or Cycle.phase(60)~="SUN" or Cycle.phase(-1)~="SUN" then
       return false,"cycle state"
    end
    return true,"decorative 30s day-night color loop"
end
return Cycle
