--!nocheck
-- P0D REALM_HUNT_V1: session-only four fantasy landmarks with real Prompts.
-- Isolated optional server Script. Never owns rounds, eggs, score, XP, Store, Remote or battle.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then warn("[P0D_REALM_HUNT] ARENA_NOT_READY"); return end
assert(not arena:FindFirstChild("P0D_REALM_HUNT_V1"), "DUPLICATE_REALM_HUNT")
local folder = Instance.new("Folder")
folder.Name = "P0D_REALM_HUNT_V1"
folder:SetAttribute("FeatureId", "REALM_HUNT_V1")
folder:SetAttribute("SessionOnly", true)
folder:SetAttribute("Rewards", "COSMETIC_ONLY")
folder:SetAttribute("Enabled", true)
folder.Parent = arena

-- The verified original arena is 250x142 with a solid sky island at y=32
-- and a sea bridge near z=-22. No physical blocking, score shortcuts or teleport.
local LANDMARKS = {
    {id="SKY", name="空のひみつ", position=Vector3.new(0, 35.5, 49),
        color=Color3.fromRGB(115,218,255)},
    {id="SEA", name="海のひみつ", position=Vector3.new(0, 2.5, -22),
        color=Color3.fromRGB(66,196,239)},
    {id="EMBER", name="炎のひみつ", position=Vector3.new(-41, 2.8, -55),
        color=Color3.fromRGB(252,121,61)},
    {id="STAR", name="星のひみつ", position=Vector3.new(41, 2.8, 55),
        color=Color3.fromRGB(198,149,255)},
}
local NAME_PREFIX = "P0D_RealmHunt_"
local records = {}
local function init(player)
    records[player] = {found={}, count=0}
    player:SetAttribute(NAME_PREFIX.."Enabled", true)
    player:SetAttribute(NAME_PREFIX.."Count", 0)
    player:SetAttribute(NAME_PREFIX.."Complete", false)
    for _,item in ipairs(LANDMARKS) do
        player:SetAttribute(NAME_PREFIX..item.id, false)
    end
end
for _,player in ipairs(Players:GetPlayers()) do init(player) end
Players.PlayerAdded:Connect(init)
Players.PlayerRemoving:Connect(function(player) records[player]=nil end)

local function markDiscovered(player, item)
    if not player or not player:IsA("Player") or player.Parent~=Players then return end
    local record=records[player]
    if not record or record.found[item.id] then return end
    local char=player.Character
    if not char then return end
    local humanoid=char:FindFirstChildOfClass("Humanoid")
    local root=char:FindFirstChild("HumanoidRootPart")
    if not humanoid or humanoid.Health<=0 or not root then return end
    if (root.Position-item.position).Magnitude>15 then return end
    -- Authoritative server-only progress; client cannot award, fake or persist it.
    record.found[item.id]=true
    record.count+=1
    player:SetAttribute(NAME_PREFIX..item.id, true)
    player:SetAttribute(NAME_PREFIX.."Count", record.count)
    if record.count==#LANDMARKS then
        player:SetAttribute(NAME_PREFIX.."Complete", true)
        local aura=Instance.new("Highlight")
        aura.Name="P0D_REALM_HUNT_CROWN"
        aura.Adornee=char
        aura.DepthMode=Enum.HighlightDepthMode.Occluded
        aura.FillColor=Color3.fromRGB(244,209,109)
        aura.OutlineColor=Color3.fromRGB(255,242,183)
        aura.FillTransparency=0.78
        aura.OutlineTransparency=0.1
        aura.Parent=char
        task.delay(22,function()
            if aura.Parent then aura:Destroy() end
        end)
    end
    print("[P0D_REALM_HUNT] DISCOVERED", player.UserId, item.id, record.count)
end

local displays={}
for _,item in ipairs(LANDMARKS) do
    local core=Instance.new("Part")
    core.Name="REALM_"..item.id
    core.Shape=Enum.PartType.Ball
    core.Size=Vector3.new(3.5,3.5,3.5)
    core.CFrame=CFrame.new(item.position)
    core.Anchored=true
    core.CanCollide=false
    core.CanTouch=false
    core.CanQuery=false
    core.Material=Enum.Material.Neon
    core.Color=item.color
    core.Transparency=0.12
    core.CastShadow=false
    core.Parent=folder
    core:SetAttribute("RealmId",item.id)
    core:SetAttribute("NoBattleEffect",true)
    local light=Instance.new("PointLight")
    light.Range=18
    light.Brightness=1.7
    light.Color=item.color
    light.Parent=core
    local ring=Instance.new("Part")
    ring.Name="RING_"..item.id
    ring.Shape=Enum.PartType.Cylinder
    ring.Size=Vector3.new(0.2,6,6)
    ring.CFrame=CFrame.new(item.position)*CFrame.Angles(0,0,math.pi/2)
    ring.Anchored=true
    ring.CanCollide=false
    ring.CanTouch=false
    ring.CanQuery=false
    ring.Material=Enum.Material.Neon
    ring.Color=item.color
    ring.Transparency=0.72
    ring.CastShadow=false
    ring.Parent=folder
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="DISCOVER_"..item.id
    prompt.ActionText="発見する"
    prompt.ObjectText=item.name
    prompt.MaxActivationDistance=10
    prompt.HoldDuration=0.35
    prompt.RequiresLineOfSight=false
    prompt.Parent=core
    prompt.Triggered:Connect(function(player) markDiscovered(player,item) end)
    local billboard=Instance.new("BillboardGui")
    billboard.Name="REALM_NAME_"..item.id
    billboard.Size=UDim2.fromOffset(150,36)
    billboard.MaxDistance=55
    billboard.StudsOffsetWorldSpace=Vector3.new(0,3.7,0)
    billboard.AlwaysOnTop=true
    billboard.Parent=core
    local label=Instance.new("TextLabel")
    label.Size=UDim2.fromScale(1,1)
    label.BackgroundColor3=Color3.fromRGB(29,33,50)
    label.BackgroundTransparency=0.3
    label.Text=item.name.." ✦"
    label.TextColor3=Color3.fromRGB(255,255,255)
    label.TextScaled=true
    label.Font=Enum.Font.GothamBold
    label.Parent=billboard
    table.insert(displays,{core=core,ring=ring,position=item.position})
end
folder:SetAttribute("Landmarks",#LANDMARKS)
folder:SetAttribute("GeneratedParts",#displays*2)
local t=0
local step=0
local beat
beat=RunService.Heartbeat:Connect(function(dt)
    if not folder.Parent then beat:Disconnect(); return end
    if dt<=0 or dt>0.5 then return end
    t+=dt
    step+=dt
    if step<0.10 then return end
    step=0
    for i,view in ipairs(displays) do
        view.core.Position=view.position+Vector3.new(0,math.sin(t*1.8+i)*0.24,0)
        view.ring.CFrame=CFrame.new(view.position)*CFrame.Angles(t*0.85,0,math.pi/2)
    end
end)
print("[P0D_REALM_HUNT] FOUR_REALMS_ACTIVE; ENGINE_PLAY_AND_MOBILE_NOT_TESTED")
