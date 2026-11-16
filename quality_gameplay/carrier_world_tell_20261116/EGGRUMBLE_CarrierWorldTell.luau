--!strict
-- Optional V3 PRIVATE GAME enhancement: real, server-derived carried-egg tell.
-- Unique ownership: quality_gameplay/carrier_world_tell_20261116 only.
-- No changes to author-owned Game, UI, roles, bot/neutral AI, inventory, damage or score.
local Players = game:GetService("Players")
local Policy = require(script.Parent:WaitForChild("EGGRUMBLE_CarrierTellPolicy"))
local Tell = {}

local function actorFor(session:any, entry:any):Model?
 local bots = session.botActors
 local bot = bots and bots[entry.id]
 if bot and bot:IsA("Model") then return bot end
 if entry.isAI then return nil end
 local userId = tonumber(entry.id)
 local player = userId and Players:GetPlayerByUserId(userId)
 return player and player.Character or nil
end

local function destroyRecord(record:any)
 if record and record.gui then
  -- Destroy even if a different script already detached the Gui. This is
  -- a read-only cosmetic leaf: never leave a stale disconnected instance.
  record.gui:Destroy()
 end
end

local function makeBillboard(root:BasePart, team:string?, aiActor:boolean):(BillboardGui,TextLabel)
 local gui = Instance.new("BillboardGui")
 gui.Name = "EGGRUMBLE_CarrierWorldTell"
 gui.Adornee = root
 gui.AlwaysOnTop = false -- preserve solid cover; never a global wallhack.
 gui.MaxDistance = Policy.MAX_WORLD_VIEW_DISTANCE
 gui.Size = UDim2.fromOffset(88, 27)
 -- The author bot actor already owns a 180x50 BotObjective billboard at
 -- head (root + 2.25 studs) + 3.3 studs. Do not stack another count
 -- directly into that 5.55-stud band; humans keep the near-head marker.
 gui.StudsOffsetWorldSpace = Vector3.new(0, if aiActor then 10.2 else 4, 0)
 local text = Instance.new("TextLabel")
 text.Name = "Count"
 text.Size = UDim2.fromScale(1,1)
 text.BackgroundTransparency = 0.22
 text.BorderSizePixel = 0
 text.TextScaled = true
 text.Font = Enum.Font.GothamBold
 text.TextColor3 = Color3.fromRGB(255,250,203)
 text.BackgroundColor3 = if team=="RED" then Color3.fromRGB(112,44,47)
  elseif team=="BLUE" then Color3.fromRGB(38,66,119)
  else Color3.fromRGB(79,61,101)
 text.Parent = gui
 gui.Parent = root
 return gui,text
end

