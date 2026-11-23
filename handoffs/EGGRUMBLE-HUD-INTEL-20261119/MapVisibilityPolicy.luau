-- GQ8_HUD_INTEL_FOG_20261119 - server-only map projection policy.
-- This code MUST run before data is sent to clients. Do not send hidden
-- world positions in a transparent GUI. Caller certifies round/role/LOS.
local M = {}
M.CELL = 40
M.SPAWN_RADIUS = 90
M.SECTOR = 80
local VALID_ROLES = {
    WARRIOR = true, MAGE = true, NINJA = true, TRAPPER = true,
    BUILDER = true, BEAST = true, ZOMBIE = true,
}
local function cell(x, z)
    return math.floor(x / M.CELL) .. ":" .. math.floor(z / M.CELL)
end
function M.newExploration(castleX, castleZ)
    local cells = {}
    M.reveal(cells, castleX, castleZ, M.SPAWN_RADIUS)
    return cells
end
function M.reveal(cells, cx, cz, radius)
    -- Only call after server-valid spawn or movement; never raw client coords.
    assert(type(cells) == "table")
    assert(type(cx) == "number" and type(cz) == "number")
    radius = math.min(math.max(0, radius), 160)
    local a = math.floor((cx - radius) / M.CELL)
    local b = math.floor((cx + radius) / M.CELL)
    local c = math.floor((cz - radius) / M.CELL)
    local d = math.floor((cz + radius) / M.CELL)
    for x = a, b do
        for z = c, d do
            local px = x * M.CELL + M.CELL / 2
            local pz = z * M.CELL + M.CELL / 2
            if (px-cx)^2 + (pz-cz)^2 <= (radius+M.CELL*.71)^2 then
                cells[x .. ":" .. z] = true
            end
        end
    end
end
local function dist(v, m)
    return math.sqrt((v.x-m.x)^2 + (v.z-m.z)^2)
end
local function layerMatches(v, m)
    return m.layer == nil or v.layer == m.layer
end
local function sectorPosition(x, z)
    local size = M.SECTOR
    return math.floor(x / size) * size + size / 2,
        math.floor(z / size) * size + size / 2
end
local function markerSnapshot(m, precision, now)
    local x, z = m.x, m.z
    if precision == "SECTOR" then x, z = sectorPosition(x, z) end
    return {id = m.id, kind = m.kind, x = x, z = z,
        layer = m.layer or "LAND", precision = precision,
        expiresAt = precision == "EXACT" and now + 2 or now + 5}
end
local function validPulse(v, kind, now)
    return type(v.pulse) == "table" and v.pulse.kind == kind
        and type(v.pulse.expiresAt) == "number"
        and v.pulse.expiresAt > now
        and v.pulse.serverVerified == true
end
-- Each marker comes from actual server-owned world state, never a client query.
function M.project(viewer, markers, now)
    assert(type(viewer) == "table" and type(markers) == "table"
        and type(now) == "number" and VALID_ROLES[viewer.role])
    assert(type(viewer.x) == "number" and type(viewer.z) == "number")
    local fog = viewer.explored
    assert(type(fog) == "table" and viewer.serverVerified == true)
    local out = {}
    for _, m in ipairs(markers) do
        if type(m) == "table" and type(m.id) == "string"
            and type(m.x) == "number" and type(m.z) == "number"
            and (m.expiresAt == nil or m.expiresAt > now) then
            local precision = nil
            local d = dist(viewer, m)
            local explored = fog[cell(m.x, m.z)] == true
            local sameLayer = layerMatches(viewer, m)
            if m.kind == "CASTLE" or m.kind == "COARSE_TERRAIN" then
                precision = "EXACT" -- immutable public strategy anchors
            elseif m.kind == "SELF" and m.ownerId == viewer.playerId then
                precision = "EXACT"
            elseif m.kind == "ALLY" and m.team == viewer.team then
                if sameLayer and d <= 140 and explored then
                    precision = "EXACT"
                elseif validPulse(viewer, "ALLY_SIGNAL", now) then
                    precision = "SECTOR"
                end
            elseif m.kind == "ENEMY" and m.team ~= viewer.team then
                if sameLayer and d <= 75 and explored
                    and m.serverLineOfSight == true and m.stealthed ~= true then
                    precision = "EXACT"
                elseif sameLayer and d <= 180 and viewer.role == "TRAPPER"
                    and validPulse(viewer, "ENEMY_SENSE", now) then
                    precision = "SECTOR"
                end
            elseif m.kind == "ENEMY_TRAIL" then
                if viewer.role == "NINJA" and sameLayer and d <= 180
                    and (explored or validPulse(viewer, "TRAIL_SENSE", now)) then
                    precision = "SECTOR"
                end
            elseif m.kind == "NEUTRAL" or m.kind == "BEAST" then
                if sameLayer and explored and d <= 95
                    and m.serverLineOfSight == true then
                    precision = "EXACT"
                elseif sameLayer and d <= 200
                    and ((viewer.role == "BEAST" and validPulse(viewer, "BEAST_SENSE", now))
                      or (viewer.role == "ZOMBIE" and validPulse(viewer, "CURSE_SENSE", now))) then
                    precision = "SECTOR"
                end
            elseif m.kind == "EGG" then
                -- Objectives become visible only through actual server exploration,
                -- never just because a client asked for them.
                if explored then precision = "EXACT" end
            elseif m.kind == "RESOURCE" or m.kind == "DEVICE" then
                if explored then precision = "EXACT"
                elseif viewer.role == "BUILDER" and d <= 200
                    and validPulse(viewer, "RESOURCE_SENSE", now) then
                    precision = "SECTOR"
                end
            elseif m.kind == "ELEMENT" or m.kind == "MAGIC_TREASURE" then
                if explored then precision = "EXACT"
                elseif viewer.role == "MAGE" and d <= 200
                    and validPulse(viewer, "MAGIC_SENSE", now) then
                    precision = "SECTOR"
                end
            elseif m.kind == "CASTLE_GATE" or m.kind == "GUARDIAN" then
                if explored and d <= 110 then precision = "EXACT"
                elseif viewer.role == "WARRIOR" and d <= 160
                    and validPulse(viewer, "SIEGE_SENSE", now) then
                    precision = "SECTOR"
                end
            elseif m.kind == "TRAP" then
                if explored and d <= 55 and m.serverLineOfSight == true then
                    precision = "EXACT"
                elseif viewer.role == "TRAPPER" and d <= 160
                    and validPulse(viewer, "TRAP_SENSE", now) then
                    precision = "SECTOR"
                end
            end
            if precision then
                table.insert(out, markerSnapshot(m, precision, now))
            end
        end
    end
    return out
end
return M
