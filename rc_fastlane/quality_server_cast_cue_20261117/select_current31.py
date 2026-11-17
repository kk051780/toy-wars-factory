#!/usr/bin/env python3
"""Select original cast-ACK cue into ONE current31 CombatFeel client, preserving 30.

Fail-closed: requires unchanged immutable original client, all source-class path
and rollback bytes exact, and final genuine Rojo Source/Class exact 31 of 31.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_cast_cue import FEATURE,ORIGINAL_GIT_BLOB,patch,undo,validate_original,git_blob
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_castle_prompt_session_20261117"))
from select_castle import mapping
# Legacy pre-GQ504 client hash retained for provenance only.
# Latest actual source requires audio and all prior HIT anchors.
CURRENT_SELECTED_CLIENT_SHA256="d234cc9177d82e41528cc0b25f9e83267f601c7f454a4ccb13a7ec0cc0ccb9c2"

def validate_current_before(before:str)->None:
    # Current RC now contains GQ504 audio; reject stale pre-audio sources.
    # Complete 31-source, inverse bytes, and real Rojo are checked below.
    if not before.startswith("--!strict\n") or not before.endswith("\n"):
        raise ValueError("RED_GQ8_CURRENT_SOURCE_FORMAT")
    if before.count("GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117")!=1:
        raise ValueError("RED_GQ8_CURRENT_GQ504_AUDIO_REQUIRED")
    for marker in (
      'hitToast.Name="ConfirmedHit042"',
      'GQ8_CONFIRMED_HIT_CHAIN_BEGIN',
      'GQ8_CONFIRMED_HIT_CHAIN_END',
      'GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117',
      'local function reduced():boolean',
      'mark.Parent=gui',
    ):
        if before.count(marker)!=1:raise ValueError("RED_GQ8_EXISTING_FEATURE_DRIFT_"+marker)

CLIENT=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFeel")
FILE="GQ8_EXISTING_COMBATFEEL_CAST_CUE.client.luau"
RECEIPT="GQ8_CAST_CUE_SELECTED31_RECEIPT.json"

def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()

def checked(base:Path,out:Path):
    _,old=mapping(base.resolve(strict=True));_,new=mapping(out.resolve(strict=True))
    if len(old)!=31 or set(old)!=set(new) or CLIENT not in old:
        raise ValueError("RED_GQ8_31_SCRIPT_SET")
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changed!=[CLIENT]:raise ValueError("RED_GQ8_ONLY_ONE_CLIENT_MAY_CHANGE_"+str(changed))
    before=old[CLIENT].read_text(encoding="utf8")
    after=new[CLIENT].read_text(encoding="utf8")
    validate_current_before(before)
    if patch(before)!=after or undo(after)!=before:
        raise ValueError("RED_GQ8_INVERSE_AND_SELECTED_SOURCE")
    if not new[CLIENT].name.endswith(".client.luau"):
        raise ValueError("RED_GQ8_SCRIPT_KIND")
    return before,after,new

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/FILE).exists() or (out.parent/RECEIPT).exists():
        raise ValueError("RED_GQ8_OUTPUT_COLLISION")
    proj,old=mapping(base)
    before=old[CLIENT].read_text(encoding="utf8")
    validate_current_before(before)
    after=patch(before)
    (out.parent/FILE).write_text(after,encoding="utf8")
    copy_proj=copy.deepcopy(proj)
    copy_proj["tree"][CLIENT[0]][CLIENT[1]][CLIENT[2]]["$path"]=FILE
    out.write_text(json.dumps(copy_proj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,_,files=checked(base,out)
    rec={
      "feature_id":FEATURE,"original_author_commit":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
      "original_client_blob":ORIGINAL_GIT_BLOB,"source_count":31,
      "gq81_confirmed_hit042_preserved":True,
      "only_changed_existing_client":CLIENT[-1],"other30_byte_exact":True,"off_exact":True,
      "new_game_remote_score_store_scripts":0,"added_scripts":0,
      "no_replacement_combat_game_host_swarm":True,
      "before_sha256":sha(before.encode()),"after_sha256":sha(after.encode()),
      "source_kind":"LocalScript","native":"PENDING","rojo":"PENDING",
      "studio_2client":"NOT_TESTED","android15m":"NOT_TESTED","owner_fun":"NOT_TESTED",
    }
    (out.parent/RECEIPT).write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("GQ8_ACTUAL_CURRENT31_SINGLE_CLIENT_30_BYTES_IDENTICAL_ROLLBACK_PASS")

def verify(base:Path,out:Path,place:Path):
    before,after,files=checked(base,out)
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ8_ROJO_PROPS")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in found:raise ValueError("RED_GQ8_ROJO_NAME")
        found[name]=(cls,source.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={r[-1] for r in files}:raise ValueError("RED_GQ8_ROJO_SET")
    for route,path in files.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(kind,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_GQ8_ROJO_CLASS_OR_SOURCE_"+route[-1])
    receipt=out.parent/RECEIPT
    rec=json.loads(receipt.read_text(encoding="utf8"))
    if rec["before_sha256"]!=sha(before.encode()) or rec["after_sha256"]!=sha(after.encode()):
        raise ValueError("RED_GQ8_RECEIPT_DRIFT")
    rec.update(native="31/31",rojo="31/31",
       selected_place_bytes=place.stat().st_size,
       selected_place_sha256=sha(place.read_bytes()))
    receipt.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("GQ8_ACTUAL31_FULL_NATIVE_ROJO_SOURCE_CLASS_EXACT_PASS",rec["selected_place_bytes"])

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("prepare","verify"))
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--place",type=Path)
    a=ap.parse_args()
    if a.command=="prepare":prepare(a.base,a.out)
    else:
       if a.place is None:ap.error("--place is required for verify")
       verify(a.base,a.out,a.place)
