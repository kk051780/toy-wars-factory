#!/usr/bin/env python3
"""Source-locked REAL69 castle guardian silhouette candidate. A-PREP only."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE="ServerScriptService/EGGRUMBLE_CastleGuardianRuntime"
PATH="sources/ServerScriptService/EGGRUMBLE_CastleGuardianRuntime.luau"
SOURCE_SHA="3b8cf7e9b939213633fde964d81bb5e9508e4fe467ef932ddad0bfbe270bd96b"
MARK="GQ470_CASTLE_GUARDIAN_SEVEN_SILHOUETTES_REAL69_20261121"
HEADER="local function decorate(model:Model,role:string,root:Part,c:any)"
STYLE="""-- GQ470_CASTLE_GUARDIAN_SEVEN_SILHOUETTES_REAL69_20261121
-- Live castle guardians; lobby GQ805 shop silhouettes are a separate owner.
local GUARDIAN_STYLE={
 WARRIOR={torso=Vector3.new(2.9,2.5,1.9),head=Vector3.new(1.75,1.5,1.55),
  shoulder=Vector3.new(1.05,.9,1.4),gear=Vector3.new(.62,2.9,.6),
  trim=Color3.fromRGB(183,169,140),helm=Color3.fromRGB(187,194,199),
  boots=Color3.fromRGB(71,77,85),material=Enum.Material.Metal,lean=0},
 MAGE={torso=Vector3.new(1.8,2.45,1.25),head=Vector3.new(1.3,1.9,1.25),
  shoulder=Vector3.new(.55,.55,1.0),gear=Vector3.new(.3,3.5,.3),
  trim=Color3.fromRGB(155,189,210),helm=Color3.fromRGB(199,226,230),
  boots=Color3.fromRGB(52,74,92),material=Enum.Material.SmoothPlastic,lean=0},
 NINJA={torso=Vector3.new(1.95,1.9,1.3),head=Vector3.new(1.45,1.2,1.3),
  shoulder=Vector3.new(.65,.55,.9),gear=Vector3.new(.3,2.6,.3),
  trim=Color3.fromRGB(85,72,125),helm=Color3.fromRGB(74,71,105),
  boots=Color3.fromRGB(43,46,65),material=Enum.Material.SmoothPlastic,lean=6},
 TRAPPER={torso=Vector3.new(2.05,2.25,1.45),head=Vector3.new(1.35,1.5,1.5),
  shoulder=Vector3.new(.78,.55,1.25),gear=Vector3.new(.33,2.8,.33),
  trim=Color3.fromRGB(155,115,186),helm=Color3.fromRGB(171,148,195),
  boots=Color3.fromRGB(72,55,99),material=Enum.Material.SmoothPlastic,lean=0},
 BUILDER={torso=Vector3.new(2.8,1.95,1.85),head=Vector3.new(1.65,1.2,1.55),
  shoulder=Vector3.new(.95,.77,1.3),gear=Vector3.new(.82,2.9,.82),
  trim=Color3.fromRGB(173,140,91),helm=Color3.fromRGB(184,166,124),
  boots=Color3.fromRGB(79,73,62),material=Enum.Material.Metal,lean=0},
 BEAST={torso=Vector3.new(2.4,1.85,1.7),head=Vector3.new(1.7,1.3,1.65),
  shoulder=Vector3.new(.85,.57,1.3),gear=Vector3.new(.4,2.8,.4),
  trim=Color3.fromRGB(116,142,105),helm=Color3.fromRGB(132,156,114),
  boots=Color3.fromRGB(55,74,61),material=Enum.Material.SmoothPlastic,lean=12},
 ZOMBIE={torso=Vector3.new(1.85,2.55,1.25),head=Vector3.new(1.35,1.72,1.33),
  shoulder=Vector3.new(.68,.65,1.08),gear=Vector3.new(.38,3.4,.38),
  trim=Color3.fromRGB(133,105,145),helm=Color3.fromRGB(155,138,160),
  boots=Color3.fromRGB(68,60,72),material=Enum.Material.Slate,lean=-5},
}
"""
OLD=""" local at=root.CFrame
 part(model,"ArmoredTorso",at*CFrame.new(0,2.2,0),Vector3.new(2.4,2.2,1.5),c.color)
 part(model,"Helm",at*CFrame.new(0,4,0),Vector3.new(1.6,1.5,1.45),Color3.fromRGB(232,218,176),
   Enum.PartType.Ball)
 part(model,"Visor",at*CFrame.new(0,4,-.78),Vector3.new(1.3,.25,.15),Color3.fromRGB(53,65,88))
 for _,side in ipairs({-1,1}) do
  part(model,"Pauldron",at*CFrame.new(side*1.45,2.65,0),Vector3.new(.85,.7,1.25),
   Color3.fromRGB(214,189,129),Enum.PartType.Ball)
  part(model,"Boot",at*CFrame.new(side*.62,.65,0),Vector3.new(.85,1.15,1),
   Color3.fromRGB(58,66,76))
 end
 local gear=part(model,"Signature_"..c.weapon,
    at*CFrame.new(1.95,2.25,-.7)*CFrame.Angles(0,0,math.rad(12)),
    Vector3.new(.45,3.1,.45),Color3.fromRGB(223,198,131))"""
NEW=""" local at=root.CFrame
 local v=assert(GUARDIAN_STYLE[role],"unknown guardian silhouette")
 -- Reuse existing 8 common Parts, preserve role extra parts and server combat.
 local torso=part(model,"ArmoredTorso",at*CFrame.new(0,2.2,0)
   *CFrame.Angles(math.rad(v.lean),0,0),v.torso,c.color)
 torso.Material=v.material
 part(model,"Helm",at*CFrame.new(0,4,0),v.head,v.helm,Enum.PartType.Ball)
 part(model,"Visor",at*CFrame.new(0,4,-.78),Vector3.new(1.25,.24,.17),
   Color3.fromRGB(44,54,72))
 for _,side in ipairs({-1,1}) do
  part(model,"Pauldron",at*CFrame.new(side*1.45,2.65,0),v.shoulder,v.trim,
   Enum.PartType.Ball)
  part(model,"Boot",at*CFrame.new(side*.62,.65,0),Vector3.new(.85,1.15,1),v.boots)
 end
 local gear=part(model,"Signature_"..c.weapon,
    at*CFrame.new(1.95,2.25,-.7)*CFrame.Angles(0,0,math.rad(12)),
    v.gear,Color3.fromRGB(211,189,142))"""

def digest(b):
    return hashlib.sha256(b).hexdigest()

def patch(original):
    if digest(original)!=SOURCE_SHA:
        raise ValueError("RED_ORIGINAL_SOURCE_DRIFT")
    text=original.decode("utf-8")
    if text.count(HEADER)!=1 or text.count(OLD)!=1 or MARK in text:
        raise ValueError("RED_VISUAL_ANCHOR_OR_DOUBLE_APPLY")
    if text.count("local function part(")!=1 or "MAX_GLOBAL=12" not in text:
        raise ValueError("RED_GUARDIAN_BUDGET_OR_HELPER")
    changed=text.replace(HEADER,STYLE+HEADER,1).replace(OLD,NEW,1)
    if changed.count(MARK)!=1 or changed.count("part(model,")!=text.count("part(model,"):
        raise ValueError("RED_PART_COUNT_OR_MARKER")
    tail=text.index("\nend\n",text.index(HEADER))+5
    newtail=changed.index("\nend\n",changed.index(HEADER))+5
    if text[tail:]!=changed[newtail:]:
        raise ValueError("RED_SESSION_AI_HP_SUFFIX")
    for forbidden in ("Instance.new","RemoteEvent","DataStore","Marketplace","Heartbeat","RenderStepped"):
        if forbidden in STYLE+NEW: raise ValueError("RED_VISUAL_AUTHORITY_"+forbidden)
    return changed.encode("utf-8")

def routes(project):
    selected={}
    def walk(node,route=""):
        if not isinstance(node,dict): return
        if "$path" in node:
            p=node["$path"]
            kind=node.get("$className") or ("LocalScript" if p.endswith(".client.luau") else "Script" if p.endswith(".server.luau") else "ModuleScript")
            selected[route]=(p,kind)
        for k,v in node.items():
            if not k.startswith("$"): walk(v,route+"/"+k if route else k)
    walk(project["tree"])
    return selected

def run(root,output):
    project=json.loads((root/"EGGRUMBLE_REAL69.project.json").read_text())
    receipt=json.loads((root/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_text())
    selected=routes(project)
    assert len(selected)==len(receipt["source_hashes"])==69,"RED_SELECTED_69"
    assert receipt["build_head"]==BASE and receipt["canonical_build"] is True,"RED_PINNED_FORMAL"
    assert receipt["source_hashes"][ROUTE]==SOURCE_SHA,"RED_ROUTE_RECEIPT"
    assert selected[ROUTE]==(PATH,"ModuleScript"),"RED_ROUTE_CLASS"
    for route,(path,kind) in selected.items():
        assert receipt["source_hashes"][route]==digest((root/path).read_bytes()),"RED_SOURCE_LOCK_"+route
        assert receipt["source_classes"][route]==kind,"RED_CLASS_LOCK_"+route
    assert not output.exists(),"RED_OVERWRITE"
    shutil.copytree(root,output)
    after=patch((root/PATH).read_bytes())
    (output/PATH).write_bytes(after)
    changes={r for r,(p,_) in selected.items() if (root/p).read_bytes()!=(output/p).read_bytes()}
    assert changes=={ROUTE},"RED_ONLY_ONE_SELECTED_SOURCE"
    oldreceipt=(root/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_bytes()
    receipt["source_hashes"][ROUTE]=digest(after)
    receipt["build_head"]="A_PREP_NOT_FORMAL"
    receipt["gq470_castle_guardian_seven_silhouettes"]={
      "feature":MARK,"formal_base":BASE,"changed_route":ROUTE,
      "unchanged_selected":68,"new_parts":0,"game_authority_changed":False,
      "studio":"NOT_TESTED","android15":"NOT_TESTED","human_art":"NOT_TESTED",
      "owner_accepted":False}
    (output/"REAL69_LEGACY_INTAKE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    assert (root/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_bytes()==oldreceipt,"RED_MUTATED_ORIGINAL"
    print(json.dumps({"candidate_sha256":digest(after),"source_bytes_delta":len(after)-len((root/PATH).read_bytes()),"unchanged_routes":68,"studio":"NOT_TESTED"}))

def selftest(root):
    original=(root/PATH).read_bytes()
    after=patch(original)
    for token in (b"part(model,",b"Instance.new(",b"RemoteEvent",b"TakeDamage",b"CanCollide="):
        assert original.count(token)==after.count(token),"RED_MUTATION_SCOPE"
    for bad in (after,original+b" ",original.replace(b"MAX_GLOBAL=12",b"MAX_GLOBAL=13"),
                original.replace(b"local function part(",b"local function sculpt("),
                original.replace(OLD.encode(),b""),
                original.replace(HEADER.encode(),b"local function decorate2(")):
        try: patch(bad)
        except ValueError: continue
        raise AssertionError("RED_NEGATIVE_ACCEPTED")
    print("PASS_6_NEGATIVES_AND_ONE_SOURCE_PART_BUDGET")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:selftest(a.base)
    else:
        assert a.output is not None,"RED_OUTPUT_REQUIRED"
        run(a.base,a.output)
