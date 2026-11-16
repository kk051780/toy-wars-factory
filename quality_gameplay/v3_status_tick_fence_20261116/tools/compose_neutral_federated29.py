#!/usr/bin/env python3
"""Join immutable original #494+#501 Swarm dual28 with existing #510/516/517/509 four-owner 27.

Reuses the two distinct author source-selective composers. This script ONLY
maps one original Swarm and two native policy modules into the EXISTING game
manifest, preserving all 7 role/field/combat/castle/AI/item/lobby/score sources.
No new game host, remotes, neutral spawner or official RC writes.
"""
import argparse
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

SWARM="EGGRUMBLE_SwarmCombat"
PACING="EGGRUMBLE_NeutralSpawnPacing"
FAIR="EGGRUMBLE_NeutralEncounterFairness"
COMBAT="EGGRUMBLE_SevenRoleCombat"
ITEM="EGGRUMBLE_FieldItemPickups"
RULES="EGGRUMBLE_CastleMatchRules"
STATUS="EGGRUMBLE_StatusTickFence"
OWNED={SWARM,COMBAT,ITEM,RULES}
EXTRA={PACING,FAIR,STATUS}

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def files(p):
 p=p.resolve(strict=True)
 d=json.loads(p.read_text(encoding="utf8"))
 m={}
 def walk(node,chain=()):
  for name,obj in node.items():
   if name.startswith("$") or not isinstance(obj,dict):continue
   key=chain+(name,)
   if "$path" in obj:
    assert set(obj)=={"$path"} and name not in m,(key,obj)
    m[name]=(key,(p.parent/obj["$path"]).resolve(strict=True))
   else:walk(obj,key)
 walk(d["tree"])
 return d,m

def ensure_linked(base,four,dual):
 p0,b=files(base)
 p4,f=files(four)
 p2,n=files(dual)
 assert len(b)==26 and len(f)==27 and len(n)==28
 assert set(f)==set(b)|{STATUS}
 assert set(n)==set(b)|{PACING,FAIR}
 assert all(b[x][0]==f[x][0]==n[x][0] for x in b)
 assert f[STATUS][0]==("ServerScriptService",STATUS)
 for extra in (PACING,FAIR):assert n[extra][0]==("ServerScriptService",extra)
 for k in b:
  old=sha(b[k][1])
  if k in {COMBAT,ITEM,RULES}:
   assert sha(f[k][1])!=old,(k,"four missing")
  else:
   assert sha(f[k][1])==old,(k,"four changed other owner")
  if k==SWARM:
   assert sha(n[k][1])!=old,(k,"dual missing")
  else:
   assert sha(n[k][1])==old,(k,"dual changed other owner")
 assert "StatusTickFence.canTick(" in f[COMBAT][1].read_text()
 assert "botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)" in f[COMBAT][1].read_text()
 assert "healUseful(kind,hum.Health,hum.MaxHealth)" in f[ITEM][1].read_text()
 assert 'if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end' in f[RULES][1].read_text()
 current=n[SWARM][1].read_text()
 assert current.count("SpawnPacing.step(")==1 and current.count("EncounterFair.chooseIndex(")==1
 assert current.count("local function credit(")==1
 assert 'and session.rules.castles[id].alive then' in current
 return p0,b,p4,f,p2,n

