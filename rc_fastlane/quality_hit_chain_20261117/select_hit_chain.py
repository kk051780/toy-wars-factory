#!/usr/bin/env python3
"""GQ8: reversible confirmed-hit chain on the EXISTING V3 CombatFeel LocalScript.
No new runtime source, score/KO authority, Remote, Game, Store, or server damage.
"""
import argparse
import copy
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path("rc_fastlane/quality_rc81_hit042_v3").resolve()))
from select_hit042 import flatten, class_for, ROUTE

FEATURE = "GQ8_SERVER_CONFIRMED_HIT_CHAIN_20261117"
ANCHOR = "local pulse=0\n"
TEXT_ANCHOR = ' hitToast.Text="HIT x"..tostring(math.floor(power))\n'
START_MARKER = "-- GQ8_CONFIRMED_HIT_CHAIN_BEGIN"
END_MARKER = "-- GQ8_CONFIRMED_HIT_CHAIN_END"
INSERT = """-- GQ8_CONFIRMED_HIT_CHAIN_BEGIN
-- Visual feedback only. Count locally from already server-confirmed impact events.
-- This is NOT the neutral KO combo, rewards, or score source of truth.
local chainHits=0
local lastChainAt=-1000000000
local function hitChainCount(now:number):number
 if now<lastChainAt or now-lastChainAt>1.6 then chainHits=0 end
 lastChainAt=now
 chainHits=math.min(30,chainHits+1)
 return chainHits
end
player:GetAttributeChangedSignal("EGGRUMBLE_QueuedMode"):Connect(function()
 chainHits=0
 lastChainAt=-1000000000
end)
-- GQ8_CONFIRMED_HIT_CHAIN_END
"""
REPLACE = """ local chainCount=hitChainCount(now)
 if chainCount>=3 then
  hitToast.Text="CHAIN x"..tostring(chainCount)
  hitToast.TextColor3=c
 else
  hitToast.Text="HIT x"..tostring(math.floor(power))
  hitToast.TextColor3=Color3.new(1,1,1)
 end
"""
CLIENT_FILE = "EGGRUMBLE_GQ8_ConfirmedHitChain.client.luau"
RECEIPT_FILE = "GQ8_HIT_CHAIN_RC31_RECEIPT.json"

def digest(raw:bytes)->str:
 return hashlib.sha256(raw).hexdigest()

def patch(src:str)->str:
 if src.count(ANCHOR)!=1 or src.count(TEXT_ANCHOR)!=1:
  raise ValueError("RED_HIT042_CLIENT_ANCHOR_DRIFT")
 for required in ('player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
                  'if reduced() then return end',
                  'local now=os.clock()',
                  'local RECENT_CD=.12',
                  'hitToast.Name="ConfirmedHit042"',
                  'if thisPulse==pulse and hitToast.Parent then hitToast.Visible=false end'):
  if required not in src:raise ValueError("RED_MISSING_SERVER_CONFIRM_OR_REDUCED_GATE "+required)
 if START_MARKER in src or "hitChainCount(" in src:
  raise ValueError("RED_DOUBLE_APPLY")
 result=src.replace(ANCHOR,ANCHOR+INSERT,1).replace(TEXT_ANCHOR,REPLACE,1)
 if unpatch(result)!=src:raise ValueError("RED_INVERSE_FAIL")
 return result

def unpatch(src:str)->str:
 if src.count(ANCHOR+INSERT)!=1 or src.count(REPLACE)!=1:
  raise ValueError("RED_BAD_REVERSE")
 return src.replace(ANCHOR+INSERT,ANCHOR,1).replace(REPLACE,TEXT_ANCHOR,1)

def prepare(base:Path,out:Path)->None:
 if out.exists():raise ValueError("RED_OVERWRITE_PROJECT")
 obj,files=flatten(base)
 client=files[ROUTE].read_text(encoding="utf-8")
 if client.count('hitToast.Name="ConfirmedHit042"')!=1:
  raise ValueError("RED_MISSING_GQ81_EXACT_CLIENT")
 revised=patch(client)
 dest=out.parent/CLIENT_FILE
 if dest.exists():raise ValueError("RED_OVERWRITE_SOURCE")
 dest.write_text(revised,encoding="utf-8")
 doc=copy.deepcopy(obj)
 doc["name"]="EGGRUMBLE_V3_31_GQ8_CONFIRMED_HIT_CHAIN"
 def rewrite(node,path=()):
  for key,value in node.items():
   if key.startswith("$"):continue
   route=path+(key,)
   if "$path" in value:
    value["$path"]=os.path.relpath(dest if route==ROUTE else files[route],
                                     out.parent).replace(os.sep,"/")
   else:rewrite(value,route)
 rewrite(doc["tree"])
 out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,final=flatten(out)
 changed=[route for route in files if files[route].read_bytes()!=final[route].read_bytes()]
 if changed!=[ROUTE]:raise ValueError("RED_NOT_ONLY_CLIENT_CHANGED "+str(changed))
 print("GQ8_CHAIN_CURRENT31_ONE_CLIENT_PATCH_OTHER30_BYTE_IDENTICAL_OFF_PASS")

