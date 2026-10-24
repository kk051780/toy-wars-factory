-- TWF v1.2 studio-only automatic bootstrap smoke checks.
-- Checks structure and core API. Does NOT verify networking across two real clients.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local ServerScriptService=game:GetService("ServerScriptService")
local checks=0
local fails=0
local function check(name, condition)
    checks=checks+1
    if not condition then fails=fails+1;warn("TWF_QA_FAIL "..name)
    else print("TWF_QA_PASS "..name) end
end
task.wait(3)
local B=require(ReplicatedStorage:WaitForChild("ToyWarsBalance",10))
check("balance_require",type(B)=="table")
check("select_event",ReplicatedStorage:FindFirstChild("ToyWarsSelectUnit")~=nil)
check("server_script",ServerScriptService:FindFirstChild("ToyWarsServer")~=nil)
check("map_exists",workspace:FindFirstChild("ToyWarsWorld")~=nil)
if B then
    check("pon_price",B.UNITS.pon.cost==10)
    check("no_junk_purchase",not B.isUnit("junk"))
    check("no_negative_coins",B.buy("pon",-5,0)==nil)
    check("no_free_tankuru",B.buy("tankuru",47,0)==nil)
    check("wave_size",B.waveSize(1)==5)
end
print(string.format("TWF_QA_SUMMARY v1.2 pass=%d fail=%d",checks-fails,fails))
