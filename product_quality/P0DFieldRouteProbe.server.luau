--!strict
-- P0D #470 FB-009: Studio-private, explicitly opt-in, READ-ONLY path probe.
-- NOT wired into canonical Rojo Place. Integration requires B #220 approval.
-- This creates no world objects, authority, Remote, rewards, or HUD.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local ServerStorage = game:GetService("ServerStorage")
if ServerStorage:GetAttribute("P0D_FIELD_ROUTE_PROBE") ~= true then return end

local PathfindingService = game:GetService("PathfindingService")
local HttpService = game:GetService("HttpService")
local world = workspace:WaitForChild("TRAP_RAIDERS_S1", 60)
if not world then
    warn("P0D_FIELD_PROBE_WORLD_MISSING")
    return
end
local arena = world:FindFirstChild("GrassArena")
local red = world:FindFirstChild("RED_CASTLE")
local blue = world:FindFirstChild("BLUE_CASTLE")
if not arena or not arena:IsA("BasePart") or not red or not blue then
    warn("P0D_FIELD_PROBE_ANCHORS_MISSING")
    return
end
local startPart = red:FindFirstChild("RED_SPAWN")
local eggPart = blue:FindFirstChild("BLUE_EGG")
local padPart = red:FindFirstChild("RED_SCORE_PAD")
if not startPart or not startPart:IsA("BasePart")
    or not eggPart or not eggPart:IsA("BasePart")
    or not padPart or not padPart:IsA("BasePart") then
    warn("P0D_FIELD_PROBE_OBJECTIVES_MISSING")
    return
end

type Leg = { ok: boolean, reason: string, length_studs: number?, waypoints: number? }
local function leg(fromPos: Vector3, toPos: Vector3): Leg
    local path = PathfindingService:CreatePath({
        AgentRadius = 2,
        AgentHeight = 5,
        AgentCanJump = true,
        AgentCanClimb = false,
        WaypointSpacing = 6,
    })
    local ok, err = pcall(function()
        path:ComputeAsync(fromPos, toPos)
    end)
    if not ok then
        return {ok = false, reason = "COMPUTE_FAILED:" .. tostring(err)}
    end
    if path.Status ~= Enum.PathStatus.Success then
        return {ok = false, reason = "PATH_NOT_SUCCESS:" .. tostring(path.Status)}
    end
    local points = path:GetWaypoints()
    if #points == 0 then
        return {ok = false, reason = "PATH_NO_WAYPOINTS"}
    end
    local distance = 0
    local last = fromPos
    for _, point in ipairs(points) do
        distance += (point.Position - last).Magnitude
        last = point.Position
    end
    distance += (toPos - last).Magnitude
    return {ok = true, reason = "NAVMESH_PATH_SUCCESS", length_studs = math.floor(distance * 100 + 0.5) / 100, waypoints = #points}
end

local function atStand(part: BasePart): Vector3
    return part.Position + Vector3.new(0, 4, 0)
end
local startPos = atStand(startPart)
local eggPos = atStand(eggPart)
local padPos = atStand(padPart)
local lanes = {
    {name = "CENTER", z = 0},
    {name = "NORTH", z = -112},
    {name = "SOUTH", z = 111},
}
local report = {
    schema = "P0D_STUDIO_FIELD_ROUTE_PROBE_V1",
    issue = "470",
    environment = "STUDIO_OPT_IN_ONLY",
    place_id = game.PlaceId,
    arena_x = arena.Size.X,
    arena_z = arena.Size.Z,
    objective_red_spawn = {startPart.Position.X, startPart.Position.Y, startPart.Position.Z},
    objective_blue_egg = {eggPart.Position.X, eggPart.Position.Y, eggPart.Position.Z},
    objective_red_score = {padPart.Position.X, padPart.Position.Y, padPart.Position.Z},
    real_character_walk_time = "NOT_MEASURED",
    mobile_fps = "NOT_MEASURED",
    fun_score = "NOT_MEASURED",
    routes = {},
}
for _, lane in ipairs(lanes) do
    -- Four bounded path calculations per lane, crossing via its central branch.
    -- A path success is only a navmesh feasibility hint; it does not prove
    -- that a child can traverse the lane or carry an egg on a real device.
    local mid = Vector3.new(0, arena.Position.Y + arena.Size.Y * 0.5 + 4, lane.z)
    local a = leg(startPos, mid)
    local b = leg(mid, eggPos)
    local c = leg(eggPos, mid)
    local d = leg(mid, padPos)
    local allOk = a.ok and b.ok and c.ok and d.ok
    local total = if allOk then
        (a.length_studs or 0) + (b.length_studs or 0) + (c.length_studs or 0) + (d.length_studs or 0)
        else nil
    table.insert(report.routes, {
        lane = lane.name,
        midpoint_z = lane.z,
        midpoint_inside_ground = math.abs(lane.z - arena.Position.Z) <= arena.Size.Z / 2,
        outbound_legs = {a, b},
        return_legs = {c, d},
        pathfinding_complete = allOk,
        round_trip_path_length_studs = if total then math.floor(total * 100 + 0.5) / 100 else nil,
        note = "PathfindingService path only; not walk/egg/AI/user evidence",
    })
end
-- Exactly one JSON line for Studio Output capture, no UI/Remote/service writes.
print("P0D_FIELD_ROUTE_PROBE_JSON " .. HttpService:JSONEncode(report))
