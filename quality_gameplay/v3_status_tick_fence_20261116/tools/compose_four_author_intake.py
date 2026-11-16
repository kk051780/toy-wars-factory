#!/usr/bin/env python3
"""Owner source-selective #510+#516 Combat, #489+#517 ITEM, #509 egg overlay.

Read-only original author inputs; no new game engine or protected branch write.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ITEM="EGGRUMBLE_FieldItemPickups"
RULES="EGGRUMBLE_CastleMatchRules"
COMBAT="EGGRUMBLE_SevenRoleCombat"
FENCE="EGGRUMBLE_StatusTickFence"
ITEM_BLOB="107046cb0bf81fed9e3cba1699ada31571e44a22"
RULES_BLOB="27da5ca1e9e6d9a7afe0674030e387f094ee7492"
RULES_PATCH_BLOB="ed87d70e7df94279af737871e8e439b9fc108d4f"

def blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def mapped(project):
 out={}
 def visit(n):
  for k,v in n.items():
   if k.startswith("$") or not isinstance(v,dict):continue
   if "$path" in v:
    assert set(v)=={"$path"} and k not in out
    p=(project.parent/v["$path"]).resolve(strict=True)
    cls=("Script" if p.name.endswith(".server.luau") else
         "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
    out[k]=(cls,p)
   else:visit(v)
 visit(json.loads(project.read_text())["tree"])
 assert len(out)==27 and {ITEM,RULES,COMBAT,FENCE}<=set(out)
 return out

def prep(args):
 base=args.base_project.resolve(strict=True)
 out=args.out.resolve()
 assert out!=base and out.parent.is_dir()
 previous=mapped(base)
 receipt=json.loads(args.base_receipt.read_text())
 assert receipt["script_count"]==27 and set(receipt["source_27_sha256"])==set(previous)
 for k,(_,p) in previous.items():assert sha(p.read_bytes())==receipt["source_27_sha256"][k],k
 combat=previous[COMBAT][1].read_text()
 assert "StatusTickFence.canTick(" in combat
 assert "botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)" in combat
 item_author=args.item_author.resolve(strict=True)
 item=args.item_overlay.resolve(strict=True)
 rules_author=args.rules_author.resolve(strict=True)
 rules=args.rules_overlay.resolve(strict=True)
 assert blob(item_author.read_bytes())==ITEM_BLOB
 assert blob(rules_author.read_bytes())==RULES_BLOB
 assert blob(rules.read_bytes())==RULES_PATCH_BLOB
 rules_original=rules_author.read_text()
 rules_new=rules.read_text()
 old="function M.onCarrierEliminated(m:any,id:any)\n local c=castleOf(m,id)\n"
 new="""function M.onCarrierEliminated(m:any,id:any)
 -- Late Humanoid.Died callbacks may arrive after the decisive castle fall.
 -- The terminal result is immutable: do not mint field tokens or rewrite egg
 -- ownership/score events after winner is known. Keep active death idempotent.
 if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end
 local c=castleOf(m,id)
