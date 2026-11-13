--!strict
-- Original neutral 3D guardian: reacts to BOTH teams and changes REAL physical
-- centre path (warn -> collide -> recover) without owning eggs/HP/win/Remote.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local Policy=require(script.Parent:WaitForChild("H2GateBeastPolicy"))
local arena=workspace:WaitForChild("TRAP_RAIDERS_S1",30)
if not arena then warn("H2_BEAST_NO_S1_ARENA"); return end
assert(not arena:FindFirstChild("H2_NEUTRAL_GATE_BEAST"),"H2_BEAST_ALREADY_EXISTS")
local world=Instance.new("Folder")
world.Name="H2_NEUTRAL_GATE_BEAST"
world:SetAttribute("PrivateStudioOnly",true)
world:SetAttribute("NeutralBothTeams",true)
world:SetAttribute("OriginalS1MatchAuthorityUnchanged",true)
world:SetAttribute("TwoClientPhysicsMobileAndFun","NOT_TESTED")
world.Parent=arena

local function rgb(r:number,g:number,b:number): Color3 return Color3.fromRGB(r,g,b) end
local count=0
local function part(name:string,size:Vector3,pos:Vector3,color:Color3,solid:boolean): Part
    count+=1
    assert(count<=20,"H2_BEAST_PART_BUDGET")
    local p=Instance.new("Part")
    p.Name=name; p.Size=size; p.Position=pos; p.Color=color
    p.Material=Enum.Material.SmoothPlastic
    p.Anchored=true; p.CanCollide=solid; p.CanTouch=false
    p.CanQuery=solid; p.Parent=world
    return p
end

-- Original friendly neutral silhouette: a sleepy pearl-bodied two-horn doorbeast.
-- Lightweight 3D geometry, not a copied existing Roblox pet asset.
local body=part("BEAST_PEARL_BODY",Vector3.new(7,6,7),
    Vector3.new(0,5,21),rgb(107,190,200),false)
body.Shape=Enum.PartType.Ball
local head=part("BEAST_HEAD",Vector3.new(5,5,5),
    Vector3.new(0,8,17),rgb(159,216,220),false)
head.Shape=Enum.PartType.Ball
local headRest=head.CFrame
local eyeL=part("BEAST_EYE_L",Vector3.new(1.1,1.3,0.6),
    Vector3.new(-1.25,8.4,14.65),rgb(115,231,159),false)
local eyeR=part("BEAST_EYE_R",Vector3.new(1.1,1.3,0.6),
    Vector3.new(1.25,8.4,14.65),rgb(115,231,159),false)
for _,eye in ipairs({eyeL,eyeR}) do
    eye.Shape=Enum.PartType.Ball; eye.Material=Enum.Material.Neon
end
for _,x in ipairs({-2.4,2.4}) do
    local horn=part("BEAST_SOFT_HORN",Vector3.new(1.6,3.5,1.8),
        Vector3.new(x,11,18),rgb(247,227,149),false)
    horn.Shape=Enum.PartType.Ball
end
for _,x in ipairs({-2.2,2.2}) do
    local foot=part("BEAST_PAWS",Vector3.new(2.3,1.4,3.0),
        Vector3.new(x,1.7,18.5),rgb(75,147,172),false)
    foot.Shape=Enum.PartType.Ball
end
local tail=part("BEAST_ROUND_TAIL",Vector3.new(3,3,3),
    Vector3.new(0,4.2,25),rgb(220,210,255),false)
tail.Shape=Enum.PartType.Ball
local signBase=part("BEAST_STORY_SIGN",Vector3.new(1,1,1),
    Vector3.new(0,13,18),rgb(255,255,255),false)
signBase.Transparency=1

-- Real physical obstacle is narrow in X and crosses ONLY central ground road.
-- It never covers the physical sky/sea routes nor original spawn/egg/score pads.
local gate=part("BEAST_TEMPORARY_CENTRE_GATE",Vector3.new(3.5,12,21),
    Vector3.new(0,6,0),rgb(248,128,180),false)
