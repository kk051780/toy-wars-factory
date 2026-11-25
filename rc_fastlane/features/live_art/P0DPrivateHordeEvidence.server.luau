--!strict
-- P0 #444: read-only PRIVATE Horde runtime evidence (never gameplay authority).
-- This script is OFF by default, never publishes, never uses remote/network/UI.
-- The only Game and MusouHorde remain unmodified in their original 81 sources.
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
if not RunService:IsServer() then return end
-- Even an accidentally set flag cannot run this probe on a PUBLIC server.
if not RunService:IsStudio() and game.PrivateServerId == "" then return end
-- Both owner-set booleans must already exist on the SERVER before this starts.
if workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") ~= true then return end
if workspace:GetAttribute("P0D_PRIVATE_HORDE_EVIDENCE") ~= true then return end

local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then
    warn("P0D_HORDE_EVIDENCE_NO_MAP")
    return
end

local SAMPLE_SECONDS = 0.5
local MAX_SAMPLES = 360 -- exactly three minutes, with upper bound
local MAX_MOBS = 9
local expected = {}
for index = 1, 8 do
    expected["MUSOU_MINION_" .. tostring(index)] = true
end
expected["MUSOU_ELITE_TELEGRAPH"] = true

local started = os.clock()
local peak = 0
local spawnComplete = false
local spawnSeconds: number? = nil
local popupEdges = 0
local knockouts = 0
local motionEvents = 0
local firstHitSeconds: number? = nil
local lastVisible = {} :: {[Instance]: boolean}
local priorPosition = {} :: {[Instance]: Vector3}
local ended = "SAMPLE_LIMIT"
local invalidNameObserved = false

local function report(state: string, sample: number, active: number)
    -- JSON is output to private server Output only; no player PII.
    local data = {
        schema = "P0D_HORDE_REAL_ENGINE_PROBE_V1",
        state = state,
        sample = sample,
        elapsedSeconds = math.floor((os.clock() - started) * 10) / 10,
        currentModels = active,
        peakModels = peak,
        allNineSeenAtOnce = spawnComplete,
        firstNineSeconds = spawnSeconds,
        serverDamagePopupEdges = popupEdges,
        firstPopupSeconds = firstHitSeconds,
        knockoutPopupEdges = knockouts,
        modelMovementSamples = motionEvents,
        unexpectedMobNames = invalidNameObserved,
        sourceGameV2DoesNotGetModified = true,
        studioMode = RunService:IsStudio(),
        privateFlagRequired = true,
        publicServerExplicitlyRejected = true,
        liveCombatQualityApproved = false,
        ownerAccepted = false,
    }
    print("P0D_HORDE_PRIVATE_EVIDENCE " .. HttpService:JSONEncode(data))
end

report("START", 0, 0)
for sample = 1, MAX_SAMPLES do
    if script.Parent == nil then
        ended = "SCRIPT_REMOVED"
        break
    end
    if workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") ~= true
        or workspace:GetAttribute("P0D_PRIVATE_HORDE_EVIDENCE") ~= true then
        ended = "OWNER_OPTIN_REVOKED"
        break
    end
    local folder = arena:FindFirstChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT")
    local observed: {[string]: boolean} = {}
    local active = 0
    if folder and folder:IsA("Folder") then
        for _, child in ipairs(folder:GetChildren()) do
            if child:IsA("Model") then
                if not expected[child.Name] or observed[child.Name] then
                    invalidNameObserved = true
                else
                    observed[child.Name] = true
                    active += 1
                    local core = child:FindFirstChild("Core")
                    if core and core:IsA("BasePart") then
                        local old = priorPosition[child]
                        if old and (core.Position - old).Magnitude > 0.4 then
                            motionEvents += 1
                        end
                        priorPosition[child] = core.Position
                        local popup = core:FindFirstChild("RealDamagePopup")
                        if popup and popup:IsA("BillboardGui") then
                            local text = popup:FindFirstChildWhichIsA("TextLabel")
                            local valid = popup.Enabled and text ~= nil
                                and string.len(text.Text) > 0
                            if valid and not lastVisible[child] then
                                popupEdges += 1
                                if firstHitSeconds == nil then
                                    firstHitSeconds = math.floor((os.clock() - started) * 10) / 10
                                end
                                if string.find(text.Text, "撃破", 1, true) then
                                    knockouts += 1
                                end
                            end
                            lastVisible[child] = valid
                        end
                    end
                end
            end
        end
    end
    peak = math.max(peak, active)
    if active == MAX_MOBS and not spawnComplete then
        spawnComplete = true
        spawnSeconds = math.floor((os.clock() - started) * 10) / 10
        report("NINE_OBSERVED", sample, active)
    end
    if sample % 60 == 0 then
        report("CHECKPOINT", sample, active)
    end
    task.wait(SAMPLE_SECONDS)
end
report(ended, MAX_SAMPLES, peak)
-- A runtime log is only a witness to observable objects. Source/runtime
-- evidence is NEVER a substitute for OWNER PC/Android visual+fun sign-off.
