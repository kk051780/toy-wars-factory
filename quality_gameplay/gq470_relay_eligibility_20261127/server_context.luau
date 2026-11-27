local now = 0
local os = { clock = function() return now end }
local Rules = { RELAY_COOLDOWN_SECONDS = 12 }
local mode = "TEAM"
local view = {}
local values = {}
local relayPrompt = {
    GetAttribute = function(_, name) return values[name] end,
    SetAttribute = function(_, name, value) values[name] = value end,
}
local carrierPlayer = {
    UserId = 42,
    GetAttribute = function(_, key)
        assert(key == "EGGRUMBLE_Eliminated")
        return view.eliminated
    end,
}
local character = { FindFirstChildOfClass = function(_, class)
    assert(class == "Humanoid")
    return view.humanoid and { Health = view.humanoid }
end }
local session = { rules = { castles = {}, eggRelayLastAt = {} } }
local joined = {}
