#!/usr/bin/env python3
"""Non-writing reuse of #503's two original FX owner modules on top of
#482/#484/#485/#487/#496/#504's immutable exact 28-source Place.

The output is source-only/private; official RC adoption requires #220 CAS.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

ADDED = {
    "EGGRUMBLE_CombatFXBudget": ("EGGRUMBLE_CombatFXBudget.luau", "return Budget"),
    "EGGRUMBLE_CombatFXClarity": ("EGGRUMBLE_CombatFXClarity.client.luau", "isOriginalArenaFX"),
}
ORIGINAL_CLIENTS = {
    "EGGRUMBLE_CombatFeel", "EGGRUMBLE_ProceduralSkills",
    "EGGRUMBLE_ArtDistanceLOD", "EGGRUMBLE_GQ_ObjectiveCompass",
    "EGGRUMBLE_RealHitAudio",
}
REQUIRED_GAME = {
    "EGGRUMBLE_SevenRoleCombat", "EGGRUMBLE_LobbyCastleModesPreview",
    "EGGRUMBLE_CastleMatchRules", "EGGRUMBLE_BotActors",
    "EGGRUMBLE_BotPathRouter", "EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_FieldItemPickups",
    "EGGRUMBLE_RaidItemIntake", "EGGRUMBLE_ScoreBalance",
    "EGGRUMBLE_MatchResultService", "EGGRUMBLE_HeroSilhouetteArt",
}
def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()
def flatten(node, prefix=()):
    mapping={}
    for key, child in node.items():
        if key.startswith("$") or not isinstance(child,dict):
            continue
        name=prefix+(key,)
        if "$path" in child:
            if set(child)!={"$path"} or name in mapping:
                raise ValueError(("invalid map",name))
            mapping[name]=child["$path"]
        else:
            extra=flatten(child,name)
            if mapping.keys() & extra.keys():
                raise ValueError("duplicate map")
            mapping.update(extra)
    return mapping

def compose(base_project, base_receipt, budget_script, client_script, output):
    project=Path(base_project).resolve(strict=True)
    receipt_file=Path(base_receipt).resolve(strict=True)
    budget=Path(budget_script).resolve(strict=True)
    client=Path(client_script).resolve(strict=True)
    output=Path(output).resolve()
    if output==project or output.parent!=project.parent:
        raise ValueError("never overwrite owned private 28-source project")
    data=json.loads(project.read_text(encoding="utf-8"))
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    if (receipt.get("status")!="SOURCE_ONLY_NOT_OFFICIAL_RC"
        or receipt.get("script_count")!=28
        or receipt.get("original_27_sources_preserved") is not True
        or receipt.get("audio_client_added")!="EGGRUMBLE_RealHitAudio"):
        raise ValueError("not approved source-only 28-source owner receipt")
    original=flatten(data["tree"])
    if len(original)!=28 or len({k[-1] for k in original})!=28:
        raise ValueError("wrong 28 original sources")
    server=data["tree"]["ServerScriptService"]
    clients=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    if (server.get("$className")!="ServerScriptService"
        or clients.get("$className")!="StarterPlayerScripts"
        or len(server)-1!=23 or set(clients)-{"$className"}!=ORIGINAL_CLIENTS
        or not REQUIRED_GAME.issubset(set(server)-{"$className"})):
        raise ValueError("missing protected 8-area sources")
    digest={}
    for key, rel in original.items():
        file=(project.parent/rel).resolve(strict=True)
        if file.suffix!=".luau" or not file.is_file():
            raise ValueError(("missing source",key))
        digest[key[-1]]=sha(file.read_bytes())
    if digest["EGGRUMBLE_RealHitAudio"]!=receipt.get("audio_source_sha256"):
        raise ValueError("audio ownership drift")
    original_scripts={"EGGRUMBLE_CombatFXBudget":budget, "EGGRUMBLE_CombatFXClarity":client}
    if (budget.name!=ADDED["EGGRUMBLE_CombatFXBudget"][0]
        or client.name!=ADDED["EGGRUMBLE_CombatFXClarity"][0]):
        raise ValueError("wrong original #503 owner files")
    for key, file in original_scripts.items():
        src=file.read_text(encoding="utf-8")
        if ADDED[key][1] not in src or any(a in src for a in
           ("FireServer(", "TakeDamage(", "SetAttribute(", "Instance.new(\"RemoteEvent\")")):
            raise ValueError(("unauthorized #503 source content",key))
        digest[key]=sha(file.read_bytes())
    composed=copy.deepcopy(data)
    composed["name"]="EGGRUMBLE_GQ_AUTHOR28_AUDIO_OBJECTIVE_FX2_30_PRIVATE"
    for key,file in original_scripts.items():
        composed["tree"]["StarterPlayer"]["StarterPlayerScripts"][key]={
            "$path":os.path.relpath(file,output.parent).replace(os.sep,"/")
        }
    after=flatten(composed["tree"])
    added={("StarterPlayer","StarterPlayerScripts",key) for key in ADDED}
    if len(after)!=30 or set(after)-set(original)!=added:
        raise ValueError("not exactly two original FX owner files")
    if any(after[k]!=v for k,v in original.items()):
        raise ValueError("source rewriting prohibited")
    output.write_text(json.dumps(composed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    result={
        "status":"SOURCE_ONLY_NOT_OFFICIAL_RC",
        "original_28_sources_preserved":True,
        "added_owner":"#503",
        "fx_source_names":list(ADDED),
        "new_source_count":30,"server_count":23,"client_count":7,
        "base_28_receipt_sha256":sha(receipt_file.read_bytes()),
        "base_28_project_sha256":sha(project.read_bytes()),
        "source_sha256":digest,
        "official_rc_integrated":False,"studio":"NOT_TESTED",
        "android":"NOT_TESTED","owner_accepted":False,
    }
    receipt_out=output.parent/"GQ_AUDIO_FX30_RECEIPT.json"
    receipt_out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_28_AUDIO_PLUS_ORIGINAL_FX2_30_SOURCE_PRESERVED_PASS")
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for key in ("base_project","base_receipt","budget_script","client_script","output"):
        ap.add_argument("--"+key.replace("_","-"),required=True)
    a=ap.parse_args()
    compose(a.base_project,a.base_receipt,a.budget_script,a.client_script,a.output)
