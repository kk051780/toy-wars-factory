"""Embed exact original R13 ServerScript under deterministic Luau service stubs.

This executes genuine SOURCE in Luau VM, not a Python source-contract mimic.
It is NOT a Roblox Studio/Android performance or networking claim.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "EGGRUMBLE_RespawnGrace.server.luau"

HEADER = r'''
local NOW = 0
local checks = 0
local function check(value, description)
    checks += 1
    if not value then error("R13_NATIVE_" .. tostring(checks) .. ":" .. description, 2) end
end
local function newSignal()
    local handlers = {}
    local event = {}
    function event:Connect(fn)
        local item = {active = true, callback = fn}
        table.insert(handlers, item)
        return {Disconnect = function() item.active = false end}
    end
    function event:Fire(...)
        for _, item in ipairs(handlers) do
            if item.active then item.callback(...) end
        end
    end
    return event
end
local function vec(x, y, z)
    return setmetatable({X = x, Y = y, Z = z}, {
        __index = function(v, k)
            if k == "Magnitude" then
                return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
            end
        end,
        __sub = function(a,b)
            return vec(a.X - b.X, a.Y - b.Y, a.Z - b.Z)
        end,
    })
end
Vector3 = {new = vec}
Color3 = {
    fromRGB = function(r,g,b) return string.format("%d,%d,%d",r,g,b) end
}
local function obj(class, name)
    local fields = {
        ClassName = class, Name = name, Children = {},
        ChildAdded = newSignal(), Died = newSignal(),
        _Parent = nil,
    }
    function fields:IsA(k)
        return self.ClassName == k or (k == "BasePart" and self.ClassName == "Part")
    end
    function fields:FindFirstChild(n)
        return self.Children[n]
    end
    function fields:FindFirstChildOfClass(k)
        for _, v in pairs(self.Children) do
            if v:IsA(k) then return v end
        end
        return nil
    end
    function fields:WaitForChild(n, _wait)
        return self:FindFirstChild(n)
    end
    function fields:GetChildren()
        local result = {}
        for _,v in pairs(self.Children) do table.insert(result,v) end
        return result
    end
    function fields:Destroy()
        self.Parent = nil
        self.Destroyed = true
    end
    return setmetatable(fields, {
        __index = function(t,k)
            if k=="Parent" then return rawget(t,"_Parent") end
        end,
        __newindex = function(t,k,v)
            if k=="Parent" then
                local old=rawget(t,"_Parent")
                if old then old.Children[t.Name] = nil end
                rawset(t,"_Parent",v)
                if v then
                    v.Children[t.Name] = t
                    v.ChildAdded:Fire(t)
                end
            else rawset(t,k,v) end
        end,
    })
end
Instance = {new = function(class) return obj(class,class) end}
local delayed = {}
local spawned = {}
task = {}
function task.delay(seconds, callback)
    table.insert(delayed,{when=NOW+seconds,callback=callback})
end
function task.spawn(callback)
    table.insert(spawned,callback)
end
function task.wait(seconds)
    NOW += seconds or 0
end
local function advance(seconds)
    local stop = NOW + seconds
    while true do
        local index = nil
        local when = math.huge
        for i,item in ipairs(delayed) do
            if item.when <= stop and item.when < when then
                index=i;when=item.when
            end
        end
        if not index then break end
        local item=table.remove(delayed,index)
        NOW=item.when
        item.callback()
    end
    NOW=stop
end
os={clock=function() return NOW end}
local PService = obj("Players","Players")
PService.PlayerAdded = newSignal()
PService.PlayerRemoving = newSignal()
PService.players={}
function PService:GetPlayers() return self.players end
local Studio = {IsStudio=function() return true end}
local Prompts = {PromptTriggered = newSignal()}
local Workspace = obj("Workspace","Workspace")
local gameServices = {Players=PService,RunService=Studio,ProximityPromptService=Prompts,Workspace=Workspace}
game={GetService=function(_,name) return assert(gameServices[name],"unknown service "..tostring(name)) end}
local scenes=obj("Folder","EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW")
scenes.Parent=Workspace
local function makeArena(mode)
    local arena=obj("Folder",mode.."_Arena")
    arena.Parent=scenes
    local castle=obj("Model","Castle_987")
    castle.Parent=arena
    local core=obj("Part","StandardCore")
    core.Color=Color3.fromRGB(170,165,155)
    core.Position=vec(0,0,0)
    core.Parent=castle
    return arena,core
end
local team,teamCore=makeArena("TEAM")
local function makeCharacter(distance)
    local ch=obj("Model","P1_Avatar")
    local hum=obj("Humanoid","Humanoid")
    hum.Health=100
    hum.Parent=ch
    local hrp=obj("Part","HumanoidRootPart")
    hrp.Position=vec(0,0,distance or -45)
    hrp.Parent=ch
    return ch,hum,hrp
end
local player=obj("Player","P1")
player.UserId=987
player.attrs={EGGRUMBLE_QueuedMode="TEAM",EGGRUMBLE_Eliminated=false}
player.signals={}
player.CharacterAdded=newSignal()
player.CharacterRemoving=newSignal()
function player:GetAttribute(name) return self.attrs[name] end
function player:GetAttributeChangedSignal(name)
    self.signals[name]=self.signals[name] or newSignal()
    return self.signals[name]
end
function player:SetAttribute(name,value)
    self.attrs[name]=value
    if self.signals[name] then self.signals[name]:Fire() end
end
player.Parent=PService
PService.players={player}
local first,firstHum=makeCharacter(-45)
player.Character=first
local function shield(character)
    return character:FindFirstChild("EGGRUMBLE_GQ_RespawnGrace")
end
local function newLife(previous, previousHum, distance)
    if previous then
        previousHum.Health=0
        previousHum.Died:Fire()
        player.CharacterRemoving:Fire()
    end
    local nextChar,nextHum=makeCharacter(distance)
    player.Character=nextChar
    player.CharacterAdded:Fire(nextChar)
    advance(0.96)
    return nextChar,nextHum
end
'''
FOOTER = r'''
-- Start with an already-existing lobby character; no verified death yet.
advance(1.1)
check(shield(first)==nil,"initial spawn must NOT grant protection")
-- Genuine death in the original same-mode live arena creates a single-use ticket.
local second,secondHum = newLife(first,firstHum,-45)
check(shield(second)~=nil,"same-arena death + home respawn must grant a shield")
check(shield(second).Visible==false,"shield must not alter #485's art")
-- First legitimate skill equip cancels protection; no invulnerable outgoing damage.
local skill=obj("Tool","EGGRUMBLE_SKILL_A")
skill.Parent=second
check(shield(second)==nil,"equipping the first tool revokes grace")
-- The next genuine death can receive one new ticket.
local third,thirdHum = newLife(second,secondHum,-45)
check(shield(third)~=nil,"next genuine death gets independent grace")
Prompts.PromptTriggered:Fire(obj("ProximityPrompt","EggPrompt"),player)
check(shield(third)==nil,"egg/item/castle prompt action revokes")
-- Dead characters must never keep a field; timed expiry cannot affect future life.
local fourth,fourthHum = newLife(third,thirdHum,-45)
check(shield(fourth)~=nil,"third genuine death shields")
advance(2.26)
check(shield(fourth)==nil,"2.25s timeout removes actual ForceField")
-- A client-visible CharacterAdded WITHOUT a death is not a ticket.
player.CharacterRemoving:Fire()
local fifth,fifthHum=makeCharacter(-45)
player.Character=fifth
player.CharacterAdded:Fire(fifth)
advance(0.96)
check(shield(fifth)==nil,"arbitrary respawn without Died is rejected")
-- Died while TEAM, then switching to BR must reject the old TEAM token.
fifthHum.Health=0
fifthHum.Died:Fire()
player.CharacterRemoving:Fire()
local br,brCore=makeArena("BATTLE_ROYALE")
player:SetAttribute("EGGRUMBLE_QueuedMode","BATTLE_ROYALE")
local sixth,sixthHum=makeCharacter(-45)
player.Character=sixth
player.CharacterAdded:Fire(sixth)
advance(.96)
check(shield(sixth)==nil,"old TEAM death cannot grant in new BR session")
-- Dying in BR and appearing too far from the own castle cannot get protection.
local seventh,seventhHum=newLife(sixth,sixthHum,-250)
check(shield(seventh)==nil,"far field respawn is denied")
-- Server observed death cannot grant when personal castle already fell.
brCore.Color=Color3.fromRGB(59,54,55)
local eighth,eighthHum=newLife(seventh,seventhHum,-45)
check(shield(eighth)==nil,"fallen original castle is denied")
brCore.Color=Color3.fromRGB(170,165,155)
-- A death ticket is pinned to its actual arena INSTANCE, not reused name.
eighthHum.Health=0
eighthHum.Died:Fire()
player.CharacterRemoving:Fire()
br.Parent=nil
br,brCore=makeArena("BATTLE_ROYALE")
local ninth,ninthHum=makeCharacter(-45)
player.Character=ninth
player.CharacterAdded:Fire(ninth)
advance(.96)
check(shield(ninth)==nil,"recreated arena cannot redeem old death")
-- Expired ticket, even same mode and home position, is rejected.
ninthHum.Health=0
ninthHum.Died:Fire()
player.CharacterRemoving:Fire()
advance(12.1)
local tenth,tenthHum=makeCharacter(-45)
player.Character=tenth
player.CharacterAdded:Fire(tenth)
advance(.96)
check(shield(tenth)==nil,"expired 12s death ticket rejected")
-- An author-owned preexisting Field is preserved, not overwritten.
tenthHum.Health=0
tenthHum.Died:Fire()
player.CharacterRemoving:Fire()
local eleventh,eleventhHum=makeCharacter(-45)
local external=obj("ForceField","EGGRUMBLE_ItemShield")
external.Parent=eleventh
player.Character=eleventh
player.CharacterAdded:Fire(eleventh)
advance(.96)
check(shield(eleventh)==nil,"never stack own grace on top of external shield")
check(external.Parent==eleventh,"never delete original item ForceField")
-- Removing the session while pending prevents another grant.
eleventhHum.Health=0
eleventhHum.Died:Fire()
player.CharacterRemoving:Fire()
br.Parent=nil
local twelfth=makeCharacter(-45)
player.Character=twelfth
player.CharacterAdded:Fire(twelfth)
advance(.96)
check(shield(twelfth)==nil,"abandoned arena does not grant")
-- Cleanup on leaving must not throw or retain a field.
PService.PlayerRemoving:Fire(player)
check(shield(eleventh)==nil,"player leaving keeps no own shield")
print("GQ_R13_GENUINE_DEATH_TICKET_NATIVE_VM_PASS", checks)
'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    body = SRC.read_text(encoding="utf-8")
    assert "local function watch(player: Player)" in body
    assert "tickets[player] = {" in body
    args.out.write_text(HEADER + "\n-- BEGIN UNMODIFIED SOURCE\n" + body
                        + "\n-- END UNMODIFIED SOURCE\n" + FOOTER, encoding="utf-8")
    print("WROTE_REAL_LUAU_VM_HARNESS", args.out)
if __name__ == "__main__":
    main()
