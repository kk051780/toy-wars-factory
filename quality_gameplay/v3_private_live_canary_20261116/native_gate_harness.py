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
local listeners = {}
local RS = {}
function RS:IsStudio() return studio end
function RS:IsServer() return isServer end
local ServerStorage = {}
function ServerStorage:GetAttribute(_name) return explicit end
function ServerStorage:GetAttributeChangedSignal(_name)
 local signal = {}
 function signal:Connect(fn)
  local item = {live=true, callback=fn}
  function item:Disconnect() self.live=false end
  table.insert(listeners,item)
  return item
 end
 return signal
end
local function setExplicit(value)
 explicit=value
 for _,listener in ipairs(listeners) do
  if listener.live then listener.callback() end
 end
end
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
local function world()
 local w = {Parent=true, destroyed=false}
 function w:Destroy() self.Parent=nil; self.destroyed=true end
 return w
end

-- Separate gate creation represents a brand-new private server instance,
-- never a new session in the same server. Original author sources stay intact.
studio=true
check(Gate.allowed(),true,"Studio development source")
check(Gate.serverAllowed(),true,"Studio server allowed")
local studioWorld=world()
check(Gate.watchWorld(studioWorld),true,"Studio preview still allowed")
check(#deferred,0,"Studio has no private watcher")
studio=false

explicit=true
game.PrivateServerId=""
check(Gate.serverAllowed(),false,"public cannot opt in")
check(Gate.advertiseServerReady(),false,"public cannot advertise READY")
local publicWorld=world()
check(Gate.watchWorld(publicWorld),false,"public cannot register world")
check(publicWorld.destroyed,true,"public candidate world destroyed")
check(ready,false,"public stale READY withdrawn")
game.PrivateServerId="private-abc"
check(Gate.serverAllowed(),false,"denied instance stays latched OFF")
Gate=makeGate()
explicit=false
check(Gate.serverAllowed(),false,"private server default OFF")
local noOptInWorld=world()
ready=true
check(Gate.watchWorld(noOptInWorld),false,"private no opt-in cannot register")
check(noOptInWorld.destroyed,true,"no opt-in arena destroyed")
check(ready,false,"no opt-in stale READY removed")
setExplicit(true)
check(Gate.serverAllowed(),false,"cannot arm server after denied attempt")

-- New isolated private instance: exactly one authorized world.
Gate=makeGate()
ready=false
check(Gate.serverAllowed(),true,"fresh private server explicit opt in")
check(Gate.advertiseServerReady(),false,"no world: early READY forbidden")
check(ready,false,"not ready before two portals")
local accepted=world()
check(Gate.watchWorld(accepted),true,"first world lease accepted")
check(#deferred,1,"one monitor spawned")
check(#listeners>=1,true,"attribute-change monitor connected")
check(Gate.advertiseServerReady(),true,"after lobby ready accepted")
check(ready,true,"READY published after authorization")
local duplicate=world()
check(Gate.watchWorld(duplicate),false,"duplicate host world rejected")
check(duplicate.destroyed,true,"duplicate castle egg horde world destroyed")
check(accepted.destroyed,false,"original world retained")
check(ready,true,"duplicate cannot revoke original READY")
check(#deferred,1,"duplicate creates no second polling task")
check(Gate.watchWorld(accepted),true,"same host idempotent lease")
check(Gate.serverAllowed(),true,"lease still allowed")
isServer=false
check(Gate.serverAllowed(),false,"client cannot call server authority")
local clientWorld=world()
check(Gate.watchWorld(clientWorld),false,"client cannot register world")
check(clientWorld.destroyed,false,"client no server-side world mutation")
check(Gate.allowed(),true,"client sees only server READY")
ready=false
check(Gate.allowed(),false,"client cannot bypass READY false")
ready=true
check(Gate.waitAllowed(0),true,"client wait allowed only on ready")
isServer=true
-- Signal must revoke synchronously; false -> true before next 0.25s poll
-- must NOT resurrect old castle, egg carriers or network readiness.
setExplicit(false)
check(accepted.destroyed,true,"change event destroys active world immediately")
check(ready,false,"change event clears READY before next poll")
check(Gate.serverAllowed(),false,"revocation latches server permanently")
setExplicit(true)
check(Gate.serverAllowed(),false,"rapid re-enable stays blocked")
check(Gate.advertiseServerReady(),false,"no READY after re-enable")
check(ready,false,"revoked READY remains false")
local reuse=world()
check(Gate.watchWorld(reuse),false,"same-server arena re-creation denied")
check(reuse.destroyed,true,"re-created arena removed")
check(#deferred,1,"no second background loop after revoke")
deferred[1]()
check(listeners[#listeners].live,false,"old change listener disconnected")

-- Another fresh dedicated private test server can opt in normally.
Gate=makeGate()
ready=false
check(Gate.serverAllowed(),true,"fresh instance can opt in")
local second=world()
check(Gate.watchWorld(second),true,"fresh private arena created")
check(Gate.advertiseServerReady(),true,"fresh private READY after host")
second.Parent=nil
deferred[2]()
check(ready,false,"normal world removal clears READY")
check(Gate.serverAllowed(),false,"normal world retirement also locks restart")
print("PRIVATE_GATE_NATIVE_"..tostring(n).."_CASES_PASS")
'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    code = (HERE / "EGGRUMBLE_PrivateLiveGate.luau").read_text(encoding="utf-8")
    if not code.rstrip().endswith("return Gate"):
        raise ValueError("gate source structure changed")
    body = code.rstrip()[:-len("return Gate")]
    args.out.write_text(PREFIX + "\nlocal function makeGate()\n" + body + "\nreturn Gate\nend\nlocal Gate=makeGate()\n" + SUFFIX, encoding="utf-8")
