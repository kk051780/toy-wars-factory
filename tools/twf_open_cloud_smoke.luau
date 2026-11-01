-- TOY WARS FACTORY — private Open Cloud engine-only structural smoke.
-- Must be independently reviewed and run only against a pinned NONPUBLIC test-place version.
-- No SavePlaceAsync, DataStore writes, HTTP, user interactions, public publish, or Play-client proof.
local RS = game:GetService("ReplicatedStorage")
local SSS = game:GetService("ServerScriptService")
local SP = game:GetService("StarterPlayer")

local module = RS:FindFirstChild("ToyWarsBalance")
assert(module ~= nil and module:IsA("ModuleScript"), "TWF: missing balance module")
local remote = RS:FindFirstChild("ToyWarsSelectUnit")
assert(remote ~= nil and remote:IsA("RemoteEvent"), "TWF: missing selector remote")
local server = SSS:FindFirstChild("ToyWarsServer")
assert(server ~= nil and server:IsA("Script"), "TWF: missing game server script")
local smoke = SSS:FindFirstChild("ToyWarsSmokeTest")
assert(smoke ~= nil and smoke:IsA("Script"), "TWF: missing smoke script")
local scripts = SP:FindFirstChild("StarterPlayerScripts")
assert(scripts ~= nil and scripts:IsA("StarterPlayerScripts"), "TWF: missing starter scripts")
local hud = scripts:FindFirstChild("ToyWarsHUD")
assert(hud ~= nil and hud:IsA("LocalScript"), "TWF: missing HUD script")

-- Balance module is designed as a pure library; pcall yields a real-engine evaluation.
local ok, balance = pcall(require, module)
assert(ok and type(balance) == "table", "TWF: balance cannot be required")
assert(balance.waveSize(1) == 5, "TWF: wave 1 shape incorrect")
assert(balance.waveSize(9) == 20, "TWF: wave 9 size incorrect")
assert(balance.isUnit("pon") == true, "TWF: PON missing")
assert(balance.isUnit("junk") == false, "TWF: JUNK purchasable")
assert(balance.canBuy("pon", 50, 0) == true, "TWF: PON purchase contract incorrect")
assert(balance.nextHP(40, 40, 9) == 31, "TWF: damage contract incorrect")

return {
    marker = "TWF_OC_ENGINE_STRUCTURE_V1",
    source_main_sha = "e5deff4d5681bca4823a3da0f848e01bc089ae6e",
    topology = "6_expected_game_objects",
    wave_one = 5,
    wave_nine = 20,
    server_player_session_verified = false,
    two_client_verified = false,
    mobile_verified = false,
    publish_authorized = false,
}