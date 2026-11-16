--!strict
-- P0D #470 independent game-quality observation ONLY.
-- Studio server Script; do not install in published/official RC without #220 review.
-- Reads live world/characters. Never grants a skill, damage, score, item, or castle HP.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local HttpService = game:GetService("HttpService")
local ROOT_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local MODES = {"TEAM", "BATTLE_ROYALE"}
local PERIOD_SECONDS = 5
local startClock = os.clock()
local output = Instance.new("StringValue")
output.Name = "EGGRUMBLE_StudioLiveObserver_JSON"
output.Value = "{}"
output.Parent = ServerStorage

local counters = {
 TEAM = {neutralDamageEvents = 0, neutralDeaths = 0, botDamageEvents = 0, botDeaths = 0, itemConsumeTransitions = 0},
 BATTLE_ROYALE = {neutralDamageEvents = 0, neutralDeaths = 0, botDamageEvents = 0, botDeaths = 0, itemConsumeTransitions = 0},
}
local observedHumanoids = setmetatable({}, {__mode = "k"})
local observedItems = setmetatable({}, {__mode = "k"})
local observedWorlds = setmetatable({}, {__mode = "k"})

local function modeOf(node: Instance): string?
 local cursor: Instance? = node
 while cursor do
  if cursor.Name == "TEAM_Arena" then return "TEAM" end
  if cursor.Name == "BATTLE_ROYALE_Arena" then return "BATTLE_ROYALE" end
  cursor = cursor.Parent
 end
 return nil
end

local function classification(model: Instance): string?
 if model.Name == "HordeSoldier" and model:GetAttribute("EGGRUMBLE_Neutral") == true then
  return "neutral"
 end
 if string.sub(model.Name, 1, 9) == "AI_Actor_" and model:GetAttribute("EGGRUMBLE_BotId") ~= nil then
  return "bot"
 end
 return nil
end

local function observeHumanoid(h: Humanoid)
 if observedHumanoids[h] then return end
 local parent = h.Parent
 if not parent or not parent:IsA("Model") then return end
 local kind = classification(parent)
 local mode = modeOf(parent)
 if not kind or not mode then return end
 observedHumanoids[h] = true
 local priorHealth = h.Health
 h.HealthChanged:Connect(function(now)
  -- Actual server Humanoid health decrease; not a confirmed attacking player.
  if now < priorHealth - 0.001 then
   local key = if kind == "neutral" then "neutralDamageEvents" else "botDamageEvents"
   counters[mode][key] += 1
  end
  priorHealth = now
 end)
 h.Died:Connect(function()
  local key = if kind == "neutral" then "neutralDeaths" else "botDeaths"
  counters[mode][key] += 1
 end)
end

local function observeItem(part: BasePart)
 if observedItems[part] then return end
 local folder = part.Parent
 if not folder or folder.Name ~= "EGGRUMBLE_FieldItems" or
  not string.match(part.Name, "^ITEM_%d+_") then return end
 local mode = modeOf(part)
 if not mode then return end
 observedItems[part] = true
 local available = part.CanQuery
 part:GetPropertyChangedSignal("CanQuery"):Connect(function()
  local nextValue = part.CanQuery
  -- True->false is the author's actual consumed transition, not mere prompt input.
  if available and not nextValue then counters[mode].itemConsumeTransitions += 1 end
  available = nextValue
 end)
end

local function watchDescendant(x: Instance)
 if x:IsA("Humanoid") then
  observeHumanoid(x)
 elseif x:IsA("BasePart") then
  observeItem(x)
 end
end

local function watchArena(arena: Instance)
 if observedWorlds[arena] then return end
 observedWorlds[arena] = true
 arena.DescendantAdded:Connect(watchDescendant)
 for _,x in ipairs(arena:GetDescendants()) do watchDescendant(x) end
end

local function rootFolder(): Instance?
 return workspace:FindFirstChild(ROOT_NAME)
end

local function attachExisting()
 local root = rootFolder()
 if not root then return end
 for _,mode in ipairs(MODES) do
  local arena = root:FindFirstChild(mode .. "_Arena")
  if arena then watchArena(arena) end
 end
end

local function emptyCounts()
 return {
  castles = 0, liveCastleModels = 0, routes = 0, neutralModels = 0,
  botModels = 0, liveNeutralHumanoids = 0, visibleItemParts = 0,
  availableFieldEggs = 0, releasedEggs = 0, stoneGiantModels = 0,
  physicalParts = 0, artParts = 0,
 }
end

