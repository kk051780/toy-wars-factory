#!/usr/bin/env python3
"""GQ470 FB015 original REAL69 selected StageTileVisualRenderer material A patch."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE="ServerScriptService/GQ802_StageTileVisualRenderer"
OLD_SHA="e5b28bc8c418b93e1d5fdea2d047962aebcb6ea11dfa1dc6e96064b6a77e173a"
MARK="-- GQ470_FB015_STAGE_MATERIALS_REAL69_20261121"
OFF="OFF69_STAGE_MATERIALS"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
ANCHOR="function M.render(world,originalFloor,manifest,stagePolicy,blueprint)\n"
OLD="    p.Material=Enum.Material.SmoothPlastic\n    p.Shape=SHAPES[spec.shape]"
NEW="    p.Material=tileMaterial(tile.theme,spec.name)\n    p.Shape=SHAPES[spec.shape]"
MATERIALS="""-- GQ470_FB015_STAGE_MATERIALS_REAL69_20261121
-- Theme-sensitive low-glare materials with ZERO new objects. Readability remains
-- from existing colors, shape, and non-colliding monuments and trail markers.
local THEME_FINISHES={
 REGAL={Enum.Material.Slate,Enum.Material.Marble,Enum.Material.Metal},
 COSMOS={Enum.Material.Slate,Enum.Material.Granite,Enum.Material.Metal},
 TIME={Enum.Material.Concrete,Enum.Material.Marble,Enum.Material.Metal},
 DREAM={Enum.Material.Marble,Enum.Material.SmoothPlastic,Enum.Material.Marble},
 HEAVEN={Enum.Material.Marble,Enum.Material.Concrete,Enum.Material.Marble},
 SKY={Enum.Material.Concrete,Enum.Material.Metal,Enum.Material.Metal},
 ICE={Enum.Material.Slate,Enum.Material.Marble,Enum.Material.Marble},
 UNDERWORLD={Enum.Material.Slate,Enum.Material.Granite,Enum.Material.Granite},
 FOREST={Enum.Material.Grass,Enum.Material.WoodPlanks,Enum.Material.Slate},
 SEA={Enum.Material.Sand,Enum.Material.Slate,Enum.Material.Marble},
}
local function tileMaterial(theme:string,partName:string):Enum.Material
 local set=THEME_FINISHES[theme]
 if not set then error("RED_UNKNOWN_STAGE_MATERIAL_THEME") end
 if partName=="TileFloorArt" then return set[1] end
 if partName=="RelicPedestal" then return set[2] end
 if partName=="RelicMonument" then return set[3] end
 if partName=="LeftTrailMark" or partName=="RightTrailMark"
    or partName=="ThemeBeacon" then return Enum.Material.SmoothPlastic end
 error("RED_UNKNOWN_STAGE_VISUAL_PART")
end

