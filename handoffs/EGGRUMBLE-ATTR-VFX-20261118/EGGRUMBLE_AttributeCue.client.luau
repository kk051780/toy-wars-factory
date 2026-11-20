-- BATTLE-ATTR-VFX: client only. Existing V3 server skill-cast signature is the sole cue trigger.
-- Deliberately does NOT claim HIT, weakness or block: those require future server-confirmed outcomes.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Input=game:GetService("UserInputService")
local player=Players.LocalPlayer
if not player then return end
local module=ReplicatedStorage:WaitForChild("EGGRUMBLE_ElementVisuals",10)
if not module or not module:IsA("ModuleScript") then return end
local ok,Visual=pcall(require,module)
if not ok or type(Visual)~="table" then return end
local lastSequence=0
local function onConfirmedServerCast()
 local sig=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 local role=player:GetAttribute("EGGRUMBLE_Role")
 local element,seq=Visual.elementForServerCast(sig,role)
 if not element or not seq or seq<=lastSequence then return end
 lastSequence=seq
 if player:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
 local ch=player.Character
 local h=ch and ch:FindFirstChildOfClass("Humanoid")
 local root=ch and ch:FindFirstChild("HumanoidRootPart")
 if not ch or not h or h.Health<=0 or not root or not root:IsA("BasePart") then return end
 -- This is a CAST flourish only, not a proof of a landed HIT or a damage multiplier.
 local where=root.Position+root.CFrame.LookVector*3+Vector3.new(0,2.5,0)
 local lowEnd=Input.TouchEnabled
 Visual.render(element,"ATTACK","NORMAL",where,lowEnd)
end
-- No replay of an old signature after a new client UI attaches.
player:GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature"):Connect(onConfirmedServerCast)
