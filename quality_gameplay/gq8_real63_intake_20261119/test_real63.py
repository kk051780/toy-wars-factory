#!/usr/bin/env python3
"""Adversarial source ownership tests; no Roblox game behavior is claimed."""
import importlib.util, pathlib, tempfile, json
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("composite",ROOT/"compose_real63.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=("ServerScriptService","Combat")
b=("ServerScriptService","Host")
c=("StarterPlayer","StarterPlayerScripts","UI")
base={a:("Script",b"hp=5"),b:("Script",b"host=true")}
valid={**base,c:("LocalScript",b"ui=true")}
m.check_diff(base,valid,set(),{c},"valid")
def negative(fn,word):
 try:fn()
 except ValueError as e:
  assert word in str(e),(word,e)
 else:raise AssertionError("RED_MUTANT_ESCAPED_"+word)
negative(lambda:m.check_diff(base,{**valid,a:("Script",b"hp=0")},set(),{c},"bad"),"RED_ORIGINAL_DRIFT")
negative(lambda:m.check_diff(base,{**valid,a:("Script",b"hp=0")},{b},{c},"bad"),"RED_ORIGINAL_DRIFT")
negative(lambda:m.check_diff(base,base,set(),{c},"bad"),"RED_ROUTE_DIFF")
negative(lambda:m.check_diff(base,{**valid,c:("BadClass",b"ui=true")},set(),{c},"bad"),"RED_NEW_CLASS")
print("GQ8_REAL63_CROSSLANE_NO_UNAUTHORIZED_LEGACY_EDIT_MUTATIONS_PASS")
