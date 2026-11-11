--!strict
-- Original isolated land / sea / sky THREE-LEVEL map source. NO gameplay authority.
-- This scene draws a glass SEA with dry walkable corridors; genuine water/physics
-- and real mobile play remain Studio-unverified until owner permits QA.
local Routes = require(script.Parent.WorldLinkRoutes)
local Scene = {}

local function part(folder: Instance, name: string, sz: Vector3, pos: Vector3,
    color: Color3, material: Enum.Material, solid: boolean, transparency: number?): Part
    local p=Instance.new("Part")
    p.Name=name
    p.Size=sz
    p.Position=pos
    p.Anchored=true
    p.Color=color
    p.Material=material
    p.CanCollide=solid
    p.CanTouch=false
    p.CanQuery=solid
    p.Transparency=transparency or 0
    p.Parent=folder
    return p
end

local function walkRamp(folder: Instance, name: string,
    x0: number, y0: number, x1: number, y1: number, z: number, width: number,
    color: Color3): Part
    local dx,dy=x1-x0,y1-y0
    assert(math.abs(dx)>10 and math.abs(dy/dx)<0.32, "WF-G5 walk slope too steep")
    local length=math.sqrt(dx*dx+dy*dy)
    local p=part(folder,name,Vector3.new(length,1.5,width),
        Vector3.new((x0+x1)/2,(y0+y1)/2,z),color,Enum.Material.SmoothPlastic,true)
    p.CFrame=CFrame.new(p.Position)*CFrame.Angles(0,0,math.atan2(dy,dx))
    p:SetAttribute("WF_WALKABLE",true)
    return p
end

local function sign(folder: Instance, name: string, anchor: Vector3, cue: string, color: Color3)
    local column=part(folder,name,Vector3.new(1,6,1),anchor,color,Enum.Material.Neon,false)
    local gui=Instance.new("BillboardGui")
    gui.Name="WFChildCue"
    gui.Size=UDim2.fromOffset(205,63)
    gui.StudsOffsetWorldSpace=Vector3.new(0,5.5,0)
    gui.MaxDistance=110
    gui.AlwaysOnTop=true
    gui.Parent=column
    local label=Instance.new("TextLabel")
    label.Size=UDim2.fromScale(1,1)
    label.BackgroundColor3=Color3.fromRGB(25,34,68)
    label.BackgroundTransparency=0.1
    label.TextColor3=Color3.fromRGB(255,255,255)
    label.TextScaled=true
    label.Font=Enum.Font.GothamBold
    label.Text=cue
    label.Parent=gui
end

local function castle(folder: Instance, prefix: string, center: Vector3, color: Color3)
    local deck=part(folder,prefix.."Deck",Vector3.new(50,2,100),
        center,color,Enum.Material.SmoothPlastic,true)
    for _, x in ipairs({center.X-18,center.X+18}) do
        local tower=part(folder,prefix.."Tower",Vector3.new(7,19,7),
            Vector3.new(x,center.Y+10,center.Z-32),
            Color3.fromRGB(222,233,251),Enum.Material.SmoothPlastic,true)
        tower:SetAttribute("WF_LANDMARK",prefix)
        part(folder,prefix.."Crown",Vector3.new(9,3,9),
            Vector3.new(x,center.Y+21,center.Z-32),color,Enum.Material.Neon,false)
    end
    return deck
end

