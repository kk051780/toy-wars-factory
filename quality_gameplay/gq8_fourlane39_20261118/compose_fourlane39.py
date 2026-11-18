#!/usr/bin/env python3
"""Immutable genuine31 + previously green Realm/Regen36 + author Mage32/VFX33."""
import argparse,copy,hashlib,json,os,re
from pathlib import Path
from quality_gameplay.gq8_crosslane_20261118.compose_rehearsal36 import flatten,digest,HOST,CORE,REGEN
MAGE={("ServerScriptService","EGGRUMBLE_MageRevive")}
VFX={("ReplicatedStorage","EGGRUMBLE_ElementVisuals"),
     ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_AttributeCue")}
PIN={
 ("ServerScriptService","EGGRUMBLE_MageRevive"):"c75c2db439a5a68f2bc866ad42562fc16687849d",
 ("ReplicatedStorage","EGGRUMBLE_ElementVisuals"):"fbbd58ba563af6bc35699969ecbc4e7d7f0a1654",
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_AttributeCue"):"977671f9bbb2c42ff43d03af93b9832b62eac68f"}
MREQ='local MageRevive=require(script.Parent:WaitForChild("EGGRUMBLE_MageRevive"))'
MCALL='MageRevive.attach(session,p,role)'
RREQ='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
RCALL='NaturalRegen.attach(session,p,role)'
def blob(p):
 b=p.read_bytes()
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def strip_attach(text,req,call):
 if text.count(req)!=1 or text.count(call)!=2: raise ValueError("RED_AUTHOR_HOOK_COUNT")
 text=text.replace(req+"\n","",1)
 text,n=re.subn(r"(?m)^[ \t]*"+re.escape(call)+r"[ \t]*\n","",text)
 if n!=2:raise ValueError("RED_AUTHOR_HOOK_LINES")
 return text
def combine_host(original,regen,mage):
 if strip_attach(mage,MREQ,MCALL)!=original:raise ValueError("RED_MAGE_AUTHOR_EXTRA")
 if strip_attach(regen,RREQ,RCALL)!=original:raise ValueError("RED_REGEN_AUTHOR_EXTRA")
 if MREQ in regen or MCALL in regen:raise ValueError("RED_DUPLICATE_MAGE")
 merged=regen.replace(RREQ,RREQ+"\n"+MREQ,1)
 merged,n=re.subn(r"(?m)^([ \t]*)"+re.escape(RCALL)+r"[ \t]*$",lambda m:m.group(0)+"\n"+m.group(1)+MCALL,merged)
 if n!=2:raise ValueError("RED_HOST_REQUIRES_TWO_EQUIP")
 return merged
def compose(original31,combined36,mage32,vfx33,out):
 srcs=[Path(x).resolve(strict=True) for x in (original31,combined36,mage32,vfx33)]
 out=Path(out).resolve()
 if out.exists() or out in srcs:raise ValueError("RED_OVERWRITE")
 _,base=flatten(srcs[0]);model36,c36=flatten(srcs[1])
 _,mage=flatten(srcs[2]);_,vfx=flatten(srcs[3])
 if [len(x) for x in (base,c36,mage,vfx)]!=[31,36,32,33]:raise ValueError("RED_COUNTS")
 b=set(base)
 if set(c36)-b!=CORE|REGEN or set(mage)-b!=MAGE or set(vfx)-b!=VFX:
  raise ValueError("RED_ROUTES_OR_WRITERS")
 for route,p in base.items():
  if route!=HOST and (digest(c36[route])!=digest(p) or digest(mage[route])!=digest(p)):
   raise ValueError("RED_ORIGINAL_GAME_MUTATED")
  if digest(vfx[route])!=digest(p):raise ValueError("RED_VFX_CHANGED_GAME")
 for route,expected in PIN.items():
  if blob((mage if route in MAGE else vfx)[route])!=expected:
   raise ValueError("RED_AUTHOR_BLOB_DRIFT")
 host=combine_host(base[HOST].read_text(),c36[HOST].read_text(),mage[HOST].read_text())
 out.parent.mkdir(parents=True,exist_ok=True)
 hostfile=out.parent/"CombinedHost39.server.luau"
 if hostfile.exists():raise ValueError("RED_HOST_EXISTS")
 hostfile.write_text(host)
 doc=copy.deepcopy(model36);doc["name"]="GQ8_FOURLANE39_QA_NOT_OFFICIAL"
 def rebase(node,route=()):
  for name,v in node.items():
   if name.startswith("$"):continue
   at=route+(name,)
   if "$path" in v:
    v["$path"]=os.path.relpath(hostfile if at==HOST else c36[at],out.parent).replace(os.sep,"/")
   else:rebase(v,at)
 rebase(doc["tree"])
 for route in sorted(MAGE|VFX):
  source=(mage if route in MAGE else vfx)[route]
  node=doc["tree"]
  for part in route[:-1]:
   if part not in node:node[part]={"$className":"ReplicatedStorage"} if part=="ReplicatedStorage" else {}
   node=node[part]
  if route[-1] in node:raise ValueError("RED_ROUTE_CONFLICT")
  node[route[-1]]={"$path":os.path.relpath(source,out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n")
 _,result=flatten(out)
 if len(result)!=39 or set(result)!=b|CORE|REGEN|MAGE|VFX:raise ValueError("RED_NOT_REAL39")
 for route,actual in result.items():
  expected=hostfile if route==HOST else mage[route] if route in MAGE else vfx[route] if route in VFX else c36[route]
  if digest(actual)!=digest(expected):raise ValueError("RED_CHANGED_SOURCE")
 receipt={"profile":"REAL39_COMPOSITE","original31":31,"source_count":39,
          "real_addons":sorted("/".join(x) for x in CORE|REGEN|MAGE|VFX),
          "existing_modified":["/".join(HOST)],"other30_original_byte_exact":True,
          "original_sha256":{"/".join(k):digest(v) for k,v in base.items()},
          "author_blobs":{"/".join(k):v for k,v in PIN.items()},
          "rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
          "rollback":"Original genuine31 exact project"}
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ8_REAL_FOURLANE39_LOCK_HOST_OFF31_PREP_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for name in ("original31","combined36","mage32","vfx33","out"):
  p.add_argument("--"+name,required=True)
 a=p.parse_args()
 compose(a.original31,a.combined36,a.mage32,a.vfx33,a.out)