function Tell.start(session:any):boolean
 assert(session and session.world and session.rules and session.roster, "server match session required")
 if session._carrierWorldTellStarted then return false end
 -- Server-only optional RC rollback switch. false means do not start; nil keeps
 -- existing preview behavior. Never derive this state from a client Remote.
 if session.carrierWorldTellEnabled == false then return false end
 if session.rules.phase ~= "ACTIVE" or session.rules.winner ~= nil then return false end
 -- Author-owned V3 field part is the one physical arena identity. If missing,
 -- fail closed: never emit a guessed badge in the lobby or another mode.
 local field = session.world:FindFirstChild("TacticalBattlefield")
 if not field or not field:IsA("BasePart")
  or field.Parent ~= session.world then return false end
 session._carrierWorldTellStarted = true
 local records:{[string]:any} = {}
 local faulted:{[string]:boolean} = {}
 task.spawn(function()
  -- This is optional visual QA. A malformed/replaced actor Model must not
  -- leave the session stuck "started" or leak labels into future rounds.
  -- Catch faults INSIDE our own spawned observer, then always clean up.
  local ok, observerError = pcall(function()
   while session.world.Parent ~= nil and field.Parent == session.world
   and session.rules.phase == "ACTIVE" and session.rules.winner == nil
   and session.carrierWorldTellEnabled ~= false do
   for _,entry in ipairs(session.roster) do
    local id = tostring(entry.id)
    -- One malformed avatar must not blank the other 15 player markers.
    -- Isolate its cosmetic inspection, not the original game/Rules code.
    local seatOk,seatError = pcall(function()
    local castle = session.rules.castles[id]
    local actor = actorFor(session,entry)
    local root = actor and actor:FindFirstChild("HumanoidRootPart")
    local humanoid = actor and actor:FindFirstChildOfClass("Humanoid")
    local rootPart = if root and root:IsA("BasePart") then root else nil
    local alive = humanoid ~= nil and humanoid.Health > 0 and rootPart ~= nil
    local withinThisArena = rootPart ~= nil and Policy.inArenaXZ(
     rootPart.Position.X, rootPart.Position.Z,
     field.Position.X, field.Position.Z, field.Size.X, field.Size.Z)
    local visible = Policy.shouldShow(
     session.rules.phase,session.rules.winner,castle,alive and withinThisArena)
    local old = records[id]
    if not visible or not rootPart then
     if old then destroyRecord(old);records[id]=nil end
    else
     if old and (old.root ~= rootPart
      or old.gui.Parent ~= rootPart or old.gui.Adornee ~= rootPart
      or old.label.Parent ~= old.gui) then
      -- External appearance cleanup can remove/reparent only this billboard
      -- while the avatar and heldEggs remain unchanged. Recreate it once;
      -- never reset item amounts, match time or other game state.
      destroyRecord(old);old=nil;records[id]=nil
     end
     if not old then
      -- Actor may be a takeover bot even when the original roster was human.
      local botModel = session.botActors and session.botActors[entry.id]
      local gui,label = makeBillboard(rootPart,castle.team,botModel == actor)
      old = {root=rootPart,gui=gui,label=label,count=0}
      records[id] = old
     end
     -- Restore only cosmetic invariants if another server-side visual
     -- system modified them. A count cache alone would leave a misleading
     -- label after text edits; AlwaysOnTop/MaxDistance drift can reveal an
     -- objective through walls or from across the map.
     if old.gui.AlwaysOnTop ~= false then old.gui.AlwaysOnTop = false end
     if old.gui.MaxDistance ~= Policy.MAX_WORLD_VIEW_DISTANCE then
      old.gui.MaxDistance = Policy.MAX_WORLD_VIEW_DISTANCE
     end
     if old.gui.Enabled == false then old.gui.Enabled = true end
     if old.label.Visible == false then old.label.Visible = true end
     local caption = Policy.caption(castle.heldEggs)
     if old.count ~= castle.heldEggs or old.label.Text ~= caption then
      old.label.Text = caption
      old.count = castle.heldEggs
     end
    end
    end)
    if seatOk then
     faulted[id] = nil
    else
     local damaged = records[id]
     if damaged then
      -- Never let a broken cosmetic Instance abort other seats' inspection.
      pcall(destroyRecord,damaged)
      records[id] = nil
     end
     if not faulted[id] then
      faulted[id] = true
      warn("[GQ511] optional carrier actor label isolated: "..tostring(seatError))
     end
    end
   end
   task.wait(Policy.POLL_SECONDS)
   end
  end)
  -- The battlefield can be removed BEFORE the parent arena is removed.
  -- A detached or reparented floor also ends the visual loop and scrubs all
  -- character-root labels, without changing the actual match/egg economy.
  -- Human avatars survive the arena; never leak a label into lobby/another mode.
  for _,record in pairs(records) do destroyRecord(record) end
  session._carrierWorldTellStarted = nil
  if not ok then
   -- Distinct from original engine errors; never change game Rules or attempt
   -- a silent restart of an optional UI when its dependencies are unhealthy.
   warn("[GQ511] optional carrier label observer stopped safely: "..tostring(observerError))
  end
 end)
 return true
end

return Tell
