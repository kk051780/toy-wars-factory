--!strict
-- FB-010 / FB-015: PRIVATE73 detailed fantasy fortress visual layer.
-- Based on original #366 3-route castle. No parts replace Game/egg/core/gate
-- collision or score. Visual geometry is noncolliding and nonqueryable.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local root = workspace:WaitForChild("TRAP_RAIDERS_S1", 90)
if not root then return end
local world = root:WaitForChild("OWNER361_CASTLE_WORLD_V1", 90)
if not world then return end
local red = world:WaitForChild("RED_CASTLE_ARCHITECTURE", 30)
local blue = world:WaitForChild("BLUE_CASTLE_ARCHITECTURE", 30)
if not red or not blue then return end
for _, castle in ipairs({red, blue}) do
    if not castle:FindFirstChild("GRAND_KEEP") or not castle:FindFirstChild("GATE_TOWER_-1")
        or not castle:FindFirstChild("GATE_TOWER_1") then
        warn("FB015_CASTLE_DETAIL_UNFINISHED_CASTLE_ANCHOR")
        return
    end
end
if root:FindFirstChild("FB015_CASTLE_DETAIL_ART_V2") then return end

local folder = Instance.new("Folder")
folder.Name = "FB015_CASTLE_DETAIL_ART_V2"
folder:SetAttribute("OwnerFeedbackID","FB-010+FB-015")
folder:SetAttribute("VisualOnly",true)
folder:SetAttribute("PlaySolo","NOT_TESTED")
folder:SetAttribute("AndroidFPS","NOT_TESTED")
folder:SetAttribute("OwnerArtAccepted",false)
folder.Parent = root

local MAX_PARTS = 190
local made = 0
local C = Color3.fromRGB
local PALE_STONE = C(189,181,160)
local TRIM_STONE = C(107,115,129)
local BASALT = C(58,67,83)
local COPPER = C(172,122,74)
local WOOD = C(91,66,57)
local GOLD = C(239,188,99)
local WINDOW = C(47,67,85)

local function ornament(parent: Instance, label: string, size: Vector3,
        position: Vector3, color: Color3, material: Enum.Material,
        shape: string, rotation: CFrame?): BasePart
    assert(made < MAX_PARTS,"FB015_CASTLE_DETAIL_BUDGET_EXCEEDED")
    local p: BasePart
    if shape == "WEDGE" then
        p = Instance.new("WedgePart")
    else
        local b = Instance.new("Part")
        if shape == "BALL" then b.Shape = Enum.PartType.Ball end
        if shape == "CYLINDER" then b.Shape = Enum.PartType.Cylinder end
        p = b
    end
    made += 1
    p.Name = label
    p.Size = size
    p.Color = color
    p.Material = material
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = shape == "WEDGE"
    p.CFrame = CFrame.new(position) * (rotation or CFrame.identity)
    p.Parent = parent
    return p
end

local function turretRoof(parent: Instance, x: number, z: number,
        y: number, width: number, depth: number, tint: Color3,
        name: string)
    -- Four steep intersecting sloped pieces: a recognizable pitched tower cap.
    -- No unlicensed external meshes or textures; actual 3D silhouette.
    for _, sx in ipairs({-1,1}) do
        local part = ornament(parent,name.."_PITCH_X_"..sx,
            Vector3.new(width*.57,6,depth*.58),
            Vector3.new(x+sx*width*.235,y+3,z), tint,
            Enum.Material.Slate, "WEDGE",
            CFrame.Angles(0,if sx<0 then math.pi else 0,0))
        part.Transparency = 0
    end
    for _, sz in ipairs({-1,1}) do
        ornament(parent,name.."_PITCH_Z_"..sz,
            Vector3.new(depth*.53,5,width*.44),
            Vector3.new(x,y+3.8,z+sz*depth*.27),
            tint,Enum.Material.Slate,"WEDGE",
            CFrame.Angles(0,(sz==1 and math.pi/2 or -math.pi/2),0))
    end
    ornament(parent,name.."_RIDGE_FINIAL",
        Vector3.new(.8,3,.8),Vector3.new(x,y+7.8,z),
        GOLD,Enum.Material.Metal,"BALL")
end

local function window(parent: Instance, x: number, y: number, z: number,
        face: number, label: string)
    local frame=ornament(parent,label.."_FRAME",
        Vector3.new(.5,4.4,2.2),Vector3.new(x,y,z),
        PALE_STONE,Enum.Material.Cobblestone,"BLOCK")
    frame.CFrame = frame.CFrame * CFrame.Angles(0, if face < 0 then .02 else -.02,0)
    ornament(parent,label.."_RECESS",
        Vector3.new(.17,3.2,1.25),Vector3.new(x+face*.31,y,z),
        WINDOW,Enum.Material.Slate,"BLOCK")
end

