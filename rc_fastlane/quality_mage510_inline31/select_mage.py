#!/usr/bin/env python3
"""GQ510 Native audit: source already contains original #510 healer; NEVER patch again."""
import argparse,copy,hashlib,importlib.util,json,sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_shield_cleanup_20261117"))
from select_shield import mapping
FEATURE="GQ510_MAGE_TEAM_AI_WALL_LOS_20261117"
NAME="EGGRUMBLE_SevenRoleCombat"
AUTHOR_BLOB="86d757b83057bc370ce8b51c459420af462e86eb"
ORIGINAL_BLOB="66e666418b7c23d41f87faa5d61eb6e2770a463e"
RULES_BLOB="27da5ca1e9e6d9a7afe0674030e387f094ee7492"
RECEIPT="GQ510_MAGE_RC31_RECEIPT.json"
def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def author_at(path):
 if blob(path.read_bytes())!=AUTHOR_BLOB:raise ValueError("RED_GQ510_AUTHOR_BLOB")
 spec=importlib.util.spec_from_file_location("gq510_original_author",str(path))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def project(path):
 obj,files,_=mapping(path);keys=[key for key in files if key[-1]==NAME]
 if len(files)!=31 or len(keys)!=1:raise ValueError("RED_GQ510_AUTHORITY")
 return obj,files,keys[0]
def check(src,author):
 anchors=(author.NEW_GUARD,author.NEW_RANGE,author.BOT_HEAL,
          "local function lineClear(", "local function healAllies(")
 for anchor in anchors:
  if src.count(anchor)!=1:raise ValueError("RED_GQ510_MAGE_EXISTING_SOURCE_MISSING "+anchor[:40])
 if author.OLD_GUARD in src or author.OLD_RANGE in src:
  raise ValueError("RED_GQ510_UNSAFE_OLD_HEAL_PRESENT")
 return True
