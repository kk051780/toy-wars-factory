-- Whole canonical server: a selector chooses future auto-production, not an immediate purchase.
-- Native Lua mock only; Roblox Studio, clients, mobile and physical prompts are NOT tested.
local Harness = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function check(name, fn)
    local ok, err = pcall(fn)
    if ok then passed=passed+1; print("PASS "..name)
    else failed=failed+1; print("FAIL "..name..": "..tostring(err)) end
end
local function eq(got, expected, context)
    assert(got==expected, context..": expected "..tostring(expected)..", got "..tostring(got))
end
check("all selector prompts accurately describe selection", function()
    local h=Harness.new(server)
    local player=h:addPlayer(h:newPlayer())
    for _,id in ipairs({"pon","guardon","tankuru"}) do
        local prompt=h:prompt(player,id.."Selector")
        eq(prompt.ActionText,"Select "..string.upper(id),id.." action")
    end
end)
check("selector changes future auto-production without immediate purchase", function()
    local h=Harness.new(server)
    local player=h:addPlayer(h:newPlayer())
    local prompt,pad=h:prompt(player,"guardonSelector")
    player.Character=h:character(pad.Position)
    local coins=assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    local before=coins.Value
    prompt.Triggered:Fire(player)
    eq(h:status(player,"SelectedToy").Value,"GUARDON","selected toy")
    eq(coins.Value,before,"coins before first production tick")
    eq(h:status(player,"Allies").Value,0,"no instant unit purchase")
end)
local pinned=".qa/server-before/src/ToyWarsServer.server.lua"
local old=io.open(pinned,"rb")
if old then
    old:close()
    check("pinned old server advertised instant Make for selection-only action", function()
        local h=Harness.new(pinned)
        local player=h:addPlayer(h:newPlayer())
        local prompt,pad=h:prompt(player,"guardonSelector")
        eq(prompt.ActionText,"Make GUARDON","old misleading action")
        player.Character=h:character(pad.Position)
        prompt.Triggered:Fire(player)
        eq(h:status(player,"SelectedToy").Value,"GUARDON","old selection effect")
        eq(h:status(player,"Allies").Value,0,"old no instant purchase")
    end)
end
print(string.format("AUTO_SELECTOR_ACTION_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