"""

def sha(b):
 return hashlib.sha256(b).hexdigest()

def check(ok,reason):
 if not ok:
  raise ValueError("RED_GQ470_STAGE_"+reason)

def selected(root):
 base=root/"sources"
 return {canonical_route(p.relative_to(base).as_posix()[:-5]):p for p in base.rglob("*.luau")}

def canonical_route(route):
 for suffix in (".server",".client"):
  if route.endswith(suffix): return route[:-len(suffix)]
 return route

def transform(text):
 check(MARK not in text,"SECOND_APPLICATION")
 check(text.count(ANCHOR)==1 and text.count(OLD)==1,"ORIGINAL_ANCHORS")
 changed=text.replace(ANCHOR,MATERIALS+ANCHOR,1).replace(OLD,NEW,1)
 check(changed.count(MARK)==1 and changed.count(NEW)==1,"MATERIAL_PATCH")
 for guard in ("plan.partCount>42","p.CanCollide=false","p.CanTouch=false",
  "p.CanQuery=false","p.CastShadow=false","p.Transparency=spec.transparency",
  "p.Color=Color3.fromRGB","p.CFrame=originalFloor.CFrame",
  "made~=plan.partCount","function M.clear(world)"):
  check(text.count(guard)==changed.count(guard) and guard in changed,"NONVISUAL_GUARD")
 for token in ("Instance.new","RemoteEvent","TakeDamage","DataStore"):
  check(text.count(token)==changed.count(token),"NEW_RUNTIME_OR_AUTHORITY")
 return changed

def validate_design(blueprint_text,manifest_text):
 # Certified render budget is a CAP of 42; actual six tiles x six details = 36.
 check("M.MAX_PARTS=42" in blueprint_text and "M.CELL_COUNT=6" in blueprint_text,
       "BLUEPRINT_BUDGET_OR_CELLS")
 details=blueprint_text.split("local details={",1)
 check(len(details)==2,"BLUEPRINT_DETAILS_MISSING")
 six=details[1].split("\\n  }",1)[0]
 check(len(re.findall(r'\\bpart\\("',six))==6,"SIX_DETAILS_PER_CELL")
 check("plan.partCount+=#details" in blueprint_text,"SOURCE_BUDGET_COUNTS")
 themes=set(re.findall(r'\\{"[A-Z0-9_]+","([A-Z]+)"',manifest_text))
 candidate=set(re.findall(r'(?m)^ ([A-Z]+)=\\{Enum\\.Material\\.',MATERIALS))
 check(themes==candidate and len(themes)==10,"ACTUAL_MANIFEST_THEME_COVERAGE")
 check("Enum.Material.Neon" not in MATERIALS and
       "Instance.new" not in MATERIALS,"LOW_GLARE_INERT_MATERIALS")
 return {"expected_render_parts":36,"certified_cap":42,"themes":sorted(themes)}

def selftest():
 tokens="plan.partCount>42 p.CanCollide=false p.CanTouch=false p.CanQuery=false p.CastShadow=false p.Transparency=spec.transparency p.Color=Color3.fromRGB p.CFrame=originalFloor.CFrame made~=plan.partCount function M.clear(world)"
 sample=tokens+"\n"+ANCHOR+OLD
 result=transform(sample)
 check(MARK in result and OLD not in result and NEW in result,"SELFTEST")
 mutations=(sample.replace(ANCHOR,""),sample.replace(OLD,OLD+"\n"+OLD),
  sample.replace(OLD,"p.Material=Enum.Material.Neon"),result)
 for mutation in mutations:
  try: transform(mutation)
  except ValueError: pass
  else: raise AssertionError("RED_STAGE_MUTANT_NOT_CAUGHT")
 blueprint='M.MAX_PARTS=42\\nM.CELL_COUNT=6\\nlocal details={\\n'+(' part("a",nil)\\n'*6)+'  }\\nplan.partCount+=#details'
 manifest=''.join('{"PREFAB_'+str(i)+'","'+theme+'",1},' for i,theme in enumerate(
  ["REGAL","COSMOS","TIME","DREAM","HEAVEN","SKY","ICE","UNDERWORLD","FOREST","SEA"]))
 # This synthetic input exercises fail-closed contract, not real Studio evidence.
 try: validate_design(blueprint.replace("M.MAX_PARTS=42","M.MAX_PARTS=43"),manifest)
 except ValueError: pass
 else: raise AssertionError("RED_CHANGED_PART_CAP_NOT_REJECTED")
 try: validate_design(blueprint,manifest.replace('"REGAL"','"INVALID"'))
 except ValueError: pass
 else: raise AssertionError("RED_UNKNOWN_THEME_NOT_REJECTED")
 try: validate_design(blueprint.replace(' part("a",nil)\\n','',1),manifest)
 except ValueError: pass
 else: raise AssertionError("RED_FIVE_PART_BLUEPRINT_NOT_REJECTED")
 print("GQ470_STAGE_THEME_SELFTEST_7_NEGATIVES_PASS")

def apply(root):
 root=root.resolve()
 for path in (RECEIPT,"EGGRUMBLE_REAL69.project.json","EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
  check((root/path).is_file(),"MISSING_ARTIFACT_FILE")
 original_receipt=json.loads((root/RECEIPT).read_text())
 originals=selected(root)
 check(len(originals)==69 and ROUTE in originals,"ACTUAL_69")
 check(original_receipt.get("build_head")==BASE and
       original_receipt.get("canonical_build") is True,"IMMUTABLE_FORMAL_BASE")
 check(original_receipt.get("source_hashes")==
       {k:sha(p.read_bytes()) for k,p in originals.items()},"69_SOURCE_LOCK")
 design=validate_design(
  originals["ServerScriptService/GQ802_StageTileBlueprintPolicy"].read_text(),
  originals["ServerScriptService/GQ802_StageManifestPolicy"].read_text())
 check(design["expected_render_parts"]<=design["certified_cap"],"BUDGET_EXCEEDED")
 old=originals[ROUTE].read_bytes()
 check(sha(old)==OLD_SHA,"TARGET_SOURCE_HASH")
 backup=root/OFF
 check(not backup.exists(),"BACKUP_ALREADY_EXISTS")
 backup.mkdir()
 shutil.copytree(root/"sources",backup/"sources")
 for path in (RECEIPT,"EGGRUMBLE_REAL69.project.json","EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
  shutil.copy2(root/path,backup/path)
 new=transform(old.decode("utf-8")).encode("utf-8")
 originals[ROUTE].write_bytes(new)
 actual=selected(root)
 unchanged=[k for k in originals if k!=ROUTE and actual[k].read_bytes()==selected(backup)[k].read_bytes()]
 check(len(unchanged)==68 and len(actual)==69,"OTHER_68_EXACT")
 check((root/"EGGRUMBLE_REAL69.project.json").read_bytes()==
       (backup/"EGGRUMBLE_REAL69.project.json").read_bytes(),"ROUTE_CLASS_DRIFT")
 original_receipt["source_hashes"]={k:sha(p.read_bytes()) for k,p in actual.items()}
 original_receipt["gq470_stage_theme_materials"]={
  "source_only":"A_PREP_NOT_FORMAL","formal_base":BASE,"route":ROUTE,
  "original_sha256":OLD_SHA,"candidate_sha256":sha(new),
  "changed_selected":1,"unchanged_selected":68,
  "render_parts_original":36,"render_parts_candidate":36,"max_parts_cap":42,
  "extra_parts":0,"extra_scripts":0,"extra_remotes":0,
  "studio":"NOT_TESTED","android":"NOT_TESTED","human_art":"NOT_TESTED",
  "screenshots_received":0,"screenshots_required":32,"owner_accepted":False}
 (root/RECEIPT).write_text(json.dumps(original_receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 packet=root/"B220_STAGE_MATERIALS_ONE_SOURCE_ONLY_NOT_FORMAL"
 file=packet/"selected_sources"/(ROUTE+".luau")
 file.parent.mkdir(parents=True,exist_ok=True)
 file.write_bytes(new)
 (packet/"SOURCE_LOCK.json").write_text(json.dumps({
  "formal_base":BASE,"selected_route":ROUTE,"script_class":"ModuleScript",
  "original_sha256":OLD_SHA,"candidate_sha256":sha(new),
  "changed_selected":1,"untouched_selected":68,"not_official":True,
  "art_accepted":False,"owner_accepted":False},indent=2)+"\n")
 print("GQ470_STAGE_MATERIALS_REAL69_ONE_SOURCE_READY",sha(new),len(new))

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--base",type=Path)
 parser.add_argument("--self-test",action="store_true")
 args=parser.parse_args()
 if args.self_test: selftest()
 elif args.base: apply(args.base)
 else: parser.error("Require --base or --self-test")
