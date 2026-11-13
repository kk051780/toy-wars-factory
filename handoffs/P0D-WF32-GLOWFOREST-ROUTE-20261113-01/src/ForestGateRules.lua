-- Pure server-side WF32 root-gate policy: no game state mutation.
local Gate={}
Gate.OPEN_SECONDS=7
Gate.COOLDOWN_SECONDS=11
Gate.RADIUS=12
local function finite(n) return type(n)=="number" and n==n and math.abs(n)<math.huge end
function Gate.initial() return {openUntil=0,nextAllowed=0} end
function Gate.activate(s,now,distance)
 if type(s)~="table" or not finite(s.nextAllowed) or not finite(s.openUntil) then
  return false,Gate.initial(),"invalid_state" end
 if not finite(now) or not finite(distance) or distance<0 then
  return false,s,"invalid_input" end
 if distance>Gate.RADIUS then return false,s,"too_far" end
 if now<s.nextAllowed then return false,s,"cooldown" end
 return true,{openUntil=now+Gate.OPEN_SECONDS,nextAllowed=now+Gate.COOLDOWN_SECONDS},"opened"
end
function Gate.isOpen(s,now)
 return type(s)=="table" and finite(now) and finite(s.openUntil) and now<s.openUntil
end
return Gate