def prepare(base,out,author):
 if out.exists() or base.parent!=out.parent:raise ValueError("RED_GQ510_OUTPUT")
 obj,files,key=project(base)
 check(files[key].read_text(encoding="utf-8"),author)
 out.write_text(json.dumps(copy.deepcopy(obj),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,selected,selkey=project(out)
 if selkey!=key or set(files)!=set(selected) or any(files[k].read_bytes()!=selected[k].read_bytes() for k in files):
  raise ValueError("RED_GQ510_SOURCE_NOT_EXACT")
 src=files[key].read_bytes()
 rec={"feature_id":FEATURE,"original_pr":510,"original_author_head":"0338bd13f9d3d199972bd4cd30e467443083dffa",
      "source_count":31,"changed_source":None,"new_game_script_source_count":0,
      "all31_byte_exact":True,"other30_exact":True,"off_rollback_exact":True,
      "new_game_remote_store":0,"source_sha256":hashlib.sha256(src).hexdigest(),
      "existing_feature_confirmed_from_original_author":True,"native":"PENDING","rojo":"PENDING",
      "studio_android_fun_owner":"NOT_TESTED"}
 (out.parent/RECEIPT).write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("GQ510_EXISTING_AUTHOR_MAGE_31_SOURCES_ALL_BYTE_IDENTICAL_NO_NEW_GAME_CODE")
def native(p,author,rules,orig,out,original,wall,ai):
 _,files,key=project(p)
 current=files[key].read_text(encoding="utf-8")
 check(current,author)
 if blob(rules.read_bytes())!=RULES_BLOB or blob(orig.read_bytes())!=ORIGINAL_BLOB:
  raise ValueError("RED_GQ510_ORIGINAL_RULES_OR_COMBAT_DRIFT")
 rules_text=rules.read_text(encoding="utf-8")
 # Reuse the exact #535/current-match helper already present in current Combat.
 # Original author #510 native harness predates the official later membership overlay.
 prefix="local function currentHumanMember(session:any,player:Player):boolean"
 if current.count(prefix)!=1:raise ValueError("RED_GQ510_MEMBERSHIP_HELPER_NOT_UNIQUE")
 helper=prefix+current.split(prefix,1)[1].split("\nend\n",1)[0]+"\nend\n"
 if "currentHumanMember(session,other)" not in current:raise ValueError("RED_GQ510_REAL_SELECTED_MEMBERSHIP_MISSING")
 def with_selected_guard(text):
  marker="local function healAllies("
  if text.count(marker)!=1:raise ValueError("RED_GQ510_NATIVE_HEAL_SCOPE")
  text=text.replace(marker,helper+marker,1)
  anchor='local session={mode="TEAM",rules={castles=castles}}'
  if text.count(anchor)!=1:raise ValueError("RED_GQ510_NATIVE_CURRENT_SESSION_FIXTURE")
  text=text.replace(anchor,anchor+'\nsession.isCurrentHuman=function(player)\n return player==source or player==ally or player==enemy or player==far\nend',1)
  return text
 out.write_text(with_selected_guard(author.harness(current,fixed=True,rules=rules_text)),encoding="utf-8")
 original.write_text(author.harness(orig.read_text(encoding="utf-8"),fixed=False,rules=rules_text),encoding="utf-8")
 wall.write_text(with_selected_guard(author.harness(current.replace(author.NEW_RANGE,author.OLD_RANGE,1),fixed=True,rules=rules_text)),encoding="utf-8")
 ai.write_text(with_selected_guard(author.harness(current.replace(author.BOT_HEAL,author.BOT_TAIL,1),fixed=True,rules=rules_text)),encoding="utf-8")
 print("GQ510_ACTUAL_SELECTED_EXISTING_COMBAT_NATIVE_PLUS_2_MUTANTS_GENERATED")
def scripts_xml(place):
 found={}
 for node in ET.parse(place).getroot().iter("Item"):
  cls=node.get("class")
  if cls not in ("Script","LocalScript","ModuleScript"):continue
  prop=node.find("Properties")
  if prop is None:raise ValueError("RED_GQ510_XML_PROPS")
  name=prop.findtext("string[@name='Name']")
  src=prop.findtext("ProtectedString[@name='Source']")
  if src is None:src=prop.findtext("string[@name='Source']")
  if not name or src is None or name in found:raise ValueError("RED_GQ510_XML_NAMES")
  found[name]=(cls,src.replace("\r\n","\n"))
 return found
def verify(base,out,place,baseplace,author):
 _,old,key=project(base);_,new,newkey=project(out)
 if key!=newkey or set(old)!=set(new) or any(old[k].read_bytes()!=new[k].read_bytes() for k in old):
  raise ValueError("RED_GQ510_SOURCE_NOT_EXACT")
 check(new[key].read_text(encoding="utf-8"),author)
 if place.read_bytes()!=baseplace.read_bytes():raise ValueError("RED_GQ510_NO_OP_PLACE_PARITY")
 found=scripts_xml(place)
 if len(found)!=31 or set(found)!={k[-1] for k in new}:raise ValueError("RED_GQ510_ROJO31")
 for route,path in new.items():
  cls="Script" if path.name.endswith(".server.luau") else ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
  if found[route[-1]]!=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")):
   raise ValueError("RED_GQ510_ROJO_SOURCE_CLASS "+route[-1])
 receipt=out.parent/RECEIPT;data=json.loads(receipt.read_text())
 data.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
             place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
 receipt.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
 print("GQ510_EXISTING_MAGE_REAL_SOURCE_NATIVE_ROJO31_ZERO_DELTA_PASS",data["place_bytes"])
def selftest(author):
 old="--!strict\nlocal function lineClear(source:Vector3,to:Vector3,first:Model,second:Model):boolean\nend\n"+author.OLD_GUARD+"\n"+author.OLD_RANGE+author.BOT_TAIL
 patched=author.patch(old)
 assert check(patched,author)
 for broken in (patched.replace(author.NEW_GUARD,"BAD",1),patched.replace(author.NEW_RANGE,"BAD",1),patched.replace(author.BOT_HEAL,"BAD",1)):
  try:check(broken,author)
  except ValueError:pass
  else:raise ValueError("RED_GQ510_NEGATIVE_ACCEPTED")
 print("GQ510_EXISTING_AUTHOR_NATIVE_EVIDENCE_NEGATIVE_3_PASS")
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("command",choices=["selftest","prepare","native","verify"])
 for name in ("base","out","project","place","baseplace","author","rules","orig","original","wall","ai"):ap.add_argument("--"+name,type=Path,required=(name=="author"))
 a=ap.parse_args();author=author_at(a.author)
 if a.command=="selftest":selftest(author)
 elif a.command=="prepare":prepare(a.base,a.out,author)
 elif a.command=="native":native(a.project,author,a.rules,a.orig,a.out,a.original,a.wall,a.ai)
 else:verify(a.base,a.out,a.place,a.baseplace,author)
