--!strict
-- GQ unique V3 ITEM/DASH stale delayed restoration fence.
-- Pure policy: one owner-authorized original pickup calls apply; no Game/Remote/Store.
-- This source has NO effect until selectively composed into original #489 ITEM.
local Lease = {}
local active = setmetatable({}, {__mode = "k"})

function Lease.apply(humanoid: any, session: any, schedule: any, stillOwner: any): boolean
 if not humanoid or not humanoid.Parent or humanoid.Health <= 0 then return false end
 if not session or not session.rules or session.rules.phase ~= "ACTIVE" then return false end
 if not session.world or not session.world.Parent then return false end
 if type(schedule) ~= "function" or type(stillOwner) ~= "function" or not stillOwner() then return false end
 local oldLease = active[humanoid]
 local previous = if oldLease and oldLease.session == session then oldLease.previous else humanoid.WalkSpeed
 if type(previous) ~= "number" or previous ~= previous or previous < 0 or previous > 200 then return false end
 local boosted = math.max(previous, 27)
 -- Unique per-Humanoid identity, not a timestamp that may collide across matches.
 local ticket = {session = session, previous = previous}
 active[humanoid] = ticket
 humanoid.WalkSpeed = boosted
 schedule(5, function()
  if active[humanoid] ~= ticket then return end
  active[humanoid] = nil
  -- A delayed callback from a retired TEAM/BR session cannot edit a new match.
  if not session.rules or session.rules.phase ~= "ACTIVE" then return end
  if not session.world or not session.world.Parent or not stillOwner() then return end
  if humanoid.Parent and humanoid.Health > 0 and humanoid.WalkSpeed == boosted then
   humanoid.WalkSpeed = previous
  end
 end)
 return true
end

function Lease.cancel(humanoid: any)
 active[humanoid] = nil
end
return Lease
