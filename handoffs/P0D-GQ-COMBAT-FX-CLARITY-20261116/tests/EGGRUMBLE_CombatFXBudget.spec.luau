--!strict
-- Execute the ACTUAL independent Luau policy, not a Python reimplementation.
-- This is native Luau VM functional proof, not Roblox Studio/FPS testing.
local B = require("../EGGRUMBLE_CombatFXBudget")
local n = 0
local function verify(value:boolean, message:string)
    assert(value,message)
    n += 1
end
local function hide(kind:string,d:number,touch:boolean,reduced:boolean,active:number,previous:boolean?):boolean
    return B.shouldHide(kind,d,touch,reduced,active,previous)
end

-- Critical battle communication MUST NOT be culled, at any distance or load.
for _,kind in ipairs({"CORE","ULTIMATE","KO","HIT","UNKNOWN"}) do
    verify(not hide(kind,10000,true,true,128,true),"critical visual hidden: "..kind)
end
verify(not hide("SECONDARY",0,true,true,128,false),"self impact should remain")
verify(not hide("SECONDARY",40,true,true,128,false),"40-stud near protection")
verify(not hide("SECONDARY",-1,true,false,20,false),"negative distance should fail open")
verify(not hide("SECONDARY",0/0,true,false,20,false),"NaN should fail open")
verify(not hide("SECONDARY",math.huge,true,false,20,false),"Inf should fail open")
-- Mobile culls distant skill decorations earlier than PC without losing close combat.
verify(not hide("SECONDARY",80,true,false,0,false),"visible touch at 80")
verify(hide("SECONDARY",105,true,false,0,false),"distant touch should hide")
verify(not hide("SECONDARY",110,false,false,0,false),"desktop wider visible range")
verify(hide("SECONDARY",150,false,false,0,false),"very far desktop should hide")
-- Low-effects setting and load shedding affect optional decoration only.
verify(hide("SECONDARY",72,true,true,0,false),"reduced effects touch")
verify(hide("SECONDARY",74,true,false,128,false),"crowded mobile")
verify(not hide("SECONDARY",55,false,false,0,false),"desktop near combat")
-- 9-stud hysteresis around touch threshold prevents flickering.
verify(not hide("SECONDARY",90,true,false,0,false),"newly visible still visible")
verify(hide("SECONDARY",95,true,false,0,false),"newly far becomes hidden")
verify(hide("SECONDARY",80,true,false,0,true),"hidden remains hidden until near")
verify(not hide("SECONDARY",75,true,false,0,true),"hidden returns at distance 75")
verify(not hide("SECONDARY",34,true,true,9999,true),"near guard overrides load")
print("EGGRUMBLE_GQ_FX_NATIVE_POLICY_PASS",n)
