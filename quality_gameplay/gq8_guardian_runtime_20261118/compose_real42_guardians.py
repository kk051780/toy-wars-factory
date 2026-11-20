#!/usr/bin/env python3
"""Append one real guardian runtime to pinned, already-built REAL41 portable source.
This modifies exactly original single Host/SevenRoleCombat and current #809 SiegeBridge
in the COMPOSED private source only. No parallel Game, Remote, or Rules damage writer.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os
from pathlib import Path
H=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
C=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
G=("ServerScriptService","EGGRUMBLE_CastleSiegeBridge")
R=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
N=("ServerScriptService","EGGRUMBLE_CastleGuardianRuntime")
HERE=Path(__file__).resolve().parent
def flatten(path:Path):
 path=Path(path).resolve(strict=True)
 model=json.loads(path.read_text(encoding="utf-8"));nodes={}
 def walk(obj,key=()):
  for name,node in obj.items():
   if name.startswith("$"):continue
   route=key+(name,)
   if "$path" in node:
    if route in nodes:raise ValueError("RED_DUPLICATE_ROUTE")
    nodes[route]=(path.parent/node["$path"]).resolve(strict=True)
   else:walk(node,route)
 walk(model["tree"])
 return model,nodes
def once(s:str,old:str,new:str,label:str)->str:
 if s.count(old)!=1:raise ValueError("RED_"+label+"_COUNT_"+str(s.count(old)))
 return s.replace(old,new,1)
def compose(original:Path,out:Path):
 original=Path(original).resolve(strict=True)
 out=Path(out).resolve()
 if out.exists() or out==original:raise ValueError("RED_CLOBBER")
 model,before=flatten(original)
 if len(before)!=41 or not {H,C,G,R}.issubset(before) or N in before:
  raise ValueError("RED_NOT_REAL41_SINGULAR")
 host=before[H].read_text(encoding="utf-8")
 role=before[C].read_text(encoding="utf-8")
 bridge=before[G].read_text(encoding="utf-8")
 host=once(host,
  'local SiegeBridge=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeBridge"))',
  'local SiegeBridge=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeBridge"))\nlocal GuardianRuntime=require(script.Parent:WaitForChild("EGGRUMBLE_CastleGuardianRuntime"))',
  "HOST_REQUIRE")
 host=once(host,'session.castleSiegeAttack=SiegeBridge.attach(session,Rules)',
  'session.castleSiegeAttack=SiegeBridge.attach(session,Rules)\n session.guardians=GuardianRuntime.attach(session,chosenRole)',
  "HOST_ATTACH")
 host=once(host,"session.refresh=function()",
  "session.refresh=function()\n  if session.guardians then session.guardians.refresh() end",
  "HOST_REFRESH")
 host=once(host,'if abandoned then session.rules.phase="ABANDONED" end',
  'if abandoned then session.rules.phase="ABANDONED" end\n  if session.guardians then session.guardians.shutdown() end',
  "HOST_ROUND_CLOSE")
 role=once(role,'count+=hitBotHeroes(session,p,root,char,at,range,damage,shape)',
   'count+=hitBotHeroes(session,p,root,char,at,range,damage,shape)\n if session.guardians then count+=session.guardians.damageFromPlayer(p,at,range,damage,shape) end',
   "COMBAT_ACTUAL_SERVER_HIT")
 bridge=once(bridge,
   'for id in pairs(session.rules.castles) do states[id]=Policy.new(epoch,id) end',
   'for id in pairs(session.rules.castles) do states[id]=Policy.new(epoch,id) end\n session.castleSiegeStates=states',
   "BRIDGE_SHARE_ORIGINAL_STATE")
 out.parent.mkdir(parents=True,exist_ok=True)
 delta={H:host,C:role,G:bridge}
 writes={}
 for route,content in delta.items():
  name=route[-1]+(".server.luau" if route==H else ".luau")
  file=out.parent/name
  file.write_text(content,encoding="utf-8",newline="\n")
  writes[route]=file
 result=copy.deepcopy(model)
 result["name"]="GQ815_REAL42_EXISTING_HOST_GUARDIAN_AI_STAGED_NOT_RC"
 def relink(node,key=()):
  for name,v in node.items():
   if name.startswith("$"):continue
   route=key+(name,)
   if "$path" in v:
    v["$path"]=os.path.relpath(writes.get(route,before[route]),out.parent).replace(os.sep,"/")
   else:relink(v,route)
 relink(result["tree"])
 actor=HERE/"EGGRUMBLE_CastleGuardianRuntime.luau"
 if not actor.is_file():raise ValueError("RED_MISSING_GUARDIAN_AUTHOR_SOURCE")
 result["tree"]["ServerScriptService"][N[-1]]={
  "$path":os.path.relpath(actor,out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 _,after=flatten(out)
 if len(after)!=42 or set(after)!=set(before)|{N}:raise ValueError("RED_SOURCE42_MAP")
 for route in before:
  if route not in delta and before[route].read_bytes()!=after[route].read_bytes():
   raise ValueError("RED_OTHER_ORIGINAL_CODE_"+"/".join(route))
 for route in delta:
  if before[route].read_bytes()==after[route].read_bytes():
   raise ValueError("RED_NO_REAL_RUNTIME_HOOK")
 if before[R].read_bytes()!=after[R].read_bytes():raise ValueError("RED_NEW_CASTLE_HP_OWNER")
 if after[H].read_text().count("session.guardians=GuardianRuntime.attach(session,chosenRole)")!=1:
  raise ValueError("RED_DUPLICATE_GUARDIAN_HOST")
 if after[C].read_text().count("session.guardians.damageFromPlayer(")!=1:
  raise ValueError("RED_DUPLICATE_COMBAT_DAMAGE")
 receipt={
  "version":"GQ815_REAL41_TO42_GUARDIAN_AI_1",
  "original41_scripts":41,"source_count":42,
  "original_modified":["/".join(x) for x in sorted(delta)],
  "unchanged_original41":38,"added":["/".join(N)],
  "unchanged_castle_rules_sha256":hashlib.sha256(before[R].read_bytes()).hexdigest(),
  "single_original_Host":True,"single_original_Combat":True,
  "new_Game_Remote_Store_Owner":False,
  "guardian_actual_NPC":True,"guardian_shop_wallet":"NOT_CONNECTED",
  "studio":"NOT_TESTED","android":"NOT_TESTED","formal_rc_adopted":False,
  "rollback":"Drop added guardian source and precisely select prior Real41 portable original source"}
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
 print("GQ815_TRUE_REAL41_TO42_EXISTING_SINGLE_HOST_COMBAT_BRIDGE_PASS")
 return receipt
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--real41",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 x=a.parse_args();compose(x.real41,x.out)
