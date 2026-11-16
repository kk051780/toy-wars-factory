#!/usr/bin/env python3
"""Reuse #482 actual 21-script V3 place; copy sources 20/21 byte-exact and swap only boss."""
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

BOSS="EGGRUMBLE_NeutralStoneGiant.luau"
DOMAINS={
 "character":"EGGRUMBLE_SevenRoleCombat.luau",
 "field":"EGGRUMBLE_LobbyCastleModesPreview.server.luau",
 "battle":"EGGRUMBLE_AttackGeometry.luau",
 "castle":"EGGRUMBLE_CastleMatchRules.luau",
 "neutral":"EGGRUMBLE_SwarmCombat.luau",
 "item":"EGGRUMBLE_FieldItemPickups.luau",
 "lobby":"EGGRUMBLE_RoundReplay.luau",
 "balance":"EGGRUMBLE_CombatBalance.luau",
}


def sha(raw):
 return hashlib.sha256(raw).hexdigest()


def source_paths(project):
 names=[]
 def walk(tree):
  if not isinstance(tree,dict): return
  if "$path" in tree:
   names.append(tree["$path"])
   return
  for k,v in tree.items():
   if not k.startswith("$"): walk(v)
 walk(project["tree"])
 assert len(names)==21 and len(set(names))==21, "original 21 authoritative script entries required"
 assert set(DOMAINS.values()).issubset(set(names)), "must retain eight gameplay domains"
 assert names.count(BOSS)==1
 return names


def prepare(base:Path,patched:Path,out:Path):
 config=base/"EGGRUMBLE_V3_STUDIO.project.json"
 source=json.loads(config.read_text(encoding="utf-8"))
 names=source_paths(source)
 out.mkdir(parents=True,exist_ok=True)
 compared={}
 for n in names:
  original=(base/n).read_bytes()
  new=patched.read_bytes() if n==BOSS else original
  (out/n).write_bytes(new)
  compared[n]={"base_sha256":sha(original),"candidate_sha256":sha(new),"changed":new!=original}
 assert [n for n,v in compared.items() if v["changed"]]==[BOSS], "one original boss replacement only"
 (out/config.name).write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 receipt={"author_source_count":21,"candidate_source_count":21,"unchanged_originals":20,
          "changed_source":[BOSS],"eight_domains":list(DOMAINS),
          "sources":compared,"official_rc_integrated":False,
          "studio_android_owner_accepted":False}
 (out/"SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
 print("GQ_BOSS_PRIVATE21_COMPOSITION_20_OF_21_AUTHOR_EXACT_PASS")


def verify(place:Path,package:Path):
 assert place.exists() and place.stat().st_size>0
 tree=ET.parse(place).getroot()
 observed={}
 for item in tree.iter("Item"):
  cls=item.attrib.get("class")
  if cls not in ("ModuleScript","Script","LocalScript"): continue
  props=item.find("Properties")
  if props is None:continue
  name=props.findtext("string[@name='Name']")
  if not name:continue
  code=props.findtext("ProtectedString[@name='Source']")
  if code is None:code=props.findtext("string[@name='Source']")
  assert code is not None,"script without source: "+name
  assert name not in observed,"duplicate script instance "+name
  observed[name]=((code or "").replace(chr(13)+chr(10),chr(10)).encode("utf-8"),cls)
 expected=json.loads((package/"SOURCE_RECEIPT.json").read_text())
 for file in expected["sources"]:
  name=file.replace(".server.luau","").replace(".client.luau","").replace(".luau","")
  assert name in observed, "missing script "+name
  assert sha(observed[name][0])==sha((package/file).read_bytes()),"script byte mismatch "+name
 assert len(observed)==21, "private Place must contain exactly 21 script bodies"
 h=sha(place.read_bytes())
 report={"private_place_bytes":place.stat().st_size,"private_place_sha256":h,"source_exact":"21/21",
         "original_exact":"20/21","domain_presence":"8/8","official_rc":False}
 (package/"PRIVATE_PLACE_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
 print("GQ_BOSS_ROJO_REAL_PRIVATE21_SOURCE_EXACT_PASS",place.stat().st_size,h)


def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("operation",choices=["prepare","verify"])
 ap.add_argument("--base",type=Path)
 ap.add_argument("--patched",type=Path)
 ap.add_argument("--out",type=Path)
 ap.add_argument("--place",type=Path)
 ap.add_argument("--package",type=Path)
 a=ap.parse_args()
 if a.operation=="prepare":
  assert a.base and a.patched and a.out
  prepare(a.base,a.patched,a.out)
 else:
  assert a.place and a.package
  verify(a.place,a.package)


if __name__=="__main__":
 main()
