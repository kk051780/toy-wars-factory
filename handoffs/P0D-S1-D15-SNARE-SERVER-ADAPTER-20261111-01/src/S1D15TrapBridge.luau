--!strict
-- TRAP RAIDERS S1 <> original D15 TrapRescueCore integration boundary.
-- THIS IS AN OPT-IN ModuleScript. Existing Game.server.luau remains sole round,
-- RemoteEvent, roles, movement and HP/damage authority. No second scheduler.
-- Original D15 Core must be supplied through exact recovered Public Source V1.
local Players = game:GetService("Players")

local Bridge = {}
Bridge.__index = Bridge

local CAST = "TRAP_CAST"
local RESCUE = "TRAP_RESCUE"
local ESCAPE = "TRAP_ESCAPE"
local MAX_VERTICAL_DELTA = 9
local MIN_FORWARD_DOT = 0.15
local EPHEMERAL_BASE = 900000000000000 -- within original Core validId <= 10^15
local EPHEMERAL_LIMIT = 900000001000000

local function getBody(p: Player): (BasePart?, Humanoid?)
    local model = p.Character
    if not model then return nil, nil end
    local root = model:FindFirstChild("HumanoidRootPart")
    local hum = model:FindFirstChildOfClass("Humanoid")
    if not root or not root:IsA("BasePart") or not hum or hum.Health <= 0 then
        return nil, nil
    end
    return root, hum
end

local function safeTeam(value: any): string?
    if value == "RED" or value == "BLUE" then return value end
    return nil
end

local function visible(source: Player, target: Player, a: Vector3, b: Vector3): boolean
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    local char = source.Character
    if not char then return false end
    params.FilterDescendantsInstances = {char}
    local delta = b - a
    if delta.Magnitude < 0.01 then return true end
    local result = workspace:Raycast(a + Vector3.new(0, 1, 0), delta, params)
    return result == nil or (target.Character ~= nil and result.Instance:IsDescendantOf(target.Character))
end

function Bridge.new(originalCore: any, callbacks: any)
    assert(type(originalCore) == "table" and type(originalCore.new) == "function"
        and type(originalCore.syncPlayer) == "function"
        and type(originalCore.advance) == "function"
        and type(originalCore.tryCast) == "function"
        and type(originalCore.tryRescue) == "function"
        and type(originalCore.tryEscape) == "function" and type(originalCore.endMatch) == "function",
        "S1_D15_ORIGINAL_CORE_API_REQUIRED")
    assert(type(callbacks) == "table" and type(callbacks.getTeam) == "function"
        and type(callbacks.getRole) == "function"
        and type(callbacks.getPhase) == "function"
        and type(callbacks.serverNow) == "function"
        and type(callbacks.applyPoisonDamage) == "function"
        and type(callbacks.onStatus) == "function",
        "S1_CANONICAL_GAME_CALLBACKS_REQUIRED")
    return setmetatable({
        core = originalCore,
        hooks = callbacks,
        state = nil,
        matchSerial = nil,
        startedAt = 0,
        ephemeralNext = EPHEMERAL_BASE,
        ephemeralIds = {} :: {[Player]: number},
        playersById = {} :: {[number]: Player},
        receipts = {} :: {[string]: boolean},
        -- A new successful cast must have a fresh damage receipt generation,
        -- even when its caster and victim are unchanged in the same round.
        castSequence = 0,
        castGenerationByTarget = {} :: {[number]: number},
    }, Bridge)
end

function Bridge:_id(player: Player): number
    local existing = self.ephemeralIds[player]
    if existing then return existing end
    local raw = player.UserId
    if type(raw) == "number" and raw % 1 == 0 and raw >= 1 and raw < EPHEMERAL_BASE then
        self.ephemeralIds[player] = raw
        self.playersById[raw] = player
        return raw
    end
    -- Studio local test Players often have negative UserIds; original D15
    -- forbids them. Allocate a private server-only positive mapping instead.
    assert(self.ephemeralNext <= EPHEMERAL_LIMIT, "S1_D15_TEST_ID_POOL_EXHAUSTED")
    local newId = self.ephemeralNext
    self.ephemeralNext += 1
    self.ephemeralIds[player] = newId
    self.playersById[newId] = player
    return newId
end

