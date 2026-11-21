--!strict
-- GQ470_FB015_BOTACTORS_SUBJECT_STUDIO_PROBE_20261121
-- Paste into the SERVER command bar during a private REAL69 Studio Play with TEAM/BR bots alive.
-- Read-only: never changes camera, world, NPC, UI, network, Store, or match state.
-- This verifies live property values; it does NOT measure visual aesthetics, phone FPS,
-- screenshot parity, gameplay win, or OWNER acceptance. Keep ART_NO_GO until full #420.
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local HttpService = game:GetService("HttpService")

assert(RunService:IsStudio(), "RED_NOT_STUDIO_PRIVATE_PLAY")
local inspected = 0
local failed = {}
local teamCounts = { RED = 0, BLUE = 0, AI = 0 }
local function requireField(ok: boolean, reason: string)
    if not ok then
        table.insert(failed, reason)
    end
end

for _, candidate in ipairs(Workspace:GetDescendants()) do
    if candidate:IsA("BillboardGui") and candidate.Name == "BotObjective" then
        inspected += 1
        local head = candidate.Parent
        local model = if head then head.Parent else nil
        local humanoid = if model then model:FindFirstChildOfClass("Humanoid") else nil
        requireField(head ~= nil and head:IsA("BasePart"), "BOT_LABEL_NOT_ON_PART")
        requireField(humanoid ~= nil, "BOT_LABEL_MISSING_HUMANOID")
        requireField(candidate.Size.X.Offset == 104 and candidate.Size.Y.Offset == 24,
            "BOT_LABEL_OVERSIZED")
        requireField(candidate.MaxDistance == 22, "BOT_LABEL_UNBOUNDED_DISTANCE")
        requireField(not candidate.AlwaysOnTop, "BOT_LABEL_ALWAYS_ON_TOP")
        if humanoid then
            requireField(humanoid.DisplayDistanceType == Enum.HumanoidDisplayDistanceType.Subject,
                "BOT_NAME_VIEWER_LEAK")
            requireField(humanoid.NameDisplayDistance == 0,
                "BOT_NATIVE_NAME_NOT_HIDDEN")
            requireField(humanoid.HealthDisplayDistance == 18,
                "BOT_HEALTH_DISTANCE_MISMATCH")
            requireField(humanoid.HealthDisplayType == Enum.HumanoidHealthDisplayType.DisplayWhenDamaged,
                "BOT_HEALTH_ALWAYS_ON")
        end
        local text = candidate:FindFirstChildWhichIsA("TextLabel", true)
        requireField(text ~= nil, "BOT_TACTIC_LABEL_MISSING")
        if text then
            requireField(text.BackgroundTransparency == 1,
                "BOT_TACTIC_BACKGROUND_OPAQUE")
            requireField(text.TextStrokeTransparency < 1,
                "BOT_TACTIC_TEXT_NO_EDGE_CONTRAST")
            requireField(text.Text:match("AI_%d+") == nil,
                "BOT_INTERNAL_AI_ID_VISIBLE")
            if text.Text:find("赤軍", 1, true) then
                teamCounts.RED += 1
            elseif text.Text:find("青軍", 1, true) then
                teamCounts.BLUE += 1
            else
                teamCounts.AI += 1
            end
        end
    end
end

-- Empty scene is NOT a pass; press Play, select TEAM/BR, start a live bot encounter first.
requireField(inspected > 0, "NOT_TESTED_NO_BOT_OBJECTIVE_IN_STUDIO_PLAY")
local result = {
    proof = "GQ470_FB015_BOTACTORS_SUBJECT_STUDIO_READ_ONLY_V1",
    status = if #failed == 0 then "PASS_PROPERTY_ONLY" else "RED",
    bot_labels = inspected,
    red = teamCounts.RED,
    blue = teamCounts.BLUE,
    ai = teamCounts.AI,
    failure_count = #failed,
    failure_reasons = failed,
    camera_visual_proven = false,
    pc_android_32_images = 0,
    android_15min_fps_proven = false,
    owner_accepted = false,
    formal_adoption_claim = false,
}
print(HttpService:JSONEncode(result))
assert(#failed == 0, "RED_BOT_LABEL_PROPERTIES_" .. table.concat(failed, ","))
