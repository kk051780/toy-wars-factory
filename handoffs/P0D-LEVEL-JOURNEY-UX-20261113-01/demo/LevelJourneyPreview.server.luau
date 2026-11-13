--!strict
-- EGG RAID RUMBLE: private read-only visual preview only.
-- Scripted legitimate policy events simulate 60s rounds in short time.
-- NOT the actual two-mode game, not actual participation and not persistent.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local P=require(script.Parent:WaitForChild("ProgressionRules"))
local View=require(script.Parent:WaitForChild("LevelJourneyView")).new(P)
local signal=Instance.new("RemoteEvent")
signal.Name="EggRumbleLevelJourneyPreviewRemote"
signal.Parent=ReplicatedStorage
local joinCounter=100000000
local profiles={}
local revisions={}
local function playerId(player)
    if player.UserId>0 then return player.UserId end
    joinCounter+=1
    return joinCounter
end
local function nextRevision(player)
    revisions[player]=(revisions[player] or 0)+1
    return revisions[player]
end
local function notify(player,view)
    if view and player.Parent==Players then signal:FireClient(player,view) end
end
local function snapshot(player,round)
    local record=profiles[player]
    if not record then return end
    local dto=View.snapshot(record,round,"starter_scout",nextRevision(player))
    notify(player,dto)
end
local function demoPlayer(player)
    local uid=playerId(player)
    local record=P.newProfile(uid)
    if not record then return end
    profiles[player]=record
    snapshot(player,nil)
    task.spawn(function()
        local i=0
        while profiles[player]==record and player.Parent==Players and i<5 do
            i+=1
            task.wait(5)
            if profiles[player]~=record or player.Parent~=Players then break end
            -- GENERATED SERVER-SIDE DEMO EVENTS: not tied to any real egg actions.
            local round=P.newRound("STUDIO_PREVIEW_"..uid.."_"..i,uid,"SCORE",
                "starter_scout",true)
            if not round then break end
            local actions={"DEPOSIT","DEFEND","PICKUP","EQUIP_USE","ESCORT","PICKUP"}
            for j,eventKind in ipairs(actions) do
                if profiles[player]~=record or player.Parent~=Players then return end
                local ok=P.recordEvent(round,"preview_"..i.."_"..j,eventKind,true)
                if not ok then break end
                snapshot(player,round)
                task.wait(.45)
            end
            local before={level=record.level,playerUserId=uid}
            local settled=P.commit(record,round,"LOSS",60,true) -- virtual duration: DEMO ONLY
            if settled then
                notify(player,View.settlement(before,record,settled,"starter_scout",nextRevision(player)))
            end
            snapshot(player,nil)
            task.wait(2)
        end
    end)
end
Players.PlayerAdded:Connect(demoPlayer)
Players.PlayerRemoving:Connect(function(player)
    profiles[player]=nil
    revisions[player]=nil
end)
for _,player in ipairs(Players:GetPlayers()) do demoPlayer(player) end
