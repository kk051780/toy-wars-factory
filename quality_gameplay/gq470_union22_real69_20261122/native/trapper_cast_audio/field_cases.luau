do
local rows={
 -- CUE_MATRIX
}
local seq=150
local function fire(role,slot)
 seq+=1
 cast(role,slot,seq)
end
local function install(id,role)
 player:SetAttribute("EGGRUMBLE_Role",role)
 equip("irrelevant localized item name"):SetAttribute("EGGRUMBLE_FixedAbilityId",id)
end
local function finish()
 advance(.41)
 finishSounds()
end
local distinct={}
local assets={}
for _,row in ipairs(rows) do
 finish()
 local id,role,slot,duration,turn,asset,pitch,volume,x,y=table.unpack(row)
 install(id,role)
 local old=#played
 fire(role,slot)
 local tween=tweens[#tweens]
 local sound=played[#played]
 local at=tween.goal.Position
 assert(cue.Visible and cue.Rotation==turn and tween.duration==duration,id.." short animation")
 assert(at and math.abs(at.x-(.5+x))<.00001 and math.abs(at.y-(.56+y))<.00001,id.." motion direction")
 assert(#played==old+1 and sound.id==asset and sound.speed==pitch and sound.volume==volume,id.." accepted cue")
 assert(sound.voice.Name=="ConfirmedHit_4" and #pool:GetChildren()==4 and volume<.12,id.." existing quiet fourth voice")
 local signature=asset.."/"..pitch
 assert(not distinct[signature],id.." identical audible cue")
 distinct[signature]=true;assets[asset]=true
end
local assetsCount=0
for _ in pairs(assets) do assetsCount+=1 end
assert(assetsCount==4 and #rows==18)
print("FIELD_CAST_18_FIXED_ROLE_SLOT_AUDIO_AND_MOTION_PROFILES_PASS")

finish()
install("BEAST-067","BEAST")
local sounds=#played
local tw=#tweens
fire("MAGE","D")
assert(#tweens==tw and #played==sounds and not cue.Visible,"foreign role cannot use held Beast cue")
fire("BEAST","B")
generic();assert(#played==sounds,"wrong slot retains ordinary unthemed cue")
finish()
local decoy=instance("Tool")
decoy.Parent=player.Character
fire("BEAST","D")
assert(#played==sounds and not cue.Visible,"two equipped Tools are ambiguous")
decoy.Parent=nil
player:SetAttribute("EGGRUMBLE_GrowthActive",false)
fire("BEAST","D")
assert(#played==sounds and not cue.Visible,"phase ended")
player:SetAttribute("EGGRUMBLE_GrowthActive",true)
player.Character:SetAttribute("EGGRUMBLE_Downed",true)
fire("BEAST","D")
assert(#played==sounds and not cue.Visible,"downed avatar has no accent")
player.Character:SetAttribute("EGGRUMBLE_Downed",false)
fire("BEAST","D")
assert(#played==sounds+1 and cue.Visible)
workspace:SetAttribute("P0D_ENABLE_PRIVATE_NINJA_CUTS",false)
assert(cue.Visible and played[#played].voice.IsPlaying,"other deck flag cannot cancel this sound")
advance(.29)
assert(not cue.Visible and played[#played].voice.IsPlaying,"stock clip may outlive its reticle")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_BEAST_ELEMENTS",false)
assert(not played[#played].voice.IsPlaying,"late OFF can still stop the isolated cast sound")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_NINJA_CUTS",true)
workspace:SetAttribute("P0D_ENABLE_PRIVATE_BEAST_ELEMENTS",true)
finish()
fire("BEAST","D")
assert(cue.Visible and played[#played].voice.IsPlaying)
player:SetAttribute("EGGRUMBLE_GrowthActive",false)
assert(not cue.Visible and not played[#played].voice.IsPlaying,"round end cancels active accent")
player:SetAttribute("EGGRUMBLE_GrowthActive",true)
finish()
fire("BEAST","D")
assert(cue.Visible and played[#played].voice.IsPlaying)
player:SetAttribute("EGGRUMBLE_Role","MAGE")
assert(not cue.Visible and not played[#played].voice.IsPlaying,"role change cancels active accent")
finish()
install("WARRIOR-004","WARRIOR")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_WARRIOR_TECH",false)
local count=#played
fire("WARRIOR","A")
generic();assert(#played==count,"child warrior deck cannot bypass ancestor OFF")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_WARRIOR_TECH",true)
print("FIELD_CAST_ACTOR_SLOT_AMBIGUITY_PHASE_AND_LIVE_OFF_PASS")

finish()
install("MAGE-079","MAGE")
sounds=#played
player:SetAttribute("EGGRUMBLE_SFXMuted",true)
fire("MAGE","C")
assert(cue.Rotation==-9 and #played==sounds,"muting preserves visual tell")
finish()
player:SetAttribute("EGGRUMBLE_SFXMuted",false)
player:SetAttribute("EGGRUMBLE_ReducedEffects",true)
tw=#tweens
fire("MAGE","C")
assert(#tweens==tw and #played==sounds,"reduced-effects mode suppresses cast-only treatment")
player:SetAttribute("EGGRUMBLE_ReducedEffects",false)
finish()
local char=player.Character
local hum=char:FindFirstChildOfClass("Humanoid")
hum.Health=0;hum.HealthChanged:Fire(0)
fire("MAGE","C")
assert(#tweens==tw and #played==sounds)
local nextChar=avatar("R15")
player.CharacterRemoving:Fire(char)
player.Character=nextChar
player.CharacterAdded:Fire(nextChar)
install("NINJA-008","NINJA")
fire("NINJA","C")
assert(#played==sounds+1 and cue.Visible)
player.CharacterRemoving:Fire(nextChar)
assert(not cue.Visible and not played[#played].voice.IsPlaying)
local nextAvatar=avatar("R6")
player.Character=nextAvatar
player.CharacterAdded:Fire(nextAvatar)
print("FIELD_CAST_MUTE_REDUCED_EFFECTS_OLD_AVATAR_AND_R6_R15_FIXTURE_PASS")

finish()
local before=#played
local seqBase=player:GetAttribute("EGGRUMBLE_ImpactSequence") or 0
install("NINJA-008","NINJA")
fire("NINJA","C")
local castVoice=played[#played].voice
assert(#played==before+1 and castVoice.Name=="ConfirmedHit_4")
player:SetAttribute("EGGRUMBLE_ImpactRole","NINJA")
player:SetAttribute("EGGRUMBLE_ImpactSlot","C")
player:SetAttribute("EGGRUMBLE_ImpactWeight",2)
for n=1,7 do
 player:SetAttribute("EGGRUMBLE_ImpactSequence",seqBase+n)
 if n~=7 then advance(.141) end
end
assert(#played==before+7,"original six confirmed impacts per second plus independent accepted cast")
for index=before+2,#played do
 local impact=played[index]
 assert(impact.volume>.15 and impact.id=="rbxasset://sounds/action_jump.mp3","original HIT profile remains distinct")
end
assert(castVoice.SoundId=="rbxasset://sounds/action_jump.mp3" and castVoice.IsPlaying,"HIT preempts cast on shared voice")
workspace:SetAttribute("P0D_ENABLE_PRIVATE_NINJA_CUTS",false)
assert(castVoice.IsPlaying,"deck OFF must not stop a confirmed impact preempting the cast")
assert(#pool:GetChildren()==4 and not cue.Visible)
print("FIELD_CAST_CONFIRMED_HIT_PRIORITY_AND_SIX_HIT_FOUR_VOICE_CAP_PASS")
end
