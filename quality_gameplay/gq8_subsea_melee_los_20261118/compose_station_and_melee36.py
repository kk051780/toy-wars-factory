#!/usr/bin/env python3
"""Reconcile #792 original station LOS + #796 subsea LOS in *one* Realm source.

No second implementation of station LOS. Read pinned upstream #792 patch
from its original branch and compose disjoint byte-locked transformations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from patch_melee import (
    apply as apply_melee, rollback as rollback_melee,
    git_blob_sha, UPSTREAM_BLOB, INSERT_AT, HELPER,
    OLD_MELEE, NEW_MELEE,
)

TARGET=("ServerScriptService","EGGRUMBLE_RealmBattleCore")
HEAD_STATION="4f741a5901506337cb43a58ff8450210ec9507e3"
HEAD_AUTHOR="c51de1ed4feb7a7500ada95d21282402053ef988"
SCRIPT_COUNT=36
OFF_COUNT=31

def compose(original_file:Path,station_library:Path,station_project:Path,
            off_project:Path,out_project:Path):
    sys.path.insert(0,str(station_library.resolve(strict=True)))
    from patch_realm_station_los import OLD as STATION_OLD, NEW as STATION_NEW, apply as apply_station
    from compose_real36 import flatten
    original=original_file.resolve(strict=True).read_bytes()
    assert git_blob_sha(original)==UPSTREAM_BLOB,"RED_ORIGINAL_REALM_AUTHOR_BLOB"
    original_source=original.decode()
    stations=flatten(station_project)
    off=flatten(off_project)
    assert len(stations)==SCRIPT_COUNT and len(off)==OFF_COUNT,"RED_REAL36_OFF31_COUNT"
    assert TARGET in stations and TARGET not in off,"RED_STATION_REALM_TARGET_ROUTE"
    selected_station=stations[TARGET].read_bytes()
    assert selected_station==apply_station(original),"RED_STATION_OWNER_SOURCE_DRIFT"
    station_text=selected_station.decode()
    assert station_text.count(INSERT_AT)==1 and station_text.count(OLD_MELEE)==1
    assert station_text.count(HELPER)==0 and station_text.count(NEW_MELEE)==0
    # First apply the existing station owner, then ONLY our neutral melee anchor.
    combined=station_text.replace(INSERT_AT,HELPER+INSERT_AT,1).replace(OLD_MELEE,NEW_MELEE,1).encode()
    # Both truly independent original-author modifications commute exactly.
    melee_first=apply_melee(original).decode().replace(STATION_OLD,STATION_NEW,1).encode()
    assert combined==melee_first,"RED_CROSSLANE_ORDER_DEPENDENCE"
    # Undo the actual station owner, then our own overlay, byte-exact original.
    undo_station=combined.decode().replace(STATION_NEW,STATION_OLD,1).encode()
    assert rollback_melee(undo_station)==original,"RED_COMBINED_ROLLBACK_BROKEN"
    assert combined!=selected_station,"RED_MELEE_NOT_SELECTED"
    out_project=out_project.resolve()
    assert not out_project.exists() and out_project.parent==station_project.resolve().parent, "RED_OVERWRITE_OR_PROJECT_DIR"
    source_file=out_project.parent/"GQ8_RealmBattleCore_Station_SubseaLOS.server.luau"
    assert not source_file.exists(),"RED_SOURCE_ALREADY_EXISTS"
    source_file.write_bytes(combined)
    document=json.loads(station_project.read_text())
    node=document["tree"]
    for key in TARGET: node=node[key]
    node["$path"]=os.path.relpath(source_file,out_project.parent).replace(os.sep,"/")
    document["name"]="EGGRUMBLE_CORE36_STATION_AND_SUBSEA_LOS_PREP"
    out_project.write_text(json.dumps(document,indent=2,ensure_ascii=False)+"\n")
    modified=flatten(out_project)
    assert len(modified)==36 and set(modified)==set(stations),"RED_AUTHORITY_OR_ROUTE_CHANGE"
    changed=[key for key in stations if stations[key].read_bytes()!=modified[key].read_bytes()]
    assert changed==[TARGET],"RED_MORE_THAN_ORIGINAL_REALM_SERVER_CHANGED"
    assert all(path.read_bytes()==flatten(off_project)[key].read_bytes() for key,path in off.items()),"RED_OFF31_MUTATED"
    receipt={
        "feature_ids":["GQ8_REALM_STATION_SERVER_LOS_20261118",
                       "GQ8_SUBSEA_LEVIATHAN_MELEE_LOS_20261118"],
        "status":"SOURCE_PREP_ONLY_NOT_OFFICIAL_RC",
        "source_owner_station_head":HEAD_STATION,
        "source_owner_realm_head":HEAD_AUTHOR,
        "original_author_blob":UPSTREAM_BLOB,
        "combined_server_git_blob":git_blob_sha(combined),
        "combined_server_sha256":hashlib.sha256(combined).hexdigest(),
        "source_count_on":36,"source_count_off":31,
        "new_script_count":0,"modified_existing_script_count":1,
        "modified_existing_script":"/".join(TARGET),
        "other_35_sources_byte_exact":True,
        "station_and_melee_patch_commute":True,
        "original_author_byte_exact_rollback":True,
        "original31_off_byte_exact":True,
        "new_damage_owner":0,"new_remote_owner":0,"new_score_owner":0,
        "formal_rc_adopted":False,
        "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
        "art_fun":"NO_GO"
    }
    out_project.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    return receipt

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--original",type=Path,required=True)
    a.add_argument("--station-library",type=Path,required=True)
    a.add_argument("--station-project",type=Path,required=True)
    a.add_argument("--off31",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    x=a.parse_args()
    print(json.dumps(compose(x.original,x.station_library,x.station_project,x.off31,x.out),
                     ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
