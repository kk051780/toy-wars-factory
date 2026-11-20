--!nocheck
-- P0D REALM_HUNT_V1 + GQ470_FB015_REALM_MATTE_SCULPT: bounded low-glare landmark silhouettes.
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

-- A four-part-per-landmark mobile budget. Only the core carries a Prompt;
-- all added pieces are non-interactive static decoration (no round or score state).
local THEMES = {
    SKY={shape=Enum.PartType.Cylinder, size=Vector3.new(5.8,2.45,2.45),
         rot=CFrame.Angles(0,0,math.pi/2), facet=Vector3.new(1.65,2.8,1.65),
         tilt=CFrame.Angles(0,math.rad(40),math.rad(-16)), rise=2.9},
    SEA={shape=Enum.PartType.Ball, size=Vector3.new(5.2,2.65,3.7),
         rot=CFrame.new(), facet=Vector3.new(2.5,1.15,3.3),
         tilt=CFrame.Angles(math.rad(-14),math.rad(22),0), rise=1.4},
    EMBER={shape=Enum.PartType.Block, size=Vector3.new(2.45,4.75,2.45),
         rot=CFrame.Angles(0,math.rad(38),0), facet=Vector3.new(1.5,3.35,1.5),
         tilt=CFrame.Angles(0,math.rad(-24),math.rad(14)), rise=2.65},
    STAR={shape=Enum.PartType.Block, size=Vector3.new(3.5,3.5,3.5),
         rot=CFrame.Angles(math.rad(22),math.rad(45),math.rad(12)), facet=Vector3.new(2.0,2.3,2.0),
         tilt=CFrame.Angles(math.rad(40),math.rad(-30),math.rad(23)), rise=2.3},
}
local displays={}
for _,item in ipairs(LANDMARKS) do
    local theme=assert(THEMES[item.id], "REALM_SCULPT_THEME_MISSING")
    local core=Instance.new("Part")
    core.Name="REALM_"..item.id
    core.Shape=theme.shape
    core.Size=theme.size
    core.CFrame=CFrame.new(item.position)*theme.rot
    core.Anchored=true
    core.CanCollide=false
    core.CanTouch=false
    core.CanQuery=false
    core.Material=Enum.Material.SmoothPlastic
    core.Color=item.color
    core.CastShadow=false
    core.Parent=folder
    core:SetAttribute("RealmId",item.id)
    core:SetAttribute("NoBattleEffect",true)
    local light=Instance.new("PointLight")
    light.Range=10
    light.Brightness=0.48
    light.Color=item.color
    light.Parent=core
    local ring=Instance.new("Part")
    ring.Name="RING_"..item.id
    ring.Shape=Enum.PartType.Cylinder
    ring.Size=Vector3.new(0.22,5.5,5.5)
    ring.CFrame=CFrame.new(item.position)*CFrame.Angles(0,0,math.pi/2)
    ring.Anchored=true
    ring.CanCollide=false
    ring.CanTouch=false
    ring.CanQuery=false
    ring.Material=Enum.Material.Metal
    ring.Color=Color3.fromRGB(115,124,141)
    ring.Transparency=0.15
    ring.CastShadow=false
    ring.Parent=folder
    local facet=Instance.new("WedgePart")
    facet.Name="SCULPT_FACET_"..item.id
    facet.Size=theme.facet
    facet.CFrame=CFrame.new(item.position+Vector3.new(0,theme.rise,0))*theme.tilt
    facet.Anchored=true
    facet.CanCollide=false
    facet.CanTouch=false
    facet.CanQuery=false
    facet.CastShadow=false
    facet.Material=Enum.Material.SmoothPlastic
    facet.Color=item.color:Lerp(Color3.fromRGB(235,230,211),0.36)
    facet.Parent=folder
    local plinth=Instance.new("Part")
    plinth.Name="SCULPT_PLINTH_"..item.id
    plinth.Shape=Enum.PartType.Cylinder
    plinth.Size=Vector3.new(0.38,5.5,5.5)
    plinth.CFrame=CFrame.new(item.position-Vector3.new(0,2.18,0))*CFrame.Angles(0,0,math.pi/2)
    plinth.Anchored=true
    plinth.CanCollide=false
    plinth.CanTouch=false
    plinth.CanQuery=false
    plinth.CastShadow=false
    plinth.Material=Enum.Material.Slate
    plinth.Color=Color3.fromRGB(68,77,88)
    plinth.Parent=folder
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
    billboard.MaxDistance=35
    billboard.StudsOffsetWorldSpace=Vector3.new(0,3.7,0)
    billboard.AlwaysOnTop=false
    billboard.Parent=core
    local label=Instance.new("TextLabel")
    label.Size=UDim2.fromScale(1,1)
    label.BackgroundColor3=Color3.fromRGB(29,33,50)
    label.BackgroundTransparency=0.45
    label.Text=item.name.." ✦"
    label.TextColor3=Color3.fromRGB(255,255,255)
    label.TextScaled=false
    label.TextSize=16
    label.TextTruncate=Enum.TextTruncate.AtEnd
    label.Font=Enum.Font.GothamBold
    label.Parent=billboard
    table.insert(displays,{core=core,ring=ring,position=item.position})
end
folder:SetAttribute("Landmarks",#LANDMARKS)
folder:SetAttribute("GeneratedParts",#displays*4)
folder:SetAttribute("VisualPartBudget",16)
folder:SetAttribute("MaterialPolicy","MATTE_4_SCULPTS")
local t=0
local step=0
local beat
beat=RunService.Heartbeat:Connect(function(dt)
    if not folder.Parent then beat:Disconnect(); return end
    if dt<=0 or dt>0.5 then return end
    t+=dt
    step+=dt
    if step<0.18 then return end
    step=0
    for i,view in ipairs(displays) do
        view.core.Position=view.position+Vector3.new(0,math.sin(t*1.8+i)*0.24,0)
        view.ring.CFrame=CFrame.new(view.position)*CFrame.Angles(t*0.45,0,math.pi/2)
    end
end)
print("[P0D_REALM_HUNT] FOUR_REALMS_ACTIVE; ENGINE_PLAY_AND_MOBILE_NOT_TESTED")