function Scene.build(world: Workspace)
    assert(world:IsA("Workspace"),"WF-G5 accepts only a standalone Workspace")
    assert(world:FindFirstChild("TRAP_RAIDERS_S1")==nil,"NO_S1_MAP_OVERLAP")
    assert(world:FindFirstChild("WF_G5_LandSeaSky")==nil,"NO_DUPLICATE_WORLD")
    local valid, reason=Routes.validate()
    assert(valid,reason)
    local folder=Instance.new("Folder")
    folder.Name="WF_G5_LandSeaSky"
    folder.Parent=world

    local green=Color3.fromRGB(80,183,129)
    local blue=Color3.fromRGB(43,171,241)
    local yellow=Color3.fromRGB(255,223,92)
    local purple=Color3.fromRGB(154,119,248)
    local white=Color3.fromRGB(233,241,255)

    -- A single central grass plaza: free, no job / paid / item gates.
    part(folder,"LAND_FreeHub",Vector3.new(74,2,105),
        Vector3.new(0,0,0),green,Enum.Material.Grass,true)
    local start=Instance.new("SpawnLocation")
    start.Name="WF_G5_FreeSpawn"
    start.Size=Vector3.new(11,1,11)
    start.Position=Vector3.new(0,2,0)
    start.Anchored=true
    start.Neutral=true
    start.Enabled=true
    start.Parent=folder

    -- Sea is deliberately dry and accessible: transparent glass-sea.
    -- Its physical submerged corridors are visible through water-blue glass;
    -- water swimming/breath meter must NOT be claimed in promotional videos.
    part(folder,"SEA_VisualWaterOnly",Vector3.new(185,28,122),
        Vector3.new(-140,-12,0),blue,Enum.Material.Glass,false,0.79)
    local dock=part(folder,"SEA_FreeDock",Vector3.new(30,2,40),
        Vector3.new(-108,1,-15),Color3.fromRGB(192,173,114),
        Enum.Material.WoodPlanks,true)
    dock:SetAttribute("WF_ROUTE","SEA_BRIDGE")
    walkRamp(folder,"SEA_BRIDGE_FreePortWalk",-28,2,-108,2,-15,15,blue)
    -- Route A: port -> long, safely sloped aquarium entrance -> sea castle.
    walkRamp(folder,"SEA_BUBBLE_A_DryRamp",-108,2,-205,-22,-15,13,blue)
    -- Route B: land -> separate secret dry descending glass tube.
    walkRamp(folder,"SEA_BUBBLE_B_DryRamp",-4,2,-205,-22,30,13,green)
    part(folder,"SEA_BUBBLE_B_LastTurn",Vector3.new(14,1.5,50),
        Vector3.new(-205,-22.9,13),green,Enum.Material.SmoothPlastic,true)
    -- Lightweight aquarium-glass canopies signal a secret but not block movement.
    for i=1,5 do
        local x=-40-i*30
        part(folder,"SEA_BUBBLE_B_GlassRoof_"..i,Vector3.new(23,1,22),
            Vector3.new(x,11-i*4.3,30),blue,Enum.Material.Glass,false,0.66)
    end
    castle(folder,"SEA_CASTLE_",Vector3.new(-205,-23,0),Color3.fromRGB(62,173,205))
    sign(folder,"SEA_PORT_Sign",Vector3.new(-35,5,-18),"🐟 うみの おしろ\nあおい はしへ",blue)
    sign(folder,"SEA_SECRET_Sign",Vector3.new(-15,5,34),"🐠 ひみつの みち\nみどりの さか",green)
    sign(folder,"SEA_CASTLE_Sign",Vector3.new(-206,-17,0),"🏰 かいていじょう\nたからを さがそう",blue)

    -- Sky has TWO separate free sloped walkways, both ending at same castle.
    local skyA=walkRamp(folder,"SKY_RAINBOW_A_Lower",20,2,95,25,-33,15,yellow)
    walkRamp(folder,"SKY_RAINBOW_A_Upper",95,25,175,49,-33,15,yellow)
    walkRamp(folder,"SKY_RAINBOW_B_Lower",20,2,95,25,33,15,purple)
    walkRamp(folder,"SKY_RAINBOW_B_Upper",95,25,175,49,33,15,purple)
    skyA:SetAttribute("WF_ROUTE","SKY_RAINBOW_A")
    castle(folder,"SKY_CASTLE_",Vector3.new(177,48,0),
        Color3.fromRGB(213,211,255))
    sign(folder,"SKY_FIRST_Sign",Vector3.new(23,5,-37),"☀ そらの おしろ\nきいろい さか",yellow)
    sign(folder,"SKY_SECOND_Sign",Vector3.new(23,5,37),"☁ くもの うらみち\nむらさきの さか",purple)
    sign(folder,"SKY_CASTLE_Sign",Vector3.new(180,55,0),"🏰 そらの おしろ\nふたつの みち",purple)
    for i=1,18 do
        local x=48+(i%7)*25
        local z=(i%5-2)*27
        local cloud=part(folder,"SKY_Cloud_"..i,Vector3.new(11+(i%3)*3,4,10),
            Vector3.new(x,63+(i%4)*5,z),white,Enum.Material.SmoothPlastic,false,0.26)
        cloud.Shape=Enum.PartType.Ball
    end
    -- Distant goals: decoration has zero game advantage or collider overhead.
    part(folder,"LAND_DestinationBeacon",Vector3.new(4,32,4),
        Vector3.new(0,18,0),yellow,Enum.Material.Neon,false,0.38)
    sign(folder,"LAND_Guidance",Vector3.new(0,6,13),
        "← 🐠 うみの おしろ\n☁ そらの おしろ →",yellow)
    folder:SetAttribute("WF_SourceMode","SOURCE_ONLY_NO_STUDIO_QA")
    folder:SetAttribute("WF_NpcSpawnProbability","NOT_SET")
    folder:SetAttribute("WF_EggAndCombatOwnedBy","S1_ONLY_NO_WF_CHANGE")
    return {folder=folder,spawn=start,dock=dock,sky=skyA}
end
return Scene
