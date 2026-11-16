#!/usr/bin/env python3
"""Overlay ONLY #533 neutral target-fallback on existing #530 real author-31 source map.

No second author composer, Swarm, Game, lobby, castle, item, score, or AI.
Composes new unpublished ON and byte-exact original OFF projects.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os
from pathlib import Path
from compose_fallback import apply, sha256

SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
REQUIRED={
    "EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_LobbyCastleModesPreview",
    "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_RaidItemIntake",
    "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_NeutralMeleePolicy","EGGRUMBLE_DualModeNeutralBudget",
    "EGGRUMBLE_BotActors","EGGRUMBLE_BotPathRouter",
    "EGGRUMBLE_MatchResultService","EGGRUMBLE_StatusTickFence",
}

def flat(project:Path):
    project=project.resolve(strict=True)
    tree=json.loads(project.read_text(encoding="utf-8"))
    found={}
    def visit(node, key=()):
        for name,entry in node.items():
            if name.startswith("$"): continue
            route=key+(name,)
            if not isinstance(entry,dict): raise ValueError("RED_INVALID_PROJECT")
            if "$path" in entry:
                if route in found or set(entry)!={"$path"}: raise ValueError("RED_DUPLICATE_MAPPING")
                found[route]=(project.parent/entry["$path"]).resolve(strict=True)
            else:visit(entry,route)
    visit(tree["tree"])
    if len({key[-1] for key in found})!=len(found):
        raise ValueError("RED_DUPLICATE_SCRIPT_NAME")
    return tree,found

def compose(source_project:Path,out_dir:Path) -> dict:
    source_project=source_project.resolve(strict=True)
    out_dir=out_dir.resolve()
    original,parts=flat(source_project)
    if len(parts)!=31 or SWARM not in parts or not REQUIRED<={p[-1] for p in parts}:
        raise ValueError("RED_MISSING_ORIGINAL_31_AUTHOR_SOURCES")
    parent_receipt=source_project.parent/"GQ31_ON_RECEIPT.json"
    receipt=json.loads(parent_receipt.read_text(encoding="utf-8"))
    if receipt.get("source_count")!=31 or receipt.get("official_rc_adopted") is not False:
        raise ValueError("RED_PARENT_RC_RECEIPT")
    for key,part in parts.items():
        if receipt["source_sha256"].get("/".join(key))!=sha256(part.read_bytes()):
            raise ValueError("RED_PARENT_31_SOURCE_DRIFT "+"/".join(key))
    raw=parts[SWARM].read_bytes()
    candidate=apply(raw.decode("utf-8")).encode("utf-8")
    if source_project.parent==out_dir: raise ValueError("RED_OUTPUT_COLLIDES_WITH_PARENT")
    if out_dir.exists(): raise ValueError("RED_NO_OVERWRITE")
    out_dir.mkdir(parents=True)
    changed=out_dir/"EGGRUMBLE_SwarmCombat_Fallback.luau"
    changed.write_bytes(candidate)
    outputs={}
    for state in ("ON","OFF"):
        project=copy.deepcopy(original)
        project["name"]="EGGRUMBLE_GQ31_NEUTRAL_FALLBACK_"+state+"_PRIVATE_ONLY"
        def remap(node,key=()):
            for name,entry in node.items():
                if name.startswith("$"):continue
                route=key+(name,)
                if "$path" in entry:
                    selected=changed if state=="ON" and route==SWARM else parts[route]
                    entry["$path"]=os.path.relpath(selected,out_dir).replace(os.sep,"/")
                else:remap(entry,route)
        remap(project["tree"])
        output=out_dir/("GQ31_FALLBACK_"+state+".project.json")
        output.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        _,mapped=flat(output)
        if len(mapped)!=31 or set(mapped)!=set(parts):raise ValueError("RED_SOURCE_COUNT")
        for key,part in parts.items():
            desired=candidate if state=="ON" and key==SWARM else part.read_bytes()
            if mapped[key].read_bytes()!=desired:raise ValueError("RED_NONOWNER_BYTES_CHANGED")
        outputs[state]=output
    return {
        "source_parent_31_manifest_sha256":sha256(parent_receipt.read_bytes()),
        "source_count":31,
        "other_author_sources_byte_exact":30,
        "changed_author_runtime_source":"ServerScriptService/EGGRUMBLE_SwarmCombat",
        "swarm_before_sha256":sha256(raw),
        "swarm_after_sha256":sha256(candidate),
        "on_project":str(outputs["ON"]),
        "off_project":str(outputs["OFF"]),
        "formal_rc_adopted":False,
        "studio_android_owner": "NOT_TESTED",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-project",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(compose(a.source_project,a.out),ensure_ascii=False,indent=2))
