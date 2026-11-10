--!strict
-- TRAP RAIDERS S1 original map architecture. Optional explicit call ONLY.
-- Does not run by itself: MapBuilder owner must call .build(root) after the map exists.
-- Every created Part is anchored, non-collidable, non-touchable, non-queryable.
-- No player, round, remotes, data, score, HP, authority, monetization or reward API.
local Plan = require(script.Parent:WaitForChild("CastleArchitecturePlan")) :: {any}
local Architecture = {}
local ROOT_NAME = "TRAP_RAIDERS_S1"
local VISUAL_NAME = "S1_ARCHITECTURE_VISUAL_ONLY"
local PART_LIMIT = 80
local PALETTE = {
    STONE = {color = Color3.fromRGB(170, 177, 188), material = Enum.Material.Slate},
    COPPER = {color = Color3.fromRGB(226, 189, 115), material = Enum.Material.Metal},
    RED = {color = Color3.fromRGB(204, 99, 104), material = Enum.Material.SmoothPlastic},
    BLUE = {color = Color3.fromRGB(96, 154, 222), material = Enum.Material.SmoothPlastic},
    DARK = {color = Color3.fromRGB(76, 92, 110), material = Enum.Material.Slate},
}

local function finite(value: any): boolean
    return type(value) == "number" and value == value and math.abs(value) < 1000000
end

local function validEntry(entry: any, seen: {[string]: boolean}): boolean
    if type(entry) ~= "table" or type(entry.id) ~= "string" then return false end
    local id = entry.id
    local prefixOk = string.sub(id, 1, 4) == "RED_" or string.sub(id, 1, 5) == "BLUE_"
        or string.sub(id, 1, 4) == "MID_"
    if seen[id] or #id > 90 or not prefixOk then return false end
    if type(entry.center) ~= "table" or #entry.center ~= 3 then return false end
    if type(entry.size) ~= "table" or #entry.size ~= 3 then return false end
    if type(entry.style) ~= "string" or PALETTE[entry.style] == nil then return false end
    for axis = 1, 3 do
        if not finite(entry.center[axis]) or not finite(entry.size[axis]) then return false end
        if entry.size[axis] < 0.1 or entry.size[axis] > 50 then return false end
    end
    local x, y, z = entry.center[1], entry.center[2], entry.center[3]
    local sx, sy, sz = entry.size[1], entry.size[2], entry.size[3]
    if math.abs(x) + sx / 2 > 129 or math.abs(z) + sz / 2 > 75 then return false end
    if y - sy / 2 < 0 or y + sy / 2 > 32 then return false end
    seen[entry.id] = true
    return true
end

-- Safe, idempotent and fail-closed. A second call never duplicates geometry.
function Architecture.build(root: Instance): (boolean, string)
    if typeof(root) ~= "Instance" or not root:IsA("Folder") or root.Name ~= ROOT_NAME then
        return false, "WRONG_MAP_ROOT"
    end
    if root.Parent ~= workspace or not root:FindFirstChild("RED_CASTLE")
        or not root:FindFirstChild("BLUE_CASTLE") then
        return false, "MAP_NOT_READY"
    end
    if root:FindFirstChild(VISUAL_NAME) then return false, "ALREADY_BUILT" end
    if #Plan == 0 or #Plan > PART_LIMIT then return false, "PART_BUDGET_INVALID" end

    local seen: {[string]: boolean} = {}
    for _, entry in ipairs(Plan) do
        if not validEntry(entry, seen) then return false, "PLAN_INVALID" end
    end

    local folder = Instance.new("Folder")
    folder.Name = VISUAL_NAME
    local ok = pcall(function()
        for _, entry in ipairs(Plan) do
            local material = PALETTE[entry.style]
            local p = Instance.new("Part")
            p.Name = entry.id
            p.Size = Vector3.new(entry.size[1], entry.size[2], entry.size[3])
            p.CFrame = CFrame.new(entry.center[1], entry.center[2], entry.center[3])
            p.Color = material.color
            p.Material = material.material
            p.Anchored = true
            p.CanCollide = false
            p.CanTouch = false
            p.CanQuery = false
            p.TopSurface = Enum.SurfaceType.Smooth
            p.BottomSurface = Enum.SurfaceType.Smooth
            p.Parent = folder
        end
    end)
    if not ok then
        folder:Destroy()
        return false, "VISUAL_CREATION_FAILED"
    end
    -- Atomic visible attachment after the source-owned map is fully built.
    if root:FindFirstChild(VISUAL_NAME) then
        folder:Destroy()
        return false, "ALREADY_BUILT"
    end
    folder.Parent = root
    return true, "BUILT_VISUAL_ONLY"
end

return Architecture
