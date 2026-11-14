--!strict
-- OWNER FB-015 / ART-WORLD: Studio-only fantasy battlefield color, light, forest silhouettes.
-- New decorative Script only. Never writes Game/Horde/Store/Remote/HP/score, Terrain voxels or movement.
-- 0 heartbeat loops / 0 collisions / 0 query / max 255 light-weight static Part descendants.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Lighting = game:GetService("Lighting")
local Terrain = workspace.Terrain
local root = workspace:WaitForChild("TRAP_RAIDERS_S1",150)
if not root then return end
local ground = root:WaitForChild("GrassArena",30)
if not ground or not ground:IsA("BasePart") then return end
if root:FindFirstChild("P0D_FB015_WORLD_ART_V1") then return end

-- OWNER FB-015 real visual bug fix:
-- CastleBattlefield asynchronously enlarges GrassArena from 250x142 to
-- 370x294. Original scatter used its old 142-z measurement in some runs,
-- planting trees into the new ocean channel (z -83..-31).
-- Do NOT generate foliage until the actual expanded castle scene is ready.
local castle = root:WaitForChild("OWNER361_CASTLE_WORLD_V1", 90)
if not castle then
    warn("FB015_FOREST_NO_CASTLE_CANNOT_PLACE_TREES")
    return
end
local ready = false
for _ = 1, 180 do
    local red = castle:FindFirstChild("RED_CASTLE_ARCHITECTURE")
    local blue = castle:FindFirstChild("BLUE_CASTLE_ARCHITECTURE")
    if math.abs(ground.Size.X - 370) < .05
        and math.abs(ground.Size.Z - 294) < .05
        and red and red:FindFirstChild("GRAND_KEEP")
        and blue and blue:FindFirstChild("GRAND_KEEP") then
        ready = true
        break
    end
    task.wait(.1)
end
if not ready then
    warn("FB015_FOREST_CASTLE_GEOMETRY_NOT_READY_FAIL_CLOSED")
    return
end

local folder = Instance.new("Folder")
folder.Name="P0D_FB015_WORLD_ART_V1"
folder.Parent=root
local count=0
local MAX_PARTS=255
local BASE_Y = ground.Position.Y + ground.Size.Y * 0.5
local greens={
    Color3.fromRGB(65,118,82),
    Color3.fromRGB(89,143,95),
    Color3.fromRGB(117,157,91),
    Color3.fromRGB(142,168,93),
}
local stone={Color3.fromRGB(111,124,125),Color3.fromRGB(137,137,126)}
local function deco(name:string,position:Vector3,size:Vector3,color:Color3,material:Enum.Material,shape:Enum.PartType?):BasePart?
    if count>=MAX_PARTS then return nil end
    local p=Instance.new("Part")
    p.Name=name
    p.Anchored=true
    p.CanCollide=false
    p.CanTouch=false
    p.CanQuery=false -- NEVER alter attacks, travel, raycasts, physics or safe routes
    p.CastShadow=false -- minor detail shadow draw cost on Android
    p.Material=material
    p.Color=color
    p.Shape=shape or Enum.PartType.Block
    p.Size=size
    p.Position=position
    p.Parent=folder
    count+=1
    return p
end
local function scatter(i:number,side:number):number
    return math.sin(i*19.41+side*7.13) -- deterministic, never invokes global RNG
