-- D15 local isolated Studio smoke. Put this ServerScript beside a ModuleScript
-- named TrapRescueCore containing the exact reference source, then Play once.
-- NEVER run as a public client or use a Remote to invoke Core directly.
local Core = require(script.Parent:WaitForChild("TrapRescueCore"))
local s = Core.new("STUDIO_D15_SMOKE_001")
assert(select(1, Core.syncPlayer(s, 11, "BLUE", "TRAPPER", true, 0, 0)))
assert(select(1, Core.syncPlayer(s, 22, "RED", "WARRIOR", true, 8, 0)))
assert(select(1, Core.syncPlayer(s, 33, "RED", "MAGE", true, 9, 0)))
assert(select(1, Core.tryCast(s, 11, 22)))
assert(Core.status(s, 22).rooted)
assert(select(1, Core.advance(s, 0.5)))
assert(select(1, Core.tryRescue(s, 33, 22)))
assert(not Core.status(s, 22).trapped)
assert(not select(1, Core.tryCast(s, 11, 22)))
Core.endMatch(s)
assert(not select(1, Core.advance(s, 1)))
print("P0D_D15_SMOKE_PASS reference_only=true")
