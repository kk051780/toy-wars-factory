#!/usr/bin/env python3
"""Overlay ONLY existing #494 Swarm pacing on #484 authored 26-source composite.

Does not recompose V3 game, ART, SCORE, AI: calls their canonical creators
separately, then strictly verifies and patches the resulting 26-source map.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from compose_private_v3 import patch_swarm, git_blob, AUTHOR_SWARM_BLOB

BASE_COUNT=26
NEW_COUNT=27
OWNED_NAME="EGGRUMBLE_NeutralSpawnPacing"
SWARM_NAME="EGGRUMBLE_SwarmCombat"

def flatten(tree):
    mapping={}
    def visit(node,key=()):
        for name,child in node.items():
            if name.startswith("$"): continue
            assert isinstance(child,dict)
            if "$path" in child:
                assert set(child)=={"$path"}
                assert key+(name,) not in mapping
                mapping[key+(name,)]=child["$path"]
            else:visit(child,key+(name,))
    visit(tree)
    return mapping

def read_project(path):
    path=path.resolve(strict=True)
    project=json.loads(path.read_text(encoding="utf-8"))
    assert project["tree"]["$className"]=="DataModel"
    mapping=flatten(project["tree"])
    return path,project,mapping

def make_overlay(base26:Path,dest:Path):
    project_path,base,mapped=read_project(base26)
    assert len(mapped)==BASE_COUNT,("wrong composite count",len(mapped))
    server=base["tree"]["ServerScriptService"]
    client=base["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert len(server)-1==23 and len(client)-1==3
    assert (("ServerScriptService",SWARM_NAME) in mapped)
    assert "EGGRUMBLE_ScoreBalance" in server
    assert "EGGRUMBLE_HeroSilhouetteArt" in server
    assert "EGGRUMBLE_EncounterReadabilityArt" in server
    assert "EGGRUMBLE_FlagshipFieldArt" in server
    assert "EGGRUMBLE_CombatFeel" in client and "EGGRUMBLE_ArtDistanceLOD" in client
    assert OWNED_NAME not in server
    receipt_path=project_path.parent/"SOURCE_RECEIPT.json"
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["script_count"]==26
    assert receipt["server_count"]==23 and receipt["client_count"]==3
    assert len(receipt["source_sha256"])==26
    original_content={}
    old_hashes={}
    for key,relative in mapped.items():
        name=key[-1]
        file=(project_path.parent/relative).resolve(strict=True)
        assert file.is_file(),name
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        assert receipt["source_sha256"][name]==digest,("26-source composer drift",name)
        old_hashes[name]=digest
        original_content[name]=file.read_text(encoding="utf-8")
    swarm_spec=server[SWARM_NAME]
    old_swarm=(project_path.parent/swarm_spec["$path"]).resolve(strict=True)
    assert git_blob(old_swarm)==AUTHOR_SWARM_BLOB, "original #482 Swarm unexpectedly replaced"
    assert old_swarm.read_text(encoding="utf-8")==original_content[SWARM_NAME]
    # Refuse to overwrite an existing output or use shared author files.
    assert not dest.exists(),"never clobber an existing candidate receipt"
    dest.mkdir(parents=True)
    host=(dest/"EGGRUMBLE_SwarmCombat.luau")
    host.write_text(patch_swarm(original_content[SWARM_NAME]),encoding="utf-8")
    policy=(ROOT/"EGGRUMBLE_NeutralSpawnPacing.luau").resolve(strict=True)
    current=copy.deepcopy(base)
    current["name"]="EGGRUMBLE_GQ_NEUTRAL27_WITH_ART_SCORE_PRIVATE_NO_RC"
    # Preserve every existing service/class and author-owned file byte EXACT.
    old_paths=dict(mapped)
    tree=current["tree"]
    def remap(node,where=()):
        for name,child in node.items():
            if name.startswith("$"): continue
            key=where+(name,)
            if "$path" in child:
                old=(project_path.parent/old_paths[key]).resolve(strict=True)
                if key==("ServerScriptService",SWARM_NAME):
                    old=host
                child["$path"]=os.path.relpath(old,dest).replace(os.sep,"/")
            else:remap(child,key)
    remap(tree)
    tree["ServerScriptService"][OWNED_NAME]={"$path":os.path.relpath(policy,dest).replace(os.sep,"/")}
    out=dest/"EGGRUMBLE_GQ_NEUTRAL27.project.json"
    out.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,_,new_map=read_project(out)
    assert len(new_map)==NEW_COUNT
    # Validate the exact content provenance before Rojo, not just script counts.
    for key,relative in new_map.items():
        if key[-1]==OWNED_NAME:continue
        file=(dest/relative).resolve(strict=True)
        if key[-1]==SWARM_NAME:
            assert file.read_text(encoding="utf-8")==patch_swarm(original_content[SWARM_NAME])
        else:
            assert hashlib.sha256(file.read_bytes()).hexdigest()==old_hashes[key[-1]],key
    metadata={
      "schema":"P0D_PQG494_AUTHOR_CURRENT26_PACING27_V1",
      "base26_quality_head":subprocess.check_output(["git","-C",str(project_path.parent.parent.resolve()),"rev-parse","HEAD"],text=True).strip() if (project_path.parent.parent/".git").exists() else "REFERENCE_PINNED_BY_WORKFLOW",
      "original26_count":BASE_COUNT,"total27_count":NEW_COUNT,
      "unchanged_original_count":25,"single_swarm_edit":True,
      "new_pacing_count":1,
      "original26_sha256":old_hashes,
      "new_swarm_sha256":hashlib.sha256(host.read_bytes()).hexdigest(),
      "pacing_sha256":hashlib.sha256(policy.read_bytes()).hexdigest(),
      "official_rc_adopted":False,
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner_accepted":False,
      "rollback":"discard this 27 overlay; reuse unmodified original #484 26-source Place"
    }
    (dest/"SOURCE27_RECEIPT.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ORIGINAL26_ART_SCORE_8DOMAIN_UNCHANGED25_AND_SWARM_SCHEDULE1_PASS")
    print("COMPOSED_NEUTRAL_PACING_27_SOURCE",len(new_map))
    return metadata

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base26",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    make_overlay(args.base26,args.out.resolve())
