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

-- Abandon a bot-filled preview if its final human leaves.
-- Preserve any match where at least one original human remains connected.
-- No fabricated winner, KO or result panel is produced for an empty match.
function Replay.abandonIfEmpty(session:any,joined:{[number]:string},closeRound:()->()):boolean
 assert(RunService:IsStudio(),"Studio preview only")
 if session.rules.phase~="ACTIVE" or session.roundReplayScheduled then return false end
 for _,entry in ipairs(session.roster) do
  if not entry.isAI then
   local userId=tonumber(entry.id)
   if userId and joined[userId]==session.mode and Players:GetPlayerByUserId(userId) then
    return false
   end
  end
 end
 session.roundReplayScheduled=true
 closeRound()
 return true
end

-- The same small lobby gate cancels its own waiting queue; the opposite gate
-- switches to another mode. No new HUD, remote or secondary lobby.
-- Epoch increments only if the last waiting human leaves; stale countdowns
-- may never auto-start a completely new queue ahead of its own 12s delay.
function Replay.leaveWaitingQueue(mode:string,p:Player,queues:{[string]:{Player}},
 joined:{[number]:string},queueEpoch:{[string]:number},sessions:{[string]:any}):boolean
 assert(RunService:IsStudio(),"Studio preview only")
 if sessions[mode] or joined[p.UserId]~=mode then return false end
 local q=queues[mode]
 if not q then return false end
 local idx=table.find(q,p)
 if not idx then return false end
 table.remove(q,idx)
 joined[p.UserId]=nil
 if #q==0 then
  queueEpoch[mode]=(queueEpoch[mode] or 0)+1
 end
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
  local loaded=pcall(function() p:LoadCharacter() end)
  if not loaded then
   -- A transient Studio respawn failure must not strand an eliminated player.
   -- Bounded retry only when the player is still in the lobby, never in a new match.
   task.delay(1,function()
    if p.Parent~=Players or p:GetAttribute("EGGRUMBLE_QueuedMode")~=nil then return end
    local current=p.Character
    local alive=current and current:FindFirstChildOfClass("Humanoid")
    if alive and alive.Health>0 then return end
    pcall(function() p:LoadCharacter() end)
   end)
  end
 end
end

return Replay
