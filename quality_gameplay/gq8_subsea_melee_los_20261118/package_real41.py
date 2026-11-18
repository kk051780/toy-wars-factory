#!/usr/bin/env python3
"""Source-exact 41-file portable packet for authenticated official RC writer B.
Never grants rights, never updates RC, main or Roblox. Original sources only.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from package_real39 import flatten,source_class,git_blob
from compose_siege41 import H,B,P,G,REALM,HUD,ITEM,STAGE

CHANGED={H,B,REALM,HUD,ITEM}
NEW=STAGE|{P,G}
def package(real41:Path,core36:Path,out:Path,sha:str)->dict:
    real41=real41.resolve(strict=True)
    core36=core36.resolve(strict=True)
    out=out.resolve()
    if not re.fullmatch("[0-9a-f]{40}",sha):raise ValueError("RED_MISSING_CANDIDATE_HEAD")
    doc,new=flatten(real41)
    _,old=flatten(core36)
    if len(new)!=41 or len(old)!=36:raise ValueError("RED_NOT_41_FROM_CORE36")
    if set(new)-set(old)!=NEW:raise ValueError("RED_WRONG_ADDED_SOURCE")
    if {k for k in old if old[k].read_bytes()!=new[k].read_bytes()}!=CHANGED:
        raise ValueError("RED_NOT_EXACT_FIVE_ORIGINAL_HOOKS")
    if len(set(old)-CHANGED)!=31:raise ValueError("RED_ORIGINAL31_CHANGED")
    if out.exists() or out.parent.exists():
        raise ValueError("RED_PORTABLE_OUTPUT_ALREADY_EXISTS")
    out.parent.mkdir(parents=True)
    product=copy.deepcopy(doc)
    product["name"]="GQ8_REAL41_PORTABLE_SOURCE_PREP_NOT_RC"
    entries=[]
    for route,source in sorted(new.items()):
        ext,cls=source_class(source)
        target=Path("sources").joinpath(*route[:-1],route[-1]+ext)
        if not all(re.fullmatch(r"[A-Za-z0-9_]+",x) for x in route):
            raise ValueError("RED_SOURCE_ROUTE_TRAVERSAL")
        p=out.parent/target
        if p.exists():raise ValueError("RED_DUPLICATE_FILE")
        p.parent.mkdir(parents=True,exist_ok=True)
        value=source.read_bytes()
        p.write_bytes(value)
        node=product["tree"]
        for x in route:node=node[x]
        node["$path"]=target.as_posix()
        entries.append({
            "route":"/".join(route),"path":target.as_posix(),"class":cls,
            "bytes":len(value),"sha256":hashlib.sha256(value).hexdigest(),
            "git_blob":git_blob(value),
            "origin":"original_author_optional_module" if route in NEW else
                     "existing_original_script_with_verified_overlay" if route in CHANGED else
                     "unchanged_official_original_core36",
        })
    out.write_text(json.dumps(product,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    _,readback=flatten(out)
    if len(readback)!=41 or set(readback)!=set(new):raise ValueError("RED_PORTABLE_ROUTE_DIFFERENCE")
    for route,source in new.items():
        if readback[route].read_bytes()!=source.read_bytes():
            raise ValueError("RED_PORTABLE_SCRIPT_CHANGED")
        if source_class(readback[route])[1]!=source_class(source)[1]:
            raise ValueError("RED_PORTABLE_CLASS_CHANGED")
    receipt={
        "directive_id":"OWNER_LATEST_LINEAGE_SINGLE_RC_DRI_20261118_2104_JST",
        "candidate_sha":sha,
        "state":"PREP_READY_41_SOURCES_BLOCKED_AUTH_NOT_OFFICIAL_RC",
        "source_count":41,
        "original36_source_count":36,
        "original_unchanged_count":31,
        "existing_modified":["/".join(k) for k in sorted(CHANGED)],
        "original_modules_reused":["/".join(k) for k in sorted(NEW)],
        "new_script_count":5,
        "original_siege_author_pr":809,
        "original_stage_author_pr":811,
        "original_policy_manifest_pr":803,
        "rollback":"Original real 36 source manifest and 31 source OFF protected; no main/public update",
        "owner_studio":"NOT_TESTED","android15":"NOT_TESTED","kid_fun":"NO_GO",
        "roblox_published":False,"official_rc_cas":False,"original_code_pinned":True,
        "sources":entries,
    }
    (out.parent/"B_PORTABLE41_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ8_PORTABLE41_ORIGINAL_SOURCE_CLASS_SHA_AND_BYTES_MATCH",
          sum(x["bytes"] for x in entries))
    return receipt

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--real41",type=Path,required=True)
    a.add_argument("--core36",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--candidate-head",required=True)
    x=a.parse_args()
    package(x.real41,x.core36,x.out,x.candidate_head)
