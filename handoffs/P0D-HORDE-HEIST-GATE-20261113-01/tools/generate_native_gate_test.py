#!/usr/bin/env python3
"""Build one executable native-Luau test using ACTUAL authored module source.
Not Studio physics or a claim that source has been accepted into Game.server.
"""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
def embed(name, module):
    body=(root/"src"/name).read_text(encoding="utf-8")
    assert body.endswith("return "+module+"\n"), name
    return "local function load"+module+"()\n"+body+"end\nlocal "+module+" = load"+module+"()\n"
source=(embed("EliteKOBridge.luau","EliteKOBridge")
        +embed("GateRules.luau","GateRules")
        +r'''
local h={round=12,mobs={
  {id=1,elite=false,hp=0,deadUntil=4},
  {id=9,elite=true,hp=72,deadUntil=0}
}}
local gate=GateRules.new("12")
local before=EliteKOBridge.capture(h)
assert(before~=nil and not EliteKOBridge.didConfirmEliteKO(h,before))
-- Minion defeated alone must not open gate
h.mobs[1].hp=0
assert(not EliteKOBridge.didConfirmEliteKO(h,before))
h.mobs[2].hp=0
h.mobs[2].deadUntil=10
assert(EliteKOBridge.didConfirmEliteKO(h,before))
assert(gate:onEliteKO("12",true,1))
assert(not gate:onEliteKO("12",true,1.5))
gate:step("12",2.5,0)
assert(gate:snapshot().phase=="WARNING")
gate:step("12",3,0)
assert(gate:snapshot().phase=="OPEN")
gate:step("12",13,2)
assert(gate:snapshot().phase=="WAIT_CLEAR")
gate:step("12",14,0)
assert(gate:snapshot().phase=="CLOSED")
-- Fail shut on stale round, duplicate elite, unreadable HP and respawn
local h2={round=13,mobs={{id=9,elite=true,hp=10,deadUntil=0}}}
local b=EliteKOBridge.capture(h2)
h2.round=14
h2.mobs[1].hp=0
h2.mobs[1].deadUntil=4
assert(not EliteKOBridge.didConfirmEliteKO(h2,b))
local dup={round=14,mobs={{id=8,elite=true,hp=3},{id=9,elite=true,hp=3}}}
assert(EliteKOBridge.capture(dup)==nil)
local dead={round=15,mobs={{id=9,elite=true,hp=0,deadUntil=3}}}
assert(EliteKOBridge.capture(dead)==nil)
print("P0D_GATE_NATIVE_ELITE_BRIDGE_RULES_PASS")
''')
p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/p0d_gate_bridge_native_test.luau")
p.write_text(source,encoding="utf-8")
print(p)
