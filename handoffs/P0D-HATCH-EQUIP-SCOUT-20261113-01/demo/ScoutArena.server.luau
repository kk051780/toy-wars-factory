-- Studio-only independent physical scout demo for EGG RAID RUMBLE #275.
-- This is NOT integrated in the canonical H1/H2 match or release project.
-- No DataStore, paid items, external remote, marketplace or production deployment.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Rules = require(script.Parent:WaitForChild("RewardEquipRules"))
local s = Rules.new()
local remote = Instance.new("RemoteEvent")
remote.Name = "EggRumbleScoutDemo"
remote.Parent = ReplicatedStorage

local plrIds, teams, nextId, activeScouts = {}, {}, 0, {}
local prng = Random.new(513)
local map = Instance.new("Folder")
map.Name = "EggRumbleScoutDemoWorld"
map.Parent = workspace

local function part(name,size,cf,color,parent,shape)
    local p=Instance.new("Part")
    p.Name=name
    p.Size=size
    p.CFrame=cf
    p.Color=color
    p.Anchored=true
    p.Material=Enum.Material.SmoothPlastic
    p.CanCollide=true
    if shape then p.Shape=shape end
    p.Parent=parent or map
    return p
end
local CYAN=Color3.fromRGB(35,167,238)
local RED=Color3.fromRGB(248,94,112)
local GREEN=Color3.fromRGB(112,235,147)
part("Ground",Vector3.new(146,2,110),CFrame.new(0,-1,0),Color3.fromRGB(76,157,115))
for i,place in ipairs({-52,52}) do
    local color=i==1 and CYAN or RED
    part("CastleBase_"..i,Vector3.new(20,6,20),CFrame.new(place,3,0),color)
    part("Flag_"..i,Vector3.new(2,10,2),CFrame.new(place,11,0),color)
end
part("ArenaIsland",Vector3.new(24,2,24),CFrame.new(0,0,0),Color3.fromRGB(238,194,103))
local centerEgg=part("DecorationEgg",Vector3.new(5,7,5),CFrame.new(0,5,0),Color3.fromRGB(255,226,124),map,Enum.PartType.Ball)
centerEgg.CanCollide=false

local function getRoot(player)
    local c=player.Character
    return c and c:FindFirstChild("HumanoidRootPart")
end
local function notify(player,kind,payload)
    if player and player.Parent==Players then
        remote:FireClient(player,kind,payload)
    end
end
local function allPlayers()
    return Players:GetPlayers()
end
local function idFor(player)
    return plrIds[player]
end
local function clearScout(uid)
    local entry=activeScouts[uid]
    if entry then
        activeScouts[uid]=nil
        if entry.model then entry.model:Destroy() end
    end
end
local function clearAllScouts()
    local copy={}
    for uid in pairs(activeScouts) do table.insert(copy,uid) end
    for _,uid in ipairs(copy) do clearScout(uid) end
end
-- An actual original 3D companion. Both clients receive the same server-owned Model.
local function constructScout(owner,color)
    local root=getRoot(owner)
    if not root then return nil end
    local model=Instance.new("Model")
    model.Name="Scout_"..owner.Name
    local pos=root.Position+Vector3.new(3,4,0)
    local core=part("Body",Vector3.new(3,2.3,3),CFrame.new(pos),color,model,Enum.PartType.Ball)
    core.CanCollide=false
    for _,side in ipairs({-1,1}) do
        local wing=part("Wing_"..side,Vector3.new(2.8,0.4,1.4),
            CFrame.new(pos+Vector3.new(side*2.3,0,0))*CFrame.Angles(0,0,math.rad(side*22)),
            Color3.fromRGB(244,244,255),model)
        wing.CanCollide=false
        local eye=part("Eye_"..side,Vector3.new(0.45,0.5,0.5),
            CFrame.new(pos+Vector3.new(side*0.7,0.4,-1.3)),
            Color3.fromRGB(30,35,54),model,Enum.PartType.Ball)
        eye.CanCollide=false
    end
    local halo=part("Antenna",Vector3.new(0.6,1.8,0.6),
        CFrame.new(pos+Vector3.new(0,1.9,0)),Color3.fromRGB(250,216,88),model)
    halo.CanCollide=false
    model.PrimaryPart=core
    local outline=Instance.new("Highlight")
    outline.Name="TeamSilhouette"
    outline.FillColor=color
    outline.FillTransparency=0.72
    outline.OutlineColor=Color3.new(1,1,1)
    outline.Parent=model
    local prompt=Instance.new("ProximityPrompt")
    prompt.ActionText="追い払う"
    prompt.ObjectText="敵の偵察魔獣"
    prompt.HoldDuration=0.5
    prompt.MaxActivationDistance=8
    prompt.RequiresLineOfSight=false
    prompt.Parent=core
    model.Parent=map
    return model,prompt
end
local function sendSnapshot(player)
    local uid=idFor(player)
    if not uid then return end
    local data=Rules.export(s,uid)
    notify(player,"STATE",{
        equipped=data and data.equipped or "starter_scout",
        ownsStar=(data and data.owned.star_scout or 0)>0,
        ownsForest=(data and data.owned.forest_scout or 0)>0,
        phase=s.phase,epoch=s.epoch,
        team=teams[uid]
    })