gate.Material=Enum.Material.Neon
gate.Transparency=1
gate.CastShadow=false
local warning=part("BEAST_ADVANCE_WARNING",Vector3.new(5.5,0.35,23),
    Vector3.new(0,0.24,0),rgb(255,203,95),false)
warning.Material=Enum.Material.Neon
warning.Transparency=1; warning.CastShadow=false
local warningGui=Instance.new("BillboardGui")
warningGui.Name="BEAST_TELEGRAPH"
warningGui.Size=UDim2.fromOffset(260,76)
warningGui.StudsOffsetWorldSpace=Vector3.new(0,3,0)
warningGui.MaxDistance=100
warningGui.AlwaysOnTop=true
warningGui.Enabled=false
warningGui.Parent=signBase
local label=Instance.new("TextLabel")
label.Size=UDim2.fromScale(1,1)
label.TextScaled=true
label.Font=Enum.Font.GothamBold
label.TextColor3=rgb(255,255,255)
label.BackgroundColor3=rgb(50,40,83)
label.BackgroundTransparency=0.1
label.Text="まもりの門獣"
label.Parent=warningGui

local status=Policy.initial()
local function refresh()
    local phase=status.phase
    local solid=Policy.solid(status)
    -- Game collision is server-only; NEVER update to solid based on client events.
    gate.CanCollide=solid
    gate.CanQuery=solid
    gate.Transparency=if solid then 0.25 else 1
    warning.Transparency=if phase==Policy.WARN then 0.08
        elseif phase==Policy.BLOCK then 0.5 else 1
    warningGui.Enabled=phase==Policy.WARN or phase==Policy.BLOCK
    if phase==Policy.WARN then
        label.Text="⚠️ 門獣が目ざめた！\nうみ・そらへ まわれるよ"
    elseif phase==Policy.BLOCK then
        label.Text="🛡️ 門獣のカベ！\nうみ・そらの道が使えるよ"
    end
    local eyes=if solid then rgb(255,137,147)
        elseif phase==Policy.WARN then rgb(255,224,105) else rgb(115,231,159)
    eyeL.Color=eyes;eyeR.Color=eyes
    world:SetAttribute("CurrentBeastPhase",phase)
    world:SetAttribute("CentreGateSolid",solid)
end
refresh()

local tickAccum=0
local lived=0
local beat
beat=RunService.Heartbeat:Connect(function(dt)
    if not world.Parent then beat:Disconnect(); return end
    if type(dt)~="number" or dt<=0 or dt>0.5 then return end
    tickAccum+=dt; lived+=dt
    if tickAccum<0.25 then return end
    tickAccum=0
    -- Move only the creature's head gently; parts anchored and non-collidable.
    head.CFrame=headRest*CFrame.new(0,0.24*math.sin(lived*2.2),0)
    local near=false
    local clear=true
    for _,player in ipairs(Players:GetPlayers()) do
        local model=player.Character
        local root=model and model:FindFirstChild("HumanoidRootPart")
        local hum=model and model:FindFirstChildOfClass("Humanoid")
        if root and root:IsA("BasePart") then
            local p=root.Position
            -- Includes players without teams; all existing living character
            -- root parts receive safety buffer before barrier becomes solid.
            if Policy.insideGate(p.X,p.Y,p.Z) then clear=false end
            local team=player.Team and player.Team.Name or "NONE"
            if hum and hum:IsA("Humanoid") and
                Policy.nearBeast(p.X,p.Y,p.Z,team,hum.Health>0) then
                near=true
            end
        end
    end
    local nextStatus=Policy.advance(status,os.clock(),near,clear)
    if nextStatus and nextStatus~=status then
        status=nextStatus
        refresh()
    end
end)
script.Destroying:Connect(function()
    if beat then beat:Disconnect() end
    gate.CanCollide=false; gate.CanQuery=false
end)
print("P0D_H2_ORIGINAL_NEUTRAL_BEAST_PRIVATE_STUDIO_ONLY; REAL_PLAY_NOT_TESTED")
