#!/usr/bin/env python3
"""GQ595 source-select ONE original AttackGeometry into actual current RC31 project.

Use original author #482 source and GQ595 immutable tested fix only.
The other 30 selected scripts remain byte-exact. Real Rojo must match all31.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path
from importlib.machinery import SourceFileLoader
import xml.etree.ElementTree as ET

ROUTE=("ServerScriptService","EGGRUMBLE_AttackGeometry")
ORIGINAL_BLOB="a47b1d803ed9bb80c27a8ac86e6bad74a337aa79"
PATCH_HEAD="eb204b9962c0d10ec937b8886d0923e6e09fb47d"
COUNT=31

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def git_blob(b:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()

def mapping(p:Path):
 module=SourceFileLoader("gq595_current_map","rc_fastlane/quality_ko508_rc31/select_original508_neutral_ko.py").load_module()
 return module.mapping(p)

def original_patch():
 path=Path("_gq595_original/quality_gameplay/v3_vertical_hit_fairness_20261116/select_vertical.py")
 return SourceFileLoader("gq595_author_patch",str(path.resolve(strict=True))).load_module()

def prepare(base:Path,out:Path):
 base=base.resolve(strict=True)
 if base==out.resolve() or out.parent.resolve()!=base.parent.resolve() or out.exists():
  raise ValueError("RED: new sibling project required (no inplace changes)")
 obj,before=mapping(base)
 if len(before)!=COUNT or ROUTE not in before:
  raise ValueError("RED: not 31 current canonical scripts")
 raw=before[ROUTE].read_bytes()
 if git_blob(raw)!=ORIGINAL_BLOB:
  raise ValueError("RED: current selected Geometry not original #482 Git blob")
 author=original_patch()
 if author.ORIGINAL_BLOB!=ORIGINAL_BLOB:
  raise ValueError("RED: immutable original author drift")
 selected=author.apply(raw.decode("utf-8")).encode("utf-8")
 new_geom=out.parent/"GQ595_ORIGINAL_VERTICAL_GEOMETRY_SELECTED.luau"
 if new_geom.exists():raise ValueError("RED: refuse overwrite of selected geometry")
 new_geom.write_bytes(selected)
 project=copy.deepcopy(obj)
 project["tree"]["ServerScriptService"][ROUTE[-1]]["$path"]=new_geom.name
 out.write_text(json.dumps(project,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 _,after=mapping(out)
 changed=[k for k in before if before[k].read_bytes()!=after[k].read_bytes()]
 if len(after)!=COUNT or set(before)!=set(after) or changed!=[ROUTE]:
  raise ValueError("RED: other 30 gameplay sources changed")
 if after[ROUTE].read_bytes()!=selected or selected.decode().replace(author.SELECTED,author.ANCHOR,1).encode()!=raw:
  raise ValueError("RED: original author source / inverse rollback mismatch")
 receipt={"status":"PREMERGE_NOT_FORMAL_RC","source_count":COUNT,
    "only_changed_script":"/".join(ROUTE),"other_30_byte_identical":True,
    "rollback_to_current_rc_byte_exact":True,"author_source_git_blob":ORIGINAL_BLOB,
    "source_author_pr":"#595","author_candidate_immutable_head":PATCH_HEAD,
    "source_original_sha256":sha(raw),"source_selected_sha256":sha(selected),
    "studio_android_fun_owner":"NOT_TESTED","formal_rc_adopted":False}
 (out.parent/"GQ595_RC31_RECEIPT.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
 print("GQ595_ONE_ORIGINAL_GEOMETRY_SELECTED_OTHER30_BYTE_EXACT_OFF_REVERSIBLE")

def verify(base:Path,out:Path,place:Path):
 _,before=mapping(base.resolve(strict=True))
 _,after=mapping(out.resolve(strict=True))
 author=original_patch()
 expected=author.apply(before[ROUTE].read_text(encoding="utf-8"))
 if len(after)!=COUNT or set(before)!=set(after) or after[ROUTE].read_text(encoding="utf-8")!=expected:
  raise ValueError("RED: exact original author source not selected")
 changed=[k for k in before if before[k].read_bytes()!=after[k].read_bytes()]
 if changed!=[ROUTE]:raise ValueError("RED: other script mutation")
 found={}
 for item in ET.parse(place).iter("Item"):
  cls=item.get("class")
  if cls not in ("Script","ModuleScript","LocalScript"): continue
  props=item.find("Properties")
  if props is None:raise ValueError("RED: Script properties missing")
  name=props.findtext("string[@name='Name']")
  text=props.findtext("ProtectedString[@name='Source']")
  if text is None:text=props.findtext("string[@name='Source']")
  if not name or text is None or name in found:raise ValueError("RED: invalid duplicate script")
  found[name]=(cls,text.replace("\r\n","\n"))
 if len(found)!=COUNT or set(found)!={key[-1] for key in after}:raise ValueError("RED: not 31 real Rojo scripts")
 for key,path in after.items():
  cls=("Script" if path.name.endswith(".server.luau") else
       "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
  if found[key[-1]]!=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")):
   raise ValueError("RED: actual Rojo class/source mismatch "+key[-1])
 receipt=out.parent/"GQ595_RC31_RECEIPT.json"
 doc=json.loads(receipt.read_text(encoding="utf-8"))
 doc.update({"real_rojo_script_class_source_exact":"31/31",
  "place_bytes":place.stat().st_size,"place_sha256":sha(place.read_bytes())})
 receipt.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n")
 print("GQ595_FULL31_REAL_ROJO_SOURCE_CLASS_EXACT",doc["place_bytes"],doc["place_sha256"])

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("action",choices=("prepare","verify"))
 p.add_argument("--base",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--place",type=Path)
 a=p.parse_args()
 if a.action=="prepare":prepare(a.base,a.out)
 else:
  if a.place is None:p.error("--place required")
  verify(a.base,a.out,a.place)