end
local function spawnScout(owner,uid,token)
    clearScout(uid)
    local color=teams[uid]=="RED" and RED or CYAN
    local model,prompt=constructScout(owner,color)
    if not model then return false end
    local entry={model=model,owner=owner,uid=uid,epoch=s.epoch,
        untilAt=os.clock()+token.duration, interrupted=false, detected=false}
    activeScouts[uid]=entry
    prompt.Triggered:Connect(function(actor)
        if activeScouts[uid]~=entry then return end
        local actorUid=idFor(actor)
        local actorRoot=getRoot(actor)
        if not actorUid or teams[actorUid]==teams[uid] or not actorRoot then return end
        if (actorRoot.Position-model:GetPivot().Position).Magnitude>9 then return end
        entry.interrupted=true
        notify(owner,"INFO","偵察魔獣が相手に追い払われた！")
        notify(actor,"INFO","敵の偵察を阻止！")
        clearScout(uid)
    end)
    task.spawn(function()
        while activeScouts[uid]==entry and os.clock()<entry.untilAt and
            s.phase=="ACTIVE" and s.epoch==entry.epoch do
            local ownerRoot=getRoot(owner)
            if not ownerRoot then break end
            local target=nil
            local closest=30
            for _,opponent in ipairs(allPlayers()) do
                local otherUid=idFor(opponent)
                local hrp=getRoot(opponent)
                if otherUid and teams[otherUid]~=teams[uid] and hrp then
                    local dist=(hrp.Position-model:GetPivot().Position).Magnitude
                    if dist<closest then target=hrp;closest=dist end
                end
            end
            local desired = target and target.Position+Vector3.new(0,5,0) or
                ownerRoot.Position+ownerRoot.CFrame.LookVector*5+Vector3.new(0,4,0)
            local current=model:GetPivot().Position
            local delta=desired-current
            local maxStep=2.5
            local nextPos=delta.Magnitude>maxStep and current+delta.Unit*maxStep or desired
            model:PivotTo(CFrame.new(nextPos))
            if target and closest<21 then
                model.TeamSilhouette.FillTransparency=0.15
                if not entry.detected then
                    entry.detected=true
                    notify(owner,"SCOUT_FOUND","敵を発見！魔獣の光を見て追跡")
                end
            else
                model.TeamSilhouette.FillTransparency=0.72
                entry.detected=false
            end
            task.wait(0.15)
        end
        if activeScouts[uid]==entry then clearScout(uid) end
    end)
    return true
end
local function addPlayer(player)
    nextId+=1
    local uid=nextId -- Positively numbered private Studio stand-in, not real user DataStore IDs.
    plrIds[player]=uid
    teams[uid]=(nextId%2==1) and "BLUE" or "RED"
    Rules.enroll(s,uid)
    player.CharacterAdded:Connect(function(character)
        task.defer(function()
            local root=character:WaitForChild("HumanoidRootPart",5)
            if root then
                local x=teams[uid]=="BLUE" and -50 or 50
                root.CFrame=CFrame.new(x,10,0)
            end
        end)
    end)
    notify(player,"INFO","待機中。2人そろうと自動開始！")
    sendSnapshot(player)
end
Players.PlayerAdded:Connect(addPlayer)
for _,plr in ipairs(allPlayers()) do addPlayer(plr) end
Players.PlayerRemoving:Connect(function(player)
    local uid=idFor(player)
    if uid then clearScout(uid) end
    plrIds[player]=nil
end)
remote.OnServerEvent:Connect(function(player,action,arg)
    if type(action)~="string" then return end
    local uid=idFor(player)
    if not uid then return end
    if action=="EQUIP" and type(arg)=="string" and #arg<40 then
        local ok,err=Rules.equip(s,uid,arg,"BEASTMASTER")
        notify(player,ok and "INFO" or "ERROR",ok and ("装備："..arg) or err)
        sendSnapshot(player)
    elseif action=="SCOUT" then
        if not getRoot(player) then
            notify(player,"ERROR","キャラ生成待ち")
            return
        end
        local ok,token=Rules.requestScout(s,uid,s.epoch,math.floor(os.clock()))
        if ok then
            if not spawnScout(player,uid,token) then
                notify(player,"ERROR","キャラ未生成のため召喚できません")
            end
        else
            notify(player,"ERROR",token)
        end
    end
end)
-- Server-only trial timeline. No client is allowed to decide round wins or hatch odds.
task.spawn(function()
    while true do
        if #allPlayers()>=2 and s.phase=="LOBBY" then
            for _,player in ipairs(allPlayers()) do sendSnapshot(player) end
            task.wait(7)
            if #allPlayers()>=2 and s.phase=="LOBBY" then
                local epoch=s.epoch+1
                Rules.startRound(s,epoch)
                for _,player in ipairs(allPlayers()) do
                    notify(player,"INFO","20秒の偵察ラウンド開始！魔獣召喚ボタンを押してね")
                    sendSnapshot(player)
                end
                task.wait(20)
                local eligible,rare={},{}
                for _,player in ipairs(allPlayers()) do
                    local uid=idFor(player)
                    if uid then
                        eligible[uid]=true
                        rare[uid]=false -- no egg authority in this isolated demo
                    end
                end
                local ok=Rules.finishRound(s,epoch,eligible,rare)
                clearAllScouts()
                if ok then
                    for _,player in ipairs(allPlayers()) do
                        local uid=idFor(player)
                        if uid then
                            local granted,item=Rules.claimFreeHatch(s,uid,epoch,prng:NextInteger(1,10000))
                            if granted then notify(player,"HATCH",item) end
                            sendSnapshot(player)
                        end
                    end
                end
            end
        end
        task.wait(1)
    end
end)
