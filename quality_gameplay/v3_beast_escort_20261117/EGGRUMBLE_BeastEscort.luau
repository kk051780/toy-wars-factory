--!strict
-- P0D-GQ-BEAST-ESCORT: a real, temporary, server-owned BEAST companion.
-- Source candidate for inlining into the EXISTING SevenRoleCombat; not a 32nd live Script.
-- All damage is delegated to the existing Combat neutralAndBotHit callback.
local BeastEscort = {}
local active: {[number]: any} = {}
local LIFETIME = 12
local LEASH = 28
local SEEK_RADIUS = 26
local MAX_NEUTRAL_SCAN = 56
local ATTACK_COOLDOWN = 1.4

local function eligible(session:any, ownerState:any, id:string):boolean
 local state = session.rules and session.rules.castles and session.rules.castles[id]
 return state ~= nil and state.alive == true
  and (session.mode ~= "TEAM" or state.team ~= ownerState.team)
end

local function validCaster(session:any, player:Player, character:Model,
 humanoid:Humanoid, ownerState:any):boolean
 return player.Parent ~= nil and player.Character == character
  and humanoid.Parent ~= nil and humanoid.Health > 0
  and character.Parent ~= nil and ownerState.alive == true
  and session.rules.phase == "ACTIVE"
  and session.world ~= nil and session.world.Parent ~= nil
  and player:GetAttribute("EGGRUMBLE_Role") == "BEAST"
  and player:GetAttribute("EGGRUMBLE_Eliminated") ~= true
  and (session.isCurrentHuman == nil or session.isCurrentHuman(player) == true)
end

local function makePet(session:any, player:Player, casterRoot:BasePart): (Model, BasePart, Humanoid)
 local pet = Instance.new("Model")
 pet.Name = "EGGRUMBLE_BeastEscort_" .. tostring(player.UserId)
 local root = Instance.new("Part")
 root.Name = "HumanoidRootPart"
 root.Size = Vector3.new(2.8, 3, 4)
 root.Transparency = 1
 root.CanCollide = true
 root.CanTouch = false
 root.CFrame = casterRoot.CFrame * CFrame.new(0, 0, 6)
 root.Parent = pet
 local body = Instance.new("Part")
 body.Name = "Armor"
 body.Size = Vector3.new(4.4, 3.2, 6.2)
 body.Material = Enum.Material.SmoothPlastic
 body.Color = Color3.fromRGB(115, 85, 54)
 body.CanCollide = false
 body.CanTouch = false
 body.Massless = true
 body.CFrame = root.CFrame
 body.Parent = pet
 local bodyWeld = Instance.new("WeldConstraint")
 bodyWeld.Part0 = root
 bodyWeld.Part1 = body
 bodyWeld.Parent = body
 local head = Instance.new("Part")
 head.Name = "Head"
 head.Shape = Enum.PartType.Ball
 head.Size = Vector3.new(3.4, 2.8, 3)
 head.Material = Enum.Material.SmoothPlastic
 head.Color = Color3.fromRGB(206, 164, 103)
 head.CanCollide = false
 head.CanTouch = false
 head.Massless = true
 head.CFrame = root.CFrame * CFrame.new(0, 1.1, -2)
 head.Parent = pet
 local headWeld = Instance.new("WeldConstraint")
 headWeld.Part0 = root
 headWeld.Part1 = head
 headWeld.Parent = head
 local hum = Instance.new("Humanoid")
 hum.MaxHealth = 60
 hum.Health = 60
 hum.WalkSpeed = 17
 hum.JumpPower = 0
 hum.Parent = pet
 pet.PrimaryPart = root
 pet:SetAttribute("EGGRUMBLE_OwnerId", player.UserId)
 pet:SetAttribute("EGGRUMBLE_BeastCompanion", true)
 pet.Parent = session.world
 pcall(function() root:SetNetworkOwner(nil) end)
 return pet, root, hum
end

local function pickTarget(session:any, player:Player, casterState:any,
 petRoot:BasePart): (Model?, BasePart?)
 local bestModel: Model? = nil
 local bestRoot: BasePart? = nil
 local bestD = SEEK_RADIUS
 local function consider(model:Model?)
  if model == nil or model.Parent == nil then return end
  local r = model.PrimaryPart
  local h = model:FindFirstChildOfClass("Humanoid")
  if r == nil or h == nil or h.Health <= 0 then return end
  local d = (r.Position - petRoot.Position).Magnitude
  if d < bestD then bestD = d; bestModel = model; bestRoot = r end
 end
 local horde = session.world:FindFirstChild("NeutralHorde")
 if horde then
  local scanned = 0
  for _, v in ipairs(horde:GetChildren()) do
   if v:IsA("Model") then
    scanned += 1
    if scanned > MAX_NEUTRAL_SCAN then break end
    consider(v)
   end
  end
 end
 for id, model in pairs(session.botActors or {}) do
  if eligible(session, casterState, id) then consider(model) end
 end
 for _, other in ipairs(game:GetService("Players"):GetPlayers()) do
  if other ~= player and eligible(session, casterState, tostring(other.UserId))
   and (session.isCurrentHuman == nil or session.isCurrentHuman(other) == true) then
   consider(other.Character)
  end
 end
 return bestModel, bestRoot
end

function BeastEscort.stop(player:Player)
 local state = active[player.UserId]
 if state == nil then return end
 active[player.UserId] = nil
 state.dead = true
 if state.model and state.model.Parent then state.model:Destroy() end
end

function BeastEscort.begin(session:any, player:Player, character:Model,
 casterRoot:BasePart, casterHumanoid:Humanoid, ownerState:any, hit:any):boolean
 if type(hit) ~= "function" or not validCaster(session, player, character, casterHumanoid, ownerState) then
  return false
 end
 BeastEscort.stop(player)
 local pet, root, hum = makePet(session, player, casterRoot)
 local state = {model = pet, dead = false, session = session}
 active[player.UserId] = state
 task.spawn(function()
  local start = os.clock()
  local lastHit = start - ATTACK_COOLDOWN
  while not state.dead and active[player.UserId] == state and os.clock() - start < LIFETIME do
   if not validCaster(session, player, character, casterHumanoid, ownerState)
    or hum.Health <= 0 or root.Parent == nil then break end
   if (root.Position - casterRoot.Position).Magnitude > LEASH then
    hum:MoveTo(casterRoot.Position + casterRoot.CFrame.RightVector * 4)
   else
    local target, targetRoot = pickTarget(session, player, ownerState, root)
    if target and targetRoot
     and (targetRoot.Position - root.Position).Magnitude <= SEEK_RADIUS
     and lineClear(root.Position + Vector3.new(0, 1.5, 0),
      targetRoot.Position + Vector3.new(0, 1, 0), pet, target) then
     local range = (targetRoot.Position - root.Position).Magnitude
     if range > 4 then
      hum:MoveTo(targetRoot.Position)
     elseif os.clock() - lastHit >= ATTACK_COOLDOWN then
      lastHit = os.clock()
      -- The same Combat authority rechecks real targets, team, world and LOS.
      -- No secondary damage/Remote/KO authority: only the original Combat callback.
      hit(root, pet, targetRoot.Position)
     end
    else
     hum:MoveTo(casterRoot.Position + casterRoot.CFrame.RightVector * 4)
    end
   end
   task.wait(0.35)
  end
  if active[player.UserId] == state then BeastEscort.stop(player) end
 end)
 return true
end

return BeastEscort
