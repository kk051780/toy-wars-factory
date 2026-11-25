#!/usr/bin/env python3
"""GQ500: inline immutable original castle defense Policy+Live in existing V3 Host.
No second server controller or new Script. Prior 31-source selected project and
all earlier role, world, castle, neutral, item, lobby/balance overlays preserved.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_castle_prompt_session_20261117"))
from select_castle import mapping,HOST

FEATURE="GQ500_ORIGINAL_LIVE_CASTLE_DEFENSE_INLINE_20261117"
AUTHOR_HEAD="abc4bd0edad4a07b159ee08d867dbdd6977f37ee"
POLICY_BLOB="fcf7612a9874c17170b7d00bdbad40b23a616f1c"
LIVE_BLOB="94c2edd8809f37ec186cb3f59226941366b62156"
HOST_REQUIRE='local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))'
BOT_START=' BotActors.start(session,Rules)'
CLOSE_ANCHOR='if session.world.Parent then session.world:Destroy() end'
START_HOOK=''' -- GQ500_ORIGINAL_LIVE_CASTLE_DEFENSE_INLINE_20261117
 -- Reuse original #500 Policy and Live; optional Studio-only, no parallel Game.
 local DEFENSE_V1_ENABLED=true
 if DEFENSE_V1_ENABLED then
  local defenseOK,defenseError=pcall(function() CastleDefense.start(session) end)
  if not defenseOK then
   if session.castleDefenseStop then session.castleDefenseStop() end
   warn("[EGGRUMBLE CASTLE DEFENSE] YELLOW_OPTIONAL source fail:",defenseError)
  end
 end'''
CLOSE_HOOK='if session.castleDefenseStop then session.castleDefenseStop() end\n  '
FILE="GQ500_CASTLE_DEFENSE_HOST.server.luau"
RECEIPT="GQ500_CASTLE_DEFENSE_RECEIPT.json"
def blob(raw:bytes):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha(raw:bytes):return hashlib.sha256(raw).hexdigest()
def inline(policy:bytes,live:bytes)->str:
    if blob(policy)!=POLICY_BLOB:raise ValueError("RED_GQ500_ORIGINAL_POLICY_BLOB_CHANGED")
    if blob(live)!=LIVE_BLOB:raise ValueError("RED_GQ500_ORIGINAL_LIVE_BLOB_CHANGED")
    a,b=policy.decode("utf8"),live.decode("utf8")
    if not a.startswith("--!strict\n") or not b.startswith("--!strict\n"):
        raise ValueError("RED_GQ500_STRICT_SOURCE_DRIFT")
    req='local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_CastleDefensePolicy"))\n'
    if b.count(req)!=1 or a.count("return Policy\n")!=1 or b.count("return Defense\n")!=1:
        raise ValueError("RED_GQ500_DEPENDENCY_SOURCE_DRIFT")
    a=a[len("--!strict\n"):]
    b=b[len("--!strict\n"):].replace(req,"",1)
    for needed in ('Policy.TICK_SECONDS=0.35','Policy.MAX_CASTLES=16',
       'Policy.canTarget(', 'Policy.mayActivate(', 'Policy.canAcquire(',
       'RunService:IsStudio()','closest.hum:TakeDamage(',
       'session.rules.phase=="ACTIVE"','session.castleDefenseStop=stop',
       'RaycastParams.new()'):
        if needed not in a+b:raise ValueError("RED_GQ500_AUTHOR_SAFETY_DEP_"+needed)
    for forbidden in ('Instance.new("RemoteEvent")','Instance.new("RemoteFunction")',
                      'GetService("DataStoreService")','GetService("MarketplaceService")'):
        if forbidden in a+b:raise ValueError("RED_GQ500_NEW_AUTHORITY_"+forbidden)
    return ("local CastleDefense=(function()\n"
            +"local Policy=(function()\n"+a+"end)()\n"
            +b+"end)()\n")
def patch(before:str,body:str)->str:
    if not before.endswith("\n"):raise ValueError("RED_GQ500_SOURCE_ENDING")
    for token in (HOST_REQUIRE,BOT_START,CLOSE_ANCHOR,
         'session.closeRound=function(abandoned:boolean?)',
         'session.castleLocations','session.castleModels','Rules.loadDefense('):
        if token not in before:raise ValueError("RED_GQ500_MISSING_HOST_ANCHOR_"+token)
    if before.count(HOST_REQUIRE)!=1 or before.count(BOT_START)!=1 or before.count(CLOSE_ANCHOR)!=1:
        raise ValueError("RED_GQ500_ANCHOR_NOT_SINGLETON")
    if "CastleDefense.start(session)" in before or "local CastleDefense=" in before:
        raise ValueError("RED_GQ500_ALREADY_SELECTED")
    out=before.replace(HOST_REQUIRE,HOST_REQUIRE+"\n"+body,1)
    out=out.replace(BOT_START,BOT_START+"\n"+START_HOOK,1)
    out=out.replace(CLOSE_ANCHOR,CLOSE_HOOK+CLOSE_ANCHOR,1)
    if undo(out,body)!=before:raise ValueError("RED_GQ500_OFF_NOT_BYTE_EXACT")
    return out
def undo(after:str,body:str)->str:
    for token in (HOST_REQUIRE+"\n"+body,BOT_START+"\n"+START_HOOK,CLOSE_HOOK+CLOSE_ANCHOR):
        if after.count(token)!=1:raise ValueError("RED_GQ500_UNDO_DRIFT")
    return (after.replace(CLOSE_HOOK+CLOSE_ANCHOR,CLOSE_ANCHOR,1)
            .replace(BOT_START+"\n"+START_HOOK,BOT_START,1)
            .replace(HOST_REQUIRE+"\n"+body,HOST_REQUIRE,1))
def inspect(base:Path,out:Path,body:str):
    _,a=mapping(base);_,b=mapping(out)
    if len(a)!=31 or set(a)!=set(b):raise ValueError("RED_GQ500_SOURCE_SET")
    modified=[k for k in a if a[k].read_bytes()!=b[k].read_bytes()]
    if modified!=[HOST]:raise ValueError("RED_GQ500_ONLY_HOST")
    before=a[HOST].read_text(encoding="utf8")
    after=b[HOST].read_text(encoding="utf8")
    if patch(before,body)!=after or undo(after,body)!=before:
        raise ValueError("RED_GQ500_RESTORE_EXACT")
    if not b[HOST].name.endswith(".server.luau"):
        raise ValueError("RED_GQ500_HOST_MUST_BE_SERVER_SCRIPT")
    return before,after,b
def prepare(base:Path,out:Path,policy:Path,live:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/FILE).exists() or (out.parent/RECEIPT).exists():
        raise ValueError("RED_GQ500_OUTPUT_COLLISION")
    body=inline(policy.read_bytes(),live.read_bytes())
    project,files=mapping(base)
    original=files[HOST].read_text(encoding="utf8")
    selected=patch(original,body)
    (out.parent/FILE).write_text(selected,encoding="utf8")
    changed=copy.deepcopy(project)
    changed["tree"][HOST[0]][HOST[1]]["$path"]=FILE
    out.write_text(json.dumps(changed,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    inspect(base,out,body)
    record={"feature_id":FEATURE,"source_author_pr":500,"author_commit":AUTHOR_HEAD,
      "policy_git_blob":POLICY_BLOB,"live_git_blob":LIVE_BLOB,
      "source_count":31,"only_changed_existing":HOST[-1],"other30_byte_exact":True,
      "off_exact":True,"host_source_class":"Script","new_script_count":0,
      "new_game_remote_store_score":0,"towers_traps_sensors":"original author #500, Studio only",
      "owner_max_castles":16,"tick_seconds":.35,
      "original_host_sha256":sha(original.encode()),"selected_host_sha256":sha(selected.encode()),
      "native":"PENDING","rojo":"PENDING","studio_android_fun_owner":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("GQ500_CASTLE_DEFENSE_ORIGINAL_ONE_HOST_30_BYTE_EXACT_INVERSE_OFF_PASS")
def verify(base:Path,out:Path,policy:Path,live:Path,place:Path):
    body=inline(policy.read_bytes(),live.read_bytes())
    before,after,files=inspect(base.resolve(strict=True),out.resolve(strict=True),body)
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ500_PROPS_MISSING")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in found:raise ValueError("RED_GQ500_DUPLICATE_SCRIPT")
        found[name]=(cls,source.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={key[-1] for key in files}:
        raise ValueError("RED_GQ500_REAL_ROJO31_SET")
    for route,file in files.items():
        kind=("Script" if file.name.endswith(".server.luau") else
              "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(kind,file.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_GQ500_ROJO_CLASS_SOURCE_"+route[-1])
    receipt=out.parent/RECEIPT
    rec=json.loads(receipt.read_text(encoding="utf8"))
    if rec["original_host_sha256"]!=sha(before.encode()) or rec["selected_host_sha256"]!=sha(after.encode()):
        raise ValueError("RED_GQ500_SOURCE_HASH")
    rec.update(native="31/31",rojo="31/31",
               place_bytes=place.stat().st_size,place_sha256=sha(place.read_bytes()))
    receipt.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n")
    print("GQ500_ORIGINAL_CASTLE_DEFENSE_NATIVE31_ROJO31_SOURCE_CLASS_PASS",rec["place_bytes"])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("prepare","verify"))
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--policy",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--place",type=Path)
    z=ap.parse_args()
    if z.command=="prepare":prepare(z.base,z.out,z.policy,z.live)
    else:
        if z.place is None:ap.error("requires --place")
        verify(z.base,z.out,z.policy,z.live,z.place)
