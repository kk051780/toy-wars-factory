--!strict
-- H2 multi-egg scored match laboratory ONLY. NOT the official H1 Game.server.
-- All 5 eggs, team identity, pickup, delivery, scoring and result are server-owned.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
local Rules=require(script.Parent:WaitForChild("MultiEggRules"))

if not RunService:IsStudio() then return end

local match=Rules.new()
local holderIds: {[Player]: number}={}
local idByPlayer: {[number]: Player}={}
local sideByPlayer: {[Player]: string}={}
local nextHolderId=0
local started=false
local eggWorld: {[string]: BasePart}={}
local eggPrompts: {[string]: ProximityPrompt}={}
local welds: {[string]: WeldConstraint}={}

local arena=Instance.new("Folder")
arena.Name="P0D_H2_FIVE_EGG_LAB_NOT_H1"
arena.Parent=workspace
local replicated=Instance.new("Folder")
replicated.Name="P0D_H2_MultiEggScoreState"
replicated.Parent=ReplicatedStorage
replicated:SetAttribute("Mode","H2_5_EGG_SCORE_STUDIO_LAB")
replicated:SetAttribute("RED",0)
replicated:SetAttribute("BLUE",0)
replicated:SetAttribute("SECONDS",Rules.LENGTH_SECONDS)
replicated:SetAttribute("ACTIVE",false)
replicated:SetAttribute("WINNER","")
local function block(name: string,pos: Vector3,size: Vector3,col: Color3): Part
    local p=Instance.new("Part")
    p.Name=name;p.Anchored=true;p.Size=size
    p.Material=Enum.Material.SmoothPlastic;p.Color=col
    p.CFrame=CFrame.new(pos);p.Parent=arena
    return p
end
local function prompt(parent: Instance,action: string,obj: string): ProximityPrompt
    local p=Instance.new("ProximityPrompt")
    p.Name="ServerValidatedAction"
    p.ActionText=action;p.ObjectText=obj
    p.MaxActivationDistance=9;p.RequiresLineOfSight=false
    p.HoldDuration=.18;p.Parent=parent
    return p
end
local function sign(parent: BasePart,message: string,color: Color3)
    local g=Instance.new("BillboardGui")
    g.Size=UDim2.fromOffset(210,48)
    g.StudsOffset=Vector3.new(0,4,0)
    g.AlwaysOnTop=true;g.MaxDistance=90
    g.Parent=parent
    local t=Instance.new("TextLabel")
    t.Name="Sign";t.Size=UDim2.fromScale(1,1)
    t.BackgroundColor3=Color3.fromRGB(19,28,50)
    t.BackgroundTransparency=.12
    t.TextColor3=color;t.Font=Enum.Font.GothamBold
    t.TextSize=18;t.TextWrapped=true;t.Text=message;t.Parent=g
end
block("NeutralFloor",Vector3.new(0,-.5,0),Vector3.new(182,1,96),Color3.fromRGB(35,63,73))
local red=Color3.fromRGB(235,77,79)
local blue=Color3.fromRGB(72,152,246)
local gold=Color3.fromRGB(251,218,102)
for _,def in ipairs({
    {"RED",Vector3.new(-66,1,0),red},
    {"BLUE",Vector3.new(66,1,0),blue}
}) do
    local name=def[1] :: string
    local pos=def[2] :: Vector3
    local col=def[3] :: Color3
    block(name.."_CASTLE",pos+Vector3.new(0,3,0),Vector3.new(12,7,23),col)
    local pad=block(name.."_VAULT_PAD",pos+Vector3.new(12,0.25,0),Vector3.new(9,.5,11),gold)
    local pu=prompt(pad,"卵を金庫へ納める",name.."のお城")
    sign(pad,name.." 金庫へ運ぶ！",col)
    pu.Triggered:Connect(function(player: Player)
        if not started or not match.active or sideByPlayer[player]~=name then return end
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        local hum=character and character:FindFirstChildOfClass("Humanoid")
        if not root or not hum or hum.Health<=0 then return end
        if (root.Position-pad.Position).Magnitude>12 then return end
        local holder=holderIds[player]
        if not holder then return end
        local eggId=match.carryByPlayer[holder]
        if not eggId then return end
        local ok,_,_bonus=Rules.deposit(match,holder,name)
        if not ok then return end
        local part=eggWorld[eggId]
        local weld=welds[eggId]
        if weld then weld:Destroy();welds[eggId]=nil end
        part.Anchored=true
        part.CanCollide=false
        part.CFrame=CFrame.new(pos+Vector3.new(12+(eggId:byte(1)%3)*1.7,3,0))
        eggPrompts[eggId].Enabled=true
    end)
