--!strict
-- EGGRUMBLE: human/BOT encounter distribution for existing neutral spawn locations.
-- PURE policy only. Does not spawn actors, mutate Humanoids, award KOs, or own a game loop.
-- Original #482 SwarmCombat remains the ONLY neutral combat/spawn authority.
local Fair = {}
Fair.MIN_HUMAN_SHARE = 0.40
Fair.MAX_TARGETS = 32

-- kinds[i] corresponds 1:1 to the existing SwarmCombat aliveTargets()[i] Vector3.
-- Epoch must be the server-owned match/session reference (not a client attribute).
-- Returns candidate INDEX only; caller keeps existing randomized angle and distance.
function Fair.chooseIndex(state: any, epoch: any, kinds: {string}): (number?, string)
 if type(state) ~= "table" then return nil, "INVALID_STATE" end
 if epoch == nil then return nil, "INVALID_EPOCH" end
 if type(kinds) ~= "table" or #kinds > Fair.MAX_TARGETS then
  return nil, "INVALID_TARGETS"
 end

 local humans = {}
 local bots = {}
 for i, kind in ipairs(kinds) do
  if kind == "HUMAN" then
   table.insert(humans, i)
  elseif kind == "BOT" then
   table.insert(bots, i)
  else
   return nil, "INVALID_KIND"
  end
 end
 -- Bot-only or empty matches must not consume neutral spawn slots.
 if #humans == 0 then return nil, "NO_LIVE_HUMAN" end
 if state.epoch ~= epoch then
  state.epoch = epoch
  state.credit = 0.60 -- starts with one early human encounter; bounded accumulator
  state.humanCursor = 0
  state.botCursor = 0
 end
 if #bots == 0 then
  state.humanCursor += 1
  return humans[(state.humanCursor - 1) % #humans + 1], "HUMAN"
 end
 local share = math.max(Fair.MIN_HUMAN_SHARE, #humans / (#humans + #bots))
 state.credit = math.min(1.60, state.credit + share)
 if state.credit >= 1 then
  state.credit -= 1
  state.humanCursor += 1
  return humans[(state.humanCursor - 1) % #humans + 1], "HUMAN"
 end
 state.botCursor += 1
 return bots[(state.botCursor - 1) % #bots + 1], "BOT"
end

function Fair.clear(state: any): ()
 if type(state) ~= "table" then return end
 state.epoch = nil
 state.credit = nil
 state.humanCursor = nil
 state.botCursor = nil
end

return Fair
