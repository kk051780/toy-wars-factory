#!/usr/bin/env python3
"""Add unchanged #500 original author castle Live + Policy modules and its
original audited host hook to #504 current 30-source PRIVATE game.

27+ optional FX/audio sources kept byte-exact except ONE private host copy.
Author and official RC branches are never written. This is NOT formal adoption.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

CASTLE_MODULES = {
    "EGGRUMBLE_CastleDefenseLive": "EGGRUMBLE_CastleDefenseLive.luau",
    "EGGRUMBLE_CastleDefensePolicy": "EGGRUMBLE_CastleDefensePolicy.luau",
}
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
BASE_NAMES = {
    "EGGRUMBLE_SevenRoleCombat", "EGGRUMBLE_BotActors",
    "EGGRUMBLE_SwarmCombat", "EGGRUMBLE_RaidItemIntake",
    "EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_FieldItemPickups",
    "EGGRUMBLE_CastleMatchRules", "EGGRUMBLE_ScoreBalance",
    "EGGRUMBLE_MatchResultService", "EGGRUMBLE_FlagshipFieldArt",
    "EGGRUMBLE_GQ_ObjectiveCompass", "EGGRUMBLE_RealHitAudio",
    "EGGRUMBLE_CombatFXBudget", "EGGRUMBLE_CombatFXClarity",
}
def sha(file:Path)->str:
    return hashlib.sha256(file.read_bytes()).hexdigest()
def mapped(tree, project:Path):
    def walk(node,prefix=()):
        out={}
        for name,v in node.items():
            if name.startswith("$") or not isinstance(v,dict):continue
            key=prefix+(name,)
            if "$path" in v:
                if set(v)!={"$path"} or key in out:
                    raise ValueError(("unsafe project path",key))
                out[key]=(project.parent/v["$path"]).resolve(strict=True)
            else:
                sub=walk(v,key)
                if out.keys()&sub.keys():raise ValueError("duplicate mapped source")
                out.update(sub)
        return out
    return walk(tree)
def overlay(base_project,base_receipt,castle_composer,castle_live,castle_policy,out):
    project=Path(base_project).resolve(strict=True)
    receipt_file=Path(base_receipt).resolve(strict=True)
    composer=Path(castle_composer).resolve(strict=True)
    live=Path(castle_live).resolve(strict=True)
    policy=Path(castle_policy).resolve(strict=True)
    dest=Path(out).resolve()
    if dest==project or dest.parent!=project.parent:
        raise ValueError("PRIVATE output must be separate in base artifacts directory")
    base=json.loads(project.read_text(encoding="utf-8"))
    prior_receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    if (prior_receipt.get("status")!="SOURCE_ONLY_NOT_OFFICIAL_RC"
        or prior_receipt.get("original_28_sources_preserved") is not True
        or prior_receipt.get("new_source_count")!=30
        or prior_receipt.get("server_count")!=23
        or prior_receipt.get("client_count")!=7):
        raise ValueError("requires exact private audio+original FX owner 30 receipt")
    before=mapped(base["tree"],project)
    names=[k[-1] for k in before]
    if len(before)!=30 or len(set(names))!=30 or not BASE_NAMES.issubset(set(names)):
        raise ValueError("missing original eight-area owner scripts")
    if any(prior_receipt.get("source_sha256",{}).get(k[-1])!=sha(p) for k,p in before.items()):
        raise ValueError("existing 30-source ownership bytes drift")
    server=base["tree"]["ServerScriptService"]
    clients=base["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    if len(server)-1!=23 or len(clients)-1!=7:
        raise ValueError("wrong source service locations")
    host_key=("ServerScriptService",HOST)
    if host_key not in before or any(n in names for n in CASTLE_MODULES):
        raise ValueError("missing original host or duplicate castle defenses")
    if (live.name!=CASTLE_MODULES["EGGRUMBLE_CastleDefenseLive"]
        or policy.name!=CASTLE_MODULES["EGGRUMBLE_CastleDefensePolicy"]):
        raise ValueError("wrong castle original source modules")
    if 'require(script.Parent:WaitForChild("EGGRUMBLE_CastleDefensePolicy"))' not in live.read_text(encoding="utf-8"):
        raise ValueError("castle owner internal module linkage changed")
    modspec=importlib.util.spec_from_file_location("p0d_gq_existing_castle500",composer)
    existing=importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(existing)
    if (set(existing.ADDED)!=set(CASTLE_MODULES) or existing.HOST!=HOST
        or existing.BASE_COUNT!=26):
        raise ValueError("original #500 audited host contract changed")
    original_host=before[host_key].read_text(encoding="utf-8")
    revised=existing.patch_host(original_host)
    if (revised.count("CastleDefense.start(session)")!=1
        or revised.count("session.castleDefenseStop()")!=2):
        raise ValueError("multiple castle start/cleanup callbacks prohibited")
    # Write only to newly generated private files, never the pinned original host.
    private_host=dest.parent/"EGGRUMBLE_CASTLE32_LobbyCastleModesPreview.server.luau"
    if private_host.exists() or dest.exists():
        raise ValueError("fail closed on existing private output")
    private_host.write_text(revised,encoding="utf-8")
    candidate=copy.deepcopy(base)
    candidate["name"]="EGGRUMBLE_SOURCE32_ORIGINAL_GAME_FX_AUDIO_CASTLE_PRIVATE_NOT_RC"
    cserver=candidate["tree"]["ServerScriptService"]
    cserver[HOST]={"$path":os.path.relpath(private_host,dest.parent).replace(os.sep,"/")}
    for name,file in (("EGGRUMBLE_CastleDefenseLive",live),("EGGRUMBLE_CastleDefensePolicy",policy)):
        cserver[name]={"$path":os.path.relpath(file,dest.parent).replace(os.sep,"/")}
    after=mapped(candidate["tree"],dest)
    new_keys={("ServerScriptService",n) for n in CASTLE_MODULES}
    if len(after)!=32 or set(after)-set(before)!=new_keys:
        raise ValueError("32-source castled overlay got unintended mappings")
    if len(cserver)-1!=25 or len(candidate["tree"]["StarterPlayer"]["StarterPlayerScripts"])-1!=7:
        raise ValueError("invalid server/client distribution")
    unchanged=0
    for key,old_file in before.items():
        if key==host_key:
            if sha(old_file)==sha(after[key]):
                raise ValueError("castle defense host was not integrated")
        elif old_file.read_bytes()!=after[key].read_bytes():
            raise ValueError(("unauthorized non-owner source rewrite",key))
        else:unchanged+=1
    if unchanged!=29:raise ValueError("expected 29 unchanged original scripts")
    dest.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt={
        "status":"PRIVATE_SOURCE_ONLY_NOT_AUTHENTICATED_RC",
        "from_source_count":30,"total_source_count":32,
        "original_29_unmodified":True,"private_host_hook_only":HOST,
        "original_castle500_modules":list(CASTLE_MODULES),
        "source_sha256":{k[-1]:sha(p) for k,p in after.items()},
        "previous_receipt_sha256":sha(receipt_file),
        "studio":"NOT_RUN","android":"NOT_RUN",
        "official_rc_integrated":False,"owner_accepted":False,
        "rollback":"remove both optional #500 modules and private host hook",
    }
    (dest.parent/"GQ_AUDIO_FX_CASTLE32_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_CASTLE32_ORIGINAL_30_29_UNCHANGED_HOST_HOOK_2_PASS")
    return receipt
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for opt in ("base_project","base_receipt","castle_composer","castle_live","castle_policy","out"):
        ap.add_argument("--"+opt.replace("_","-"),required=True)
    a=ap.parse_args()
    overlay(a.base_project,a.base_receipt,a.castle_composer,a.castle_live,a.castle_policy,a.out)
