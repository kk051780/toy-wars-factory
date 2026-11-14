--!strict
-- P0D GAME_CORE_REBUILD: optional Studio 3D visual battlefield extension.
-- Keeps original Game/Remote/Store/egg/score/HP authoritative and untouched.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local stage = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not stage then return end
if stage:FindFirstChild("P0D_CASTLE_WORLD_UPGRADE") then return end
local arena = stage:FindFirstChild("GrassArena")
local north = stage:FindFirstChild("ARENA_BOUNDARY_N")
local south = stage:FindFirstChild("ARENA_BOUNDARY_S")
local red = stage:FindFirstChild("RED_CASTLE")
local blue = stage:FindFirstChild("BLUE_CASTLE")
-- Fail closed; only augment the author's known 250x142 world.
if not (arena and arena:IsA("BasePart") and math.abs(arena.Size.X-250)<1
    and math.abs(arena.Size.Z-142)<1
    and north and north:IsA("BasePart") and south and south:IsA("BasePart")
    and red and blue) then return end
local model = Instance.new("Folder")
model.Name = "P0D_CASTLE_WORLD_UPGRADE"
model.Parent = stage

local slate = Color3.fromRGB(106,115,128)
local brick = Color3.fromRGB(136,138,142)
local darker = Color3.fromRGB(72,82,101)
local grass = Color3.fromRGB(62,112,73)
local sand = Color3.fromRGB(187,165,122)
local forest = Color3.fromRGB(37,97,64)
local gold = Color3.fromRGB(255,203,79)
local function block(parent: Instance,name: string,size: Vector3,pos: Vector3,
    color: Color3,material: Enum.Material,solid: boolean?): Part
    local p=Instance.new("Part")
    p.Name=name
    p.Size=size
    p.Position=pos
    p.Color=color
    p.Material=material
    p.Anchored=true
    p.CanCollide=solid==true
    p.CanTouch=false
    p.CanQuery=solid==true
    p.TopSurface=Enum.SurfaceType.Smooth
    p.BottomSurface=Enum.SurfaceType.Smooth
    p.Parent=parent
    return p
end
local function battlement(parent: Instance,tag: string,center: Vector3,accent: Color3)
    -- 4 crenellated towers per fortress, visible from across the map.
    block(parent,tag.."_BODY",Vector3.new(13,27,13),center+Vector3.new(0,13.5,0),
        brick,Enum.Material.Brick,true)
    block(parent,tag.."_CROWN",Vector3.new(17,2.5,17),center+Vector3.new(0,28,0),
        darker,Enum.Material.Cobblestone,true)
    for dx=-1,1,2 do
        for dz=-1,1,2 do
            block(parent,tag.."_MERLON",Vector3.new(3,5,3),
                center+Vector3.new(dx*6,31,dz*6),slate,Enum.Material.Cobblestone,false)
        end
    end
    local spire=block(parent,tag.."_BANNER_POLE",Vector3.new(0.8,17,0.8),
        center+Vector3.new(0,38,0),gold,Enum.Material.Metal,false)
    spire.CanQuery=false
    local flag=block(parent,tag.."_BANNER",Vector3.new(1,7,10),
        center+Vector3.new(0,43,5),accent,Enum.Material.Fabric,false)
    flag.Transparency=0.06
end
local function gatehouse(parent: Instance,side: number,accent: Color3,tag: string)
    local x=side*87
    -- A 19 stud clear central gateway keeps the old egg and core approachable.
    for _,z in ipairs({-15,15}) do
        block(parent,tag.."_GATE_PIER",Vector3.new(7,20,8),
            Vector3.new(x,10,z),slate,Enum.Material.Cobblestone,true)
    end
    block(parent,tag.."_GATE_LINTEL",Vector3.new(7,7,37),
        Vector3.new(x,23,0),brick,Enum.Material.Brick,true)
    for _,z in ipairs({-12,-4,4,12}) do
        block(parent,tag.."_CREST",Vector3.new(7,4,5),
            Vector3.new(x,28,z),accent,Enum.Material.Slate,false)
    end
    -- Elevated window/roof on the rear of the existing core, visual only.
    block(parent,tag.."_KEEP_WALL",Vector3.new(9,18,26),
        Vector3.new(side*119,18,0),darker,Enum.Material.Cobblestone,false)
    block(parent,tag.."_KEEP_ROOF",Vector3.new(13,3,31),
        Vector3.new(side*119,28,0),accent,Enum.Material.Slate,false)
