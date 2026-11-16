--!strict
-- EGGRUMBLE V3 Studio-only match-end feedback; no persistent HUD, datastore or paid rewards.
-- Displays only source-true server results (castle outcome, actual neutral KO, egg delivery).
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local ResultService={}
local DISPLAY_SECONDS=8

local function castleEliminations(events:{any},attackerId:string):number
 local n=0
 for _,event in ipairs(events) do
  if event.type=="CASTLE_FALL" and event.attacker==attackerId then n+=1 end
 end
 return n
end

local function resultText(session:any,player:Player,mode:string):(string,string)
 local id=tostring(player.UserId)
 local castle=session.rules.castles[id]
 if not castle then return "試合終了","観戦をありがとう" end
 local won=if mode=="TEAM" then session.rules.winner==castle.team
  else session.rules.winner==id
 local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"
 local kos=0
 if session.swarm and session.swarm.kills then kos=session.swarm.kills[id] or 0 end
 local eggs=castle.depositedEggs or 0
 local fallen=castleEliminations(session.rules.events or {},id)
 return status,"中立撃破 "..tostring(kos).."   卵納入 "..tostring(eggs).."   城攻略 "..tostring(fallen)
end

local function makeResultGui(player:Player,title:string,stats:string,won:boolean)
 local container=player:FindFirstChildOfClass("PlayerGui")
 if not container then return end
 local old=container:FindFirstChild("EGGRUMBLE_MatchResult")
 if old then old:Destroy() end

 local gui=Instance.new("ScreenGui")
 gui.Name="EGGRUMBLE_MatchResult"
 gui.ResetOnSpawn=false
 gui.IgnoreGuiInset=true
 gui.DisplayOrder=35
 gui.Parent=container

 local frame=Instance.new("Frame")
 frame.Name="CompactResult"
 frame.AnchorPoint=Vector2.new(.5,1)
 frame.Position=UDim2.new(.5,0,1,-22)
 frame.Size=UDim2.new(.82,0,0,94)
 frame.BackgroundColor3=Color3.fromRGB(23,34,48)
 frame.BackgroundTransparency=.06
 frame.BorderSizePixel=0
 frame.Parent=gui
 local constraint=Instance.new("UISizeConstraint")
 constraint.MaxSize=Vector2.new(480,94)
 constraint.MinSize=Vector2.new(245,94)
 constraint.Parent=frame
 local corner=Instance.new("UICorner")
 corner.CornerRadius=UDim.new(0,14)
 corner.Parent=frame

 local titleLabel=Instance.new("TextLabel")
 titleLabel.Name="ResultTitle"
 titleLabel.BackgroundTransparency=1
 titleLabel.Size=UDim2.new(1,-24,0,45)
 titleLabel.Position=UDim2.fromOffset(12,4)
 titleLabel.Font=Enum.Font.GothamBlack
 titleLabel.TextScaled=true
 titleLabel.TextColor3=if won then Color3.fromRGB(250,223,119)
  else Color3.fromRGB(230,236,245)
 titleLabel.Text="EGGRUMBLE  "..title
 titleLabel.Parent=frame

 local statsLabel=Instance.new("TextLabel")
 statsLabel.Name="VerifiedPersonalStats"
 statsLabel.BackgroundTransparency=1
 statsLabel.Position=UDim2.fromOffset(12,51)
 statsLabel.Size=UDim2.new(1,-24,0,30)
 statsLabel.Font=Enum.Font.GothamBold
 statsLabel.TextColor3=Color3.fromRGB(232,236,245)
 statsLabel.TextScaled=true
 statsLabel.TextWrapped=false
 statsLabel.Text=stats
 statsLabel.Parent=frame

 task.delay(DISPLAY_SECONDS,function()
  if gui.Parent then gui:Destroy() end
 end)
end

function ResultService.showIfFinished(session:any,queue:{Player},mode:string):boolean
 assert(RunService:IsStudio(),"match result preview is Studio-only")
 if session.resultsDelivered or session.rules.phase~="FINISHED"
  or session.rules.winner==nil then return false end
 -- Consume a finished round once so repeated refresh cannot spam the result overlay.
 session.resultsDelivered=true
 for _,player in ipairs(queue) do
  if player.Parent==Players then
   local castle=session.rules.castles[tostring(player.UserId)]
   if castle then
    local title,stats=resultText(session,player,mode)
    local won=if mode=="TEAM" then session.rules.winner==castle.team
     else session.rules.winner==tostring(player.UserId)
    makeResultGui(player,title,stats,won)
   end
  end
 end
 return true
end

return ResultService
