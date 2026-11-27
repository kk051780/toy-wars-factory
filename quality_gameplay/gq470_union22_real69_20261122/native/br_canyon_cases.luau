-- Execute the locked placement fragments with translation-only CFrames.
local Vec = {}
Vec.__index = Vec
function Vec.__add(a, b)
 return setmetatable({X = a.X + b.X, Y = a.Y + b.Y, Z = a.Z + b.Z}, Vec)
end
local function vector(x, y, z)
 return setmetatable({X = x, Y = y, Z = z}, Vec)
end
local Vector3 = {new = vector}
local CFrame = {new = function(x, y, z)
 return if type(x) == "table" then x else vector(x, y, z)
end}
Vec.__mul = Vec.__add

local root = vector(0, 0, 0)
local Color3 = {fromRGB = function() return {} end}
local Enum = {Material = {Grass = true, Slate = true, Neon = true}}

-- @CASTLE_POINTS@

local function testMode(mode, expected)
 local session = {world = {}}
 local parts = {}
 local function block(name, size, center, _, _, collision)
  local part = {name = name, Size = size, Position = center, CFrame = center, CanCollide = collision}
  parts[name] = part
  return part
 end
 local function battlefieldBlock(_, name, position, size)
  return block(name, size, position)
 end
 local battlefield
 do
  local block = battlefieldBlock
  -- @BATTLEFIELD@
  battlefield = floor
 end
 local floor = battlefield
 local x, y, z = floor.Position.X, floor.Position.Y + floor.Size.Y / 2, floor.Position.Z
 local attributes = {}
 local core = {
  SetAttribute = function(_, name, value) attributes[name] = value end,
  GetAttribute = function(_, name) return attributes[name] end,
 }
 local CORE_NAME = "EGGRUMBLE_REALM_BATTLE_CORE"
 local world = session.world
 -- @REALM_OFFSET@
 local stars, meteors
 do
  -- @STARFALL_CENTER@
  stars = center
 end
 do
  -- @METEOR_CENTER@
  meteors = center
 end
 local arena = {FindFirstChild = function(_, name)
  if name == CORE_NAME and core.Parent == world then return core end
 end}
 -- @CANYON_OFFSET@
 -- @CANYON_ORIGIN@
 local grass, slate, violet = {}, {}, {}
 local function atOrigin(name, size, center, color, material, collision)
  return block(name, size, origin * center, color, material, collision)
 end
 do
  local block = atOrigin
  -- @CANYON_PARTS@
 end
 local lanes = {parts.AlwaysOpenSafeRoute.Position.Z, parts.ShortcutBridge.Position.Z,
                stars.Z, meteors.Z}
 for i, wanted in ipairs(expected) do
  assert(lanes[i] == wanted, mode .. " lane " .. i .. " " .. lanes[i] .. " vs " .. wanted)
 end
 assert(origin.Z == stars.Z and meteors.Z == stars.Z + 30)
 print("PASS " .. mode .. " CENTER_AND_FOUR_LANES")
 local function approachBlocked(castle, bank)
  return bank.CanCollide and math.abs(castle.X - bank.Position.X) <= bank.Size.X / 2
   and castle.Z - 60 < bank.Position.Z + bank.Size.Z / 2
   and castle.Z - 13 > bank.Position.Z - bank.Size.Z / 2
 end
 for i = 1, 16 do
  local castle = getCastlePoint(mode, i)
  assert(not approachBlocked(castle, parts.WestBank) and not approachBlocked(castle, parts.EastBank),
         mode .. " blocked castle " .. i)
 end
 print("PASS " .. mode .. " 16_CASTLE_FRONT_APPROACHES")
end

testMode("TEAM", {260, 275, 290, 320})
testMode("BATTLE_ROYALE", {130, 145, 160, 190})
