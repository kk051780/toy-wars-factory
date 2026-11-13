#!/usr/bin/env python3
"""Run real MusouHorde Luau against physical player height vs floating beast VFX.

This test uses the *actual* #288 V5 Horde and CombatRules in the existing tiny
Roblox mock, and the actual 40-source bridge Game text. NOT real Roblox Studio.
"""
from __future__ import annotations
from pathlib import Path
import argparse,importlib.util

OWN=Path(__file__).resolve().parents[1]
GEN=OWN/"tools/generate_native_horde_state_test.py"
spec=importlib.util.spec_from_file_location("existing_horde_native",GEN)
assert spec and spec.loader
up=importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)
DIST=OWN/"dist/EGG_RAID_RUMBLE_H1_EVOLUTION_MUSOU_V5_PRIVATE_BRIDGE"
game=(DIST/"src/server/Game.server.luau").read_text("utf8")
assert game.count('local hits=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,')==1
assert game.count('local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,')==0
assert game.count("local scoutExpiresAt=serverNow()+SCOUT_DURATION")==1
assert game.count("evolvedStrikes<2")==1
assert "Evolution.nextEvolution(" in game and "Power.beginAwaken(" in game
source=up.source
assert source.count('print("MUSOU_HORDE_NATIVE_"..tostring(passed).."_STATE_ASSERTIONS_PASS")')==1
source += r'''
-- An actual V5 minion's body is centered at floor +1.65 studs, while the
-- original full #40 evolved scout VFX hovers rootY+4.5. Thus a hit emitted
-- from that cosmetic altitude fails the actual Combat.SWEEP_MAX_VERTICAL=5.
local assault=Horde.new(world)
assault:reset(43,100)
local target=assault.mobs[1]
local rootPhysical=target.pos+vec(-5,1.35,0)
local originalVisual=rootPhysical+vec(0,4.5,0)
local front=vec(1,0,0)
local visuals,visualKOs=assault:hit(originalVisual,front,26,101,nil)
eq(visuals,0,"original floating visual Y cannot hit true grounded minion")
eq(visualKOs,0,"airborne cosmetic attack must never count a kill")
local grounded,kos=assault:hit(rootPhysical,front,26,101.5,nil)
eq(grounded,1,"actual player physical Y restores near-enemy attack")
eq(kos,1,"real Horde player-ground attack KO accepted by server")
eq(target.hp,0,"real target receives server HP damage once")
local repeatHits=assault:hit(rootPhysical,front,26,102,nil)
eq(repeatHits,0,"same defeated target cannot farm rewards")
assault:reset(44,110)
workspace.blocked=true
local behindWall=assault:hit(rootPhysical,front,26,111,nil)
eq(behindWall,0,"true physical player origin still obeys LOS")
workspace.blocked=false
assault:clear()
eq(assault:livingCount(),0,"realtime single H1 Horde cleanup")
print("P0D_EVOLVED_ASSAULT_GROUND_ORIGIN_REAL_HORDE_NATIVE_8_ASSERTIONS_PASS")
'''
def build():
 ap=argparse.ArgumentParser()
 ap.add_argument("--write",required=True)
 args=ap.parse_args()
 output=Path(args.write)
 output.write_text(source,encoding="utf8")
 print("P0D_EVOLVED_ASSAULT_ACTUAL_HORDE_NATIVE_TEST_GENERATED",str(output))
if __name__=="__main__":
 build()
