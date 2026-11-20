--!strict
-- Executed by pinned native Luau CLI in a temp directory containing Rules.luau and Spec.luau.
-- Source-only simulation: no Roblox engine, physics, Android, NPC pathfinding, or OWNER acceptance.
local Rules=require("./Rules")
local spec=require("./Spec")
assert(spec(Rules)==true, "V3 egg-vault lifecycle regression")
print("EGGRUMBLE_V3_EGG_VAULT_LIFECYCLE_NATIVE_PASS_SOURCE_ONLY")