def embed_place(place:Path)->dict:
 actual={}
 for item in ET.parse(place).getroot().iter("Item"):
  cls=item.get("class")
  if cls not in ("Script","LocalScript","ModuleScript"):continue
  props=item.find("Properties")
  if props is None:raise ValueError("RED_NO_ROJO_PROPS")
  name=props.findtext("string[@name='Name']")
  src=props.findtext("ProtectedString[@name='Source']")
  if src is None:src=props.findtext("string[@name='Source']")
  if not name or src is None or name in actual:raise ValueError("RED_DUPLICATE_ROJO")
  actual[name]=(cls,src.replace("\r\n","\n"))
 return actual

def verify(base:Path,out:Path,place:Path)->None:
 _,before=flatten(base)
 _,after=flatten(out)
 if len(after)!=31 or set(before)!=set(after):raise ValueError("RED_SCRIPT_SET_CHANGED")
 for route in before:
  earlier=before[route].read_bytes()
  later=after[route].read_bytes()
  if route==ROUTE:
   if later!=patch(earlier.decode("utf-8")).encode("utf-8"):
    raise ValueError("RED_PATCH_MISMATCH")
   if unpatch(later.decode("utf-8")).encode("utf-8")!=earlier:
    raise ValueError("RED_ROLLBACK_MISMATCH")
  elif later!=earlier:raise ValueError("RED_30_CHANGED "+str(route))
 actual=embed_place(place)
 if len(actual)!=31 or set(actual)!={route[-1] for route in after}:
  raise ValueError("RED_ROJO31_SCRIPT_SET")
 for route,p in after.items():
  expected=(class_for(p),p.read_text(encoding="utf-8").replace("\r\n","\n"))
  if actual[route[-1]]!=expected:raise ValueError("RED_ROJO_SOURCE_CLASS "+str(route))
 receipt={
  "feature_id":FEATURE,"source_count":31,
  "only_changed_script":"/".join(ROUTE),
  "other30_byte_exact":True,"one_client_rollback_exact":True,
  "trigger":"server-confirmed EGGRUMBLE_ImpactSequence only",
  "hit_chain_reset_seconds":1.6,"chain_cap":30,
  "native_31":"TO_BE_CONFIRMED_BY_CI","rojo":"31/31",
  "place_bytes":place.stat().st_size,"place_sha256":digest(place.read_bytes()),
  "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
  "owner_fun":"NOT_TESTED","formal_rc":"CI_CANDIDATE_NOT_YET_ADOPTED"
 }
 (out.parent/RECEIPT_FILE).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print("GQ8_REAL_SELECTED31_CHAIN_ROJO_CLASS_SOURCE_EXACT_PASS",receipt["place_bytes"])

def native_fixture(project:Path,out:Path,mutant:Path)->None:
 _,files=flatten(project)
 source=files[ROUTE].read_text(encoding="utf-8")
 if source.count(START_MARKER)!=1 or source.count(END_MARKER)!=1:
  raise ValueError("RED_CHAIN_MARKER")
 part=source.split(START_MARKER,1)[1].split(END_MARKER,1)[0]
 part=part.split('player:GetAttributeChangedSignal("EGGRUMBLE_QueuedMode")',1)[0]
 cases="""
assert(hitChainCount(0)==1)
assert(hitChainCount(0.20)==2)
assert(hitChainCount(0.40)==3)
assert(hitChainCount(2.01)==1)
for i=1,40 do
 local got=hitChainCount(2.01+i*.20)
 assert(got==math.min(30,i+1))
end
assert(hitChainCount(1.0)==1)
print("GQ8_REAL_SELECTED_CLIENT_HIT_CHAIN_NATIVE_PASSES")
"""
 out.write_text(part+"\n"+cases,encoding="utf-8")
 mutant.write_text(part.replace("now-lastChainAt>1.6","false",1)+"\n"+cases,encoding="utf-8")
 print("GQ8_CHAIN_NATIVE_FIXTURE_DERIVED_FROM_ACTUAL_SELECTED_CLIENT")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("action",choices=("prepare","verify","native"))
 p.add_argument("--base",type=Path)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--place",type=Path)
 p.add_argument("--mutant",type=Path)
 a=p.parse_args()
 if a.action=="prepare":
  if not a.base:p.error("--base needed")
  prepare(a.base.resolve(strict=True),a.out.resolve())
 elif a.action=="verify":
  if not a.base or not a.place:p.error("--base/--place needed")
  verify(a.base.resolve(strict=True),a.out.resolve(strict=True),a.place.resolve(strict=True))
 else:
  if not a.mutant:p.error("--mutant needed")
  native_fixture(a.base.resolve(strict=True),a.out.resolve(),a.mutant.resolve())
if __name__=="__main__":main()