local function scanMode(mode: string)
 local counts = emptyCounts()
 local root = rootFolder()
 local arena = root and root:FindFirstChild(mode .. "_Arena")
 if not arena then
  return {state = "NOT_STARTED", counts = counts, observedEvents = counters[mode]}
 end
 for _,x in ipairs(arena:GetDescendants()) do
  if x:IsA("BasePart") then
   counts.physicalParts += 1
   if string.sub(x.Name, 1, 4) == "ART_" then counts.artParts += 1 end
   if string.match(x.Name, "^TacticalRoute_%d+$") then counts.routes += 1 end
   if string.match(x.Name, "^FieldEgg_%d+$") then counts.availableFieldEggs += 1 end
   if string.match(x.Name, "^ReleasedEgg_") then counts.releasedEggs += 1 end
   if x.Parent and x.Parent.Name == "EGGRUMBLE_FieldItems" and
    string.match(x.Name, "^ITEM_%d+_") and x.CanQuery and x.Transparency < 1 then
    counts.visibleItemParts += 1
   end
  elseif x:IsA("Model") then
   if string.match(x.Name, "^Castle_") then
    counts.castles += 1
    if x.Parent ~= nil then counts.liveCastleModels += 1 end
   elseif x.Name == "HordeSoldier" and x:GetAttribute("EGGRUMBLE_Neutral") == true then
    counts.neutralModels += 1
    local h = x:FindFirstChildOfClass("Humanoid")
    if h and h.Health > 0 then counts.liveNeutralHumanoids += 1 end
   elseif string.sub(x.Name, 1, 9) == "AI_Actor_" then
    counts.botModels += 1
   elseif x.Name == "NEUTRAL_BOSS_STONE_GIANT" then
    counts.stoneGiantModels += 1
   end
  end
 end
 return {state = "WORLD_OBSERVED", counts = counts, observedEvents = counters[mode]}
end

local function scanPlayers()
 local out = {total = 0, selectedRoles = {}, equippedRoles = {}, queuedModes = {}, neutralKOCredits = 0}
 for _,player in ipairs(Players:GetPlayers()) do
  out.total += 1
  local selected = player:GetAttribute("EGGRUMBLE_SelectedRole")
  local equipped = player:GetAttribute("EGGRUMBLE_Role")
  local queued = player:GetAttribute("EGGRUMBLE_QueuedMode")
  if type(selected) == "string" then out.selectedRoles[selected] = (out.selectedRoles[selected] or 0) + 1 end
  if type(equipped) == "string" then out.equippedRoles[equipped] = (out.equippedRoles[equipped] or 0) + 1 end
  if type(queued) == "string" then out.queuedModes[queued] = (out.queuedModes[queued] or 0) + 1 end
  local kos = player:GetAttribute("EGGRUMBLE_NeutralKOs")
  if type(kos) == "number" and kos >= 0 and kos < 1000000 then out.neutralKOCredits += kos end
 end
 return out
end

local function snapshot()
 attachExisting()
 local data = {
  schema = "EGGRUMBLE_STUDIO_LIVE_OBSERVER_V1",
  engine = "ROBLOX_STUDIO_SERVER",
  elapsedSeconds = math.floor(os.clock() - startClock),
  modes = {TEAM = scanMode("TEAM"), BATTLE_ROYALE = scanMode("BATTLE_ROYALE")},
  players = scanPlayers(),
  -- These cannot be inferred authoritatively from the public Instance tree.
  unverified = {
   castleServerHP = "NOT_INSPECTED",
   eggDepositScore = "NOT_INSPECTED",
   itemActorAttribution = "NOT_INSPECTED",
   androidFpsThermal = "NOT_TESTED",
   ownerFunAndArt = "NOT_TESTED",
   officialRCIntegration = "NOT_CLAIMED",
  },
  decision = "OBSERVATION_ONLY_PRODUCT_NO_GO",
 }
 output.Value = HttpService:JSONEncode(data)
end

workspace.ChildAdded:Connect(function(child)
 if child.Name == ROOT_NAME then
  child.ChildAdded:Connect(function(arena)
   if arena.Name == "TEAM_Arena" or arena.Name == "BATTLE_ROYALE_Arena" then
    watchArena(arena)
   end
  end)
 end
end)
local existingRoot = rootFolder()
if existingRoot then
 existingRoot.ChildAdded:Connect(function(arena)
  if arena.Name == "TEAM_Arena" or arena.Name == "BATTLE_ROYALE_Arena" then watchArena(arena) end
 end)
end
snapshot()
task.spawn(function()
 while output.Parent ~= nil and RunService:IsStudio() do
  task.wait(PERIOD_SECONDS)
  snapshot()
 end
end)
