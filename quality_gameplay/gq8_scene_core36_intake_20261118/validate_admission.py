#!/usr/bin/env python3
"""Read-only, source-exact admission proof for the existing Core36 + PR799 LSS.

Reuse the original #764/#775/#780 composers. Never create a second runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE=Path("handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/EGGRUMBLE_LandSeaSkyTraversal.server.luau")
LOCK=Path("handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/GQ8_RC32_SOURCE_LOCK.json")
OPTIONAL=Path("rc_fastlane/EGGRUMBLE_V3_LSS_OPTIONAL32.json")
LSS_ROUTE=("ServerScriptService","EGGRUMBLE_LandSeaSkyTraversal")
HOST_ROUTE=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
REQUIRED_ADDITIONS={
 ("ServerScriptService","EGGRUMBLE_LandSeaSkyTraversal"),
 ("ServerScriptService","EGGRUMBLE_RealmBattleCore"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls"),
 ("ServerScriptService","EGGRUMBLE_NaturalRegen"),
 ("ServerScriptService","EGGRUMBLE_PassiveRegenPolicy"),
}
EXPECTED_BLOB="f7c210ed62e9a0ee8cca78749d8f716317539cd4"
STUDIO_GATE="if not RunService:IsStudio() then return end"
PROMOTION="-- Promoted REALM34 core: same V3 session guards on all servers; no Studio gate."
FEATURE="GQ8_LSS_SCENE_DETACH_RETIRE_20261118"

class AdmissionError(RuntimeError):
 pass

def blob_sha(src:str)->str:
 raw=src.encode("utf-8")
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\\0"+raw).hexdigest()

def assert_runtime_source(src:str, exact_blob:bool=True)->dict:
 if exact_blob and blob_sha(src)!=EXPECTED_BLOB:
  raise AdmissionError("RED_LSS_SOURCE_BLOB_DRIFT")
 required={
  "current-world cleanup":"local function retireScene(removeVisual)",
  "current arena test":"shouldRetireDetachedScene(",
  "heartbeat retirement":"retireScene(true)",
  "world Destroying":"world.Destroying:Connect(function() retireScene(false) end)",
  "original dismount rescue":"flightDismountNeedsRescue(",
  "original idle craft reclaim":"emptyCraftLease(",
  "server current player guard":"currentCraftOwner(v.owner,mode,world,v.role)",
  "unchanged existing swarm":"EGGRUMBLE_SwarmCombat",
  "visual scene disposal":"if removeVisual and scene.Parent then scene:Destroy() end",
 }
 for name,marker in required.items():
  if marker not in src:
   raise AdmissionError("RED_MISSING_RUNTIME_GUARD:"+name)
 if src.count(STUDIO_GATE)!=1:
  raise AdmissionError("RED_STUDIO_PROMOTION_ANCHOR")
 if 'Instance.new("RemoteEvent")' in src or 'DataStoreService' in src:
  raise AdmissionError("RED_SECOND_REMOTE_OR_STORE")
 if src.count("local function retireScene(removeVisual)")!=1:
  raise AdmissionError("RED_MULTIPLE_RETIRE_AUTHORITY")
 return {"source_git_blob":blob_sha(src),"lss_bytes":len(src.encode("utf-8"))}

def ensure_promoted_source(original:str,promoted:str)->None:
 assert_runtime_source(original)
 expected=original.replace(STUDIO_GATE,PROMOTION,1)
 if promoted!=expected:
  raise AdmissionError("RED_CORE36_SELECTED_LSS_NOT_EXACT_PROMOTION")

def verify_locks() ->dict:
 source=SOURCE.read_text(encoding="utf-8")
 result=assert_runtime_source(source)
 a=json.loads(LOCK.read_text(encoding="utf-8"))
 b=json.loads(OPTIONAL.read_text(encoding="utf-8"))
 if a["optional_profile"]["source_blob_sha"]!=EXPECTED_BLOB or b["added_source_git_blob"]!=EXPECTED_BLOB:
  raise AdmissionError("RED_OPTIONAL32_MANIFEST_SOURCE_MISMATCH")
 if FEATURE not in b["feature_ids"]:
  raise AdmissionError("RED_LIFECYCLE_FEATURE_UNREGISTERED")
 if b["source_count"]!=32 or not a["authority"]["canonical_v3_31_profile_untouched"]:
  raise AdmissionError("RED_BASELINE_PROFILE_WAS_CHANGED")
 return result

def verify_combined(baseline:Path,combined:Path)->dict:
 # The composer originates from author #780 and performs independent source-lock checks.
 from quality_gameplay.gq8_crosslane_20261118.compose_rehearsal36 import flatten
 _,a=flatten(baseline)
 _,b=flatten(combined)
 if len(a)!=31 or len(b)!=36:
  raise AdmissionError("RED_BASE31_OR_CORE36_COUNT")
 if set(b)-set(a)!=REQUIRED_ADDITIONS or set(a)-set(b):
  raise AdmissionError("RED_UNREVIEWED_SCRIPT_ADDITION_REMOVAL")
 if HOST_ROUTE not in a or LSS_ROUTE not in b:
  raise AdmissionError("RED_MISSING_AUTHORITATIVE_SOURCE")
 ensure_promoted_source(SOURCE.read_text(encoding="utf-8"),
                        b[LSS_ROUTE].read_text(encoding="utf-8"))
 for route in a:
  if route==HOST_ROUTE:
   continue
  if a[route].read_bytes()!=b[route].read_bytes():
   raise AdmissionError("RED_ORIGINAL31_CHANGED:"+"/".join(route))
 host_a=a[HOST_ROUTE].read_text(encoding="utf-8")
 host_b=b[HOST_ROUTE].read_text(encoding="utf-8")
 require='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
 call="NaturalRegen.attach(session,p,role)"
 if require in host_a or call in host_a or host_b.count(require)!=1 or host_b.count(call)!=2:
  raise AdmissionError("RED_HOST_REGEN_AUTHORITY_DRIFT")
 # Existing project route/class checks performed by real Rojo Source/Class verifier.
 return {"original31":len(a),"selected36":len(b),"new_script_routes":5,
         "changed_original_routes":1,"lss_source_blob":EXPECTED_BLOB,
         "studio": "NOT_TESTED","android":"NOT_TESTED","fun":"NOT_TESTED",
         "formal_rc_adopted":False}

def main()->None:
 ap=argparse.ArgumentParser()
 ap.add_argument("--original31",type=Path)
 ap.add_argument("--combined36",type=Path)
 ap.add_argument("--receipt",type=Path)
 args=ap.parse_args()
 result=verify_locks()
 if args.original31 or args.combined36:
  if not args.original31 or not args.combined36:
   raise AdmissionError("RED_PARTIAL_FULL36_INPUTS")
  result.update(verify_combined(args.original31,args.combined36))
 if args.receipt:
  args.receipt.parent.mkdir(parents=True,exist_ok=True)
  args.receipt.write_text(json.dumps({"schema":"GQ8_LSS_SCENE_FULL36_CANDIDATE_V1",
    "feature_id":FEATURE,**result},ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
 print("GQ8_LSS_SCENE_CORE36_SOURCE_EXACT_CANDIDATE_GREEN",json.dumps(result,sort_keys=True))

if __name__=="__main__":
 main()
