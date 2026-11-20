#!/usr/bin/env python3
"""Read-only PREP compose of four ORIGINAL-author Realm changes in real Core36.

Import the actual source of #792 (station), #796 (Leviathan), #797 (storm)
and #795 (compact client). No rewrite of other authors, new damage
authority, new gameplay Script or formal RC update.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from patch_melee import (
    UPSTREAM_BLOB, INSERT_AT, HELPER, OLD_MELEE, NEW_MELEE,
    git_blob_sha, rollback as rollback_melee,
)

SERVER=("ServerScriptService","EGGRUMBLE_RealmBattleCore")
CLIENT=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls")
FEATURES=[
    "GQ8_REALM_STATION_SERVER_LOS_20261118",
    "GQ8_SUBSEA_LEVIATHAN_MELEE_LOS_20261118",
    "GQ8_REALM_STORM_PHASE_FENCE_20261118",
    "GQ8_REALM_COMPACT_TOUCH_HUD_20261118",
]
AUTHORS={
    "station": "4f741a5901506337cb43a58ff8450210ec9507e3",
    "storm": "458d726fd0e335827e5c64d2c02c0f51fd37e512",
    "compact": "0db4493e11c328707495647ead446cd97b665f6b",
    "subsea_candidate": "68a94cd38b3308961deb3df91553b73179fd7b61",
    "realm_original": "c51de1ed4feb7a7500ada95d21282402053ef988",
}

def module_from_file(path:Path, name:str):
    spec=importlib.util.spec_from_file_location(name,path.resolve(strict=True))
    assert spec and spec.loader,"RED_IMPORT_AUTHOR_MODULE"
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def flatten(project:Path):
    p=project.resolve(strict=True)
    document=json.loads(p.read_text(encoding="utf8"))
    files={}
    def visit(node,route=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            assert isinstance(child,dict),"RED_NOT_ROJO_NODE"
            key=route+(name,)
            if "$path" in child:
                assert key not in files,"RED_DUPLICATE_ROUTE"
                files[key]=(p.parent/child["$path"]).resolve(strict=True)
            else:visit(child,key)
    visit(document["tree"])
    return document,files

def compose(project36:Path,off31:Path,original_server:Path,original_client:Path,
            station_module:Path,storm_module:Path,compact_module:Path,
            compact_candidate:Path,output:Path):
    src_doc,src=flatten(project36)
    _,off=flatten(off31)
    assert len(src)==36 and len(off)==31,"RED_SOURCE_COUNT_36_OR_31"
    assert SERVER in src and CLIENT in src,"RED_REALM_SOURCE_ROUTE_MISSING"
    assert SERVER not in off and CLIENT not in off,"RED_ORIGINAL31_ALREADY_HAS_REALM"
    original_server_bytes=original_server.resolve(strict=True).read_bytes()
    original_client_bytes=original_client.resolve(strict=True).read_bytes()
    assert git_blob_sha(original_server_bytes)==UPSTREAM_BLOB,"RED_REALM_SERVER_AUTHOR_BLOB"
    station=module_from_file(station_module,"gq8_original_station792")
    storm=module_from_file(storm_module,"gq8_original_storm797")
    hud=module_from_file(compact_module,"gq8_original_hud795")
    assert station.UPSTREAM_BLOB==storm.SOURCE_BLOB==UPSTREAM_BLOB,"RED_AUTHOR_SERVER_BLOB_DISAGREES"
    assert hud.git_blob(original_client_bytes)==hud.ORIGINAL_BLOB,"RED_ORIGINAL_CLIENT_BLOB"
    assert original_client_bytes.decode().count(hud.ANCHOR)==1,"RED_CLIENT_ANCHOR"
    candidate_client=compact_candidate.resolve(strict=True).read_bytes()
    expected_client=original_client_bytes.decode().replace(hud.ANCHOR,hud.INSERT,1).encode()
    assert expected_client==candidate_client,"RED_AUTHOR_COMPACT_CLIENT_DRIFT"
    assert src[CLIENT].read_bytes()==original_client_bytes,"RED_REAL36_CLIENT_NOT_ORIGINAL"

    # Only existing original #792 + independent #796 should already be selected.
    shared=src[SERVER].read_bytes()
    expected_station=station.apply(original_server_bytes).decode()
    expected_shared=expected_station.replace(INSERT_AT,HELPER+INSERT_AT,1).replace(OLD_MELEE,NEW_MELEE,1).encode()
    assert shared==expected_shared,"RED_STATION_MELEE_COMPOSE_BASE_DRIFT"
    # Existing original-author #797 policy has exactly 2 disjoint fixed anchors.
    storm_first=storm.patch_source(original_server_bytes,verify_blob=True).decode()
    assert storm_first.count(storm.PATCHED_TRANSITION)==1
    assert storm_first.count(storm.PATCHED_STRIKE)==1
    combined=storm.patch_source(shared,verify_blob=False)
    assert combined.decode().count(storm.PATCHED_TRANSITION)==1
    assert combined.decode().count(storm.PATCHED_STRIKE)==1
    # Independently prove overlay composition commutes from immutable source.
    other_order=storm_first.replace(station.OLD,station.NEW,1).replace(INSERT_AT,HELPER+INSERT_AT,1).replace(OLD_MELEE,NEW_MELEE,1).encode()
    assert combined==other_order,"RED_REALM_FOUR_LANE_ORDER_CONFLICT"
    # Reverse #797, #792 and #796, check exact immutable original, preserving other author.
    unstorm=combined.decode().replace(storm.PATCHED_TRANSITION,storm.ORIGINAL_TRANSITION,1).replace(storm.PATCHED_STRIKE,storm.ORIGINAL_STRIKE,1)
    assert unstorm.encode()==shared,"RED_STORM_INVERSE"
    unstation=unstorm.replace(station.NEW,station.OLD,1).encode()
    assert rollback_melee(unstation)==original_server_bytes,"RED_REALM_ALL_SERVER_INVERSE"
    client_rollback=candidate_client.decode().replace(hud.INSERT,hud.ANCHOR,1).encode()
    assert client_rollback==original_client_bytes,"RED_COMPACT_CLIENT_INVERSE"
    assert src[SERVER].read_bytes()==shared,"RED_PRIOR_TWO_LANE_SOURCE_DRIFT"

    output=output.resolve()
    assert not output.exists() and output.parent==project36.resolve(strict=True).parent,"RED_OUTPUT_LOCATION_OR_EXISTS"
    server_out=output.parent/"GQ8_RealmCore_Station_Subsea_Storm.server.luau"
    client_out=output.parent/"GQ8_RealmControls_Compact.client.luau"
    assert not server_out.exists() and not client_out.exists(),"RED_SOURCE_OUTPUT_COLLISION"
    server_out.write_bytes(combined)
    client_out.write_bytes(candidate_client)
    def route_node(doc,route):
        node=doc["tree"]
        for seg in route:node=node[seg]
        return node
    route_node(src_doc,SERVER)["$path"]=server_out.name
    route_node(src_doc,CLIENT)["$path"]=client_out.name
    src_doc["name"]="GQ8_REALM_FOUR_AUTHOR_FIXES_REAL36_PREP"
    output.write_text(json.dumps(src_doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,selected=flatten(output)
    assert len(selected)==36 and set(selected)==set(src),"RED_SOURCE_ROUTE_DRIFT"
    modified=[k for k in src if src[k].read_bytes()!=selected[k].read_bytes()]
    assert set(modified)=={SERVER,CLIENT},"RED_MORE_THAN_TWO_REALM_SCRIPTS"
    assert selected[SERVER].read_bytes()==combined and selected[CLIENT].read_bytes()==candidate_client,"RED_SELECTED_SOURCE_NOT_MATCH"
    assert all(f.read_bytes()==flatten(off31)[1][r].read_bytes() for r,f in off.items()),"RED_ORIGINAL31_CHANGED"
    receipt={
        "status":"PREP_READY_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "original_author_heads":AUTHORS,
        "feature_ids":FEATURES,
        "original_server_git_blob":UPSTREAM_BLOB,
        "selected_server_git_blob":git_blob_sha(combined),
        "original_client_git_blob":hud.ORIGINAL_BLOB,
        "selected_client_git_blob":hud.git_blob(candidate_client),
        "same_original_36_script_routes":True,
        "script_count_on":36,"script_count_off":31,
        "existing_original_scripts_changed":["/".join(SERVER),"/".join(CLIENT)],
        "other_34_source_blobs_equal":True,
        "author_transformations_commute":True,
        "server_original_rollback_exact":True,
        "client_original_rollback_exact":True,
        "original31_off_exact":True,
        "new_authorities_or_gameplay_scripts":0,
        "owner_studio":"NOT_TESTED","android_15min":"NOT_TESTED",
        "kid_fun":"NO_GO","formal_rc_adopted":False,"published":False,
        "source_sha256_server":hashlib.sha256(combined).hexdigest(),
        "source_sha256_client":hashlib.sha256(candidate_client).hexdigest(),
    }
    output.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    return receipt

def main():
    arg=argparse.ArgumentParser()
    for name in ("project36","off31","original-server","original-client","station-module",
                 "storm-module","compact-module","compact-candidate","out"):
        arg.add_argument("--"+name,type=Path,required=True)
    a=arg.parse_args()
    kw=vars(a)
    print(json.dumps(compose(kw["project36"],kw["off31"],kw["original_server"],
        kw["original_client"],kw["station_module"],kw["storm_module"],
        kw["compact_module"],kw["compact_candidate"],kw["out"]),sort_keys=True,ensure_ascii=False))
if __name__=="__main__":
    main()
