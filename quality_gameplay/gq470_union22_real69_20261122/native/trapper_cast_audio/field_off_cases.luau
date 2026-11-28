do
local rows={
 -- CUE_MATRIX
}
local seq=150
for _,row in ipairs(rows) do
 advance(.41)
 finishSounds()
 local id,role,slot=table.unpack(row)
 equip("same equipped fixed Tool ID"):SetAttribute("EGGRUMBLE_FixedAbilityId",id)
 player:SetAttribute("EGGRUMBLE_Role",role)
 local sounds=#played
 local priorTweens=#tweens
 seq+=1
 cast(role,slot,seq)
 assert(#played==sounds and #pool:GetChildren()==4,id.." physical OFF adds no themed audio")
 if slot=="D" then
  assert(not cue.Visible and #tweens==priorTweens,id.." no unknown D cue")
 else
  assert(#tweens==priorTweens+1,id.." ordinary A/B/C still plays")
  generic()
 end
end
assert(#rows==18)
print("FIELD_CAST_PHYSICAL_OFF_18_GENERIC_AND_NO_NEW_AUDIO_PASS")
end
