#!/usr/bin/env python3
"""Fail-closed regression for surgical v5 patch into untouched H1 evolution40."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"tools/build_40_evolution_v5.py"
spec=importlib.util.spec_from_file_location("v5_bridge",p)
assert spec and spec.loader
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
checks=0
def check(condition:bool,label:str):
 global checks
 assert condition,label
 checks+=1
def fails(call,label:str):
 global checks
 try:call()
 except AssertionError:checks+=1
 else:raise AssertionError("FAIL_OPEN_NEGATIVE_"+label)
check(len(b.P39)==len(b.P40)==len(b.H1V5)==40,"immutable pins")
check(len(b.ORIG40_BLOBS)==5,"five exact 40 source locks")
check(all(len(v)==40 for v in b.ORIG40_BLOBS.values()),"original 40 gitblob pins")
check(len(b.V5_HORDE_BLOB)==40 and len(b.BASE39_POWER_BLOB)==40,"real horde/power source blobs")
check(b.HUD_OLD!=b.HUD_NEW,"actual HUD patch")
good_g='''local Evolution = true
local Power = true
Power.beginAwaken()
Evolution.nextEvolution()
if mobHits>0 then return end
        musouMobCount = horde:livingCount(),
'''
fixed_g=b.upgrade_game(good_g)
check('musouEliteWarningSeconds' in fixed_g,"40 Game patch")
check(good_g in fixed_g,"40 Game keeps all original text")
fails(lambda:b.upgrade_game(good_g.replace("horde:livingCount()","horde:allEnemies()")),"Game source drift")
fails(lambda:b.upgrade_game(fixed_g),"Game cannot double inject")
good_h='''local function action() end
EVOLVE_SCOUT AWAKEN_POWER
'''+b.HUD_OLD+'''
other_unchanged
'''
fixed_h=b.upgrade_hud(good_h)
check('赤い円の外へ' in fixed_h,"original HUD cue")
check("other_unchanged" in fixed_h and "EVOLVE_SCOUT" in fixed_h,"evolution controls retained")
fails(lambda:b.upgrade_hud(good_h.replace(b.HUD_OLD,"")), "HUD anchor missing")
fails(lambda:b.upgrade_hud(fixed_h),"HUD cannot double inject")
fails(lambda:b.insertion("foo","bar","baz","missing"),"strict source anchored insertion")
check("shutil.copytree(old,DIST)" in p.read_text(),"separate output root only")
check("FAIL_CLOSED_NO_DESTRUCTIVE_REPLACE" in p.read_text(),"no source overwrite")
check("official_RC_adopted" in p.read_text(),"honest not-RC lock")
check("actual_studio_tested" in p.read_text(),"honest not engine test lock")
check("original_40_unchanged" in p.read_text(),"source retention check")
print(f"P0D_EVOLUTION40_V5_SURGICAL_PATCH_NEGATIVE_PASS {checks}/{checks}")
