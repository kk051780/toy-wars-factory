-- Engine-independent real Luau behavior assertions; run with pinned native Luau CLI.
local P=require("../EGGRUMBLE_FXBudgetRules")
local names={
 "WarGod_FlyingSlash","Mage_CrystalStorm","Assassin_ShadowAfterimage",
 "Esper_PsiOrbit","MadScientist_RailShot","Beast_FangClaw","CurseMaster_SoulFlame"
}
for _,name in ipairs(names) do
 assert(P.isDecorative(name),name)
 assert(not P.shouldCull(name,124,true,false),name.." near")
 assert(P.shouldCull(name,125,true,false),name.." far-low")
 assert(P.shouldCull(name,150,false,true),name.." forced")
 assert(not P.shouldCull(name,150,false,false),name.." normal")
end
for _,safe in ipairs({
 "FX_WARRIOR_A_FLASH","FX_MAGE_RING","ULTIMATE_Mage_StormPillar",
 "HitSparks","EGGRUMBLE_ItemShield","Castle_1","TacticalRoute_1",
 "EGGRUMBLE_HitConfirmLocal","NeutralStoneGiant"
}) do
 assert(not P.isDecorative(safe),safe)
 assert(not P.shouldCull(safe,999,true,true),safe.." must remain visible")
end
local s=P.newState()
assert(not P.sample(s,20))
assert(P.sample(s,21))
assert(P.sample(s,40))
assert(P.sample(s,48))
assert(not P.sample(s,49))
assert(not P.sample(s,30))
assert(P.sample(s,30))
assert(P.sample(s,33))
assert(P.sample(s,35))
assert(P.sample(s,48))
assert(not P.sample(s,48))
print("EGGRUMBLE_FX_BUDGET_NATIVE_PASS")
