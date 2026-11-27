-- Native Luau test doubles for the Roblox calls made by the extracted source.
local vector = {}
local function xyz(x, y, z)
    return setmetatable({X=x, Y=y, Z=z}, vector)
end

function vector:Dot(other)
    return self.X*other.X + self.Y*other.Y + self.Z*other.Z
end

function vector.__index(self, key)
    if key == "Magnitude" then return math.sqrt(self:Dot(self)) end
    if key == "Unit" then return self * (1 / self.Magnitude) end
    return vector[key]
end

function vector.__add(a, b) return xyz(a.X+b.X, a.Y+b.Y, a.Z+b.Z) end
function vector.__sub(a, b) return xyz(a.X-b.X, a.Y-b.Y, a.Z-b.Z) end
function vector.__mul(a, b) return xyz(a.X*b, a.Y*b, a.Z*b) end

local frame = {}
local function pointFrame(position)
    return setmetatable({Position=position}, frame)
end

function frame.__add(a, b) return pointFrame(a.Position+b) end

local Vector3 = {new=xyz}
local CFrame = {new=pointFrame}
local RaycastParams = {new=function() return {} end}
local OverlapParams = {new=function() return {} end}
local Enum = {RaycastFilterType={Exclude={}}}
local workspace = {}

-- @movement-source

local function movementParameters(model)
-- @movement-settings
    return movementRay, movementOverlap
end

local function assertVector(actual, expected, field)
    assert(actual and expected, field .. " is absent")
    assert((actual-expected).Magnitude < 1e-6, field .. " changed")
end

local model = {}
local ray, overlap = movementParameters(model)
assert(ray ~= overlap, "Raycast and overlap need independent settings")
for _, params in ipairs({ray, overlap}) do
    assert(params.FilterType == Enum.RaycastFilterType.Exclude)
    assert(#params.FilterDescendantsInstances == 1 and params.FilterDescendantsInstances[1] == model)
    assert(params.RespectCanCollide == true)
end
assert(overlap.MaxParts == 1)
assertVector(GUARD_BODY_SIZE, xyz(2.8, 3.4, 2.8), "body size")
assertVector(GUARD_BODY_OFFSET, xyz(0, 1.85, 0), "body offset")

local start = xyz(7, 9, -13)
local expectedCenter = xyz(7, 10.85, -13)
local shallowWall = {center=xyz(7, 12, -14.8), size=xyz(30, 12, 2)}
local function occupants(center, size, wall)
    if not wall then return {} end
    local delta = center-wall.center
    if math.abs(delta.X) < (size.X+wall.size.X)/2
        and math.abs(delta.Y) < (size.Y+wall.size.Y)/2
        and math.abs(delta.Z) < (size.Z+wall.size.Z)/2 then
        return {wall}
    end
    return {}
end

local scenario, castCount, overlapCount
function workspace:Blockcast(origin, size, delta, params)
    castCount += 1
    local observation = assert(scenario.casts[castCount], "Unexpected sweep")
    assert(params == ray, "The original sweep settings are required")
    assertVector(origin.Position, expectedCenter, "sweep center")
    assertVector(size, GUARD_BODY_SIZE, "sweep size")
    assertVector(delta, observation.direction, "sweep direction")
    return if observation.normal then {Normal=observation.normal} else nil
end

function workspace:GetPartBoundsInBox(origin, size, params)
    overlapCount += 1
    local delta = assert(scenario.endCheck, "Unexpected endpoint check")
    assert(params == overlap, "The original overlap settings are required")
    assertVector(origin.Position, expectedCenter+delta, "endpoint center")
    assertVector(size, GUARD_BODY_SIZE, "endpoint size")
    return occupants(origin.Position, size, scenario.wall)
end

local clear = xyz(.6, 0, .5)
local towardWall = xyz(0, 0, .8)
local oblique = xyz(.6, 0, .7)
local tangent = xyz(.6, 0, 0)
local frontNormal = xyz(0, 0, -1)
local inward = xyz(0, 0, -.8)
local outward = xyz(0, 0, .8)

assert(#occupants(expectedCenter, GUARD_BODY_SIZE, shallowWall) == 1)
assert(#occupants(expectedCenter+inward, GUARD_BODY_SIZE, shallowWall) == 1)
assert(#occupants(expectedCenter+outward, GUARD_BODY_SIZE, shallowWall) == 0)

local cases = {
    {name="clear", step=clear, casts={{direction=clear}}, endCheck=clear, result=clear},
    {name="straight_wall", step=towardWall, casts={{direction=towardWall, normal=frontNormal}}},
    {name="oblique_tangent", step=oblique,
        casts={{direction=oblique, normal=frontNormal}, {direction=tangent}}, endCheck=tangent, result=tangent},
    {name="vertical_normal", step=clear, casts={{direction=clear, normal=xyz(0, 1, 0)}}},
    -- Roblox's sweep omits initial intersections. Verify the endpoint decision in each direction.
    {name="initial_and_end_overlap", step=inward, casts={{direction=inward}}, endCheck=inward, wall=shallowWall},
    {name="shallow_overlap_exit", step=outward, casts={{direction=outward}},
        endCheck=outward, wall=shallowWall, result=outward},
    {name="tangent_blocked_by_second_wall", step=oblique,
        casts={{direction=oblique, normal=frontNormal}, {direction=tangent, normal=xyz(-1, 0, 0)}}},
}

for _, case in ipairs(cases) do
    scenario, castCount, overlapCount = case, 0, 0
    local actual = clearGuardStep(start, case.step, ray, overlap)
    if case.result then
        assertVector(actual, start+case.result, case.name)
    else
        assert(actual == nil, case.name .. " must block movement")
    end
    assert(castCount == #case.casts, case.name .. " did not run every expected sweep")
    assert(overlapCount == (if case.endCheck then 1 else 0), case.name .. " used the wrong endpoint checks")
    print("PASS " .. case.name)
end
