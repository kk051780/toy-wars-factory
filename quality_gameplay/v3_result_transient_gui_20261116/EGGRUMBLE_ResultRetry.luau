--!strict
-- GQ unique: bounded retries for a transient missing PlayerGui at authentic match end.
-- This pure helper creates NO GUI, score, round or player authority.
local Retry = {}
Retry.MAX_RETRIES = 8
Retry.INTERVAL_SECONDS = 0.25

-- isCurrent(): only this original finished session, real joined player and existing world.
-- renderOnce(): original #487 makeResultGui; true only after actual GUI parented.
-- delay(): server task.delay supplied by original ResultService.
function Retry.deliver(isCurrent: () -> boolean, renderOnce: () -> boolean, delay: (number, () -> ()) -> ()): boolean
 assert(type(isCurrent) == "function" and type(renderOnce) == "function" and type(delay) == "function",
  "server callbacks are required")
 local finished = false
 local retries = 0
 local function attempt()
  if finished then return end
  -- Never place an old result into a new mode/round or a disconnected player.
  local validOK, valid = pcall(isCurrent)
  if not validOK or valid ~= true then
   finished = true
   return
  end
  local renderOK, rendered = pcall(renderOnce)
  if renderOK and rendered == true then
   finished = true
   return
  end
  if retries >= Retry.MAX_RETRIES then
   finished = true
   return
  end
  retries += 1
  delay(Retry.INTERVAL_SECONDS, attempt)
 end
 attempt()
 return finished -- true means immediately delivered OR safely aborted, NOT RC acceptance
end
return Retry
