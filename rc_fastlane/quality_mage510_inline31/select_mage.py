#!/usr/bin/env python3
"""Reuse original PR #510 MAGE healer exact-author patch inside existing RC31 Combat."""
import argparse,copy,hashlib,importlib.util,json,sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_shield_cleanup_20261117"))
from select_shield import mapping
FEATURE="GQ510_MAGE_TEAM_AI_WALL_LOS_20261117"
NAME="EGGRUMBLE_SevenRoleCombat"
ORIGINAL_BLOB="86d757b83057bc370ce8b51c459420af462e86eb"
FILE="EGGRUMBLE_SevenRoleCombat_GQ510_MAGE.luau"
RECEIPT="GQ510_MAGE_RC31_RECEIPT.json"
def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def load(path):
 if blob(path.read_bytes())!=ORIGINAL_BLOB:raise ValueError("RED_GQ510_AUTHOR_CHANGED")
 spec=importlib.util.spec_from_file_location("gq510_exact_author",path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m
def project(path):
 obj,files,_=mapping(path)
 keys=[key for key in files if key[-1]==NAME]
 if len(keys)!=1:raise ValueError("RED_GQ510_COMBAT_AUTHORITY")
 return obj,files,keys[0]
def undo(code,author):
 for new,old in [(author.BOT_HEAL,author.BOT_TAIL),(author.NEW_RANGE,author.OLD_RANGE),(author.NEW_GUARD,author.OLD_GUARD)]:
  if code.count(new)!=1:raise ValueError("RED_GQ510_INVERSE_ANCHOR")
  code=code.replace(new,old,1)
 return code
def patch(code,author):
 if author.NEW_GUARD in code:raise ValueError("RED_GQ510_DOUBLE_APPLY")
 new=author.patch(code)
 if undo(new,author)!=code:raise ValueError("RED_GQ510_INVERSE")
 begin="local function healAllies(";end="\nend\n-- Status effects"
 if code.count(begin)!=1 or code.count(end)!=1 or new.count(begin)!=1 or new.count(end)!=1:
  raise ValueError("RED_GQ510_FUNC_ANCHOR")
 if code.split(begin)[0]!=new.split(begin)[0] or code.split(end,1)[1]!=new.split(end,1)[1]:
  raise ValueError("RED_GQ510_NONHEAL_CHANGE")
 return new
def prepare(base,out,author):
 if out.exists() or base.parent!=out.parent:raise ValueError("RED_GQ510_OUTPUT_COLLISION")
 obj,files,key=project(base)
 before=files[key].read_text();after=patch(before,author)
 output=out.parent/FILE
 if output.exists():raise ValueError("RED_GQ510_SOURCE_COLLISION")
 output.write_text(after)
 selected=copy.deepcopy(obj);cursor=selected["tree"]
 for k in key:cursor=cursor[k]
 cursor["$path"]=FILE
 out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n")
 _,later,newkey=project(out)
 if key!=newkey or [k for k in files if files[k].read_bytes()!=later[k].read_bytes()]!=[key]:
  raise ValueError("RED_GQ510_OTHER30")
 rec={"feature_id":FEATURE,"original_pr":510,"original_head":"0338bd13f9d3d199972bd4cd30e467443083dffa",
      "original_author_git_blob":ORIGINAL_BLOB,"source_count":31,"changed_source":NAME,
      "other30_exact":True,"off_rollback_exact":True,"new_game_remote_store":0,
      "before_sha256":hashlib.sha256(before.encode()).hexdigest(),
      "after_sha256":hashlib.sha256(after.encode()).hexdigest(),
      "native":"PENDING","rojo":"PENDING","studio_android_fun_owner":"NOT_TESTED"}
 (out.parent/RECEIPT).write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n")
 print("GQ510_SELECTED_ONE_EXISTING_COMBAT_OTHER30_EXACT_OFF_PASS")
def native(p,author,rules,out,original,wall,ai):
 _,files,key=project(p);new=files[key].read_text();old=undo(new,author)
 if blob(rules.read_bytes())!="27da5ca1e9e6d9a7afe0674030e387f094ee7492":raise ValueError("RED_GQ510_TEAM_ROSTER_BLOB")
 raw=rules.read_text()
 out.write_text(author.harness(new,fixed=True,rules=raw))
 original.write_text(author.harness(old,fixed=False,rules=raw))
 if new.count(author.NEW_RANGE)!=1 or new.count(author.BOT_HEAL)!=1:raise ValueError("RED_GQ510_MUTANT")
 wall.write_text(author.harness(new.replace(author.NEW_RANGE,author.OLD_RANGE,1),fixed=True,rules=raw))
 ai.write_text(author.harness(new.replace(author.BOT_HEAL,author.BOT_TAIL,1),fixed=True,rules=raw))
 print("GQ510_NATIVE_CURRENT_AUTHOR_FIXED_ORIGINAL_WALL_AI_MUTANTS_CREATED")
def verify(base,out,place,author):
 _,older,key=project(base);_,newer,otherkey=project(out)
 if key!=otherkey or len(newer)!=31 or set(older)!=set(newer):raise ValueError("RED_GQ510_BAD31")
 old=older[key].read_text();new=newer[key].read_text()
 if patch(old,author)!=new or undo(new,author)!=old:raise ValueError("RED_GQ510_DIFF")
 if [k for k in older if older[k].read_bytes()!=newer[k].read_bytes()]!=[key]:raise ValueError("RED_GQ510_30")
 actual={}
 for item in ET.parse(place).getroot().iter("Item"):
  cls=item.get("class")
  if cls not in ("Script","LocalScript","ModuleScript"):continue
  p=item.find("Properties")
  if p is None:raise ValueError("RED_GQ510_XML_PROPS")
  name=p.findtext("string[@name='Name']")
  src=p.findtext("ProtectedString[@name='Source']")
  if src is None:src=p.findtext("string[@name='Source']")
  if not name or src is None or name in actual:raise ValueError("RED_GQ510_XML_NAMES")
  actual[name]=(cls,src.replace("\r\n","\n"))
 if len(actual)!=31 or set(actual)!={k[-1] for k in newer}:raise ValueError("RED_GQ510_ROJO31")
 for key,f in newer.items():
  cls="Script" if f.name.endswith(".server.luau") else ("LocalScript" if f.name.endswith(".client.luau") else "ModuleScript")
  if actual[key[-1]]!=(cls,f.read_text().replace("\r\n","\n")):
   raise ValueError("RED_GQ510_ROJO_SOURCE_CLASS "+key[-1])
 receipt=out.parent/RECEIPT;data=json.loads(receipt.read_text())
 data.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
 receipt.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
 print("GQ510_REAL_MAGE_NATIVE_ROJO31_SOURCE_CLASS_OFF_EXACT_PASS",data["place_bytes"])
def selftest(author):
 s="--!strict\nlocal function lineClear(source:Vector3,to:Vector3,first:Model,second:Model):boolean\nend\n"+author.OLD_GUARD+"\n"+author.OLD_RANGE+author.BOT_TAIL
 after=patch(s,author)
 assert undo(after,author)==s
 for bad in (s.replace(author.OLD_GUARD,"bad"),s.replace(author.OLD_RANGE,"bad"),s.replace(author.BOT_TAIL,"bad")):
  try:patch(bad,author)
  except (ValueError,AssertionError):pass
  else:raise ValueError("RED_GQ510_BAD_SOURCE_ACCEPTED")
 try:patch(after,author)
 except (ValueError,AssertionError):pass
 else:raise ValueError("RED_GQ510_DUPLICATE")
 print("GQ510_AUTHOR_PATCH_OFF_NEGATIVE_4_PASS")
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("command",choices=["selftest","prepare","native","verify"])
 for arg in ("base","out","project","place","author","rules","original","wall","ai"):ap.add_argument("--"+arg,type=Path,required=(arg=="author"))
 a=ap.parse_args();author=load(a.author)
 if a.command=="selftest":selftest(author)
 elif a.command=="prepare":prepare(a.base,a.out,author)
 elif a.command=="native":native(a.project,author,a.rules,a.out,a.original,a.wall,a.ai)
 else:verify(a.base,a.out,a.place,author)
