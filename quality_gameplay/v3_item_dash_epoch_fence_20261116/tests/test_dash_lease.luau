--!strict
-- Native Luau VM tests: real policy file, fake Roblox-independent humanoid/session.
local Lease = require("../EGGRUMBLE_DashLease")
local function setup()
 local s = {rules={phase="ACTIVE"}, world={Parent=true}}
 local h = {Parent=true, Health=100, WalkSpeed=16}
 local pending = {}
 local owner = true
 local function schedule(delay, fn)
  assert(delay == 5)
  table.insert(pending, fn)
 end
 local function stillOwner() return owner end
 return s,h,pending,schedule,stillOwner,function(v) owner=v end
end
local passes=0
local function ok(cond)
 assert(cond)
 passes += 1
end
-- 1. Normal expiry restores baseline.
do
 local s,h,q,after,owner=setup()
 ok(Lease.apply(h,s,after,owner) and h.WalkSpeed==27)
 q[1]()
 ok(h.WalkSpeed==16)
end
-- 2. Repeated same-session lease must not leave speed permanently at 27.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 Lease.apply(h,s,after,owner)
 q[1]()
 ok(h.WalkSpeed==27)
 q[2]()
 ok(h.WalkSpeed==16)
end
-- 3. Old TEAM timer cannot override a new BR timer on the same humanoid.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 h.WalkSpeed=16 -- round replay restored baseline
 local s2={rules={phase="ACTIVE"},world={Parent=true}}
 Lease.apply(h,s2,after,owner)
 q[1]()
 ok(h.WalkSpeed==27)
 q[2]()
 ok(h.WalkSpeed==16)
end
-- 4. Retired round cannot write speed after results.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 s.rules.phase="FINISHED"
 q[1]()
 ok(h.WalkSpeed==27) -- cleanup is handled by original Replay.resetHuman
end
-- 5. Destroyed world cancels delayed restoration.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 s.world.Parent=nil
 q[1]()
 ok(h.WalkSpeed==27)
end
-- 6. Membership lost; do not change later match state.
do
 local s,h,q,after,owner,setOwner=setup()
 Lease.apply(h,s,after,owner)
 setOwner(false)
 q[1]()
 ok(h.WalkSpeed==27)
end
-- 7. Another combat effect changed speed; preserve its authority.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 h.WalkSpeed=11
 q[1]()
 ok(h.WalkSpeed==11)
end
-- 8. Dead/removed Humanoid must not be mutated.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 h.Health=0
 q[1]()
 ok(h.WalkSpeed==27)
end
-- 9. Manual cancellation prevents stale callback.
do
 local s,h,q,after,owner=setup()
 Lease.apply(h,s,after,owner)
 Lease.cancel(h)
 q[1]()
 ok(h.WalkSpeed==27)
end
-- 10. Reject invalid session/character and never schedule.
do
 local s,h,q,after,owner=setup()
 s.rules.phase="FINISHED"
 ok(not Lease.apply(h,s,after,owner) and #q==0)
end
print("GQ_ITEM_DASH_EPOCH_NATIVE_PASS",passes)
