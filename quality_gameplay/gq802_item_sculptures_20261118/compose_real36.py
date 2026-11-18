#!/usr/bin/env python3
"""Inject only the existing Item visual into ORIGINAL official Core36 project."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from patch_item import apply, inverse, git_blob_sha, FEATURE

ITEM=("ServerScriptService","EGGRUMBLE_FieldItemPickups")
def flatten(project:Path):
    p=project.resolve(strict=True)
    obj=json.loads(p.read_text(encoding="utf-8"))
    files={}
    def rec(node,path=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            t=path+(k,)
            if "$path" in v:
                assert t not in files,"RED_DUPLICATE_SCRIPT_ROUTE"
                files[t]=(p.parent/v["$path"]).resolve(strict=True)
            else:rec(v,t)
    rec(obj["tree"])
    return obj,files

def compose(project:Path,off31:Path,out:Path):
    project=project.resolve(strict=True)
    off31=off31.resolve(strict=True)
    out=out.resolve()
    assert out.parent==project.parent and not out.exists(),"RED_OUTPUT_PROVENANCE"
    doc,live=flatten(project)
    _,old=flatten(off31)
    assert len(live)==36 and len(old)==31,"RED_CORE36_OFF31_COUNT"
    assert ITEM in live and ITEM in old,"RED_SINGLE_ITEM_AUTHORITY"
    assert live[ITEM].read_bytes()==old[ITEM].read_bytes(),"RED_ITEM_NOT_ORIGINAL31_IN_CORE36"
    original=live[ITEM].read_bytes()
    modified=apply(original)
    assert inverse(modified)==original,"RED_ITEM_VISUAL_NONINVERSE"
    selected_file=out.parent/"GQ802_FieldItems_ThreeSculptures.luau"
    assert not selected_file.exists(),"RED_OUTPUT_SOURCE_COLLISION"
    selected_file.write_bytes(modified)
    doc["name"]="GQ802_FIELD_ITEMS_TRUE_3D_SILHOUETTE_PRIVATE36_PREP"
    doc["tree"][ITEM[0]][ITEM[1]]["$path"]=selected_file.name
    out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,new=flatten(out)
    assert set(new)==set(live) and len(new)==36,"RED_SOURCE_AUTHORITY_DUPLICATE"
    changed=[p for p in live if live[p].read_bytes()!=new[p].read_bytes()]
    assert changed==[ITEM],"RED_OTHER_35_SCRIPTS_CHANGED"
    assert all(path.read_bytes()==flatten(off31)[1][k].read_bytes() for k,path in old.items()),"RED_OFF31_CHANGED"
    receipt={
        "feature_id":FEATURE,
        "base_source_count":36,"prepared_source_count":36,"off_source_count":31,
        "only_modified_existing_script":"/".join(ITEM),
        "other35_byte_exact":True,"original31_off_byte_exact":True,
        "base_item_sha256":hashlib.sha256(original).hexdigest(),
        "selected_item_sha256":hashlib.sha256(modified).hexdigest(),
        "original_item_git_blob":git_blob_sha(original),
        "selected_item_git_blob":git_blob_sha(modified),
        "new_gameplay_scripts":0,"new_remote_or_datastore_or_score":0,
        "new_gameplay_item_types":0,
        "per_item_max_additional_parts":3,
        "all_decorations_nonquery_noncollidable":True,
        "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
        "art_fun":"NO_GO","official_rc_adopted":False,"published":False,
        "rollback":"OFF original31 item byte exact, existing Realm36 unaffected",
    }
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ802_ITEM_ONE_REAL_EXISTING_SOURCE_35_EXACT_OFF31_PASS",receipt)
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project36",type=Path,required=True)
    ap.add_argument("--off31",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    compose(a.project36,a.off31,a.out)
if __name__=="__main__":main()
