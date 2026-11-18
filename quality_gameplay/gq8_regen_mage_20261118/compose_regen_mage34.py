#!/usr/bin/env python3
"""Source-lock crosslane intake: existing #775 Regen33 + exact #777 Mage32 -> 34.

The extra source is the immutable author's MageRevive ModuleScript. The existing
(single) Host gets two Mage attach hooks after already-installed Regen attach;
original Gameplay/Combat/Store/Swarm etc untouched; OFF is exact official31.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

HOST=("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
REGEN={
    ("ServerScriptService","EGGRUMBLE_NaturalRegen"),
    ("ServerScriptService","EGGRUMBLE_PassiveRegenPolicy"),
}
MAGE=("ServerScriptService","EGGRUMBLE_MageRevive")
EXPECTED_MAGE_BLOB="c75c2db439a5a68f2bc866ad42562fc16687849d"
REGEN_REQUIRE='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
MAGE_REQUIRE='local MageRevive=require(script.Parent:WaitForChild("EGGRUMBLE_MageRevive"))'
REGEN_ATTACH='NaturalRegen.attach(session,p,role)'
MAGE_ATTACH='MageRevive.attach(session,p,role)'

def files(project:Path):
    project=Path(project).resolve(strict=True)
    model=json.loads(project.read_text(encoding="utf-8"))
    if not isinstance(model.get("tree"),dict):
        raise ValueError("RED_PROJECT_TREE")
    out={}
    def walk(node,route=()):
        for name,entry in node.items():
            if name.startswith("$"):continue
            if not isinstance(entry,dict):raise ValueError("RED_INVALID_ROUTE")
            here=route+(name,)
            if "$path" in entry:
                if here in out or not isinstance(entry["$path"],str):
                    raise ValueError("RED_DUPLICATE_ROUTE")
                out[here]=(project.parent/entry["$path"]).resolve(strict=True)
            else:walk(entry,here)
    walk(model["tree"])
    return model,out

def git_blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def compose(original31:Path,regen33:Path,mage_source:Path,out:Path,mage_expected_blob=EXPECTED_MAGE_BLOB):
    original31=Path(original31).resolve(strict=True)
    regen33=Path(regen33).resolve(strict=True)
    mage_source=Path(mage_source).resolve(strict=True)
    out=Path(out).resolve()
    if out.exists() or out in (original31,regen33,mage_source):
        raise ValueError("RED_OUTPUT_OVERWRITE")
    if git_blob(mage_source)!=mage_expected_blob:
        raise ValueError("RED_MAGE_SOURCE_BLOB_CHANGED")
    base_model,base=files(original31)
    regen_model,reg=files(regen33)
    if len(base)!=31 or len(reg)!=33 or HOST not in base:
        raise ValueError("RED_NOT_GENUINE31_AND_REGEN33")
    if set(reg)-set(base)!=REGEN or MAGE in reg:
        raise ValueError("RED_REGEN_SOURCE_OWNERSHIP_COLLISION")
    if len({route[-1] for route in base})!=31:
        raise ValueError("RED_DUPLICATE_ORIGINAL_NAMES")
    for route,p in base.items():
        if route!=HOST and digest(p)!=digest(reg[route]):
            raise ValueError("RED_ORIGINAL_MUTATION_"+"/".join(route))
    actual_host=reg[HOST].read_text(encoding="utf-8")
    original_host=base[HOST].read_text(encoding="utf-8")
    if (actual_host.count(REGEN_REQUIRE)!=1 or
        actual_host.count(REGEN_ATTACH)!=2 or
        actual_host.count(MAGE_ATTACH)!=0 or
        MAGE_REQUIRE in actual_host):
        raise ValueError("RED_REGEN_HOST_MALFORMED")
    reversed_host=actual_host.replace(REGEN_REQUIRE+"\n","",1)
    reversed_host,n=re.subn(r"(?m)^[ \t]*NaturalRegen\.attach\(session,p,role\)\n","",reversed_host)
    if n!=2 or reversed_host!=original_host:
        raise ValueError("RED_REGEN_HOST_UNAPPROVED_EDIT")
    # The sole Host has ordered real role equip -> regen -> Mage rescue on both
    # original attach/respawn callsites. No copy of the author Mage Lua.
    host=actual_host.replace(REGEN_REQUIRE,REGEN_REQUIRE+"\n"+MAGE_REQUIRE,1)
    host,n=re.subn(r"(?m)^([ \t]*)NaturalRegen\.attach\(session,p,role\)[ \t]*$",
                   lambda m:m.group(0)+"\n"+m.group(1)+MAGE_ATTACH,host)
    if n!=2 or host.count(MAGE_ATTACH)!=2 or host.count(MAGE_REQUIRE)!=1:
        raise ValueError("RED_MAGE_HOOK_ADDITION")
    model=copy.deepcopy(regen_model)
    model["name"]="GQ8_REGEN33_MAGE32_CURRENT31_COMBINED34_NOT_OFFICIAL"
    out.parent.mkdir(parents=True,exist_ok=True)
    host_copy=out.parent/"GQ8_CombinedHost.server.luau"
    if host_copy.exists():
        raise ValueError("RED_HOST_COPY_EXISTS")
    host_copy.write_text(host,encoding="utf-8",newline="\n")
    def rebase(node,route=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            here=route+(k,)
            if "$path" in v:
                source=host_copy if here==HOST else reg[here]
                v["$path"]=os.path.relpath(source,out.parent).replace(os.sep,"/")
            else:rebase(v,here)
    rebase(model["tree"])
    if MAGE[-1] in model["tree"]["ServerScriptService"]:
        raise ValueError("RED_SECOND_MAGE_MODULE")
    model["tree"]["ServerScriptService"][MAGE[-1]]={
        "$path":os.path.relpath(mage_source,out.parent).replace(os.sep,"/")
    }
    out.write_text(json.dumps(model,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,combined=files(out)
    if len(combined)!=34 or set(combined)!=set(base)|REGEN|{MAGE}:
        raise ValueError("RED_NOT_EXACT_34")
    for route,p in reg.items():
        if route!=HOST and digest(p)!=digest(combined[route]):
            raise ValueError("RED_REGEN_OWNER_BLOB_MUTATION_"+"/".join(route))
    if digest(combined[MAGE])!=digest(mage_source):
        raise ValueError("RED_MAGE_BLOB_MUTATED")
    for route,p in base.items():
        if route!=HOST and digest(combined[route])!=digest(p):
            raise ValueError("RED_ORIGINAL31_MUTATION")
    evidence={
        "feature_id":"GQ8_REGEN_MAGE_CROSSLANE_20261118",
        "source_count":34,"source_additions":3,
        "original31_except_host_byte_exact":True,
        "new_regen_policy_and_adapter_author_bytes_exact":True,
        "new_mage_module_author_bytes_exact":True,
        "mage_blob":git_blob(mage_source),
        "host_sole_authority":True,
        "host_hooks":{"regen":2,"mage":2},
        "source_owner":{"regen_pr":775,"policy_pr":773,"mage_pr":777},
        "base_31_source_sha256":{"/".join(k):digest(p) for k,p in sorted(base.items())},
        "formal_rc_changed":False,"studio_tested":False,"android_tested":False,
        "rollback":"Original 31 project byte-exact; omit Regen2 Mage1 modules"
    }
    out.with_suffix(".receipt.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ8_REGEN_MAGE_ACTUAL34_SOURCE_EXACT_PASS",len(combined))
    return out

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--original31",type=Path,required=True)
    a.add_argument("--regen33",type=Path,required=True)
    a.add_argument("--mage-source",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    compose(args.original31,args.regen33,args.mage_source,args.out)
