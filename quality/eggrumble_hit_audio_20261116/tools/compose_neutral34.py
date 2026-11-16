#!/usr/bin/env python3
"""Attach original #494 pacing + #501 encounter fairness into the existing
#504 32-script candidate using #501's independently generated dual28 source.

NO new Swarm/loop, no re-authored neutral algorithm; only source-selective map.
29+ source refs remain byte-exact; one private Swarm copy is replaced, two
original owner policies are appended. Official RC untouched.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
PACING=("ServerScriptService","EGGRUMBLE_NeutralSpawnPacing")
FAIR=("ServerScriptService","EGGRUMBLE_NeutralEncounterFairness")
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def mapped(project, root):
    result={}
    def visit(obj,parts=()):
        for n,v in obj.items():
            if n.startswith("$") or not isinstance(v,dict):continue
            k=parts+(n,)
            if "$path" in v:
                if set(v)!={"$path"} or k in result:raise ValueError("unsafe script mapping")
                result[k]=(root.parent/v["$path"]).resolve(strict=True)
            else:visit(v,k)
    visit(project["tree"])
    return result
def compose(base_project, base_receipt, neutral_project, neutral_receipt, out):
    base_path=Path(base_project).resolve(strict=True)
    base_receipt=Path(base_receipt).resolve(strict=True)
    dual_path=Path(neutral_project).resolve(strict=True)
    dual_receipt=Path(neutral_receipt).resolve(strict=True)
    dest=Path(out).resolve()
    if dest.parent!=base_path.parent or dest==base_path or dest.exists():
        raise ValueError("wrong output directory or unintended overwrite")
    source=json.loads(base_path.read_text(encoding="utf-8"))
    rec=json.loads(base_receipt.read_text(encoding="utf-8"))
    neutral=json.loads(dual_path.read_text(encoding="utf-8"))
    nrec=json.loads(dual_receipt.read_text(encoding="utf-8"))
    if (rec.get("status")!="PRIVATE_SOURCE_ONLY_NOT_AUTHENTICATED_RC"
        or rec.get("total_source_count")!=32
        or rec.get("original_29_unmodified") is not True
        or rec.get("private_host_hook_only")!="EGGRUMBLE_LobbyCastleModesPreview"
        or nrec.get("total_mapped")!=28
        or nrec.get("official_rc")!="NOT_ADOPTED"
        or nrec.get("unchanged_original26")!=25):
        raise ValueError("unapproved original source lineage")
    originals=mapped(source,base_path)
    dual=mapped(neutral,dual_path)
    if len(originals)!=32 or len(dual)!=28 or SWARM not in originals or SWARM not in dual:
        raise ValueError("source-count or original Swarm mismatch")
    if any(x in originals for x in (PACING,FAIR)):
        raise ValueError("neutral module was already adopted")
    if set(dual)-{PACING,FAIR} != set(originals)-{k for k in originals if k[-1] in
       {"EGGRUMBLE_CastleDefenseLive","EGGRUMBLE_CastleDefensePolicy",
        "EGGRUMBLE_GQ_ObjectiveCompass","EGGRUMBLE_RealHitAudio",
        "EGGRUMBLE_CombatFXBudget","EGGRUMBLE_CombatFXClarity"}}:
        raise ValueError("neutral author manifest must cover exactly the shared original 26 scripts")
    if sha(originals[SWARM])!=nrec.get("original_swarm_sha256"):
        raise ValueError("baseline Swarm drift from source-authored #501")
    if sha(dual[SWARM])!=nrec.get("dual_swarm_sha256"):
        raise ValueError("dual #494+#501 swarm drift")
    if sha(dual[PACING])!=nrec.get("pacing_policy_sha256") or sha(dual[FAIR])!=nrec.get("fair_policy_sha256"):
        raise ValueError("neutral author policy byte mismatch")
    for k,p in originals.items():
        if sha(p)!=rec.get("source_sha256",{}).get(k[-1]):
            raise ValueError(("base32 source drift",k))
    for k,p in dual.items():
        if k in originals and k!=SWARM and k[-1]!="EGGRUMBLE_LobbyCastleModesPreview":
            if p.read_bytes()!=originals[k].read_bytes():
                raise ValueError(("neutral dual composer altered other owner code",k))
    outmap=copy.deepcopy(source)
    outmap["name"]="EGGRUMBLE_GQ_GAME_AUDIO_FX_CASTLE_NEUTRAL34_PRIVATE"
    server=outmap["tree"]["ServerScriptService"]
    if len(server)-1!=25 or len(outmap["tree"]["StarterPlayer"]["StarterPlayerScripts"])-1!=7:
        raise ValueError("wrong existing client/server distribution")
    server[SWARM[-1]]={"$path":os.path.relpath(dual[SWARM],dest.parent).replace(os.sep,"/")}
    for key in (PACING,FAIR):
        server[key[-1]]={"$path":os.path.relpath(dual[key],dest.parent).replace(os.sep,"/")}
    post=mapped(outmap,dest)
    if len(post)!=34 or len(server)-1!=27 or set(post)-set(originals)!={PACING,FAIR}:
        raise ValueError("new Swarm/policies must be unique")
    for k,p in originals.items():
        if k!=SWARM and p.read_bytes()!=post[k].read_bytes():
            raise ValueError(("unexpected owner source changed",k))
    if sha(post[SWARM])==sha(originals[SWARM]):
        raise ValueError("combined original #494+#501 Swarm never attached")
    if 'EGGRUMBLE_NeutralSpawnPacing' not in post[SWARM].read_text(encoding="utf-8"):
        raise ValueError("pacing Lua reference missing")
    if 'EGGRUMBLE_NeutralEncounterFairness' not in post[SWARM].read_text(encoding="utf-8"):
        raise ValueError("fairness Lua reference missing")
    dest.write_text(json.dumps(outmap,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    final={
        "status":"PRIVATE_SOURCE_ONLY_NOT_AUTHENTICATED_RC",
        "total_source_count":34,"server_scripts":27,"client_scripts":7,
        "unchanged_previous_count":31,"neutral_swarm_private_overlay":True,
        "added_existing_owner_modules":[PACING[-1],FAIR[-1]],
        "unchanged_previous_sha256":{k[-1]:sha(p) for k,p in originals.items() if k!=SWARM},
        "source_sha256":{k[-1]:sha(p) for k,p in post.items()},
        "source32_receipt_sha256":sha(base_receipt),
        "dual28_receipt_sha256":sha(dual_receipt),
        "official_rc_integrated":False,"studio":"NOT_RUN","android":"NOT_RUN",
        "owner_accepted":False,
        "rollback":"restore unchanged 32-source Swarm mapping and remove two optional neutral policies",
    }
    (dest.parent/"GQ_GAME34_NEUTRAL_RECEIPT.json").write_text(
        json.dumps(final,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_NEUTRAL_34_SOURCE_EXACT_31_ORIGINAL_SCRIPTS_UNCHANGED_PASS")
    return final
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for opt in ("base_project","base_receipt","neutral_project","neutral_receipt","out"):
        p.add_argument("--"+opt.replace("_","-"),required=True)
    a=p.parse_args()
    compose(a.base_project,a.base_receipt,a.neutral_project,a.neutral_receipt,a.out)
