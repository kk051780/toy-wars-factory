--!strict
-- EGGRUMBLE QUALITY: real server-confirmed hit sound, seven distinct role profiles.
-- Optional Studio-only LocalScript. Never creates damage/remotes/rewards or changes world state.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local SoundService=game:GetService("SoundService")
local player=Players.LocalPlayer
if not RunService:IsStudio() then return end
local GROUP="EGGRUMBLE_GQ_ConfirmedHitAudio"
local MIN_GAP=.14
local WINDOW_SECONDS=1
local MAX_PER_WINDOW=6
local MAX_VOICES=4
local MAX_VOLUME=.30
-- Roblox built-in character sound assets; preliminary, not premium final SFX.
local profiles={
 WARRIOR={id="rbxasset://sounds/action_jump_land.mp3",speed=.78,volume=.27},
 MAGE={id="rbxasset://sounds/impact_water.mp3",speed=1.36,volume=.23},
 NINJA={id="rbxasset://sounds/action_jump.mp3",speed=1.80,volume=.19},
 TRAPPER={id="rbxasset://sounds/action_get_up.mp3",speed=1.44,volume=.21},
 BUILDER={id="rbxasset://sounds/action_footsteps_plastic.mp3",speed=.76,volume=.22},
 BEAST={id="rbxasset://sounds/uuhhh.mp3",speed=1.55,volume=.16},
 ZOMBIE={id="rbxasset://sounds/action_swim.mp3",speed=.82,volume=.24},
}
-- Fail closed on accidental duplicate scripts to avoid double sound.
if SoundService:FindFirstChild(GROUP) then
 warn("[EGGRUMBLE GQ AUDIO] duplicate sound module; newer script inactive")
 return
end
local folder=Instance.new("Folder")
folder.Name=GROUP
folder.Parent=SoundService
local voices:{Sound}={}
for i=1,MAX_VOICES do
 local voice=Instance.new("Sound")
 voice.Name="ConfirmedHit_"..i
 voice.Looped=false
 voice.Volume=0
 voice.PlayOnRemove=false
 voice.Parent=folder
 table.insert(voices,voice)
end
local lastSequence=player:GetAttribute("EGGRUMBLE_ImpactSequence")
local lastPlayed=-math.huge
local windowStart=-math.huge
local windowCount=0
local nextVoice=1
local closed=false
local function isEligible():boolean
 if closed or player:GetAttribute("EGGRUMBLE_SFXMuted")==true
  or player:GetAttribute("EGGRUMBLE_Eliminated")==true then return false end
 local character=player.Character
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 return humanoid~=nil and humanoid.Health>0
end
local function confirmedHit()
 local sequence=player:GetAttribute("EGGRUMBLE_ImpactSequence")
 if type(sequence)~="number" or sequence~=sequence or sequence<=0
  or sequence==lastSequence then return end
 lastSequence=sequence
 if not isEligible() then return end
 local now=os.clock()
 if now-lastPlayed<MIN_GAP then return end
 if now-windowStart>=WINDOW_SECONDS then windowStart=now;windowCount=0 end
 if windowCount>=MAX_PER_WINDOW then return end
 local role=player:GetAttribute("EGGRUMBLE_ImpactRole")
 local profile=if type(role)=="string" then profiles[role] else nil
 if not profile then return end
 local weight=player:GetAttribute("EGGRUMBLE_ImpactWeight")
 if type(weight)~="number" or weight~=weight then weight=1 end
 weight=math.clamp(weight,1,3)
 local slot=player:GetAttribute("EGGRUMBLE_ImpactSlot")
 local slotPitch=if slot=="C" then .91 elseif slot=="B" then 1.05 else 1
 local voice=voices[nextVoice]
 nextVoice=nextVoice%MAX_VOICES+1
 voice:Stop()
 voice.SoundId=profile.id
 voice.PlaybackSpeed=math.clamp(profile.speed*slotPitch,.5,2)
 voice.Volume=math.min(MAX_VOLUME,profile.volume*(.85+weight*.08))
 lastPlayed=now
 windowCount+=1
 voice:Play()
end
local onHit=player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)
local onRemove:RBXScriptConnection?=nil
onRemove=player.AncestryChanged:Connect(function(_,parent)
 if parent then return end
 closed=true
 onHit:Disconnect()
 if onRemove then onRemove:Disconnect() end
 for _,voice in ipairs(voices) do voice:Stop() end
 if folder.Parent then folder:Destroy() end
end)
