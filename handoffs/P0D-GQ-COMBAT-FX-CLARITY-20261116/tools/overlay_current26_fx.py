#!/usr/bin/env python3
"""Only append two optional client cosmetic scripts to #484's already composed
original-author+ART+SCORE 26-source Place. Never rewrite/merge any original.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

ALLOWED = ("EGGRUMBLE_CombatFXBudget", "EGGRUMBLE_CombatFXClarity")
PROTECTED = {"EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_CastleMatchRules",
             "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_SwarmCombat",
             "EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_NeutralStoneGiant",
             "EGGRUMBLE_RaidItemIntake","EGGRUMBLE_MatchResultService",
             "EGGRUMBLE_ScoreBalance","EGGRUMBLE_CombatFeel",
             "EGGRUMBLE_ProceduralSkills","EGGRUMBLE_ArtDistanceLOD"}
def flatten(tree, prefix=()):
    out={}
    for name,child in tree.items():
        if name.startswith("$") or not isinstance(child,dict):continue
        key=prefix+(name,)
        if "$path" in child:
            if set(child)!={"$path"} or key in out:raise ValueError("invalid or duplicate path "+str(key))
            out[key]=child["$path"]
        else:out.update(flatten(child,key))
    return out

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def overlay(base_project,base_receipt,fx_budget,fx_client,out):
    bp=Path(base_project).resolve(strict=True)
    br=Path(base_receipt).resolve(strict=True)
    dest=Path(out).resolve()
    if dest==bp or dest.parent!=bp.parent:
        raise ValueError("Output must be a different project in same artifacts folder")
    receipt=json.loads(br.read_text(encoding="utf-8"))
    if receipt.get("status")!="SOURCE_ONLY_NOT_OFFICIAL_RC" or receipt.get("script_count")!=26:
        raise ValueError("Not an original private 26-source receipt")
    data=json.loads(bp.read_text(encoding="utf-8"))
    prior=flatten(data["tree"])
    if len(prior)!=26 or len({key[-1] for key in prior})!=26:
        raise ValueError("Original 26 source map incomplete or duplicated")
    server=data["tree"]["ServerScriptService"]
    client=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    if server.get("$className")!="ServerScriptService" or client.get("$className")!="StarterPlayerScripts":
        raise ValueError("Expected original Game service placement")
    if len(server)-1!=23 or len(client)-1!=3 or not PROTECTED.issubset({k[-1] for k in prior}):
        raise ValueError("Required 7-role, boss, castle, item, ART, SCORE source missing")
    for chain,relative in prior.items():
        src=(bp.parent/relative).resolve(strict=True)
        if receipt.get("source_sha256",{}).get(chain[-1])!=sha(src):
            raise ValueError("Original 26 source drift "+str(chain))
    clean=copy.deepcopy(data)
    scripts=clean["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    for name,input_path in zip(ALLOWED,(fx_budget,fx_client)):
        script=Path(input_path).resolve(strict=True)
        if name in scripts or name in server:raise ValueError("Already adopted or duplicate "+name)
        if name=="EGGRUMBLE_CombatFXClarity" and not script.name.endswith(".client.luau"):
            raise ValueError("Not a local client script")
        if name=="EGGRUMBLE_CombatFXBudget" and script.name.endswith(".client.luau"):
            raise ValueError("Policy cannot be a second runner")
        code=script.read_text(encoding="utf-8")
        if "FireServer(" in code or "TakeDamage(" in code:
            raise ValueError("Authority violation")
        if name=="EGGRUMBLE_CombatFXClarity" and "isOriginalArenaFX" not in code:
            raise ValueError("Unsafe unscoped client overlay")
        scripts[name]={"$path":os.path.relpath(script,dest.parent).replace(os.sep,"/")}
    clean["name"]="EGGRUMBLE_GQ_26_PLUS_FX2_PRIVATE_NO_PUBLISH"
    final=flatten(clean["tree"])
    expected_add={
        ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFXBudget"),
        ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFXClarity"),
    }
    if len(final)!=28 or set(final)-set(prior)!=expected_add:
        raise ValueError("More than two opt-in sources")
    for k,v in prior.items():
        if final[k]!=v:raise ValueError("Original writer path altered "+str(k))
    dest.write_text(json.dumps(clean,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    source_hash={
        chain[-1]:sha((dest.parent/relative).resolve(strict=True))
        for chain,relative in final.items()
    }
    new_receipt={
        "status":"SOURCE_ONLY_NOT_OFFICIAL_RC","source_count":28,
        "original_26_sources_preserved":True,"server_count":23,"client_count":5,
        "base_receipt_sha256":sha(br),"base_project_sha256":sha(bp),
        "source_sha256":source_hash,"added_client_scripts":list(ALLOWED),
        "official_rc_integrated":False,"studio":"NOT_TESTED",
        "android":"NOT_TESTED","owner_accepted":False,
    }
    rec=dest.parent/"GQ_FX_28_RECEIPT.json"
    rec.write_text(json.dumps(new_receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_FX_REAL26_PLUS_TWO_SOURCE_PRESERVATION_PASS 28")
    return new_receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("base_project","base_receipt","fx_budget","fx_client","out"):
        p.add_argument("--"+name.replace("_","-"),required=True)
    v=p.parse_args()
    overlay(v.base_project,v.base_receipt,v.fx_budget,v.fx_client,v.out)