function Bridge:beginRound(serial: number, now: number): (boolean, string)
    if type(serial) ~= "number" or serial % 1 ~= 0 or serial < 1
        or type(now) ~= "number" or now ~= now or now == math.huge or now == -math.huge then
        return false, "BAD_CANONICAL_ROUND"
    end
    if self.state ~= nil then return false, "ROUND_ALREADY_ACTIVE" end
    self.matchSerial = serial
    self.startedAt = now
    self.receipts = {}
    self.castSequence = 0
    self.castGenerationByTarget = {}
    self.state = self.core.new("S1_" .. tostring(serial))
    return true, "TRAP_ROUND_STARTED"
end

function Bridge:_syncPlayers()
    local state = self.state
    if not state then return end
    for _, player in ipairs(Players:GetPlayers()) do
        local id = self:_id(player)
        local team = safeTeam(self.hooks.getTeam(player))
        local role = self.hooks.getRole(player)
        local root = getBody(player)
        if not team or type(role) ~= "string" then
            self.core.removePlayer(state, id)
        else
            local alive = root ~= nil
            local p = if root then root.Position else Vector3.zero
            self.core.syncPlayer(state, id, team, role, alive, p.X, p.Z)
        end
    end
end

function Bridge:_clock(): number?
    local server = self.hooks.serverNow()
    if type(server) ~= "number" or server ~= server or server == math.huge or server == -math.huge then
        return nil
    end
    local elapsed = server - self.startedAt
    if elapsed < 0 or elapsed > self.core.CONFIG.MAX_DURATION_SECONDS then return nil end
    return elapsed
end

function Bridge:update(): (boolean, string)
    if not self.state or self.hooks.getPhase() ~= "ACTIVE" then return false, "ROUND_NOT_ACTIVE" end
    local elapsed = self:_clock()
    if elapsed == nil then return false, "BAD_CANONICAL_CLOCK" end
    self:_syncPlayers() -- always reconcile deaths/teams BEFORE scheduled DOT
    local advanced, reason, events = self.core.advance(self.state, elapsed)
    if not advanced then return false, reason end
    for _, event in ipairs(events) do
        if event.kind == "POISON_DAMAGE" and event.matchId == self.state.matchId
            and type(event.tick) == "number" and event.tick >= 1
            and event.tick <= self.core.CONFIG.DOT_TICKS
            and event.damage == self.core.CONFIG.DOT_PER_TICK then
            local source = self.playersById[event.casterId]
            local target = self.playersById[event.targetId]
            local castGeneration = self.castGenerationByTarget[event.targetId]
            -- Original D15 emits (caster, target, tick), but NO unique cast ID.
            -- Preserve per-successful-cast generation to avoid treating a
            -- second legitimate trap as replay of the first one.
            local key = self.state.matchId .. ":" .. tostring(event.casterId)
                .. ":" .. tostring(event.targetId) .. ":" .. tostring(castGeneration)
                .. ":" .. tostring(event.tick)
            local sourceTeam = if source then safeTeam(self.hooks.getTeam(source)) else nil
            local targetTeam = if target then safeTeam(self.hooks.getTeam(target)) else nil
            if castGeneration ~= nil and not self.receipts[key]
                and source and target and source.Parent == Players
                and target.Parent == Players and getBody(source) ~= nil and getBody(target) ~= nil
                and sourceTeam ~= nil and targetTeam ~= nil and sourceTeam ~= targetTeam then
                -- Single existing Game.server damage callback retains sole
                -- ownership of canonical HP. Callback MUST recheck authority.
                self.receipts[key] = true -- mark before callback to prevent re-entry
                self.hooks.applyPoisonDamage(target, source, event.damage, key)
            end
        end
    end
    for _, player in ipairs(Players:GetPlayers()) do
        local id = self.ephemeralIds[player]
        if id then self.hooks.onStatus(player, self.core.status(self.state, id)) end
    end
    return true, "TRAP_UPDATED"
end