"""
 assert rules_original.count(old)==1 and rules_new==rules_original.replace(old,new,1)
 item_original=item_author.read_text()
 item_new=item.read_text()
 left="-- GQ_HEAL_NO_WASTE_BEGIN\n"
 right="-- GQ_HEAL_NO_WASTE_END\n"
 start=item_new.index(left);end=item_new.index(right,start)+len(right)
 helper=item_new[start:end]
 call=("   -- Full-HP HEAL has no effect: preserve the 35-second shared pickup and cooldown.\n"
       "   if not healUseful(kind,hum.Health,hum.MaxHealth) then return end\n")
 assert item_new.count(helper)==1 and item_new.count(call)==1
 assert item_new.replace(helper,"",1).replace(call,"",1)==item_original
 assert 'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end' in item_new
 data=json.loads(base.read_text())
 srv=data["tree"]["ServerScriptService"]
 for key,p in ((ITEM,item),(RULES,rules)):
  assert set(srv[key])=={"$path"} and previous[key][1]!=p
  srv[key]={"$path":os.path.relpath(p,out.parent).replace(os.sep,"/")}
 data["name"]="EGGRUMBLE_GQ_510_516_517_509_UNION27_PRIVATE_NOT_RC"
 out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
 after=mapped(out)
 assert set(after)==set(previous)
 for key in previous:
  if key not in (ITEM,RULES):assert after[key]==previous[key],key
 assert after[COMBAT]==previous[COMBAT] and after[FENCE]==previous[FENCE]
 m={"status":"PRIVATE_SOURCE_CANDIDATE_NOT_OFFICIAL_RC",
  "base":"#482/484/485/487 original26, #510/#516 combined Combat +1 policy",
  "owner_lineage":["#510 MAGE (READ_ONLY)","#516 STATUS","#489 ITEM (READ_ONLY)","#517 NO_WASTE (READ_ONLY)","#509 POSTWIN (READ_ONLY)"],
  "features":["MAGE_LOS_TEAM_AI_HEAL","DOT_TARGET_FENCE","ITEM_HEAL_NO_WASTE","POSTWIN_EGG_NO_MUTATION"],
  "script_count":27,"original26_byte_identical_count":23,
  "previous27_byte_identical_count":25,
  "modified_existing_sources":[COMBAT,ITEM,RULES],"added_helper":FENCE,
  "item_original_git_blob":ITEM_BLOB,"rules_original_git_blob":RULES_BLOB,
  "rules_patch_git_blob":RULES_PATCH_BLOB,
  "source_27_sha256":{k:sha(p.read_bytes()) for k,(_,p) in sorted(after.items())},
  "original_27_sha256":receipt["source_27_sha256"],
  "official_rc_integrated":False,"studio":"NOT_TESTED","android":"NOT_TESTED","owner_accepted":False,
  "rollback":"remove Combat, ITEM, Rules overlay and status helper; use exact original #484 26 source"}
 args.receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
 print("GQ_510_516_517_509_SOURCE_SELECTIVE27_PASS unchanged_original23_of26")

def verify(args):
 proj=args.project.resolve(strict=True)
 place=args.place.resolve(strict=True)
 m=json.loads(args.receipt.read_text())
 before=mapped(proj)
 assert len(before)==27 and set(before)==set(m["source_27_sha256"])
 want={}
 for k,(cls,p) in before.items():
  raw=p.read_bytes()
  assert sha(raw)==m["source_27_sha256"][k]
  want[k]=(cls,raw.decode().replace("\r\n","\n"))
 got={}
 for e in ET.fromstring(place.read_bytes()).iter("Item"):
  cls=e.attrib.get("class")
  if cls not in {"Script","ModuleScript","LocalScript"}:continue
  props=e.find("Properties")
  assert props is not None
  name=props.findtext("string[@name='Name']")
  body=props.findtext("ProtectedString[@name='Source']")
  if body is None:body=props.findtext("string[@name='Source']")
  assert name and body is not None and name not in got
  got[name]=(cls,body.replace("\r\n","\n"))
 assert got==want,{"missing":sorted(set(want)-set(got)),"extra":sorted(set(got)-set(want)),
                  "different":sorted(k for k in set(got)&set(want) if got[k]!=want[k])}
 m.update({"same_head":os.environ.get("GITHUB_SHA","UNKNOWN"),
           "source_exact":"27/27","place_bytes":place.stat().st_size,
           "place_sha256":sha(place.read_bytes())})
 args.receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
 print("GQ_FOUR_AUTHOR_PRIVATE27_ROJO_EXACT_PASS",m["place_bytes"],m["place_sha256"])

def main():
 ap=argparse.ArgumentParser()
 sub=ap.add_subparsers(dest="cmd",required=True)
 p=sub.add_parser("prepare")
 for key in ("base-project","base-receipt","item-author","item-overlay",
             "rules-author","rules-overlay","out","receipt"):p.add_argument("--"+key,required=True,type=Path)
 p=sub.add_parser("verify")
 for key in ("project","place","receipt"):p.add_argument("--"+key,required=True,type=Path)
 x=ap.parse_args()
 (prep if x.cmd=="prepare" else verify)(x)
if __name__=="__main__":main()
