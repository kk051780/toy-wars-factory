#!/usr/bin/env python3
"""Add three source-only dynamic-world modules to real canonical Core36, no game owner rewrite."""
from __future__ import annotations
import argparse, copy, hashlib, json, os
from pathlib import Path

ADDITIONS={
  ("ServerScriptService","GQ802_StageManifestPolicy"):
     "EGGRUMBLE_StageManifestPolicy.luau",
  ("ServerScriptService","GQ802_StageTileBlueprintPolicy"):
     "EGGRUMBLE_StageTileBlueprintPolicy.luau",
  ("ServerScriptService","GQ802_StageTileVisualRenderer"):
     "EGGRUMBLE_StageTileVisualRenderer.luau",
}
UPSTREAM_GIT_BLOB="696d2312ef7408e26b03281caede7606472c155b"
REQUIRED={
 ("ServerScriptService","EGGRUMBLE_RealmBattleCore"),
 ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview"),
 ("ServerScriptService","EGGRUMBLE_SevenRoleCombat"),
 ("ServerScriptService","EGGRUMBLE_SwarmCombat"),
 ("ServerScriptService","EGGRUMBLE_NaturalRegen"),
}

def git_blob(data:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def digest(path:Path)->str:
 return hashlib.sha256(path.read_bytes()).hexdigest()

def flatten(project:Path):
 project=project.resolve(strict=True)
 model=json.loads(project.read_text("utf-8"))
 found={}
 def walk(node,prefix=()):
  for name,child in node.items():
   if name.startswith("$"):continue
   if not isinstance(child,dict):raise ValueError("RED_BAD_ROJO_NODE")
   route=prefix+(name,)
   if "$path" in child:
    if route in found:raise ValueError("RED_DUPLICATE_SCRIPT_ROUTE")
    src=(project.parent/child["$path"]).resolve(strict=True)
    found[route]=src
   else: walk(child,route)
 if not isinstance(model.get("tree"),dict):raise ValueError("RED_BAD_ROJO_PROJECT")
 walk(model["tree"])
 return model,found

def compose(core36:Path,source_dir:Path,out:Path)->Path:
 core36=core36.resolve(strict=True)
 source_dir=source_dir.resolve(strict=True)
 out=out.resolve()
 if out.exists() or out==core36:raise ValueError("RED_EXISTING_OUTPUT")
 old,files=flatten(core36)
 if len(files)!=36 or not REQUIRED.issubset(files):raise ValueError("RED_NOT_REAL_CORE36")
 if set(files)&set(ADDITIONS):raise ValueError("RED_SECOND_STAGE_AUTHORITY")
 sources={route:(source_dir/filename).resolve(strict=True)
          for route,filename in ADDITIONS.items()}
 if git_blob(sources[("ServerScriptService","GQ802_StageManifestPolicy")].read_bytes())!=UPSTREAM_GIT_BLOB:
  raise ValueError("RED_MANIFEST_AUTHOR_SOURCE_DRIFT")
 for route,p in sources.items():
  if not p.name.endswith(".luau") or p.stat().st_size<800:
   raise ValueError("RED_BAD_MODULE_SOURCE")
 old_sig={k:digest(v) for k,v in files.items()}
 new=copy.deepcopy(old)
 new["name"]="GQ802_DW_VISUAL39_PRIVATE_SOURCE_ONLY_NOT_LIVE"
 out.parent.mkdir(parents=True,exist_ok=True)
 def rebase(node,prefix=()):
  for name,child in node.items():
   if name.startswith("$"):continue
   route=prefix+(name,)
   if "$path" in child:
    child["$path"]=os.path.relpath(files[route],out.parent).replace(os.sep,"/")
   else: rebase(child,route)
 rebase(new["tree"])
 server=new["tree"].get("ServerScriptService")
 if not isinstance(server,dict):raise ValueError("RED_NO_SERVER_AUTHORITY")
 for route,p in sorted(sources.items()):
  name=route[-1]
  if name in server:raise ValueError("RED_MODULE_COLLISION")
  server[name]={"$path":os.path.relpath(p,out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,check=flatten(out)
 if len(check)!=39 or set(check)!=set(files)|set(ADDITIONS):
  raise ValueError("RED_NOT_REAL39")
 if any(digest(check[k])!=sha for k,sha in old_sig.items()):
  raise ValueError("RED_ORIGINAL_CORE36_DRIFT")
 if any(digest(check[k])!=digest(s) for k,s in sources.items()):
  raise ValueError("RED_STAGE_SOURCE_DRIFT")
 evidence={
  "schema":"GQ802_STAGE_VISUAL_REAL36_TO39_SOURCE_PREP_V1",
  "source_count":39, "real_canonical_original36":36,
  "added_modules":["/".join(k) for k in sorted(ADDITIONS)],
  "original_36_sources_exact_sha256":{"/".join(k):v for k,v in sorted(old_sig.items())},
  "gq803_policy_blob":UPSTREAM_GIT_BLOB,
  "runtime_host_hook":False,
  "actual_dynamic_walkable_route":False,
  "studio":"NOT_TESTED","android":"NOT_TESTED",
  "official_rc_adopted":False,"main_changed":False,"published":False,
  "off":"Select original exact Core36 project; official OFF31 unchanged",
 }
 out.with_suffix(".receipt.json").write_text(json.dumps(evidence,indent=2)+"\n")
 print("GQ802_STAGE_REAL36_TO39_SOURCE_EXACT_ADD_ONLY_PASS",len(files),len(check))
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--core36",type=Path,required=True)
 p.add_argument("--source-dir",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 compose(a.core36,a.source_dir,a.out)
