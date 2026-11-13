--!strict
-- S2+ optional S1-map-safe *physical* dual approach gate: two RED/BLUE
-- symmetric chokepoints (x = +/- 30, z = 0). It is NOT an auto-running script.
-- Requires the original sole Game server + GateRules snapshot integration.
-- The ever-open grass detour at |z| >= 15 is deliberate: no pay/role gate.
-- Does not overwrite MapBuilder, H1FunWorld, NPC, egg, score, or prompt.
local GateRouteOverlay = {}

-- Keep these constants inspectable by static owner-source geometry tests.
local ROUTE_GATE_X = 30
local ROUTE_DOOR_WIDTH = 8
local ROUTE_WALL_Z = 7.8
local ROUTE_WALL_Z_LENGTH = 7.5
local ROUTE_WALL_THICKNESS = 2.4
local ROUTE_WALL_HEIGHT = 12

local function makeBarrier(parent: Instance, name: string, position: Vector3): Part
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.CanCollide = true
    part.CanQuery = true
    part.CanTouch = false
    part.Material = Enum.Material.Cobblestone
    part.Color = Color3.fromRGB(112, 131, 152)
    part.Size = Vector3.new(ROUTE_WALL_THICKNESS, ROUTE_WALL_HEIGHT, ROUTE_WALL_Z_LENGTH)
    part.Position = position
    part.Parent = parent
    return part
end

function GateRouteOverlay.create(parent: Instance, gateVisual)
    assert(parent ~= nil and parent:IsA("Instance"), "parent must be existing Roblox Instance")
    assert(gateVisual ~= nil and type(gateVisual.create) == "function"
        and type(gateVisual.render) == "function", "authored GateVisual required")
    local model = Instance.new("Model")
    model.Name = "P0D_S2_NeutralShortcut_ReviewOnly"
    model.Parent = parent
    local doors = {}
    for _,side in ipairs({-1,1}) do
        local x = side * ROUTE_GATE_X
        local prefix = side == -1 and "RED" or "BLUE"
        -- The door's long local X must align with WORLD Z, not X.
        -- Two 7.5-stud wall arms block only the central sand road's z +/- 12.
        -- Minions occupy z +/- 18, castle walls are at x +/- 103,z +/- 44.
        local door = gateVisual.create(model,
            CFrame.new(x,ROUTE_WALL_HEIGHT/2,0) * CFrame.Angles(0,math.pi/2,0),
            ROUTE_DOOR_WIDTH)
        door.Name = prefix .. "_SHARED_GATE"
        table.insert(doors, door)
        for _,zSide in ipairs({-1,1}) do
            makeBarrier(model,prefix .. (zSide < 0 and "_LOWER" or "_UPPER") .. "_ARM",
                Vector3.new(x,ROUTE_WALL_HEIGHT/2,zSide*ROUTE_WALL_Z))
        end
    end
    assert(#doors == 2, "red/blue physical shared gate is required")
    return { model = model, doors = doors }
end

-- Single server GateRules snapshot drives both; never 2 different timers.
function GateRouteOverlay.render(route,gateVisual,snapshot)
    assert(route ~= nil and #route.doors == 2, "two doors required")
    assert(type(snapshot) == "table" and type(snapshot.passable) == "boolean",
        "server GateRules snapshot required")
    for _,door in ipairs(route.doors) do
        gateVisual.render(door,snapshot)
    end
end

return GateRouteOverlay
