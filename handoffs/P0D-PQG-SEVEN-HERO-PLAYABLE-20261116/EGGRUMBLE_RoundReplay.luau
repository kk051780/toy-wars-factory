--!strict
-- EGGRUMBLE Studio-only replay cleanup after genuine round end.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Replay={}
Replay.RESULT_HOLD_SECONDS=10 -- result panel is visible for 8 seconds

function Replay.schedule(session:any,closeRound:()->()):boolean
 assert(RunService:IsStudio(),"Studio preview only")
 if session.roundReplayScheduled or session.rules.phase~="FINISHED"
  or session.rules.winner==nil then return false end
 session.roundReplayScheduled=true
 task.delay(Replay.RESULT_HOLD_SECONDS,function()
  -- closeRound checks the session identity to avoid clearing a newer match.
  if session.rules.phase=="FINISHED" then closeRound() end
 end)
 return true
end

function Replay.resetHuman(p:Player,returnTo:Vector3):()
 if p.Parent~=Players then return end
 p:SetAttribute("EGGRUMBLE_QueuedMode",nil)
 p:SetAttribute("EGGRUMBLE_Eliminated",nil)
 p:SetAttribute("EGGRUMBLE_NeutralKOs",0)
 p:SetAttribute("EGGRUMBLE_BattleLevel",1)
 p:SetAttribute("EGGRUMBLE_SlashEvolution","BASE")
 p:SetAttribute("EGGRUMBLE_StealthUntil",nil)
 p:SetAttribute("EGGRUMBLE_GiantFeedUntil",nil)
 p:SetAttribute("EGGRUMBLE_Role",nil)
 local stats=p:FindFirstChild("leaderstats")
 local ko=stats and stats:FindFirstChild("NeutralKO")
 if ko and ko:IsA("IntValue") then ko.Value=0 end
 local ch=p.Character
 local hum=ch and ch:FindFirstChildOfClass("Humanoid")
 local root=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
 if hum and hum.Health>0 and root then
  root.CFrame=CFrame.new(returnTo)
 else
  pcall(function() p:LoadCharacter() end)
 end
end

return Replay
