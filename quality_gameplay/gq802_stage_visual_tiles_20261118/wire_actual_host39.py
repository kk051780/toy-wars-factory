#!/usr/bin/env python3
"""Single existing canonical Host source overlay to call real GQ802 StageVisual renderer.
No new Host/remote/score/round loop; exact inverse proof. Isolated private source rehearsal.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os
from pathlib import Path
from compose_visual39 import flatten, digest

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
ADDITIONS={
 ("ServerScriptService","GQ802_StageManifestPolicy"),
 ("ServerScriptService","GQ802_StageTileBlueprintPolicy"),
 ("ServerScriptService","GQ802_StageTileVisualRenderer"),
}
# Existing original #482 FieldItems authority import, present in combined Core36 Host.
OLD_IMPORT='local FieldItems=require(script.Parent:WaitForChild("EGGRUMBLE_FieldItemPickups"))\n'
NEW_IMPORT=OLD_IMPORT+(
 'local GQ802StageManifest=require(script.Parent:WaitForChild("GQ802_StageManifestPolicy"))\n'
 'local GQ802StageBlueprint=require(script.Parent:WaitForChild("GQ802_StageTileBlueprintPolicy"))\n'
 'local GQ802StageVisuals=require(script.Parent:WaitForChild("GQ802_StageTileVisualRenderer"))\n'
)
OLD_BEGIN=' Rules.start(session.rules)\n'
NEW_BEGIN=(
 '  -- One trusted visual stage seed/manifest per real session, never a client Remote.\n'
 '  -- Optional visual error keeps original castles, eggs and three routes playable.\n'
 '  local visualOK,visualError=pcall(function()\n'
 '   local stageMode=if mode=="BATTLE_ROYALE" then "BR" else "TEAM"\n'
 '   local stageSeed=Random.new():NextInteger(1,2147483646)\n'
 '   local stageManifest,reason=GQ802StageManifest.build(stageSeed,stageMode,#roster)\n'
 '   if not stageManifest then error(reason or "INVALID_STAGE_SEED") end\n'
 '   local stageRoot,renderError=GQ802StageVisuals.render(session.world,floor,\n'
 '    stageManifest,GQ802StageManifest,GQ802StageBlueprint)\n'
 '   if not stageRoot then error(renderError or "NO_STAGE_VISUAL") end\n'
 '   session.GQ802StageSeed=stageSeed\n'
 '   session.GQ802StageRoot=stageRoot\n'
 '  end)\n'
 '  if not visualOK then\n'
 '   warn("[GQ802] Stage visuals OFF; legacy match kept:",visualError)\n'
 '  end\n'
 +OLD_BEGIN
)
OLD_CLOSE='  if session.world.Parent then session.world:Destroy() end\n'
NEW_CLOSE='   GQ802StageVisuals.clear(session.world)\n'+OLD_CLOSE

def patch(source:str)->str:
 if source.count('NaturalRegen.attach(session,p,role)')!=2:
  raise ValueError("RED_NOT_ACTUAL_CORE36_HOST_REGEN")
 for old,new in ((OLD_IMPORT,NEW_IMPORT),(OLD_BEGIN,NEW_BEGIN),(OLD_CLOSE,NEW_CLOSE)):
  if source.count(old)!=1 or new in source:
   raise ValueError("RED_NOT_ONE_ORIGINAL_HOST_ANCHOR:"+repr((old,source.count(old),new in source)))
  source=source.replace(old,new,1)
 return source

def inverse(modified:str)->str:
 for old,new in reversed(((OLD_IMPORT,NEW_IMPORT),(OLD_BEGIN,NEW_BEGIN),(OLD_CLOSE,NEW_CLOSE))):
  if modified.count(new)!=1:raise ValueError("RED_NOT_EXACT_HOST_INVERSE")
  modified=modified.replace(new,old,1)
 return modified

def wire(project:Path,out:Path):
 project=project.resolve(strict=True);out=out.resolve()
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 model,sources=flatten(project)
 if len(sources)!=39 or HOST not in sources or not ADDITIONS.issubset(sources):
  raise ValueError("RED_NOT_VERIFIED_REAL39_SOURCE")
 original=sources[HOST].read_text("utf-8")
 changed=patch(original)
 if inverse(changed)!=original:raise ValueError("RED_DIFFERENT_ORIGINAL_HOST")
 out.parent.mkdir(parents=True,exist_ok=True)
 host_file=out.parent/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
 host_file.write_text(changed,encoding="utf-8",newline="\n")
 composed=copy.deepcopy(model)
 composed["name"]="GQ802_WIRED39_REAL_GAME_HOST_STUDIO_ONLY_NOT_FORMAL_RC"
 def reb(node,route=()):
  for name,child in node.items():
   if name.startswith("$"):continue
   p=route+(name,)
   if "$path" in child:
    file=host_file if p==HOST else sources[p]
    child["$path"]=os.path.relpath(file,out.parent).replace(os.sep,"/")
   else: reb(child,p)
 reb(composed["tree"])
 out.write_text(json.dumps(composed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,verified=flatten(out)
 if len(verified)!=39 or set(verified)!=set(sources):
  raise ValueError("RED_LOST_OR_DUPLICATE_SCRIPTS")
 for route,file in sources.items():
  if route!=HOST and digest(verified[route])!=digest(file):
   raise ValueError("RED_UNRELATED_AUTHORITY_SOURCE_DRIFT")
 if inverse(verified[HOST].read_text("utf-8"))!=original:
  raise ValueError("RED_MALICIOUS_HOST_DIFF")
 receipt={
  "feature":"GQ802_DW_VISUAL_STAGE_HOST_HOOK_PRIVATE_20261118",
  "source_count":39,"original36_scripts_unmodified_except_one_host":35,
  "host_patch_one_original_script":True,
  "stage_modules":3,"new_remote_owner":0,"new_map_builder_owner":0,
  "one_seed_per_round":True,"new_weather_owner":False,
  "existing_castle_egg_item_authority_preserved":True,
  "actual_host_calls_visual_renderer":True,
  "studio_2client":"NOT_TESTED","android":"NOT_TESTED",
  "actual_dynamic_navigable_tiles":False,"official_rc_adopted":False,
  "rollback":"Original real Core36 Host and all 36 sources exact; OFF31 stays byte identical",
  "original_host_sha256":hashlib.sha256(original.encode()).hexdigest(),
 }
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ802_REAL39_HOST_ACTUAL_STAGE_VISUAL_RUNTIME_HOOK_SOURCE_PASS")
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--project",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 wire(a.project,a.out)
