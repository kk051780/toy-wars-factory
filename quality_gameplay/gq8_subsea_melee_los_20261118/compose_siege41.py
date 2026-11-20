#!/usr/bin/env python3
"""Zero reimplementation: compose immutable #809 real Core38 siege into #796 wired39.

The sole Host is the ORIGINAL #809 Host with ORIGINAL #811 visual-stage patch
applied once. BotActors and two castle Modules are exact #809 author-selected
sources. All original 31 other script bodies are byte unchanged. No new
Remote, HP authority, Store, Combat, Game or Roblox release.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,sys
from pathlib import Path

H=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
B=("ServerScriptService","EGGRUMBLE_BotActors")
R=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
P=("ServerScriptService","EGGRUMBLE_CastleSiegeGuardianPolicy")
G=("ServerScriptService","EGGRUMBLE_CastleSiegeBridge")
REALM=("ServerScriptService","EGGRUMBLE_RealmBattleCore")
HUD=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls")
ITEM=("ServerScriptService","EGGRUMBLE_FieldItemPickups")
STAGE={
 ("ServerScriptService","GQ802_StageManifestPolicy"),
 ("ServerScriptService","GQ802_StageTileBlueprintPolicy"),
 ("ServerScriptService","GQ802_StageTileVisualRenderer"),
}

def flatten(project:Path):
    project=project.resolve(strict=True)
    doc=json.loads(project.read_text(encoding="utf-8"));found={}
    def walk(node,route=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            key=route+(k,)
            if "$path" in v:
                if key in found:raise ValueError("RED_DUPLICATE_ROUTE")
                found[key]=(project.parent/v["$path"]).resolve(strict=True)
            else:walk(v,key)
    walk(doc["tree"])
    return doc,found

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def compose(core36:Path,wired39:Path,siege38:Path,stage_author_dir:Path,out:Path):
    core36=core36.resolve(strict=True)
    wired39=wired39.resolve(strict=True)
    siege38=siege38.resolve(strict=True)
    out=out.resolve()
    if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
    base,old=flatten(core36)
    stage_doc,stage=flatten(wired39)
    siege_doc,siege=flatten(siege38)
    if len(old)!=36 or len(stage)!=39 or len(siege)!=38:
        raise ValueError("RED_EXPECT_36_39_38")
    if set(stage)!=set(old)|STAGE or set(siege)!=set(old)|{P,G}:
        raise ValueError("RED_UNEXPECTED_ADDED_AUTHORITY")
    if not {H,B,R}.issubset(old):raise ValueError("RED_MISSING_ORIGINAL_SIEGE_AUTHORITY")
    if stage[B].read_bytes()!=old[B].read_bytes():
        raise ValueError("RED_STAGE_OWNS_BOT_CONFLICT")
    if siege[R].read_bytes()!=old[R].read_bytes():
        raise ValueError("RED_SIEGE_DUPLICATED_RULES")
    # #809 original Author Core38 may modify exactly H+B, never another host.
    changed_siege={r for r in old if old[r].read_bytes()!=siege[r].read_bytes()}
    if changed_siege!={H,B}:raise ValueError("RED_ORIGINAL_SIEGE_OWNS_UNEXPECTED_SOURCE")
    changed_stage={r for r in old if old[r].read_bytes()!=stage[r].read_bytes()}
    if changed_stage!={H,REALM,HUD,ITEM}:
        raise ValueError("RED_STAGE_BATCH_OWNS_UNEXPECTED_SOURCE")
    # Import EXACT original author's single Host visual transform, not our
    # imitation. The original #809 Host already includes the authoritative
    # siege bridge so the stage hook is applied *on top of* that real code.
    sys.path.insert(0,str(stage_author_dir.resolve(strict=True)))
    from wire_actual_host39 import patch as stage_host_patch,inverse as stage_host_inverse
    original_host=old[H].read_text(encoding="utf-8")
    stage_host=stage[H].read_text(encoding="utf-8")
    siege_host=siege[H].read_text(encoding="utf-8")
    if stage_host_patch(original_host)!=stage_host:
        raise ValueError("RED_STAGE_AUTHOR_HOST_DRIFT")
    composed_host=stage_host_patch(siege_host)
    if stage_host_inverse(composed_host)!=siege_host:
        raise ValueError("RED_STAGE_INV_DAMAGED_SIEGE")
    if stage_host_inverse(stage_host)!=original_host:
        raise ValueError("RED_STAGE_INV_DAMAGED_ORIGINAL")
    # Original #809 Host text must be the only CastleSiegeBridge authority.
    if composed_host.count('local SiegeBridge=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeBridge"))')!=1:
        raise ValueError("RED_MISSING_OR_DOUBLE_BRIDGE_AUTHORITY")
    if composed_host.count("session.castleSiegeAttack=SiegeBridge.attach(session,Rules)")!=1:
        raise ValueError("RED_MISSING_OR_DOUBLE_SIEGE_ATTACH")
    if composed_host.count("session.castleSiegeAttack(entry.id,from,120,true)")!=1:
        raise ValueError("RED_ORIGINAL_HUMAN_ATTACK_MISSING")
    if siege[B].read_text(encoding="utf8").count("session.castleSiegeAttack(enemy.id,id,26,false)")!=1:
        raise ValueError("RED_ORIGINAL_AI_ATTACK_MISSING")
    if composed_host.count("GQ802StageVisuals.render(")!=1:
        raise ValueError("RED_LOST_PHYSICAL_STAGE_HOST_HOOK")
    if composed_host.count("GQ802StageVisuals.clear(")!=1:
        raise ValueError("RED_LOST_STAGE_CLEANUP")
    if composed_host.count("NaturalRegen.attach(session,p,role)")!=2:
        raise ValueError("RED_ORIGINAL_REGEN_HOOKS_LOST")
    # Source-selected 41: original 39 plus only two existing author modules.
    outputs={H:composed_host.encode("utf-8"),B:siege[B].read_bytes()}
    out.parent.mkdir(parents=True,exist_ok=True)
    patch_paths={}
    for route,content in outputs.items():
        suffix=".server.luau" if route==H else ".luau"
        p=out.parent/(route[-1]+"_GQ804"+suffix)
        if p.exists():raise ValueError("RED_SOURCE_ALREADY_EXISTS")
        p.write_bytes(content);patch_paths[route]=p
    composed=copy.deepcopy(stage_doc)
    composed["name"]="GQ8_REAL41_STAGE_REALM_ITEM_SIEGE_PRIVATE_NOT_OFFICIAL"
    def relink(node,route=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            dest=route+(k,)
            if "$path" in v:
                v["$path"]=os.path.relpath(patch_paths.get(dest,stage[dest]),out.parent).replace(os.sep,"/")
            else:relink(v,dest)
    relink(composed["tree"])
    for route in (P,G):
        file=siege[route]
        if file.name!="EGGRUMBLE_"+route[-1].replace("EGGRUMBLE_","")+".luau":
            raise ValueError("RED_SIEGE_AUTHOR_MODULE_PATH")
        composed["tree"]["ServerScriptService"][route[-1]]={
            "$path":os.path.relpath(file,out.parent).replace(os.sep,"/")}
    out.write_text(json.dumps(composed,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    _,selected=flatten(out)
    if len(selected)!=41 or set(selected)!=set(stage)|{P,G}:
        raise ValueError("RED_SOURCE41_OR_AUTHORITY_DUPLICATE")
    vs39={r for r in stage if stage[r].read_bytes()!=selected[r].read_bytes()}
    if vs39!={H,B}:raise ValueError("RED_ORIGINAL_STAGE39_OVERWRITTEN")
    vs36={r for r in old if old[r].read_bytes()!=selected[r].read_bytes()}
    if vs36!={H,B,REALM,HUD,ITEM}:
        raise ValueError("RED_CORE36_LOST_OR_TOO_MANY_SCRIPTS")
    for route in set(old)-vs36:
        if old[route].read_bytes()!=selected[route].read_bytes():
            raise ValueError("RED_ORIGINAL_31_SCRIPTS_DRIFT")
    for route in (P,G):
        if selected[route].read_bytes()!=siege[route].read_bytes():
            raise ValueError("RED_AUTHENTIC_AUTHOR_SIEGE_MODULE_DRIFT")
    if selected[H].read_bytes()!=outputs[H]:
        raise ValueError("RED_CONFLICTED_SINGLE_HOST")
    receipt={
        "status":"PREP_REAL41_NATIVE_ROJO_NOT_OFFICIAL_RC",
        "feature_ids":["GQ8_REALM_STATION_LOS","GQ8_SUBSEA_NEUTRAL_LOS",
                       "GQ8_REALM_STORM_CANCEL","GQ8_REALM_COMPACT_HUD",
                       "GQ802_ITEM_SCULPTURE","GQ802_STAGE_VISUAL_WIRED",
                       "GQ804_CASTLE_GATE_WIRED"],
        "source_count":41,
        "original_core36_sources":36,
        "original_sources_modified":["/".join(x) for x in sorted(vs36)],
        "unchanged_original_source_count":31,
        "prior_wired39_diff":["/".join(x) for x in sorted(vs39)],
        "added_stage_modules":["/".join(x) for x in sorted(STAGE)],
        "added_original_siege_modules":["/".join(P),"/".join(G)],
        "author_siege_host_inverse_to_core38_exact":True,
        "author_stage_host_inverse_exact":True,
        "castle_match_rules_single_authority_git_sha256":sha(old[R].read_bytes()),
        "original_botactors_selected_exact":selected[B].read_bytes()==siege[B].read_bytes(),
        "original_31_off":"EXACT_BY_SOURCE_RECEIPT",
        "core36_off":"EXACT_BY_SOURCE_RECEIPT",
        "source39_off":"EXACT_BY_SOURCE_RECEIPT",
        "art_fun_owner":"NO_GO",
        "guardian_ai_runtime":"NOT_WIRED",
        "robux":"NOT_ACTIVE",
        "physical_procedural_battlefield":"NOT_IMPLEMENTED",
        "studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "formal_rc_adopted":False,
    }
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ8_REAL41_ORIGINAL_SIEGE_HOST_STAGE_COMPOSE_LOCK_PASS")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--core36",type=Path,required=True)
    p.add_argument("--wired39",type=Path,required=True)
    p.add_argument("--siege38",type=Path,required=True)
    p.add_argument("--stage-author-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compose(a.core36,a.wired39,a.siege38,a.stage_author_dir,a.out)
