#!/usr/bin/env python3
"""GQ515: Source-select original off-arena egg recovery into existing RC31 Host.
Reuses exact immutable original #515 Drop.recover and original #482 Host hook.
Adds NO extra Luau authority: 31 existing scripts, 30 byte-identical.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
AUTHOR_HEAD="fee49d82816e65448f1b0b5803bba6fe06b17229"
AUTHOR_POLICY_BLOB="3114c469169ad667978485d5b8d0b038a2dbd4f5"
REQUIRE='local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))\n'
ORIGINAL="local landing=Vector3.new(at.X,session.groundY or at.Y,at.Z+17)"
ORIGINAL_SOURCE_ONLY='''local home=session.castleLocations[ownerId]
   local safe=DropBounds.recover(mode,root.X,root.Z,at.X,at.Z,
    home and home.X or nil,home and home.Z or nil)
   local landing=Vector3.new(safe.x,session.groundY or at.Y,safe.z+17)'''
HEADER="local DropBounds=(function()\n"
TAIL="end)()\n"

def sha(b:bytes)->str:
 return hashlib.sha256(b).hexdigest()

def blob(b:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def original_mapper():
 p=Path("rc_fastlane/select_gq538_original_result_inline.py")
 if not p.is_file():raise ValueError("RED_MISSING_CURRENT_ORIGINAL31_MAPPER")
 spec=importlib.util.spec_from_file_location("gq538_current_mapper",p.resolve())
 if not spec or not spec.loader:raise ValueError("RED_ORIGINAL31_MAPPER_LOAD")
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def source_select(host:bytes,policy:bytes)->bytes:
 if blob(policy)!=AUTHOR_POLICY_BLOB:
  raise ValueError("RED_ORIGINAL_GQ515_LUA_BLOB_CHANGED")
 text=policy.decode("utf-8")
 if not text.startswith("--!strict\n") or not text.rstrip().endswith("return Drop") or text.count("function Drop.recover(")!=1 or text.count("local Drop={}")!=1:
  raise ValueError("RED_GQ515_POLICY_STRUCTURE_CHANGED")
 body=text[len("--!strict\n"):].rstrip()+"\n"
 inline=HEADER+body+TAIL
 host_text=host.decode("utf-8")
 for name,needle in [("ORIGINAL_RULES_REQUIRE",REQUIRE),("AUTHOR_DROP_POSITION",ORIGINAL),("ORIGINAL_DROP_HANDLER","session.dropCarrierEggs=function(ownerId:string,at:Vector3):number")]:
  if host_text.count(needle)!=1:raise ValueError(f"RED_GQ515_STALE_OR_MULTI_{name}:{host_text.count(needle)}")
 if "DropBounds.recover(" in host_text or "local DropBounds=" in host_text or "EGGRUMBLE_FieldEggDropBounds" in host_text:
  raise ValueError("RED_GQ515_ALREADY_SELECTED")
 updated=host_text.replace(REQUIRE,REQUIRE+inline,1).replace(ORIGINAL,ORIGINAL_SOURCE_ONLY,1)
 if updated.count("function Drop.recover(")!=1 or updated.count("DropBounds.recover(")!=1:
  raise ValueError("RED_GQ515_MULTIPLE_DROP_AUTHORITIES")
 if updated.count("Rules.onCarrierEliminated(")!=host_text.count("Rules.onCarrierEliminated("):
  raise ValueError("RED_GQ515_EGG_COUNT_AUTHORITY_DRIFT")
 if updated.count("session.releaseEggs(")!=host_text.count("session.releaseEggs("):
  raise ValueError("RED_GQ515_PHYSICAL_TOKEN_AUTHORITY_DRIFT")
 if updated.replace(REQUIRE+inline,REQUIRE,1).replace(ORIGINAL_SOURCE_ONLY,ORIGINAL,1)!=host_text:
  raise ValueError("RED_GQ515_REVERSE_NOT_BYTE_EXACT")
 return updated.encode("utf-8")

def staged_project(base:Path,author:Path,out:Path):
 mapper=original_mapper()
 data,sources=mapper.scan(base)
 if len(sources)!=31 or HOST not in sources:raise ValueError("RED_CURRENT_OFFICIAL_31_UNEXPECTED")
 src=sources[HOST].read_bytes()
 patched=source_select(src,author.read_bytes())
 out=out.resolve()
 if out in (base.resolve(),base.parent.resolve()):raise ValueError("RED_IN_PLACE_WRITE")
 out.mkdir(parents=True,exist_ok=True)
 dest=out/"EGGRUMBLE_LobbyCastleModesPreview_515.server.luau"
 if dest.resolve()==sources[HOST].resolve():raise ValueError("RED_AUTHOR_HOST_OVERWRITE")
 dest.write_bytes(patched)
 project=json.loads(json.dumps(data))
 def rebase(node,path=()):
  for name,child in node.items():
   if name.startswith("$"):continue
   if not isinstance(child,dict):raise ValueError("RED_NON_SCRIPT_PROJECT_CHILD")
   key=path+(name,)
   if "$path" in child:
    if key not in sources or set(child)!={"$path"}:raise ValueError("RED_CURRENT_PROJECT_OWNERSHIP_CHANGED")
    target=dest if key==HOST else sources[key]
    child["$path"]=os.path.relpath(target,out).replace(os.sep,"/")
   else:rebase(child,key)
 rebase(project["tree"])
 project["name"]="EGGRUMBLE_GQ515_ORIGINAL_EGG_DROP_BOUNDS_SINGLE_HOST_RC31"
 selected=out/"GQ515_SELECTED31.project.json"
 selected.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,after=mapper.scan(selected)
 if set(after)!=set(sources) or len(after)!=31:raise ValueError("RED_GQ515_NEW_SOURCE_ADDED")
 for key,path in sources.items():
  actual=after[key].read_bytes()
  if key==HOST:
   if actual!=patched:raise ValueError("RED_GQ515_HOST_PATCH_MISSING")
  elif actual!=path.read_bytes():
   raise ValueError("RED_GQ515_OTHER_SOURCE_DRIFT:"+"/".join(key))
 manifest={
  "author_original_pr":515,"author_original_sha":AUTHOR_HEAD,
  "author_policy_git_blob":AUTHOR_POLICY_BLOB,
  "source_count":31,"original_host_only_changed":True,"other_30_source_byte_exact":True,
  "original_host_sha256":sha(src),"selected_host_sha256":sha(patched),
  "source_by_name_sha256":{"/".join(k):sha(p.read_bytes()) for k,p in sorted(after.items())},
  "source_project_sha256":sha(selected.read_bytes()),
  "rollback":"restore original #508-selected Host source and remove only inlined DropBounds code/landing line",
  "official_rc_adopted":False,"studio_android_owner":"NOT_TESTED"
 }
 (out/"GQ515_SOURCE_RECEIPT.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("GQ515_REAL_ORIGINAL_DROP_BOUNDS_SELECTED31_ONE_HOST_OTHER30_BYTE_EXACT_PASS")
 return selected

def verify(base:Path,author:Path,selected:Path,place:Path):
 mapper=original_mapper()
 _,old=mapper.scan(base)
 _,new=mapper.scan(selected)
 if len(new)!=31 or set(old)!=set(new):raise ValueError("RED_GQ515_SELECTED_SCRIPT_SET_MISMATCH")
 if new[HOST].read_bytes()!=source_select(old[HOST].read_bytes(),author.read_bytes()):
  raise ValueError("RED_GQ515_SELECTED_HOST_NOT_ORIGINAL_AUTHOR")
 for key in set(old)-{HOST}:
  if old[key].read_bytes()!=new[key].read_bytes():raise ValueError("RED_GQ515_OTHER_30_SCRIPT_DRIFT")
 embedded={}
 for node in ET.fromstring(place.read_bytes()).iter("Item"):
  klass=node.attrib.get("class")
  if klass not in {"Script","LocalScript","ModuleScript"}:continue
  p=node.find("Properties")
  if p is None:raise ValueError("RED_GQ515_NO_SCRIPT_PROPERTIES")
  name=p.findtext("string[@name='Name']")
  source=p.findtext("ProtectedString[@name='Source']")
  if source is None:source=p.findtext("string[@name='Source']")
  if not name or source is None or name in embedded:raise ValueError("RED_GQ515_DUPLICATE_SCRIPT")
  embedded[name]=(klass,source.replace("\r\n","\n"))
 if len(embedded)!=31 or set(embedded)!={key[-1] for key in new}:raise ValueError("RED_GQ515_PLACE_SCRIPT_SET_MISMATCH")
 for key,path in new.items():
  kind=("Script" if path.name.endswith(".server.luau") else
        "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
  if embedded[key[-1]]!=(kind,path.read_text(encoding="utf-8").replace("\r\n","\n")):
   raise ValueError("RED_GQ515_ROJO_SOURCE_CLASS_DRIFT:"+"/".join(key))
 evidence={"rojo_source_class_exact":"31/31","other_30_scripts_byte_exact":True,
           "author_policy_git_blob":AUTHOR_POLICY_BLOB,"original_host_only":True,
           "canonical_private_place_bytes":place.stat().st_size,
           "canonical_private_place_sha256":sha(place.read_bytes()),
           "official_rc_adopted":False}
 (selected.parent/"GQ515_ROJO_RECEIPT.json").write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
 print("GQ515_REAL_ORIGINAL_EGG_BOUNDS_ROJO31_SOURCE_CLASS_EXACT_PASS",place.stat().st_size,evidence["canonical_private_place_sha256"])

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("command",choices=("prepare","verify"))
 ap.add_argument("--base",type=Path,required=True)
 ap.add_argument("--author",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 ap.add_argument("--place",type=Path)
 args=ap.parse_args()
 if args.command=="prepare":staged_project(args.base,args.author,args.out)
 else:
  if args.place is None:ap.error("--place required for verify")
  verify(args.base,args.author,args.out,args.place)
if __name__=="__main__":main()