function Bridge:_closest(player: Player, range: number, rescue: boolean): Player?
    local root = getBody(player)
    if not root then return nil end
    local team = safeTeam(self.hooks.getTeam(player))
    if not team then return nil end
    local best: Player? = nil
    local bestDist = range + 0.001
    local bestId = math.huge
    for _, other in ipairs(Players:GetPlayers()) do
        if other ~= player then
            local targetTeam = safeTeam(self.hooks.getTeam(other))
            if targetTeam and ((rescue and targetTeam == team) or (not rescue and targetTeam ~= team)) then
                local otherRoot = getBody(other)
                if otherRoot then
                    local status = self.core.status(self.state, self:_id(other))
                    local eligible = if rescue then status.trapped
                        else not status.trapped and status.immunityRemaining <= 0
                    local d = otherRoot.Position - root.Position
                    local len = d.Magnitude
                    local dot = if len > 0.01 then root.CFrame.LookVector:Dot(d.Unit) else 1
                    if eligible and len >= 0.01 and len <= range and math.abs(d.Y) <= MAX_VERTICAL_DELTA
                        and (rescue or dot >= MIN_FORWARD_DOT)
                        and visible(player, other, root.Position, otherRoot.Position)
                        and (len < bestDist - 0.001
                            or (math.abs(len - bestDist) < 0.001 and self:_id(other) < bestId)) then
                        best, bestDist, bestId = other, len, self:_id(other)
                    end
                end
            end
        end
    end
    return best
end

function Bridge:handleIntent(player: Player, action: any, sequenceAuthorized: boolean): (boolean, string)
    -- Game.server.luau, and ONLY it, must authenticate OnServerEvent player
    -- and consume Rules.validSeq before invoking this function.
    if sequenceAuthorized ~= true then return false, "UNVERIFIED_SEQUENCE" end
    if typeof(player) ~= "Instance" or not player:IsA("Player") or player.Parent ~= Players then
        return false, "UNTRUSTED_PLAYER"
    end
    if not self.state or self.hooks.getPhase() ~= "ACTIVE" then return false, "ROUND_NOT_ACTIVE" end
    if action ~= CAST and action ~= RESCUE and action ~= ESCAPE then return false, "UNKNOWN_TRAP_ACTION" end
    if not safeTeam(self.hooks.getTeam(player)) or not getBody(player) then
        return false, "NO_ACTIVE_ACTOR"
    end
    local updated, why = self:update()
    if not updated then return false, why end
    local id = self:_id(player)
    if action == ESCAPE then
        local accepted, reason = self.core.tryEscape(self.state, id)
        if accepted then self.hooks.onStatus(player, self.core.status(self.state, id)) end
        return accepted, reason
    elseif action == CAST then
        -- Original D15 needs job TRAPPER; existing S1 initially has only
        -- RAIDER/GUARDIAN. The integrator must explicitly add TRAPPER role.
        if self.hooks.getRole(player) ~= "TRAPPER" then return false, "WRONG_JOB" end
        local target = self:_closest(player, self.core.CONFIG.CAST_RANGE, false)
        if not target then return false, "NO_SERVER_SELECTED_TARGET" end
        local targetId = self:_id(target)
        local accepted, reason = self.core.tryCast(self.state, id, targetId)
        if accepted then
            self.castSequence += 1 -- only accepted casts consume a generation
            self.castGenerationByTarget[targetId] = self.castSequence
            self.hooks.onStatus(target, self.core.status(self.state, targetId))
        end
        return accepted, reason
    else
        local target = self:_closest(player, self.core.CONFIG.RESCUE_RANGE, true)
        if not target then return false, "NO_SERVER_SELECTED_TARGET" end
        local accepted, reason = self.core.tryRescue(self.state, id, self:_id(target))
        if accepted then self.hooks.onStatus(target, self.core.status(self.state, self:_id(target))) end
        return accepted, reason
    end
end

function Bridge:removePlayer(player: Player)
    local id = self.ephemeralIds[player]
    if id and self.state then self.core.removePlayer(self.state, id) end
    if id then
        self.playersById[id] = nil
        self.castGenerationByTarget[id] = nil
    end
    self.ephemeralIds[player] = nil
end

function Bridge:endRound()
    if self.state then self.core.endMatch(self.state) end
    self.state = nil
    self.matchSerial = nil
    self.receipts = {}
    self.castSequence = 0
    self.castGenerationByTarget = {}
    for _, p in ipairs(Players:GetPlayers()) do
        self.hooks.onStatus(p, {trapped = false, rooted = false,
            poison = false, immunityRemaining = 0})
    end
end

return Bridge
