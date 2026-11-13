--!nocheck
-- P0D S2 Sky Cosmos: Starfall bridge, third physical route in WCS canyon.
-- Original Game/Remote/Store/HP/score/egg/XP writers are never duplicated.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local ServerStorage=game:GetService("ServerStorage")
if ServerStorage:GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true then return end
local Workspace=game:GetService("Workspace")
local Players=game:GetService("Players")
-- WCS may wait up to 45s for the arena, 45s for H1 world, and 12s for SkyV5.
-- Starfall must not give up before its prerequisite has finished booting.
local anchor=Workspace:WaitForChild("P0D_CrystalCanyonAnchor",120)
local canyon=Workspace:WaitForChild("P0D_WCS_CrystalCanyon",20)
if not anchor or not anchor:IsA("BasePart") or not canyon or not canyon:IsA("Model") then
    warn("[P0D/STAR] WCS canyon missing: independent star route disabled")
    return
end
if not canyon:WaitForChild("ShortcutBridge",15) then
    warn("[P0D/STAR] WCS collision terrain missing: refusing orphan stage")
    return
end
if Workspace:FindFirstChild("P0D_STARRY_PATH") then
    warn("[P0D/STAR] duplicate star route; refusing second scene")
    return
end

local stage=Instance.new("Model")
stage.Name="P0D_STARRY_PATH"
stage:SetAttribute("FeatureId","STARRY_PATH_V1")
stage:SetAttribute("RuntimeScope","STUDIO_ONLY_EXPLICIT_OPT_IN")
stage:SetAttribute("NoDamageScoreXpSave",true)
stage:SetAttribute("PathOpen",false)
stage.Parent=Workspace

local function part(name:string,size:Vector3,offset:Vector3,color:Color3,collide:boolean)
    local p=Instance.new("Part")
    p.Name=name
    p.Size=size
    p.CFrame=anchor.CFrame*CFrame.new(offset)
    p.Anchored=true
    p.CanCollide=collide
    p.CanTouch=false
    p.CanQuery=collide
    p.Material=Enum.Material.Neon
    p.Color=color
    p.TopSurface=Enum.SurfaceType.Smooth
    p.BottomSurface=Enum.SurfaceType.Smooth
    p.Parent=stage
    return p
end

local stars={}
-- WCS banks occupy world-local x<=-25 and x>=25, top local y=0.
-- This optional third route spans the canyon around local z=-35, inside
-- Game recovery bounds. The existing safe WCS z=+30 route NEVER disappears.
for i=1,10 do
    local x=-22.5+(i-1)*5
    local color=if i%2==0 then Color3.fromRGB(89,208,255)
        else Color3.fromRGB(235,160,255)
    local stone=part("StarStep_"..tostring(i),Vector3.new(6,1.5,13),
        Vector3.new(x,-0.75,-35),color,false)
    stone.Transparency=0.82
    table.insert(stars,stone)
end

local cosmetic=part("ConstellationCore",Vector3.new(2,2,2),
    Vector3.new(0,9,-35),Color3.fromRGB(250,236,125),false)
cosmetic.Shape=Enum.PartType.Ball
cosmetic.Transparency=0.35
local glow=Instance.new("PointLight")
glow.Range=19
glow.Brightness=1.4
glow.Color=Color3.fromRGB(180,180,255)
glow.Enabled=false
glow.Parent=cosmetic
local glitter=Instance.new("ParticleEmitter")
glitter.Name="StarfallDust"
glitter.Texture="rbxasset://textures/particles/sparkles_main.dds"
glitter.Rate=5
glitter.Lifetime=NumberRange.new(0.8,1.8)
glitter.Speed=NumberRange.new(0.5,2)
glitter.SpreadAngle=Vector2.new(90,90)
glitter.LightEmission=1
glitter.Enabled=false
glitter.Parent=cosmetic

local active=false
local expiresAt=0
local readyAt=0
local OPEN_SECONDS=16
local REOPEN_COOLDOWN=7

local function occupied():boolean
    for _,player in ipairs(Players:GetPlayers()) do
        local char=player.Character
        local root=char and char:FindFirstChild("HumanoidRootPart")
        local humanoid=char and char:FindFirstChildOfClass("Humanoid")
        if root and humanoid and humanoid.Health>0 then
            local v=anchor.CFrame:PointToObjectSpace(root.Position)
            if math.abs(v.X)<=26 and math.abs(v.Z+35)<=9
                and v.Y>=-4 and v.Y<=9 then
                return true
            end
        end
    end
    return false
end

local function setOpen(on:boolean)
    if active and not on then
        readyAt=os.clock()+REOPEN_COOLDOWN
    end
    active=on
    for _,stone in ipairs(stars) do
        stone.CanCollide=on
        stone.CanQuery=on
        stone.Transparency=on and 0.07 or 0.82
    end
    glow.Enabled=on
    glitter.Enabled=on
    stage:SetAttribute("PathOpen",on)
    stage:SetAttribute("LastOpenedSeconds",if on then OPEN_SECONDS else 0)
end

local function makeSwitch(side:string,x:number,color:Color3)
    local orb=part("StarSwitch_"..side,Vector3.new(3,3,3),
        Vector3.new(x,3,-35),color,false)
    orb.Shape=Enum.PartType.Ball
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="SummonStarBridge"
    prompt.ActionText="星の橋を呼ぶ"
    prompt.ObjectText="星降る秘境 16秒"
    prompt.HoldDuration=0.5
    prompt.MaxActivationDistance=12
    prompt.RequiresLineOfSight=false
    prompt.Parent=orb
    prompt.Triggered:Connect(function(player)
        if active or os.clock()<readyAt or not player.Character then return end
        local root=player.Character:FindFirstChild("HumanoidRootPart")
        local hum=player.Character:FindFirstChildOfClass("Humanoid")
        if not root or not hum or hum.Health<=0 then return end
        if (root.Position-orb.Position).Magnitude>13 then return end
        setOpen(true)
        expiresAt=os.clock()+OPEN_SECONDS
    end)
    local billboard=Instance.new("BillboardGui")
    billboard.Name="StarPathHint"
    billboard.Size=UDim2.fromOffset(210,54)
    billboard.StudsOffsetWorldSpace=Vector3.new(0,4,0)
    billboard.AlwaysOnTop=true
    billboard.MaxDistance=65
    billboard.Parent=orb
    local t=Instance.new("TextLabel")
    t.Name="Hint"
    t.Size=UDim2.fromScale(1,1)
    t.BackgroundTransparency=0.3
    t.BackgroundColor3=Color3.fromRGB(30,19,71)
    t.TextColor3=Color3.fromRGB(255,242,180)
    t.Text="星降る橋を出現させる！"
    t.TextScaled=true
    t.Font=Enum.Font.GothamBold
    t.Parent=billboard
end
-- Both teams have symmetric access from their existing canyon banks.
makeSwitch("WEST",-34,Color3.fromRGB(228,158,255))
makeSwitch("EAST",34,Color3.fromRGB(114,215,255))
stage:SetAttribute("SafeWCSRouteAlwaysAvailable",true)
stage:SetAttribute("ThirdPhysicalRouteLocalZ",-35)
stage:SetAttribute("Switches",2)
stage:SetAttribute("TimedStarSteps",10)
setOpen(false)
task.spawn(function()
    while stage.Parent do
        if active and os.clock()>=expiresAt and not occupied() then
            -- Never make the physical bridge disappear beneath a living player.
            setOpen(false)
        end
        task.wait(0.4)
    end
end)
