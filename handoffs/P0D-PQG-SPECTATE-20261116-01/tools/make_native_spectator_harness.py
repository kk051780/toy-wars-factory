#!/usr/bin/env python3
"""Execute the unchanged original V3 spectator LocalScript in native Luau fakes.

This is a *behavioral* VM harness, NOT a physical Roblox Studio/Android simulation.
The runtime source body is copied exactly from Git checkout, never reauthored.
Optional deliberate source mutations are mandatory negative controls.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EGGRUMBLE_Spectate.client.luau"

PRELUDE = r'''
-- Minimal isolated Roblox surface for authentic client script behavior.
local function Signal()
    local result = {listeners = {}}
    function result:Connect(fn)
        table.insert(self.listeners, fn)
        return {Disconnect = function() end}
    end
    function result:Fire(...)
        for _, fn in ipairs(self.listeners) do fn(...) end
    end
    return result
end

local objectMethods = {}
local objectMeta = {}
function objectMeta.__index(obj, key)
    local m = objectMethods[key]
    if m then return m end
    return rawget(obj, "_props")[key]
end
function objectMeta.__newindex(obj, key, value)
    if key == "Parent" then
        local before = obj._props.Parent
        if before then
            for i, other in ipairs(before._children) do
                if other == obj then
                    table.remove(before._children, i)
                    break
                end
            end
        end
        if value then table.insert(value._children, obj) end
    end
    obj._props[key] = value
end
local function newNode(kind)
    local n = {_props = {ClassName = kind, Name = kind}, _children = {}, _signals = {}}
    return setmetatable(n, objectMeta)
end
function objectMethods:IsA(kind)
    return self.ClassName == kind or (kind == "BasePart" and self.ClassName == "Part")
end
function objectMethods:FindFirstChild(name)
    for _, item in ipairs(self._children) do
        if item.Name == name then return item end
    end
    return nil
end
function objectMethods:WaitForChild(name)
    local v = self:FindFirstChild(name)
    assert(v, "test mock missing required child " .. name)
    return v
end
function objectMethods:GetChildren()
    return self._children
end
function objectMethods:FindFirstChildOfClass(kind)
    for _, child in ipairs(self._children) do
        if child:IsA(kind) then return child end
    end
    return nil
end
function objectMethods:GetPivot()
    return {Position = self.PivotPosition or Vector3.new(0, 0, 0)}
end
function objectMethods:GetAttribute(name)
    return self._props.Attributes and self._props.Attributes[name] or nil
end
function objectMethods:GetAttributeChangedSignal(name)
    local key = "attr:" .. name
    if not self._signals[key] then self._signals[key] = Signal() end
    return self._signals[key]
end
function objectMethods:SetAttribute(name, value)
    if not self._props.Attributes then self._props.Attributes = {} end
    local before = self._props.Attributes[name]
    self._props.Attributes[name] = value
    if before ~= value then self:GetAttributeChangedSignal(name):Fire() end
end
function objectMethods:GetPropertyChangedSignal(name)
    local key = "property:" .. name
    if not self._signals[key] then self._signals[key] = Signal() end
    return self._signals[key]
end

local Instance = {}
function Instance.new(kind, parent)
    local n = newNode(kind)
    if kind == "TextButton" then n.Activated = Signal() end
    if parent then n.Parent = parent end
    return n
end

local vecMeta = {}
function vecMeta.__add(a,b)
    return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},vecMeta)
end
local Vector3 = {}
function Vector3.new(x,y,z)
    return setmetatable({X=x,Y=y,Z=z},vecMeta)
end
local Vector2 = {}
function Vector2.new(x,y) return {X=x,Y=y} end
local CFrame = {}
function CFrame.new(pos) return {pos=pos} end
function CFrame.lookAt(eye,focus) return {eye=eye,focus=focus} end
local UDim2 = {}
function UDim2.fromOffset(x,y) return {x=x,y=y} end
function UDim2.new(xs,xo,ys,yo) return {xs=xs,xo=xo,ys=ys,yo=yo} end
local UDim = {}
function UDim.new(s,o) return {s=s,o=o} end
local Color3 = {}
function Color3.fromRGB(r,g,b) return {r=r,g=g,b=b} end
function Color3.new(r,g,b) return {r=r,g=g,b=b} end
local Enum = {
    CameraType = {Custom="Custom",Scriptable="Scriptable"},
    Font = {GothamBold="GothamBold",GothamMedium="GothamMedium"},
    KeyCode = {Left="Left",Right="Right"},
}

local player = newNode("Player")
player.Name = "Owner101"
player.UserId = 101
local playerGui = Instance.new("PlayerGui", player)
local avatar = newNode("Model")
local humanoid = Instance.new("Humanoid", avatar)
player.Character = avatar

local camera = newNode("Camera")
camera.CameraType = Enum.CameraType.Custom
camera.CameraSubject = humanoid
local Workspace = newNode("Workspace")
Workspace.CurrentCamera = camera
local lobby = Instance.new("Folder", Workspace)
lobby.Name = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local teamArena = Instance.new("Folder", lobby)
teamArena.Name = "TEAM_Arena"
local brArena = Instance.new("Folder", lobby)
brArena.Name = "BATTLE_ROYALE_Arena"
local function castle(parent, name, x)
    local model = Instance.new("Model", parent)
    model.Name = name
    model.PivotPosition = Vector3.new(x, 2, 12)
    local core = Instance.new("Part", model)
    core.Name = "StandardCore"
    return model
end
local ownCastle = castle(teamArena, "Castle_101", 0)
local otherCastle = castle(teamArena, "Castle_202", 20)
local otherModeCastle = castle(brArena, "Castle_303", 1000)

local Players = {LocalPlayer=player}
local UserInputService = {TouchEnabled=true,InputBegan=Signal()}
local RunService = {Heartbeat=Signal()}
function RunService:IsStudio() return true end
local services = {
    Players=Players, Workspace=Workspace,
    UserInputService=UserInputService,RunService=RunService,
}
local game = {}
function game:GetService(name)
    assert(services[name], "unexpected game service " .. name)
    return services[name]
end
'''

TEST = r'''
-- The actual source above has already run and wired real signal callbacks.
local gui = playerGui:FindFirstChild("EGGRUMBLE_EliminatedSpectate")
assert(gui and gui.Enabled == false, "active player must not see spectator UI")
assert(camera.CameraType == Enum.CameraType.Custom and camera.CameraSubject == humanoid,
       "active player camera mutated")
local panel = gui:FindFirstChild("SpectateControls")
assert(panel and panel.Size.x == 252 and panel.Size.y == 56, "touch layout")
local buttons = {}
for _, child in ipairs(panel:GetChildren()) do
    if child:IsA("TextButton") then table.insert(buttons, child) end
end
assert(#buttons == 2)
for _,b in ipairs(buttons) do
    assert(b.Size.x >= 44 and b.Size.y >= 44, "child touch target too small")
end
assert(player:GetAttribute("EGGRUMBLE_Eliminated") ~= true)

-- Real server-confirmed elimination enables existing-team observer only.
player:SetAttribute("EGGRUMBLE_Eliminated",true)
assert(gui.Enabled == true and camera.CameraType == Enum.CameraType.Scriptable,
       "eliminated camera not activated")
assert(camera.CFrame and camera.CFrame.focus.X == 0, "first own-mode target")
assert(camera.Focus.pos.X == 0, "scriptable Focus not set")
local label = panel:FindFirstChild("TextLabel")
-- label is unnamed, source does not require public stable label identifier.
assert(label and label.Text == "観戦 1/2", "wrong spectator count")

-- GUI navigation cycles over original OWN arena castles only.
local right = buttons[2]
right.Activated:Fire()
assert(camera.CFrame.focus.X == 20 and camera.Focus.pos.X == 20,
       "touch right must select second same-mode castle")
assert(label.Text == "観戦 2/2")
UserInputService.InputBegan:Fire({KeyCode=Enum.KeyCode.Left},true)
assert(camera.CFrame.focus.X == 20,"consumed game input changed spectator target")
UserInputService.InputBegan:Fire({KeyCode=Enum.KeyCode.Left},false)
assert(camera.CFrame.focus.X == 0,"keyboard left did not cycle")
UserInputService.InputBegan:Fire({KeyCode=Enum.KeyCode.Right},false)
assert(camera.CFrame.focus.X == 20,"keyboard right did not cycle")
assert(camera.CFrame.focus.X ~= 1000,"observed another match mode")

-- Castle and mode transitions are server-owned. Client never edits match HP.
assert(ownCastle.Parent == teamArena and otherCastle.Parent == teamArena)

-- Round ends: attribute cleared by original Game restores ordinary camera.
player:SetAttribute("EGGRUMBLE_Eliminated",nil)
assert(gui.Enabled == false and camera.CameraType == Enum.CameraType.Custom
       and camera.CameraSubject == humanoid, "reset did not restore camera")
assert(player:GetAttribute("EGGRUMBLE_Eliminated")==nil)
print("NATIVE_SPECTATOR_RESET_FLAG_PASS")

-- Next elimination / new arena cleanup must restore the camera again.
player:SetAttribute("EGGRUMBLE_Eliminated",true)
assert(gui.Enabled==true)
teamArena.Parent=nil
RunService.Heartbeat:Fire(.5)
assert(gui.Enabled==false and camera.CameraType==Enum.CameraType.Custom,
       "stale completed arena kept Scriptable camera")
assert(camera.CameraSubject==humanoid)
assert(otherModeCastle.Parent==brArena,"other-mode castle unexpectedly modified")
assert(brArena.Parent==lobby)
print("NATIVE_SPECTATOR_ARENA_REMOVAL_PASS")

-- Even with server's Eliminated flag true, no own castle in BR => NO observer.
RunService.Heartbeat:Fire(.5)
assert(gui.Enabled==false and camera.CameraType==Enum.CameraType.Custom,
       "wrong BR arena leak when no own castle")
print("NATIVE_SPECTATOR_CROSS_MODE_ISOLATION_PASS")

-- Gameplay recovery without settable remote, damage or rewards.
assert(ownCastle.PivotPosition.X==0 and otherCastle.PivotPosition.X==20)
print("NATIVE_SPECTATOR_REAL_CLIENT_LIFECYCLE_PASS")
'''

MUTATIONS = {
    "elimination": (
        'GetAttribute("EGGRUMBLE_Eliminated") ~= true',
        'GetAttribute("EGGRUMBLE_Eliminated") == true',
    ),
    "mode": (
        'candidate and candidate:FindFirstChild("Castle_" .. tostring(player.UserId))',
        'candidate and true',
    ),
    "recovery": (
        '    gui.Enabled = false\n    restoreCamera()',
        '    gui.Enabled = true\n    restoreCamera()',
    ),
}


def generate(out: Path, mutation: str) -> None:
    source = SOURCE.read_text(encoding="utf-8")
    if mutation != "none":
        old, new = MUTATIONS[mutation]
        if source.count(old) != 1:
            raise ValueError(f"source drift for {mutation}: expected one exact anchor")
        source = source.replace(old, new)
    else:
        if source.count('GetAttribute("EGGRUMBLE_Eliminated") ~= true') != 1:
            raise ValueError("Elimination contract drift; stop, do not reauthor")
    out.write_text(PRELUDE + "\n" + source + "\n" + TEST, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mutation", choices=("none", *MUTATIONS), default="none")
    args = parser.parse_args()
    generate(args.out, args.mutation)
    print("Native V3 spectator real-source lifecycle harness generated:", args.out, args.mutation)
