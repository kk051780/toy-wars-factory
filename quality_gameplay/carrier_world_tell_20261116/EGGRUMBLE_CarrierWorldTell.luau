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
 if record and record.gui and record.gui.Parent then
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
 if session.rules.phase ~= "ACTIVE" or session.rules.winner ~= nil then return false end
 session._carrierWorldTellStarted = true
 local records:{[string]:any} = {}
 task.spawn(function()
  while session.world.Parent ~= nil and session.rules.phase == "ACTIVE"
   and session.rules.winner == nil do
   for _,entry in ipairs(session.roster) do
    local id = tostring(entry.id)
    local castle = session.rules.castles[id]
    local actor = actorFor(session,entry)
    local root = actor and actor:FindFirstChild("HumanoidRootPart")
    local humanoid = actor and actor:FindFirstChildOfClass("Humanoid")
    local rootPart = if root and root:IsA("BasePart") then root else nil
    local alive = humanoid ~= nil and humanoid.Health > 0 and rootPart ~= nil
    local visible = Policy.shouldShow(session.rules.phase,session.rules.winner,castle,alive)
    local old = records[id]
    if not visible or not rootPart then
     if old then destroyRecord(old);records[id]=nil end
    else
     if old and old.root ~= rootPart then
      destroyRecord(old);old=nil;records[id]=nil
     end
     if not old then
      -- Actor may be a takeover bot even when the original roster was human.
      local botModel = session.botActors and session.botActors[entry.id]
      local gui,label = makeBillboard(rootPart,castle.team,botModel == actor)
      old = {root=rootPart,gui=gui,label=label,count=0}
      records[id] = old
     end
     if old.count ~= castle.heldEggs then
      old.label.Text = Policy.caption(castle.heldEggs)
      old.count = castle.heldEggs
     end
    end
   end
   task.wait(Policy.POLL_SECONDS)
  end
  -- Human avatars survive the arena; never leak a label into lobby/another mode.
  for _,record in pairs(records) do destroyRecord(record) end
  session._carrierWorldTellStarted = nil
 end)
 return true
end

return Tell