end
block("CENTER_NEST",Vector3.new(0,.5,0),Vector3.new(15,1,15),Color3.fromRGB(124,83,169))
local initial={
    R1=Vector3.new(-60,4,-6),
    R2=Vector3.new(-60,4,6),
    B1=Vector3.new(60,4,-6),
    B2=Vector3.new(60,4,6),
    N1=Vector3.new(0,4,0),
}
local colorByOwner={RED=red,BLUE=blue,NEUTRAL=gold}
local function safeDropPosition(player: Player): Vector3
    local char=player.Character
    local root=char and char:FindFirstChild("HumanoidRootPart")
    local p=if root and root:IsA("BasePart") then root.Position else Vector3.new(0,3,0)
    return Vector3.new(math.clamp(p.X,-81,81),3,math.clamp(p.Z,-41,41))
end
local function dropPlayer(player: Player)
    local holder=holderIds[player]
    if not holder then return end
    local eggId=match.carryByPlayer[holder]
    if eggId==nil then return end
    local spot=safeDropPosition(player)
    local ok=Rules.drop(match,holder)
    if not ok then return end
    if welds[eggId] then welds[eggId]:Destroy();welds[eggId]=nil end
    local egg=eggWorld[eggId]
    egg.Anchored=true
    egg.CanCollide=false
    egg.CFrame=CFrame.new(spot)
    eggPrompts[eggId].Enabled=true
end
for _,id in ipairs({"R1","R2","B1","B2","N1"}) do
    local owner=match.eggs[id].owner
    local p=Instance.new("Part")
    p.Name="EGG_"..id
    p.Shape=Enum.PartType.Ball
    p.Size=Vector3.new(3,3.6,3)
    p.Material=Enum.Material.Neon
    p.Color=colorByOwner[owner]
    p.Anchored=true;p.CanCollide=false
    p.CFrame=CFrame.new(initial[id])
    p.Parent=arena
    eggWorld[id]=p
    local pu=prompt(p,"卵を持つ",owner.."の卵 "..id)
    eggPrompts[id]=pu
    sign(p,id.." "..(if owner=="NEUTRAL" then "中央レア" else owner),colorByOwner[owner])
    pu.Triggered:Connect(function(player: Player)
        if not started or not match.active then return end
        local holder=holderIds[player]
        local side=sideByPlayer[player]
        if not holder or not side then return end
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        local hum=character and character:FindFirstChildOfClass("Humanoid")
        if not root or not root:IsA("BasePart") or not hum or hum.Health<=0
            or (root.Position-p.Position).Magnitude>11 then return end
        local ok=Rules.pickup(match,id,holder,side)
        if not ok then return end
        p.Anchored=false
        p.CanCollide=false
        p.Massless=true
        p.CFrame=root.CFrame*CFrame.new(0,3.6,0)
        local w=Instance.new("WeldConstraint")
        w.Name="ServerCarriedEgg"
        w.Part0=root;w.Part1=p;w.Parent=p
        welds[id]=w
        pu.Enabled=false
    end)
end

local function sendScores()
    replicated:SetAttribute("RED",match.scores.RED)
    replicated:SetAttribute("BLUE",match.scores.BLUE)
    replicated:SetAttribute("SECONDS",math.max(0,Rules.LENGTH_SECONDS-match.now))
    replicated:SetAttribute("ACTIVE",match.active and started)
    replicated:SetAttribute("WINNER",match.winner)
end
local function teamCount(side:string):number
    local count=0
    for player,t in pairs(sideByPlayer) do
        if player.Parent==Players and t==side then count+=1 end
    end
    return count
end
local function addPlayer(player: Player)
    nextHolderId+=1
    holderIds[player]=nextHolderId
    idByPlayer[nextHolderId]=player
    local side=if teamCount("RED")<=teamCount("BLUE") then "RED" else "BLUE"
    sideByPlayer[player]=side
    player:SetAttribute("H2LabTeam",side)
    player.CharacterAdded:Connect(function(character)
        dropPlayer(player)
        local root=character:WaitForChild("HumanoidRootPart",8)
        if root and root:IsA("BasePart") then
            root.CFrame=CFrame.new(if side=="RED" then -75 else 75,5,0)
        end
        local hum=character:FindFirstChildOfClass("Humanoid")
        if hum then
            hum.Died:Connect(function() dropPlayer(player) end)
        end
    end)
    if teamCount("RED")>0 and teamCount("BLUE")>0 then started=true end
    sendScores()
end
Players.PlayerAdded:Connect(addPlayer)
for _,p in ipairs(Players:GetPlayers()) do addPlayer(p) end
Players.PlayerRemoving:Connect(function(player)
    dropPlayer(player)
    local holder=holderIds[player]
    if holder then idByPlayer[holder]=nil end
    holderIds[player]=nil
    sideByPlayer[player]=nil
end)
task.spawn(function()
    while match.active do
        task.wait(1)
        if started then
            local ok=Rules.advance(match,1)
            if not ok then break end
            if not Rules.assertConserved(match) then
                error("P0D_H2_LAB_EGG_CONSERVATION_VIOLATION")
            end
            sendScores()
        end
    end
    sendScores()
end)
