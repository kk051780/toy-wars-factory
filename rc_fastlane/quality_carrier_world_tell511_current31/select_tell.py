#!/usr/bin/env python3
"""GQ511: source-inline ORIGINAL author carrier egg 3D indicator in existing V3 Host.

Reuse immutable original #511 Luau policy and world observer. Exactly 31 existing
game scripts; only existing Host changes, other30 byte exact; safe OFF inverse.
Do NOT create an additional Game, Remote, economy, score, or timer owner.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_castle_prompt_session_20261117"))
from select_castle import mapping,HOST

FEATURE="GQ511_ORIGINAL_CARRIER_WORLD_TELL_INLINE_20261117"
AUTHOR_HEAD="554d5a179897c2a84016e7049296c317063b126b"
AUTHOR_POLICY_BLOB="3c426af0af6f34649eaffbf057f8ac91cbecbaf0"
AUTHOR_WORLD_BLOB="dab4e5bb7b4f33f0fad7eed4c2333bab34d49a2b"
AUTHOR_PATH="quality_gameplay/carrier_world_tell_20261116"
REQUIRE='local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))\n'
START=' BotActors.start(session,Rules)'
START_PATCH=START+'\n CarrierWorldTell.start(session)'
FILE="GQ511_CARRIER_WORLD_TELL_HOST.server.luau"
RECEIPT="GQ511_CARRIER_WORLD_TELL_RECEIPT.json"

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def gitblob(raw:bytes)->str:return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def author_inline(policy:bytes,world:bytes)->str:
    if gitblob(policy)!=AUTHOR_POLICY_BLOB:raise ValueError("RED_GQ511_ORIGINAL_POLICY_BLOB_CHANGED")
    if gitblob(world)!=AUTHOR_WORLD_BLOB:raise ValueError("RED_GQ511_ORIGINAL_WORLD_BLOB_CHANGED")
    policy_text=policy.decode("utf8")
    world_text=world.decode("utf8")
    if not policy_text.startswith("--!strict\n") or not world_text.startswith("--!strict\n"):
        raise ValueError("RED_GQ511_ORIGINAL_STRICT")
    policy_text=policy_text[len("--!strict\n"):]
    world_text=world_text[len("--!strict\n"):]
    source_require='local Policy = require(script.Parent:WaitForChild("EGGRUMBLE_CarrierTellPolicy"))\n'
    if world_text.count(source_require)!=1 or policy_text.count("return Policy\n")!=1 or world_text.count("return Tell\n")!=1:
        raise ValueError("RED_GQ511_AUTHOR_IMPORT_OR_RETURN_CHANGED")
    if "function Tell.start(session:any):boolean" not in world_text:
        raise ValueError("RED_GQ511_START_MISSING")
    for token in ("session.world:FindFirstChild(\"TacticalBattlefield\")",
                  "gui.AlwaysOnTop = false","gui.MaxDistance = Policy.MAX_WORLD_VIEW_DISTANCE",
                  "task.wait(Policy.POLL_SECONDS)","session.rules.castles[id]",
                  "Policy.inArenaXZ(","Policy.shouldShow(",
                  "session.carrierWorldTellEnabled == false"):
        if token not in world_text:raise ValueError("RED_GQ511_AUTHOR_VISIBILITY_GUARD_"+token)
    for forbidden in ("RemoteEvent","DataStore","TakeDamage","ProximityPrompt"):
        if forbidden in world_text or forbidden in policy_text:
            raise ValueError("RED_GQ511_UNEXPECTED_AUTHOR_AUTHORITY")
    world_text=world_text.replace(source_require,"",1)
    return ("local CarrierWorldTell=(function()\n"
            "local Policy=(function()\n"+policy_text+"end)()\n"
            +world_text+"end)()\n")
def patch(src:str,inline:str)->str:
    if not src.endswith("\n") or src.count(REQUIRE)!=1 or src.count(START)!=1:
        raise ValueError("RED_GQ511_HOST_ANCHOR_DRIFT")
    if "CarrierWorldTell.start(" in src or "local CarrierWorldTell=" in src:
        raise ValueError("RED_GQ511_ALREADY_SELECTED")
    if 'session.isCurrentHuman=function(player:Player):boolean' not in src:
        raise ValueError("RED_GQ511_ORIGINAL_CURRENT_SESSION_HOST_MISSING")
    for needed in ('session.rules','session.roster','session.world','TacticalBattlefield'):
        if needed not in src:raise ValueError("RED_GQ511_MISSING_CURRENT_SESSION_DEP_"+needed)
    changed=src.replace(REQUIRE,REQUIRE+inline,1).replace(START,START_PATCH,1)
    if unpatch(changed,inline)!=src:raise ValueError("RED_GQ511_OFF_NOT_EXACT")
    return changed
def unpatch(src:str,inline:str)->str:
    if src.count(REQUIRE+inline)!=1 or src.count(START_PATCH)!=1:
        raise ValueError("RED_GQ511_UNPATCH_ANCHOR_DRIFT")
    return src.replace(START_PATCH,START,1).replace(REQUIRE+inline,REQUIRE,1)
def scan(base:Path,out:Path,inline:str):
    _,original=mapping(base)
    _,selected=mapping(out)
    if len(original)!=31 or set(original)!=set(selected):
        raise ValueError("RED_GQ511_SCRIPT_SET")
    changed=[k for k in original if original[k].read_bytes()!=selected[k].read_bytes()]
    if changed!=[HOST]:raise ValueError("RED_GQ511_ONLY_ONE_HOST_ALLOWED")
    a=original[HOST].read_text(encoding="utf8")
    b=selected[HOST].read_text(encoding="utf8")
    if patch(a,inline)!=b or unpatch(b,inline)!=a:
        raise ValueError("RED_GQ511_SOURCE_LOCK_ROLLBACK")
    if not selected[HOST].name.endswith(".server.luau"):
        raise ValueError("RED_GQ511_HOST_CLASS_SCRIPT")
    return a,b,selected
def prepare(base:Path,out:Path,policy:Path,world:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/FILE).exists() or (out.parent/RECEIPT).exists():
        raise ValueError("RED_GQ511_OUTPUT_COLLISION")
    inline=author_inline(policy.read_bytes(),world.read_bytes())
    project,files=mapping(base)
    old=files[HOST].read_text(encoding="utf8")
    after=patch(old,inline)
    (out.parent/FILE).write_text(after,encoding="utf8")
    modified=copy.deepcopy(project)
    modified["tree"][HOST[0]][HOST[1]]["$path"]=FILE
    out.write_text(json.dumps(modified,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    scan(base,out,inline)
    (out.parent/RECEIPT).write_text(json.dumps({
      "feature_id":FEATURE,"original_pr":511,"author_head":AUTHOR_HEAD,
      "author_policy_git_blob":AUTHOR_POLICY_BLOB,"author_world_git_blob":AUTHOR_WORLD_BLOB,
      "source_count":31,"only_changed_script":HOST[-1],"other30_byte_exact":True,
      "off_rollback_byte_exact":True,"one_host_script_class":"Script",
      "new_runtime_script_count":0,"new_game_remote_store_score_authority":0,
      "visibility":"ACTIVE winner_nil alive heldEggs1to3 in_real_TEAM_BR_field",
      "art":"70-stud MaxDistance, AlwaysOnTop=false, max roster16, 0.3-second poll",
      "original_host_sha256":sha(old.encode()),"selected_host_sha256":sha(after.encode()),
      "native":"PENDING","rojo":"PENDING","studio_android_fun_owner":"NOT_TESTED"
    },sort_keys=True,indent=2)+"\n")
    print("GQ511_ORIGINAL_CARRIER_WORLD_TELL_ONE_HOST_30_EXACT_OFF_PASS")
def verify(base:Path,out:Path,policy:Path,world:Path,place:Path):
    inline=author_inline(policy.read_bytes(),world.read_bytes())
    old,new,files=scan(base.resolve(strict=True),out.resolve(strict=True),inline)
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        clazz=item.get("class")
        if clazz not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ511_PLACE_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in embedded:
            raise ValueError("RED_GQ511_PLACE_DUPLICATE_OR_MISSING")
        embedded[name]=(clazz,src.replace("\r\n","\n"))
    if len(embedded)!=31 or set(embedded)!={k[-1] for k in files}:
        raise ValueError("RED_GQ511_REAL_ROJO31_MAPPING")
    for route,filename in files.items():
        kind=("Script" if filename.name.endswith(".server.luau") else
              "LocalScript" if filename.name.endswith(".client.luau") else "ModuleScript")
        if embedded[route[-1]]!=(kind,filename.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_GQ511_PLACE_SOURCE_CLASS_"+route[-1])
    receipt=out.parent/RECEIPT
    data=json.loads(receipt.read_text(encoding="utf8"))
    if data["original_host_sha256"]!=sha(old.encode()) or data["selected_host_sha256"]!=sha(new.encode()):
        raise ValueError("RED_GQ511_CURRENT_HOST_SHA_CHANGED")
    data.update(native="31/31",rojo="31/31",
                place_bytes=place.stat().st_size,place_sha256=sha(place.read_bytes()))
    receipt.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print("GQ511_CARRIER_WORLD_TELL_NATIVE31_ROJO31_TRUE_SOURCE_CLASS_PASS",data["place_bytes"])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("prepare","verify"))
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--policy",type=Path,required=True)
    ap.add_argument("--world",type=Path,required=True)
    ap.add_argument("--place",type=Path)
    args=ap.parse_args()
    if args.command=="prepare":
        prepare(args.base,args.out,args.policy,args.world)
    else:
        if args.place is None:ap.error("verify requires place")
        verify(args.base,args.out,args.policy,args.world,args.place)
