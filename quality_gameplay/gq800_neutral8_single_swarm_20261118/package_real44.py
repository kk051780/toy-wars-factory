#!/usr/bin/env python3
"""Portable B intake of exact 44 source paths with unchanged 43-source rollback."""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from pathlib import Path
from compose_charm44 import flatten,blob,SWARM,CHARM,FINISHER,CHARM_BLOB

def pack(original43:Path,real44:Path,out:Path,head:str):
    if not re.fullmatch(r"[0-9a-f]{40}",head):
        raise ValueError("RED_BAD_CANDIDATE_SHA")
    _,old=flatten(original43)
    doc,live=flatten(real44)
    if len(old)!=43 or len(live)!=44 or set(live)!=set(old)|{CHARM}:
        raise ValueError("RED_NOT_ORIGINAL43_PLUS_EXACT_CURSE")
    if FINISHER not in old or CHARM in old or SWARM not in old:
        raise ValueError("RED_ORIGINAL_SINGLE_SWARM_MISSING")
    if blob(live[CHARM].read_bytes())!=CHARM_BLOB:
        raise ValueError("RED_MUTATED_ORIGINAL_CURSE_POLICY")
    if any(live[route].read_bytes()!=source.read_bytes()
           for route,source in old.items() if route!=SWARM):
        raise ValueError("RED_OTHER_AUTHOR_SOURCE_CHANGED")
    if live[SWARM].read_bytes()==old[SWARM].read_bytes():
        raise ValueError("RED_NO_ACTUAL_CURSE_GAMEPLAY")
    out=Path(out).resolve()
    if out.exists() or out.parent.exists():
        raise ValueError("RED_REFUSE_OVERWRITE_PORTABLE")
    out.parent.mkdir(parents=True)
    new=copy.deepcopy(doc)
    new["name"]="GQ800_SINGLE_SWARM_TERRAIN_AND_CURSE_REAL44_PORTABLE_NOT_OFFICIAL"
    receipts=[]
    def suffix(path:Path):
        name=path.name
        for value in (".client.luau",".server.luau",".luau"):
            if name.endswith(value):return value
        raise ValueError("RED_UNKNOWN_LUAU_CLASS")
    for route,source in sorted(live.items()):
        relative=Path("sources").joinpath(*route[:-1],route[-1]+suffix(source))
        dst=out.parent/relative
        dst.parent.mkdir(parents=True,exist_ok=True)
        data=source.read_bytes()
        dst.write_bytes(data)
        node=new["tree"]
        for key in route:node=node[key]
        node["$path"]=relative.as_posix()
        receipts.append({"route":"/".join(route),"path":relative.as_posix(),
            "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
            "origin":"original43_exact" if route in old and route!=SWARM
                else ("singleton_swarm_scope_overlay" if route==SWARM else "original_801_curse_policy")})
    out.write_text(json.dumps(new,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    _,portable=flatten(out)
    if set(portable)!=set(live) or any(portable[r].read_bytes()!=f.read_bytes() for r,f in live.items()):
        raise ValueError("RED_PORTABLE_AUTHOR_SOURCE_CLASS_DRIFT")
    receipt={
      "schema":"GQ800_SINGLETON_44_PORTABLE_B_INTAKE_V1",
      "current_candidate_sha":head,
      "original_source_count":43,"candidate_source_count":44,
      "remaining_original43_byte_exact":42,
      "modified_original":["/".join(SWARM)],
      "added_exact_original_801":["/".join(CHARM)],
      "curse_original_blob":CHARM_BLOB,
      "original_real43_swarm_blob":blob(old[SWARM].read_bytes()),
      "new_single_swarm_blob":blob(live[SWARM].read_bytes()),
      "rollback":"Select exact complete portable43 from same CI; no second Swarm",
      "official_rc_adopted":False,"studio_2client":"NOT_TESTED",
      "android15":"NOT_TESTED","owner_fun":"NO_GO",
      "sources":receipts}
    (out.parent/"B_PORTABLE44_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ800_PORTABLE44_SINGLETON_NO_OTHER_SOURCE_CHANGED_PASS",
        sum(x["bytes"] for x in receipts))
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original43",required=True,type=Path)
    p.add_argument("--real44",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--candidate-head",required=True)
    args=p.parse_args()
    pack(args.original43,args.real44,args.out,args.candidate_head)
