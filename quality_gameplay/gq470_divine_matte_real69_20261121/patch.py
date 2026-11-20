#!/usr/bin/env python3
"""#470 REAL69 Source-locked matte WarGod mantle. One selected ModuleScript; A only."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROUTE="ServerScriptService/EGGRUMBLE_DivineMantle"
SRC="sources/ServerScriptService/EGGRUMBLE_DivineMantle.luau"
BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
LOCK="e6019aea60ac7ba214b44468302e6945093e3f73111857042982cf58451a2ef1"
MARK="GQ470_DIVINE_MANTLE_LOW_GLARE_MATTE_REAL69_20261121"
REPL={
 "local gold=Color3.fromRGB(255,214,73)":"local gold=Color3.fromRGB(224,183,110)",
 "local flame=Color3.fromRGB(246,112,52)":"local flame=Color3.fromRGB(216,123,79)",
 "p.Color=color;p.Material=Enum.Material.Neon\n p.Transparency=.35;p.CastShadow=false":
 "-- "+MARK+": matte sculpt, no oversized six neon spheres.\n p.Color=color\n p.Material=if name==\"DivineCircleBack\" then Enum.Material.Metal else Enum.Material.SmoothPlastic\n p.Transparency=.12;p.CastShadow=false",
 'ornament("DivineCircleBack",Enum.PartType.Cylinder,Vector3.new(.18,5.5,5.5),':
 'ornament("DivineCircleBack",Enum.PartType.Cylinder,Vector3.new(.18,4.2,4.2),',
 'ornament("DivineFlameLeft",Enum.PartType.Ball,Vector3.new(1.2,2.3,1),\n  CFrame.new(-1.6,1.6,.2),flame)':
 'ornament("DivineFlameLeft",Enum.PartType.Block,Vector3.new(.75,2.65,.85),\n  CFrame.new(-1.6,1.7,.2)*CFrame.Angles(0,0,math.rad(-25)),flame)',
 'ornament("DivineFlameRight",Enum.PartType.Ball,Vector3.new(1.2,2.3,1),\n  CFrame.new(1.6,1.6,.2),flame)':
 'ornament("DivineFlameRight",Enum.PartType.Block,Vector3.new(.75,2.65,.85),\n  CFrame.new(1.6,1.7,.2)*CFrame.Angles(0,0,math.rad(25)),flame)',
 'hlt.FillTransparency=.84;hlt.OutlineTransparency=.48':
 'hlt.FillTransparency=.94;hlt.OutlineTransparency=.72',
}
def digest(b):return hashlib.sha256(b).hexdigest()
def patch(b):
 if digest(b)!=LOCK:raise AssertionError("RED_SOURCE_SHA")
 s=b.decode()
 if MARK in s:raise AssertionError("RED_REPEAT")
 for old,new in REPL.items():
  if s.count(old)!=1:raise AssertionError("RED_ANCHOR_"+old[:12])
  s=s.replace(old,new,1)
 if s.count(MARK)!=1:raise AssertionError("RED_MARKER")
 if s.count("ornament(")!=b.count(b"ornament("):raise AssertionError("RED_ORNAMENT_COUNT")
 if s.count("Instance.new(")!=b.count(b"Instance.new("):raise AssertionError("RED_INSTANCE")
 for anchor in ("MAX_ACTIVE_MANTLES=8","PART_LIMIT_PER_MANTLE=6","CanCollide=false","CanQuery=false","CanTouch=false","Massless=true"):
  if anchor not in s:raise AssertionError("RED_BOUND_"+anchor)
 begin="local function clear(id:number)"
 if b.decode().split(begin,1)[1].split("function Mantle.activate",1)[0] != s.split(begin,1)[1].split("function Mantle.activate",1)[0]:
  raise AssertionError("RED_CLEANUP_SCOPE")
 return s.encode()
def selected(project):
 ret={}
 def walk(node,route=""):
  if not isinstance(node,dict):return
  if "$path" in node:ret[route]=node["$path"]
  for k,v in node.items():
   if not k.startswith("$"):walk(v,route+"/"+k if route else k)
 walk(project["tree"])
 return ret
def run(root,out):
 receipt=json.loads((root/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_text())
 paths=selected(json.loads((root/"EGGRUMBLE_REAL69.project.json").read_text()))
 assert receipt["build_head"]==BASE and receipt["canonical_build"] is True
 assert len(paths)==len(receipt["source_hashes"])==69 and paths[ROUTE]==SRC
 for route,path in paths.items():assert digest((root/path).read_bytes())==receipt["source_hashes"][route],"RED_ALL69_"+route
 assert receipt["source_hashes"][ROUTE]==LOCK
 assert not out.exists()
 shutil.copytree(root,out)
 original=(root/SRC).read_bytes();changed=patch(original)
 (out/SRC).write_bytes(changed)
 assert [k for k,p in paths.items() if (root/p).read_bytes()!=(out/p).read_bytes()]==[ROUTE]
 receipt["source_hashes"][ROUTE]=digest(changed)
 receipt["build_head"]="A_PREP_NOT_FORMAL"
 receipt["gq470_divine_matte"]={"feature":MARK,"selected_changed":1,"others_unchanged":68,"new_parts":0,
  "owner":False,"art":"ART_NO_GO","studio":"NOT_TESTED","android":"NOT_TESTED"}
 (out/"REAL69_LEGACY_INTAKE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print("SOURCE_ONLY_PATCH_PASS",digest(changed),len(changed)-len(original))
def selftest(root):
 old=(root/SRC).read_bytes();changed=patch(old)
 for bad in (old+b" ",old.replace(b"MAX_ACTIVE_MANTLES=8",b"MAX_ACTIVE_MANTLES=9"),
   old.replace(b"Enum.Material.Neon",b"Enum.Material.Metal"),changed):
  try:patch(bad)
  except AssertionError:continue
  raise AssertionError("RED_NEGATIVE_ACCEPT")
 print("PASS_4_NEGATIVES_SOURCE_ONLY")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--base",type=Path,required=True)
 p.add_argument("--output",type=Path);p.add_argument("--self-test",action="store_true")
 a=p.parse_args()
 if a.self_test:selftest(a.base)
 else:
  assert a.output is not None
  run(a.base,a.output)