local function teamCastle(side: number, name: string, theme: Color3)
    local art = Instance.new("Folder")
    art.Name = name.."_ARCHITECTURAL_DETAIL"
    art.Parent = folder
    local paint = if name=="RED" then C(137,61,65) else C(57,85,129)
    local keepX=side*145
    -- The outer keep gains roofs, openings, buttresses, banners and landmarks.
    -- All additions at or above original keep envelope; no egg/core hitbox.
    turretRoof(art,keepX,0,44,25,39,paint,"KEEP")
    ornament(art,"KEEP_HERALDRY",Vector3.new(.25,6.4,7.5),
        Vector3.new(keepX-side*10.2,31,0),theme,
        Enum.Material.Metal,"BLOCK")
    ornament(art,"KEEP_HERALDRY_MEDALLION",Vector3.new(.35,3.1,3.1),
        Vector3.new(keepX-side*10.52,31,0),GOLD,
        Enum.Material.Metal,"BALL")
    for _, z in ipairs({-13,0,13}) do
        window(art,keepX-side*10.15,22,z,-side,
            "KEEP_WINDOW_"..z)
    end
    -- Vertical ashlar pilasters supply real facade depth instead of flat boxes.
    for _, z in ipairs({-19,19}) do
        ornament(art,"KEEP_CORNER_PILASTER_"..z,
            Vector3.new(1.4,36,2.1),Vector3.new(keepX-side*10.4,19,z),
            PALE_STONE,Enum.Material.Limestone,"BLOCK")
    end

    for _, bank in ipairs({-1,1}) do
        local z=bank*53
        local towerX=side*85
        turretRoof(art,towerX,z,33,19,19,paint,"GATE_TOWER_"..bank)
        -- Shaded slit windows, an accent stripe and hanging fabric.
        window(art,towerX-side*8.2,19,z,-side,"GATE_ARROWSLIT_"..bank)
        ornament(art,"TOWER_BANNER_"..bank,
            Vector3.new(.4,6.2,4.4),
            Vector3.new(towerX-side*9.3,27,z),
            theme,Enum.Material.Fabric,"WEDGE")
        for _, railZ in ipairs({z-5,z+5}) do
            ornament(art,"TOWER_CORNICE_"..bank.."_"..railZ,
                Vector3.new(2,1.1,2),Vector3.new(towerX-side*9.5,29,railZ),
                TRIM_STONE,Enum.Material.Cobblestone,"BLOCK")
        end

        local innerX=side*123
        local innerZ=bank*36
        turretRoof(art,innerX,innerZ,29,17.5,17.5,
            BASALT,"INNER_WATCH_"..bank)
        ornament(art,"INNER_HERALDRY_"..bank,
            Vector3.new(.35,4.5,3.7),
            Vector3.new(innerX-side*7.5,20,innerZ),
            theme,Enum.Material.Fabric,"WEDGE")
    end

    -- Gate arch around an open and traversable entrance. Unlike an old flat
    -- black board, all detail remains visual-only and above eye level.
    local gateX=side*84.3
    for _, z in ipairs({-12,12}) do
        ornament(art,"PORTCULLIS_STONE_PIER_"..z,
            Vector3.new(2.5,13,3),Vector3.new(gateX,12.5,z),
            PALE_STONE,Enum.Material.Cobblestone,"BLOCK")
    end
    ornament(art,"PORTCULLIS_ARCH_TOP",Vector3.new(2.5,2.8,28),
        Vector3.new(gateX,20.3,0),
        PALE_STONE,Enum.Material.Cobblestone,"BLOCK")
    for _, z in ipairs({-8,0,8}) do
        ornament(art,"PORTCULLIS_IRON_TEETH_"..z,
            Vector3.new(.6,4.5,.85),Vector3.new(gateX-side*1.1,19,z),
            BASALT,Enum.Material.Metal,"WEDGE")
    end

    -- Two guard beacons at the castle entry, giving the team a memorable look.
    for _, z in ipairs({-13,13}) do
        local basin=ornament(art,"BRAZIER_"..z,Vector3.new(2.8,1.1,2.8),
            Vector3.new(gateX-side*3.3,8.3,z),COPPER,Enum.Material.Metal,"BALL")
        local light=Instance.new("PointLight")
        light.Name="FB015_FortressBrazierGlow"
        light.Color=GOLD
        light.Range=13
        light.Brightness=.7
        light.Shadows=false
        light.Parent=basin
        ornament(art,"BRAZIER_EMBER_"..z,Vector3.new(1.3,1.4,1.3),
            Vector3.new(gateX-side*3.3,9.2,z),
            GOLD,Enum.Material.Neon,"BALL")
    end

    -- Gold/stone badges face the field; avoids giant world Billboard labels.
    art:SetAttribute("Theme",name)
    art:SetAttribute("NoNewGui",true)
end

teamCastle(-1,"RED",C(235,103,92))
teamCastle(1,"BLUE",C(95,161,232))
folder:SetAttribute("DecorativePartCount",made)
folder:SetAttribute("MaximumDecorativePartCount",MAX_PARTS)
folder:SetAttribute("GameAuthorityUntouched",true)
print("FB015_FORTRESS_DETAIL_PRIVATE73_SOURCE_READY_NO_STUDIO_FUN")
