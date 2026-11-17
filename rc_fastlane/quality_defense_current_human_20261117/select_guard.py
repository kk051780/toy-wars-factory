#!/usr/bin/env python3
"""GQ8: reject cross-round humans in existing castle Live Defense; one Host only.

Original #500 pure Policy/Live source stays byte-identical in its pinned repo.
Two precise gates are added in the selected CURRENT 31-source Host: acquisition
and immediately before action. 30 other original script bytes and OFF exact.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,sys,tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path("rc_fastlane/quality_rc81_hit042_v3").resolve()))
from select_hit042 import flatten,class_for
sys.path.insert(0,str(Path("rc_fastlane/quality_castle_defense500_current31").resolve()))
from native_defense import make as original_native_make
from select_defense import blob as gitblob,POLICY_BLOB,LIVE_BLOB

FEATURE="GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117"
SCRIPT="EGGRUMBLE_LobbyCastleModesPreview"
MARK="-- GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117"
A='''  player=userId and Players:GetPlayerByUserId(userId) or nil
  model=player and player.Character or nil'''
B='''  -- The moment of effect is the only point that consumes the per-castle cooldown.
  last[id][kind]=now'''
A2='''  player=userId and Players:GetPlayerByUserId(userId) or nil
  -- GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117
  -- Do not acquire a human who left/rejoined this specific round.
  if not player or type(session.isCurrentHuman)~="function"
   or session.isCurrentHuman(player)~=true then
   return nil,nil,nil,nil
  end
  model=player and player.Character or nil'''
B2='''  -- Recheck membership immediately before damage or sensor state mutation.
  -- A human can change rounds between target selection and attack.
  if closest.player and (type(session.isCurrentHuman)~="function"
   or session.isCurrentHuman(closest.player)~=true) then return end
  -- The moment of effect is the only point that consumes the per-castle cooldown.
  last[id][kind]=now'''
SELECT="GQ8_DEFENSE_CURRENT_HUMAN_HOST.server.luau"
RECEIPT="GQ8_DEFENSE_CURRENT_HUMAN_RECEIPT.json"

def sha(raw:bytes):return hashlib.sha256(raw).hexdigest()
def once(old:str,needle:str,replace:str,tag:str)->str:
 c=old.count(needle)
 if c!=1:raise ValueError("RED_"+tag+"_ANCHOR_COUNT_"+str(c))
 return old.replace(needle,replace,1)
def check_base(text:str):
 for s in (
  "GQ500_ORIGINAL_LIVE_CASTLE_DEFENSE_INLINE_20261117",
  'session.isCurrentHuman=function(player:Player):boolean',
  'session.castleDefenseStop=stop',
  'CastleDefense.start(session)',
  'closest.hum:TakeDamage(Policy.CONFIG[kind].damage)',
  'local function aliveTarget(session:any,id:string)',
  'local function tickOne(id:string,owner:any,kind:string,part:BasePart,now:number)',
 ):
  if s not in text:raise ValueError("RED_ORIGINAL_CASTLE_DEPENDENCY_"+s)
 if text.index('session.isCurrentHuman=function(player:Player):boolean')>=text.index(" BotActors.start(session,Rules)"):
  raise ValueError("RED_SESSION_AUTHORITY_INITIALIZED_AFTER_DEFENSE_START")
def patch(src:str)->str:
 check_base(src)
 if MARK in src:raise ValueError("RED_ALREADY_PATCHED")
 out=once(src,A,A2,"ACQUIRE")
 out=once(out,B,B2,"PRE_DAMAGE")
 if unpatch(out)!=src:raise ValueError("RED_NONEXACT_OFF")
 return out
def unpatch(src:str)->str:
 return once(once(src,B2,B,"OFF_PRE_DAMAGE"),A2,A,"OFF_ACQUIRE")
def project(path:Path):
 obj,files=flatten(path)
 routes=[r for r in files if r[-1]==SCRIPT]
 if len(routes)!=1:raise ValueError("RED_ONE_HOST")
 return obj,files,routes[0]
def prepare(base:Path,out:Path):
 if out.exists():raise ValueError("RED_SELECTED_EXISTS")
 obj,old,host=project(base)
 oldb=old[host].read_bytes()
 after=patch(oldb.decode("utf-8")).encode("utf-8")
 selected=out.parent/SELECT
 if selected.exists():raise ValueError("RED_SELECTED_SCRIPT_EXISTS")
 selected.write_bytes(after)
 obj=copy.deepcopy(obj)
 obj["name"]="GQ8_DEFENSE_HUMAN_CURRENT_SESSION_RC31"
 def walk(tree,prefix=()):
  for key,v in tree.items():
   if key.startswith("$"):continue
   r=prefix+(key,)
   if "$path" in v:
    v["$path"]=os.path.relpath(selected if r==host else old[r],out.parent).replace(os.sep,"/")
   else:walk(v,r)
 walk(obj["tree"])
 out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
 _,new,newhost=project(out)
 if set(old)!=set(new) or len(new)!=31 or host!=newhost:
  raise ValueError("RED_SCRIPT_SET_CHANGED")
 changes=[r for r in old if old[r].read_bytes()!=new[r].read_bytes()]
 if changes!=[host]:raise ValueError("RED_NOT_ONLY_HOST")
 if unpatch(new[host].read_text(encoding="utf8")).encode("utf8")!=oldb:
  raise ValueError("RED_OFF_NOT_EXACT")
 print("GQ8_DEFENSE_CURRENT_HUMAN_ONE_HOST_OTHER30_EXACT_OFF_PASS")
def xmlscripts(place:Path):
 result={}
 for item in ET.parse(place).getroot().iter("Item"):
  kind=item.get("class")
  if kind not in ("Script","LocalScript","ModuleScript"):continue
  props=item.find("Properties")
  if props is None:raise ValueError("RED_ROJO_NO_PROPERTIES")
  name=props.findtext("string[@name='Name']")
  source=props.findtext("ProtectedString[@name='Source']")
  if source is None:source=props.findtext("string[@name='Source']")
  if not name or source is None or name in result:raise ValueError("RED_ROJO_SCRIPT")
  result[name]=(kind,source.replace("\r\n","\n"))
 return result
def verify(base:Path,out:Path,place:Path):
 _,old,host=project(base);_,new,otherhost=project(out)
 if len(old)!=31 or len(new)!=31 or set(old)!=set(new) or host!=otherhost:
  raise ValueError("RED_31_ROUTE")
 for r in old:
  before=old[r].read_bytes();after=new[r].read_bytes()
  if r==host:
   if after!=patch(before.decode("utf8")).encode("utf8") or unpatch(after.decode("utf8")).encode("utf8")!=before:
    raise ValueError("RED_HOST_SOURCE_OR_OFF")
  elif before!=after:raise ValueError("RED_OTHER30_CHANGED")
 actual=xmlscripts(place)
 if len(actual)!=31 or set(actual)!={r[-1] for r in new}:raise ValueError("RED_ROJO_31")
 for r,p in new.items():
  expected=(class_for(p),p.read_text(encoding="utf8").replace("\r\n","\n"))
  if actual[r[-1]]!=expected:raise ValueError("RED_ROJO_SOURCE_CLASS_"+r[-1])
 receipt={
  "feature_id":FEATURE,"script_count":31,"existing_host_only":True,
  "other30_byte_exact":True,"inverse_off_byte_exact":True,
  "human_acquisition_rechecks_current_server_session":True,
  "human_before_hit_rechecks_current_server_session":True,
  "original_policy_live_source_author_sha_unchanged":True,
  "new_script_remote_store_score_authority":0,
  "native":"SAME_HEAD_WITH_TWO_NEGATIVE_MUTANTS",
  "rojo":"31/31","owner_fun":"NO_GO",
  "real_studio_two_client":"NOT_TESTED","android15":"NOT_TESTED",
  "place_size_bytes":place.stat().st_size,
  "place_sha256":sha(place.read_bytes())
 }
 (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print("GQ8_DEFENSE_HUMAN_TRUE_ROJO31_SOURCE_CLASS_INVERSE_OFF_PASS",receipt["place_size_bytes"])

def native(projectpath:Path,policy:Path,live:Path,spec:Path,out:Path,mutant_acquire:Path,mutant_hit:Path):
 _,files,host=project(projectpath)
 selected=files[host].read_text(encoding="utf8")
 if selected.count(A2)!=1 or selected.count(B2)!=1:
  raise ValueError("RED_NATIVE_SELECTED_HOST_GATES_MISSING")
 if gitblob(policy.read_bytes())!=POLICY_BLOB or gitblob(live.read_bytes())!=LIVE_BLOB:
  raise ValueError("RED_IMMUTABLE_GQ500_AUTHOR_DRIFT")
 # Generate real immutable author VM harness first; adjust only the two source
 # snippets in the ACTUAL selected Host that are identical to its original Live.
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp)
  original_native_make(policy,live,spec,
      root/"policy.luau",root/"policy_mutant.luau",root/"live.luau")
  base=(root/"live.luau").read_text(encoding="utf8")
 for needle,repl,tag in ((A,A2,"NATIVE_ACQUIRE"),(B,B2,"NATIVE_PREHIT")):
  base=once(base,needle,repl,tag)
 # Verify the harness source intervention matches exactly what is embedded
 # in the current selected Host, rather than testing invented standalone code.
 for snippet in (A2,B2):
  if selected.count(snippet)!=1 or base.count(snippet)!=1:
   raise ValueError("RED_NATIVE_SELECTED_SOURCE_MISMATCH")
 # Distinguish acquisition from the redundant pre-hit fence: a stale
 # human must not cause even a line-of-sight ray query from old castle.
 base=once(base,
   'workspace={Raycast=function(_,from,direction,params)\n',
   'local __gq8Raycasts=0\nworkspace={Raycast=function(_,from,direction,params)\n __gq8Raycasts+=1\n',
   "NATIVE_LOS_PROBE")
 init=' makeHuman("1",Vector3.new(-100,0,0))'
 injection=''' session.isCurrentHuman=function(player)
  return player~=nil and (not session.invalidHumans
   or not session.invalidHumans[player.UserId])
 end
'''
 base=once(base,init,injection+init,"NATIVE_SESSION_AUTHORITY")
 marker='print("GQ500_ORIGINAL_LIVE_SERVER_NATIVE_VM_PASS checks="..tostring(n))'
 extra='''-- GQ8 actual original Live additional cross-match runtime assertions.
local stale,staleHum=scenario({"TURRET"},Vector3.new(25,6,-18),Vector3.new(25,6,-18),0)
stale.invalidHumans={[2]=true}
__gq8Raycasts=0
Defense.start(stale);step()
eq(__gq8Raycasts,0,"GQ8_STALE_HUMAN_NEVER_QUERIED_FOR_LOS")
eq(staleHum.Health,100,"GQ8_STALE_PLAYER_OTHER_MATCH_NO_TURRET_HIT")
stale.castleDefenseStop()
local switched,swHum=scenario({"TURRET"},Vector3.new(25,6,-18),Vector3.new(25,6,-18),0)
local membershipCalls=0
switched.isCurrentHuman=function(p)
 if p.UserId~=2 then return true end
 membershipCalls+=1
 return membershipCalls==1
end
Defense.start(switched);step()
eq(swHum.Health,100,"GQ8_SWITCHED_DURING_SELECTION_NO_TURRET_HIT")
eq(membershipCalls,2,"GQ8_TWO_SEPARATE_SERVER_MEMBERSHIP_CHECKS")
switched.castleDefenseStop()
print("GQ8_CURRENT_MATCH_CASTLE_DEFENSE_ACTUAL_VM_CROSS_ROUND_3_CASES_PASS")
'''
 full=once(base,marker,extra+marker,"NATIVE_TESTS")
 out.write_text(full)
 mutant_acquire.write_text(once(full,A2,A,"MUTANT_SKIP_ACQUIRE"))
 mutant_hit.write_text(once(full,B2,B,"MUTANT_SKIP_PREHIT"))
 print("GQ8_DEFENSE_SELECTED_SOURCE_TWO_NEGATIVE_MUTANTS_BUILT")

def selftest():
 original='''session.isCurrentHuman=function(player:Player):boolean
end
 BotActors.start(session,Rules)
GQ500_ORIGINAL_LIVE_CASTLE_DEFENSE_INLINE_20261117
session.castleDefenseStop=stop
CastleDefense.start(session)
local function aliveTarget(session:any,id:string)
  player=userId and Players:GetPlayerByUserId(userId) or nil
  model=player and player.Character or nil
end
local function tickOne(id:string,owner:any,kind:string,part:BasePart,now:number)
closest.hum:TakeDamage(Policy.CONFIG[kind].damage)
  -- The moment of effect is the only point that consumes the per-castle cooldown.
  last[id][kind]=now
'''
 out=patch(original)
 assert unpatch(out)==original
 assert out.count(MARK)==1
 assert out.count("session.isCurrentHuman(closest.player)") ==1
 for bad in (out,original.replace(A,""),original.replace(B,"")):
  try:patch(bad)
  except ValueError:pass
  else:raise AssertionError("RED_BAD_SOURCE_ACCEPTED")
 try:unpatch(original)
 except ValueError:pass
 else:raise AssertionError("RED_UNPATCH_OLD_ACCEPTED")
 print("GQ8_DEFENSE_CURRENT_HUMAN_SOURCE_INVERSE_DRIFT_SELFTEST_PASS")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("action",choices=("selftest","prepare","native","verify"))
 for arg in ("base","out","place","policy","live","spec","mutant-acquire","mutant-hit"):
  p.add_argument("--"+arg,type=Path)
 a=p.parse_args()
 if a.action=="selftest":selftest();return
 if not a.base or not a.out:p.error("need --base --out")
 if a.action=="prepare":prepare(a.base.resolve(strict=True),a.out.resolve());return
 if a.action=="verify":
  if not a.place:p.error("need --place")
  verify(a.base.resolve(strict=True),a.out.resolve(strict=True),a.place.resolve(strict=True));return
 if not all((a.policy,a.live,a.spec,a.mutant_acquire,a.mutant_hit)):
  p.error("native requires policy/live/spec/mutant-acquire/mutant-hit")
 native(a.base.resolve(strict=True),a.policy.resolve(strict=True),a.live.resolve(strict=True),
        a.spec.resolve(strict=True),a.out.resolve(),a.mutant_acquire.resolve(),a.mutant_hit.resolve())
if __name__=="__main__":main()