def prepare(a):
 base=a.base26.resolve(strict=True)
 four=a.four27.resolve(strict=True)
 dual=a.dual28.resolve(strict=True)
 out=a.out.resolve()
 assert not out.exists() and out.parent.is_dir()
 bobj,b,fobj,f,nobj,n=ensure_linked(base,four,dual)
 receipt4=json.loads(a.four_receipt.read_text())
 receipt2=json.loads(a.dual_receipt.read_text())
 assert receipt4["script_count"]==27
 assert receipt2["total_mapped"]==28
 assert set(receipt4["source_27_sha256"])==set(f)
 for k,(_,path) in f.items():assert sha(path)==receipt4["source_27_sha256"][k],k
 for k,(_,path) in n.items():
  assert sha(path)==receipt2["mapped_sha256"]["/".join(n[k][0])],k
 # Four-owner project is authoritative. Add only original Swarm author's
 # existing two policies and their single original SwarmCombat patch.
 obj=json.loads(four.read_text())
 srv=obj["tree"]["ServerScriptService"]
 assert set(srv[SWARM])=={"$path"} and FAIR not in srv and PACING not in srv
 selected={SWARM:n[SWARM][1],FAIR:n[FAIR][1],PACING:n[PACING][1]}
 for key,source in selected.items():
  srv[key]={"$path":os.path.relpath(source,out.parent).replace(os.sep,"/")}
 obj["name"]="EGGRUMBLE_GQ_6_OWNER29_ALL8_PRIVATE_NO_OFFICIAL_RC"
 out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
 _,final=files(out)
 assert len(final)==29 and set(final)==set(b)|EXTRA
 assert all(final[k][0]==b[k][0] for k in b)
 for key in final:
  target=selected[key] if key in selected else f[key][1]
  assert final[key][1]==target and sha(final[key][1])==sha(target),key
 originalunchanged={k for k in b if sha(final[k][1])==sha(b[k][1])}
 assert originalunchanged==set(b)-OWNED
 artifact={
  "schema":"GQ516_CURRENT_ORIGINAL29_SOURCE_SELECTIVE_V1",
  "stage":"SOURCE_PRIVATE_NOT_OFFICIAL_RC",
  "script_count":29,"source_original26":26,
  "byte_identical_original26":22,
  "replaced_original_scripts":sorted(OWNED),
  "original_owner_policy_modules":sorted(EXTRA),
  "feature_owners":{
   COMBAT:"#510+#516 exact original author repair",
   RULES:"#509 exact original author repair",
   ITEM:"#489+#517 exact original author repair",
   SWARM:"#494+#501 exact original author repair",
   STATUS:"#516 policy",
   PACING:"#494 policy",FAIR:"#501 policy"},
  "original26_sha256":{k:sha(p) for k,(_,p) in sorted(b.items())},
  "source29_sha256":{k:sha(p) for k,(_,p) in sorted(final.items())},
  "source_class29":{k:("Script" if p.name.endswith(".server.luau") else
                 "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
                 for k,(_,p) in final.items()},
  "original_unchanged_names":sorted(originalunchanged),
  "official_rc_adopted":False,
  "studio":"NOT_TESTED","android":"NOT_TESTED","art_fun":"NO_GO","owner_accepted":False,
  "rollback":"#220 source-select original 26, or revert each 4 changed scripts and 3 optional policy modules separately",
 }
 a.receipt.write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+"\n")
 print("GQ_516_ORIGINAL29_SIX_OWNER_SOURCE_SELECTIVE_22_OF_26_EXACT_PASS")

def verify(a):
 project=a.project.resolve(strict=True)
 place=a.place.resolve(strict=True)
 m=json.loads(a.receipt.read_text())
 _,mapped=files(project)
 assert len(mapped)==m["script_count"]==29
 want={}
 for key,(chain,p) in mapped.items():
  raw=p.read_bytes()
  assert sha(p)==m["source29_sha256"][key],key
  typ=m["source_class29"][key]
  want[key]=(typ,raw.decode("utf8").replace("\r\n","\n"))
 got={}
 for entry in ET.fromstring(place.read_bytes()).iter("Item"):
  typ=entry.attrib.get("class")
  if typ not in {"Script","LocalScript","ModuleScript"}:continue
  props=entry.find("Properties")
  if props is None:continue
  name=props.findtext("string[@name='Name']")
  src=props.findtext("ProtectedString[@name='Source']")
  if src is None:src=props.findtext("string[@name='Source']")
  assert name and src is not None and name not in got
  got[name]=(typ,src.replace("\r\n","\n"))
 assert want==got,{"missing":sorted(set(want)-set(got)),"extra":sorted(set(got)-set(want)),
                  "altered":sorted(x for x in set(want)&set(got) if want[x]!=got[x])}
 m["candidate_head"]=os.getenv("GITHUB_SHA","UNSET")
 m["exact_source_in_rbxlx"]="29/29"
 m["private_place_bytes"]=place.stat().st_size
 m["private_place_sha256"]=sha(place)
 a.receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
 print("GQ_516_ORIGINAL29_ROJO_SOURCE_AND_CLASS_EXACT_PASS",m["private_place_bytes"],m["private_place_sha256"])

def main():
 parser=argparse.ArgumentParser()
 sub=parser.add_subparsers(dest="command",required=True)
 p=sub.add_parser("prepare")
 for x in ("base26","four27","dual28","four-receipt","dual-receipt","out","receipt"):
  p.add_argument("--"+x,type=Path,required=True)
 v=sub.add_parser("verify")
 for x in ("project","place","receipt"):
  v.add_argument("--"+x,type=Path,required=True)
 a=parser.parse_args()
 (prepare if a.command=="prepare" else verify)(a)
if __name__=="__main__":main()
