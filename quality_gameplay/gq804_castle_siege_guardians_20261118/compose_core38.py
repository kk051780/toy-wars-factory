#!/usr/bin/env python3
"""Source-exact Core36 -> Core38: existing one Host & BotActors siege calls, two new modules."""
from __future__ import annotations
import argparse,copy,hashlib,json,os
from pathlib import Path
H=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
B=("ServerScriptService","EGGRUMBLE_BotActors")
RULE=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
P=("ServerScriptService","EGGRUMBLE_CastleSiegeGuardianPolicy")
G=("ServerScriptService","EGGRUMBLE_CastleSiegeBridge")
HERE=Path(__file__).resolve().parent

def flatten(proj):
 proj=Path(proj).resolve(strict=True);d=json.loads(proj.read_text(encoding="utf-8"));files={}
 def go(node,path=()):
  for key,v in node.items():
   if key.startswith("$"):continue
   route=path+(key,)
   if "$path" in v:
    if route in files:raise ValueError("RED_DUPLICATE_ROUTE")
    files[route]=(proj.parent/v["$path"]).resolve(strict=True)
   else:go(v,route)
 go(d["tree"]);return d,files
def replace_once(src,old,new,label):
 if src.count(old)!=1:raise ValueError("RED_"+label+"_ANCHOR_COUNT="+str(src.count(old)))
 return src.replace(old,new,1)
def compose(core36,out):
 core36=Path(core36).resolve(strict=True);out=Path(out).resolve()
 if out.exists() or core36==out:raise ValueError("RED_OVERWRITE")
 project,orig=flatten(core36)
 if len(orig)!=36 or not {H,B,RULE}.issubset(orig) or P in orig or G in orig:
  raise ValueError("RED_NOT_ORIGINAL_CORE36")
 host=orig[H].read_text(encoding="utf-8");bot=orig[B].read_text(encoding="utf-8")
 host=replace_once(host,'local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))',
  'local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))\nlocal SiegeBridge=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeBridge"))',"HOST_REQUIRE")
 host=replace_once(host,'Rules.damageCastle(state,entry.id,from,120)',
  'session.castleSiegeAttack(entry.id,from,120,true)',"HOST_SIEGE")
 host=replace_once(host,'for idx,entry in ipairs(roster) do createWorldCastle(session,entry,idx) end',
  'session.castleSiegeAttack=SiegeBridge.attach(session,Rules)\n for idx,entry in ipairs(roster) do createWorldCastle(session,entry,idx) end',"HOST_ATTACH")
 bot=replace_once(bot,'Rules.damageCastle(session.rules,enemy.id,id,26)',
  'session.castleSiegeAttack(enemy.id,id,26,false)',"BOT_SIEGE")
 out.parent.mkdir(parents=True,exist_ok=True)
 patch={}
 for route,source in ((H,host),(B,bot)):
  ext=".server.luau" if route==H else ".luau"
  dst=out.parent/(route[-1]+ext);dst.write_text(source,encoding="utf-8",newline="\n")
  patch[route]=dst
 result=copy.deepcopy(project);result["name"]="GQ804_CORE38_STAGED_GAMEPLAY_NOT_OFFICIAL_RC"
 def relink(node,route=()):
  for key,v in node.items():
   if key.startswith("$"):continue
   path=route+(key,)
   if "$path" in v:
    v["$path"]=os.path.relpath(patch.get(path,orig[path]),out.parent).replace(os.sep,"/")
   else:relink(v,path)
 relink(result["tree"])
 for route,pth in ((P,HERE/"EGGRUMBLE_CastleSiegeGuardianPolicy.luau"),
                   (G,HERE/"EGGRUMBLE_CastleSiegeBridge.luau")):
  if not pth.is_file():raise ValueError("RED_MISSING_SOURCE_"+pth.name)
  result["tree"]["ServerScriptService"][route[-1]]={
    "$path":os.path.relpath(pth,out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,selected=flatten(out)
 if len(selected)!=38 or set(selected)!=set(orig)|{P,G}:raise ValueError("RED_SOURCE_COUNT")
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 for route in orig:
  if route not in {H,B} and sha(orig[route])!=sha(selected[route]):
   raise ValueError("RED_NONOWNED_SOURCE_CHANGE_"+"/".join(route))
 for route in (H,B):
  if sha(orig[route])==sha(selected[route]):raise ValueError("RED_NO_RUNTIME_HOOK")
 receipt={"stage":"SOURCE_WIRED_CORE38_CANDIDATE","profile":"PRIVATE",
  "base36_original_source_bytes_preserved_except":["/".join(H),"/".join(B)],
  "original_rules_sha256":sha(orig[RULE]),
  "new_sources":["/".join(P),"/".join(G)],
  "rollback":"Use original36 unchanged",
  "source_count":38,"original_hp_egg_winner_authority":1,
  "real_guardian_ai":"NOT_WIRED","official_rc_adopted":False,
  "studio":"NOT_TESTED","android":"NOT_TESTED"}
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ804_REAL_CORE36_TO38_HOST_BOT_SIEGE_RUNTIME_SOURCE_SELECTED_PASS")
 return out
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--core36",required=True,type=Path)
 a.add_argument("--out",required=True,type=Path);args=a.parse_args()
 compose(args.core36,args.out)
