workspace:SetAttribute("P0D_ENABLE_PRIVATE_MAGE_PROJECTILES",true)
local specifications={
 {"MAGE-041","MAGE","A",15,.19},
 {"MAGE-025","MAGE","C",-18,.24},
 {"COMBO-004","MAGE","D",-20,.24},
 {"MAGE-001","MAGE","A",20,.18},
 {"MAGE-011","MAGE","A",45,.18},
 {"MAGE-012","MAGE","A",90,.20},
 {"MAGE-026","MAGE","A",-39,.16},
 {"MAGE-040","MAGE","C",-8,.22},
 {"COMBO-005","MAGE","D",18,.22},
 {"NINJA-031","NINJA","B",-18,.18},
 {"NINJA-061","NINJA","C",0,.17},
 {"COMBO-008","NINJA","D",-24,.18},
 {"WARRIOR-071","WARRIOR","B",19,.18},
 {"WARRIOR-016","WARRIOR","C",0,.20},
 {"COMBO-002","WARRIOR","D",-12,.22},
 {"BUILDER-018","BUILDER","B",0,0.2},
 {"BUILDER-040","BUILDER","C",22,0.22},
 {"COMBO-013","BUILDER","D",-15,0.23},
 {"BEAST-005","BEAST","D",-22,0.22},
 {"TRAPPER-015","TRAPPER","B",22,0.22},
 {"TRAPPER-036","TRAPPER","C",-35,0.2},
 {"COMBO-010","TRAPPER","D",32,0.24},
 {"ZOMBIE-035","ZOMBIE","B",45,0.19},
 {"ZOMBIE-040","ZOMBIE","C",0,0.22},
 {"COMBO-019","ZOMBIE","D",19,0.24},
 {"WARRIOR-020","WARRIOR","B",90,0.21},
 {"WARRIOR-060","WARRIOR","C",26,0.22},
 {"COMBO-001","WARRIOR","D",-22,0.23},
 {"MAGE-006","MAGE","A",0,0.21},
 {"MAGE-022","MAGE","B",-38,0.22},
 {"MAGE-058","MAGE","C",14,0.2},
 {"MAGE-069","MAGE","D",90,0.24},
 {"NINJA-025","NINJA","B",-18,0.18},
 {"NINJA-060","NINJA","C",17,0.2},
 {"COMBO-009","NINJA","D",-29,0.22},
}
local sequence=40
for _,row in ipairs(specifications) do
 advance(.41);finishSounds()
 local id,role,slot,rotation,duration=table.unpack(row)
 equip("nonlocalized inventory label"):SetAttribute("EGGRUMBLE_FixedAbilityId",id)
 player:SetAttribute("EGGRUMBLE_Role",role)
 local sounds=#played
 sequence+=1
 cast(role,slot,sequence)
 assert(cue.Visible and cue.Rotation==rotation and tweens[#tweens].duration==duration,id)
 assert(#played==sounds+1 and played[#played].voice.Name=="ConfirmedHit_4",id.." audio")
 assert(played[#played].volume<.15 and #pool:GetChildren()==4,id.." pool")
end
print("FIXED_PRIVATE_CAST_IDS_35_PASS")
advance(.41);finishSounds()
local sounds=#played
local tweenCount=#tweens
equip("nonlocalized inventory label"):SetAttribute("EGGRUMBLE_FixedAbilityId","COMBO-005")
player:SetAttribute("EGGRUMBLE_Role","NINJA")
cast("NINJA","D",sequence+1)
assert(#tweens==tweenCount and #played==sounds,"real Combo D cannot select another role cue")
advance(.41)
player:SetAttribute("EGGRUMBLE_Role","MAGE")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_MAGE_ELEMENTAL",false)
cast("MAGE","D",sequence+2)
assert(#tweens==tweenCount and #played==sounds,"wing cue depends on server elemental gate")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_MAGE_ELEMENTAL",true)
cast("MAGE","D",sequence+3)
assert(cue.Visible and #played==sounds+1)
workspace:SetAttribute("P0D_ENABLE_PRIVATE_MAGE_COMBO_005",false)
assert(not cue.Visible and not played[#played].voice.IsPlaying,"disabling 005 cancels only its own cue")
print("FIXED_PRIVATE_CAST_CUE_ROLE_GATE_AND_CANCELLATION_PASS")

advance(.41);finishSounds()
local total = #played
equip("server owned trapper tool"):SetAttribute("EGGRUMBLE_FixedAbilityId", "COMBO-010")
player:SetAttribute("EGGRUMBLE_Role", "TRAPPER")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_TRAPPER_015", false)
cast("TRAPPER", "D", sequence+5)
assert(#played==total and not cue.Visible)
workspace:SetAttribute("P0D_ENABLE_PRIVATE_TRAPPER_015", true)
cast("TRAPPER", "D", sequence+6)
assert(#played==total+1 and cue.Visible)
workspace:SetAttribute("P0D_ENABLE_PRIVATE_TRAPPER_015", false)
assert(not cue.Visible and not played[#played].voice.IsPlaying)
print("FIXED_PRIVATE_RETURN_REQUIRES_GRAVITY_AND_CANCELS_PASS")