end
local function makeTree(index:number,side:number,x:number,z:number,scale:number)
    local center=Vector3.new(x,BASE_Y,z)
    local trunkH=5.1*scale
    local trunk=deco("Bark_"..index.."_"..side,center+Vector3.new(0,trunkH*0.5,0),
        Vector3.new(trunkH,.9*scale,.9*scale),Color3.fromRGB(90,70,60),Enum.Material.Wood,Enum.PartType.Cylinder)
    if trunk then trunk.CFrame=CFrame.new(trunk.Position)*CFrame.Angles(0,0,math.pi*.5) end
    -- Overlapping asymmetrical organic crowns: no square "toy-box" leaves.
    local branches={
        {Vector3.new(-1.25,4.8,-.3),Vector3.new(4.7,3.3,3.6),1},
        {Vector3.new(1.25,5.65,.2),Vector3.new(4.5,3.8,4.2),2},
        {Vector3.new(.1,7.35,-.2),Vector3.new(4.1,3.2,3.8),3},
        {Vector3.new(-.45,5.4,1.55),Vector3.new(3.2,2.6,3),4},
    }
    for j,data in ipairs(branches) do
        local p=deco("LeafMass_"..index.."_"..side.."_"..j,
            center+data[1]*scale,data[2]*scale,
            greens[(index+j+math.abs(side))%#greens+1],Enum.Material.Grass,Enum.PartType.Ball)
        if p then p.Transparency=0 end
    end
    for j,sign in ipairs({-1,1}) do
        local p=deco("RootFlare_"..index.."_"..j,
            center+Vector3.new(sign*.54,.36,-.25)*scale,
            Vector3.new(.75,1.3,.95)*scale,
            Color3.fromRGB(103,82,67),Enum.Material.Wood,Enum.PartType.Ball)
        if p then p.Transparency=0 end
    end
end
local leftMargin=math.min(85,ground.Size.X*.33)
local sideZ=math.max(29,ground.Size.Z*.40)
-- Near-bank silhouette, leaving the central 24-stud road / sea / spawn / castle / eggs clear.
-- Exactly 18 trees in two short bands, low enough to not cover castle silhouettes.
for side=-1,1,2 do
    for i=1,9 do
        local x=-leftMargin+(i-1)*(2*leftMargin/8)+scatter(i,side)*3.3
        local z=side*(sideZ+scatter(i+21,side)*3.2)
        local scale=.84+(scatter(i+43,side)+1)*.14
        makeTree(i,side,x,z,scale)
    end
end
-- 12 pairs of stone outcrops / flower tufts at visual edges; zero gameplay collisions.
for i=1,12 do
    local side=if i%2==0 then 1 else -1
    local x=-leftMargin+((i-1)%6)*(2*leftMargin/5)+scatter(i+79,side)*2
    local z=side*(sideZ-7+scatter(i+39,side)*3)
    local center=Vector3.new(x,BASE_Y,z)
    local shape=deco("StoneArc_"..i,center+Vector3.new(0,.48,0),
        Vector3.new(1.4,.98,1.1)*(.9+math.abs(scatter(i,side))*.32),
        stone[(i%#stone)+1],Enum.Material.Slate,Enum.PartType.Ball)
    if shape then shape.Orientation=Vector3.new(11,i*39,7) end
    local tuft=deco("BrushCluster_"..i,center+Vector3.new(1.4,.5,0),
        Vector3.new(1.15,1.1,.75),greens[(i%#greens)+1],Enum.Material.Grass,Enum.PartType.Ball)
    if tuft then tuft.Orientation=Vector3.new(9,31*i,18) end
end
-- Two small visual trails of natural ground patches to lead the eye toward each castle.
-- Not solid obstacles; no large neon boards or labels.
for side=-1,1,2 do
    for i=1,8 do
        local x=side*(15+i*9.4)
        local z=side*(25+math.sin(i*3.7)*3)
        local p=deco("GroundMoss_"..side.."_"..i,
            Vector3.new(x,BASE_Y+.028,z),
            Vector3.new(2.5+.3*i,.07,2.8),
            greens[(i%#greens)+1],Enum.Material.Grass,Enum.PartType.Ball)
        if p then p.Transparency=.12 end
    end
end
-- Color grading is global but only in the author's Studio preview.
-- Never change another scene's Atmosphere/Clouds or third-party named post-effect.
Lighting.ClockTime=15.65
Lighting.Brightness=2.35
Lighting.ExposureCompensation=0
Lighting.Ambient=Color3.fromRGB(118,123,127)
Lighting.OutdoorAmbient=Color3.fromRGB(150,155,161)
Lighting.GlobalShadows=true
if not Lighting:FindFirstChildOfClass("Atmosphere") then
    local at=Instance.new("Atmosphere")
    at.Name="P0D_FB015_HorizonAtmosphere"
    at.Density=.28
    at.Offset=.12
    at.Haze=1.2
    at.Glare=.1
    at.Color=Color3.fromRGB(205,220,228)
    at.Decay=Color3.fromRGB(114,134,142)
    at.Parent=Lighting
end
if not Lighting:FindFirstChild("P0D_FB015_WarmColorGrade") then
    local grade=Instance.new("ColorCorrectionEffect")
    grade.Name="P0D_FB015_WarmColorGrade"
    grade.Contrast=.07
    grade.Saturation=.1
    grade.Brightness=.01
    grade.TintColor=Color3.fromRGB(251,243,232)
    grade.Parent=Lighting
end
if not Terrain:FindFirstChildOfClass("Clouds") then
    local clouds=Instance.new("Clouds")
    clouds.Name="P0D_FB015_CanvasClouds"
    clouds.Cover=.34
    clouds.Density=.38
    clouds.Color=Color3.fromRGB(245,238,231)
    clouds.Parent=Terrain
end
folder:SetAttribute("NonBlocking",true)
folder:SetAttribute("MaxPartBudget",MAX_PARTS)
folder:SetAttribute("ActualPartCount",count)
folder:SetAttribute("ForestPlacedAfterCastleExpanded",true)
folder:SetAttribute("ForestNorthSouthZ",sideZ)
folder:SetAttribute("ForestSourceMapWidth",ground.Size.X)
folder:SetAttribute("ForestSourceMapDepth",ground.Size.Z)
folder:SetAttribute("ArtPass","FB015_WORLD_PALETTE_FOLIAGE_ONLY")
folder:SetAttribute("OfficialOwnerAccepted",false)
