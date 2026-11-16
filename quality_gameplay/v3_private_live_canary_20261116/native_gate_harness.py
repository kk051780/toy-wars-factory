#!/usr/bin/env python3
"""Executable Luau VM gate test; deliberately NOT Roblox Studio engine validation."""
from pathlib import Path
import argparse

HERE = Path(__file__).resolve().parent
PREFIX = r'''
local studio = false
local isServer = true
local explicit = false
local ready = false
local RS = {}
function RS:IsStudio() return studio end
function RS:IsServer() return isServer end
local ServerStorage = {}
function ServerStorage:GetAttribute(_name) return explicit end
local ReplicatedStorage = {}
function ReplicatedStorage:GetAttribute(_name) return ready end
function ReplicatedStorage:SetAttribute(_name, value) ready = value end
game = {PrivateServerId = ""}
function game:GetService(name)
 if name == "RunService" then return RS end
 if name == "ServerStorage" then return ServerStorage end
 if name == "ReplicatedStorage" then return ReplicatedStorage end
 error("unavailable service " .. tostring(name))
end
local deferred = {}
task = {
 wait = function(_n) return end,
 spawn = function(fn) table.insert(deferred, fn) end
}
'''
SUFFIX = r'''
local n = 0
local function check(value, expected, msg)
 assert(value == expected, msg)
 n += 1
end
studio = true
check(Gate.allowed(), true, "Studio development place")
studio = false
explicit = true
game.PrivateServerId = ""
check(Gate.serverAllowed(), false, "Public server blocked despite flag")
check(Gate.advertiseServerReady(), false, "No readiness from public server")
game.PrivateServerId = "private-abc"
explicit = false
check(Gate.serverAllowed(), false, "Private server default OFF")
check(Gate.advertiseServerReady(), false, "Private server requires opt in")
explicit = true
check(Gate.serverAllowed(), true, "Private + explicit allowed")
check(Gate.advertiseServerReady(), true, "Server advertises readiness")
check(ready, true, "Replicated ready only after server allows")
isServer = false
ready = false
check(Gate.allowed(), false, "Client cannot self-authorize")
ready = true
check(Gate.waitAllowed(0), true, "Client sees only server readiness")
check(Gate.serverAllowed(), false, "Client cannot call server privileged gate")
-- PRIVATE arena lifecycle: opt-in revocation destroys only its owned world and
-- unpublishes READY; never opens public-server access or changes score authority.
local function world()
 local w = {Parent=true, destroyed=false}
 function w:Destroy() self.Parent=nil; self.destroyed=true end
 return w
end
local fakeClientWorld = world()
check(Gate.watchWorld(fakeClientWorld), false, "client cannot register server watcher")
check(fakeClientWorld.destroyed, false, "client cannot destroy via server watcher")
isServer = true
studio = true
local studioWorld = world()
check(Gate.watchWorld(studioWorld), true, "Studio source still playable")
check(#deferred, 0, "Studio source does not poll private permission")
studio = false
game.PrivateServerId = ""
explicit = true
ready = true
local publicWorld = world()
check(Gate.watchWorld(publicWorld), false, "public server cannot start despite opt-in")
check(publicWorld.destroyed, true, "public server test arena is dismantled")
check(ready, false, "public server cannot hold READY lease")
game.PrivateServerId = "private-abc"
explicit = false
ready = true
local noOptInWorld = world()
check(Gate.watchWorld(noOptInWorld), false, "private default OFF cannot start")
check(noOptInWorld.destroyed, true, "unapproved private arena dismantled")
check(ready, false, "private default OFF clears stale READY")
explicit = true
ready = true
local approvedWorld = world()
check(Gate.watchWorld(approvedWorld), true, "approved private canary starts")
check(#deferred, 1, "exactly one host-scoped revocation watcher")
check(approvedWorld.destroyed, false, "authorized world remains before revocation")
explicit = false
deferred[1]()
check(approvedWorld.destroyed, true, "revoked world destroyed")
check(ready, false, "revoked READY withdrawn")
check(Gate.serverAllowed(), false, "authorization revoked")
print("PRIVATE_GATE_NATIVE_" .. tostring(n) .. "_CASES_PASS")
'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    code = (HERE / "EGGRUMBLE_PrivateLiveGate.luau").read_text(encoding="utf-8")
    if not code.rstrip().endswith("return Gate"):
        raise ValueError("gate source structure changed")
    body = code.rstrip()[:-len("return Gate")]
    args.out.write_text(PREFIX + "\n" + body + "\n" + SUFFIX, encoding="utf-8")