end

-- Grow the land without moving any original interactables or trusted spawns.
arena.Size=Vector3.new(520,4,254)
for _,wall in ipairs({north,south}) do
    local sign=if wall==north then -1 else 1
    wall.Size=Vector3.new(520,15,5)
    wall.Position=Vector3.new(0,7,sign*127)
end
-- Three recognizable routes: central siege, forest flank, rocky highland.
for i,route in ipairs({{z=0,w=26},{z=-84,w=17},{z=84,w=17}}) do
    block(model,"INVASION_ROUTE_"..tostring(i),Vector3.new(477,.32,route.w),
        Vector3.new(0,-.79,route.z),if i==1 then sand else slate,
        if i==1 then Enum.Material.Sand else Enum.Material.Cobblestone,false)
end
-- Shallow river is a visual marker, never an untested lethal physics hazard.
local river=block(model,"RIVER_VISUAL_ONLY",Vector3.new(16,.13,230),
    Vector3.new(0,-.59,0),Color3.fromRGB(69,145,178),Enum.Material.Glass,false)
river.Transparency=0.24
for i,z in ipairs({0,-84,84}) do
    block(model,"RIVER_BRIDGE_"..i,Vector3.new(25,.6,if z==0 then 29 else 21),
        Vector3.new(0,-.4,z),sand,Enum.Material.WoodPlanks,true)
end
-- Flank forests create cover without blocking the three route centerlines.
for _,z in ipairs({-112,112}) do
    for _,x in ipairs({-210,-168,-119,-62,62,119,168,210}) do
        local side=if z<0 then "N" else "S"
        local tag="TREE_"..side.."_"..tostring(math.abs(x)).."_"..(if x<0 then "W" else "E")
        block(model,tag.."_TRUNK",Vector3.new(3.2,11,3.2),
            Vector3.new(x,5.5,z),Color3.fromRGB(100,76,53),Enum.Material.Wood,true)
        local crown=block(model,tag.."_CANOPY",Vector3.new(13,15,13),
            Vector3.new(x,15,z),forest,Enum.Material.Grass,false)
        crown.Shape=Enum.PartType.Ball
    end
end
-- Rocks and low terraces support line-of-sight decisions and flank identity.
for _,x in ipairs({-181,-130,-51,51,130,181}) do
    for _,z in ipairs({-64,64}) do
        local rock=block(model,"ROCK_COVER",Vector3.new(12,8,8),
            Vector3.new(x,4,z),slate,Enum.Material.Slate,true)
        rock.CFrame=CFrame.new(rock.Position)*CFrame.Angles(0,math.rad(18),0)
    end
end
for _,side in ipairs({-1,1}) do
    local name=if side<0 then "RED" else "BLUE"
    local accent=if name=="RED" then Color3.fromRGB(213,63,65)
        else Color3.fromRGB(65,119,227)
    local castle=Instance.new("Folder")
    castle.Name=name.."_3D_FORTRESS"
    castle.Parent=model
    gatehouse(castle,side,accent,name)
    for _,x in ipairs({96,121}) do
        for _,z in ipairs({-39,39}) do
            battlement(castle,name.."_TOWER",Vector3.new(side*x,0,z),accent)
        end
    end
    -- Huge colored flags distinguish the castles without obstructive text GUIs.
    block(castle,name.."_FLAG_MAST",Vector3.new(1.2,28,1.2),
        Vector3.new(side*109,42,0),gold,Enum.Material.Metal,false)
    block(castle,name.."_ROYAL_BANNER",Vector3.new(1.2,12,15),
        Vector3.new(side*109,51,8),accent,Enum.Material.Fabric,false)
end
-- Do not create a second map/model/Game or any RemoteEvent/score/Damage handler.
print("P0D_CASTLE_WORLD_UPGRADE_STUDIO_3_ROUTES_REAL_CASTLES_READY_FOR_STUDIO_QA")
