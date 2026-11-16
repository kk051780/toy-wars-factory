"""Build native Luau executable for the ACTUAL optional server observer, not just its policy."""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
policy = (HERE / "EGGRUMBLE_BossCreditPolicy.luau").read_text(encoding="utf-8")
observer = (HERE / "EGGRUMBLE_BossCreditRoundFence.server.luau").read_text(encoding="utf-8")
target = 'local Policy = require(script.Parent:WaitForChild("EGGRUMBLE_BossCreditPolicy"))'
assert observer.count(target) == 1, "observer source changed; fail closed"
observer = observer.replace(target, "local Policy = (function()\n" + policy + "\nend)()")
mock = r'''
local checked = 0
local function check(yes, label)
    assert(yes, label)
    checked += 1
end
local function signal()
    local entries = {}
    local object = {}
    function object:Connect(fn)
        local connection = {connected=true}
        function connection:Disconnect()
            self.connected = false
        end
        table.insert(entries, {fn=fn, connection=connection})
        return connection
    end
    function object:Fire(...)
        for _, entry in ipairs(entries) do
            if entry.connection.connected then
                entry.fn(...)
            end
        end
    end
    function object:LiveCount()
        local n=0
        for _,entry in ipairs(entries) do
            if entry.connection.connected then n+=1 end
        end
        return n
    end
    return object
end

local Players = {PlayerAdded=signal(), PlayerRemoving=signal(), roster={}}
function Players:GetPlayers()
    return self.roster
end
local RunService = {}
function RunService:IsStudio()
    return true
end
local game = {}
function game:GetService(name)
    if name == "Players" then return Players end
    if name == "RunService" then return RunService end
    error("unexpected service " .. tostring(name))
end
local MODE = "EGGRUMBLE_QueuedMode"
local COUNTER = "EGGRUMBLE_BossDefeats"
local function makePlayer(id, mode, bossKOs)
    local p = {
        UserId=id, Parent=Players,
        attributes={[MODE]=mode, [COUNTER]=bossKOs},
        signals={},
    }
    function p:GetAttribute(key)
        return self.attributes[key]
    end
    function p:GetAttributeChangedSignal(key)
        if not self.signals[key] then self.signals[key]=signal() end
        return self.signals[key]
    end
    function p:SetAttribute(key, value)
        local old=self.attributes[key]
        self.attributes[key]=value
        if old~=value and self.signals[key] then self.signals[key]:Fire() end
    end
    table.insert(Players.roster, p)
    return p
end
local idle = makePlayer(101,nil,7)
local active = makePlayer(102,"TEAM",2)
'''
cases = r'''
check(idle:GetAttribute(COUNTER)==0, "idle player stale boss credit cleared on initial bind")
check(active:GetAttribute(COUNTER)==2, "do NOT wipe live TEAM counter at late observer boot")
check(active.signals[MODE]:LiveCount()==1, "one attribute listener per player")
idle:SetAttribute(COUNTER,4)
idle:SetAttribute(MODE,"TEAM")
check(idle:GetAttribute(COUNTER)==0, "idle -> TEAM clears cross-round boss count")
active:SetAttribute(COUNTER,8)
active:SetAttribute(MODE,"TEAM")
check(active:GetAttribute(COUNTER)==8, "duplicate TEAM notification never erases current KO")
active:SetAttribute(MODE,nil)
check(active:GetAttribute(COUNTER)==0, "TEAM -> lobby clears KO")
active:SetAttribute(COUNTER,9)
active:SetAttribute(MODE,"BATTLE_ROYALE")
check(active:GetAttribute(COUNTER)==0, "lobby -> BR clears KO")
active:SetAttribute(COUNTER,3)
active:SetAttribute(MODE,"TEAM")
check(active:GetAttribute(COUNTER)==0, "direct BR -> TEAM clears KO")
active:SetAttribute(COUNTER,12)
active:SetAttribute(MODE,"INVALID")
check(active:GetAttribute(COUNTER)==12, "invalid mode never resets credit")
active:SetAttribute(MODE,"TEAM")
check(active:GetAttribute(COUNTER)==12, "invalid previous mode never resets credit")
local other = makePlayer(103,nil,5)
Players.PlayerAdded:Fire(other)
check(other:GetAttribute(COUNTER)==0, "later PlayerAdded initializes idle player")
other:SetAttribute(COUNTER,10)
other:SetAttribute(MODE,"BATTLE_ROYALE")
check(other:GetAttribute(COUNTER)==0, "later PlayerAdded listener is live")
other:SetAttribute(COUNTER,14)
other:SetAttribute(MODE,"BATTLE_ROYALE")
check(other:GetAttribute(COUNTER)==14, "same-mode update keeps current win")
check(other.signals[MODE]:LiveCount()==1, "new player has exactly one listener")
Players.PlayerRemoving:Fire(other)
other.Parent=nil
check(other.signals[MODE]:LiveCount()==0, "PlayerRemoving disconnects listener")
other:SetAttribute(MODE,nil)
check(other:GetAttribute(COUNTER)==14, "no stale listener after departing")
check(active:GetAttribute(COUNTER)==12, "other mode owner remains unchanged")
check(idle:GetAttribute(COUNTER)==0, "separate player unaffected by leaving")
assert(checked==18, "unexpected coverage drift: " .. tostring(checked))
print("BOSS_CREDIT_ACTUAL_OBSERVER_NATIVE: 18/18 PASS")
'''
output = mock + "\nlocal observerBoot = (function()\n" + observer + "\nend)()\n" + cases
out = Path(sys.argv[1])
out.write_text(output,encoding="utf-8")
print(out)
