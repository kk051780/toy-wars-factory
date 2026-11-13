--!strict
-- S2+ OPTIONAL physical shortcut choke. SOURCE_ONLY, NOT S1 or RC integrated.
-- Two mirror-symmetric doors gate the actual H1 SEA route at z=-22.
-- Free outer grass detours (z>=12), SKY route (z=18) remain available.
-- Single original Game server must publish ONE GateRules snapshot to BOTH.
local GateRouteOverlay = {}

-- Literal, testable geometry tied to the existing H1 sea passage.
local ROUTE_GATE_X = 36
local ROUTE_GATE_Z = -22
local ROUTE_GATE_WIDTH = 10
local ROUTE_ARM_NORTH_Z = -3.5
local ROUTE_ARM_NORTH_LENGTH = 27
local ROUTE_ARM_SOUTH_Z = -34.5
local ROUTE_ARM_SOUTH_LENGTH = 15
local ROUTE_WALL_THICKNESS = 2.4
local ROUTE_WALL_HEIGHT = 10

local function validH1World(arena)
    if arena == nil or not arena:IsA("Instance") then
        return nil
    end
    local existing = arena:FindFirstChild("H1_FUN_WORLD")
    if not existing then return nil end
    local sea = existing:FindFirstChild("SEA_LOW_CAUSEWAY")
    local left = existing:FindFirstChild("SEA_ENTRY_RED")
    local right = existing:FindFirstChild("SEA_ENTRY_BLUE")
    if not sea or not left or not right then return nil end
    if not sea:IsA("BasePart") or not left:IsA("BasePart")
        or not right:IsA("BasePart") or not sea.CanCollide then return nil end
    if math.abs(sea.Position.Z - ROUTE_GATE_Z) > 0.5 then return nil end
    if math.abs(sea.Position.X) > 0.5 then return nil end
    if sea.Size.X < ROUTE_GATE_WIDTH then return nil end
    return existing
end

local function barrier(model: Model, name: string, x: number, z: number, length: number)
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.CanCollide = true
    part.CanQuery = true
    part.CanTouch = false
    part.Material = Enum.Material.Cobblestone
    part.Color = Color3.fromRGB(112,131,152)
    part.Size = Vector3.new(ROUTE_WALL_THICKNESS,ROUTE_WALL_HEIGHT,length)
    part.Position = Vector3.new(x,ROUTE_WALL_HEIGHT/2,z)
    part.Parent = model
    return part
end

-- Fail closed without mutating any map if the real route is absent/misaligned.
-- The original Game owner is responsible for calling ONLY after H1 source built.
function GateRouteOverlay.create(arena: Instance,gateVisual)
    local h1 = validH1World(arena)
    if not h1 then return nil,"H1_SEA_SOURCE_NOT_READY_OR_CHANGED" end
    if arena:FindFirstChild("P0D_S2_NeutralShortcut_ReviewOnly") then
        return nil,"DUPLICATE_S2_GATE_REJECTED"
    end
    if gateVisual == nil or type(gateVisual.create) ~= "function"
        or type(gateVisual.render) ~= "function" then
        return nil,"ORIGINAL_GATE_VISUAL_REQUIRED"
    end
    local model = Instance.new("Model")
    model.Name = "P0D_S2_NeutralShortcut_ReviewOnly"
    local doors = {}
    for _,teamSign in ipairs({-1,1}) do
        local x = teamSign * ROUTE_GATE_X
        local prefix = teamSign == -1 and "RED" or "BLUE"
        -- Door long local X aligns to world Z after a 90 degree Y rotation.
        local door = gateVisual.create(model,
            CFrame.new(x,6,ROUTE_GATE_Z) * CFrame.Angles(0,math.pi/2,0),
            ROUTE_GATE_WIDTH)
        door.Name = prefix .. "_SHARED_SEA_GATE"
        table.insert(doors,door)
        barrier(model,prefix .. "_NORTH_ARM",x,ROUTE_ARM_NORTH_Z,ROUTE_ARM_NORTH_LENGTH)
        barrier(model,prefix .. "_SOUTH_ARM",x,ROUTE_ARM_SOUTH_Z,ROUTE_ARM_SOUTH_LENGTH)
    end
    assert(#doors==2,"must have two mirror-symmetric real gates")
    model.Parent = arena
    return {model=model,doors=doors},nil
end

function GateRouteOverlay.render(route,gateVisual,snapshot)
    assert(route ~= nil and type(route.doors) == "table" and #route.doors==2,
        "two real sea route doors required")
    assert(type(snapshot)=="table" and type(snapshot.passable)=="boolean",
        "server GateRules snapshot required")
    for _,door in ipairs(route.doors) do
        gateVisual.render(door,snapshot)
    end
end

return GateRouteOverlay
