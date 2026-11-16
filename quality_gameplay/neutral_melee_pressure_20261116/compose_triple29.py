#!/usr/bin/env python3
"""Append ONLY #533 neutral melee to original #494+#501 private28, yielding private29.

All 28 existing source paths read from the original #501 composer are preserved.
No writes to original game branches, official RC, Studio devices or production.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from compose_melee_candidate import patch, SOURCE_BLOB, git_blob

ORIGINAL = ("ServerScriptService", "EGGRUMBLE_SwarmCombat")
POLICY = ("ServerScriptService", "EGGRUMBLE_NeutralMeleePolicy")
EXPECTED_PREVIOUS = 28
EXPECTED_CURRENT = 29

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def flatten(project: Path):
    project=project.resolve(strict=True)
    data=json.loads(project.read_text(encoding="utf-8"))
    def walk(node: dict, prefix=()):
        for name,part in node.items():
            if name.startswith("$"):continue
            if "$path" in part:
                assert set(part)=={"$path"},"RED project alias"
                yield prefix+(name,),(project.parent/part["$path"]).resolve(strict=True)
            else:
                yield from walk(part,prefix+(name,))
    return data,dict(walk(data["tree"]))

def compose(base28: Path, original_swarm: Path, out: Path, melee_policy: Path) -> dict:
    base28=base28.resolve(strict=True)
    original_swarm=original_swarm.resolve(strict=True)
    melee_policy=melee_policy.resolve(strict=True)
    out=out.resolve()
    assert not out.exists(), "RED never overwrite private composite"
    assert out.parent.is_dir()
    before, originals=flatten(base28)
    assert len(originals)==EXPECTED_PREVIOUS and ORIGINAL in originals
    assert POLICY not in originals
    assert len({k[-1] for k in originals})==len(originals)
    receipt_path=base28.parent/"DUAL28_SOURCE_RECEIPT.json"
    prev=json.loads(receipt_path.read_text(encoding="utf-8"))
    assert prev["total_mapped"]==EXPECTED_PREVIOUS
    assert prev["originals"]==26 and prev["unchanged_original26"]==25
    assert prev["stage"]=="PRIVATE_NON_RELEASE_ONLY"
    assert prev["official_rc"]=="NOT_ADOPTED"
    assert git_blob(original_swarm.read_bytes())==SOURCE_BLOB
    assert prev["original_swarm_sha256"]==digest(original_swarm)
    assert prev["dual_swarm_sha256"]==digest(originals[ORIGINAL])
    for key,path in originals.items():
        assert prev["mapped_sha256"]["/".join(key)]==digest(path),("RED source drift",key)
    existing_swarm=originals[ORIGINAL].read_text(encoding="utf-8")
    for required in ("SpawnPacing.step(", "EncounterFair.chooseIndex(",
                     "EncounterFair.clear(", 'and session.rules.castles[id].alive then'):
        assert existing_swarm.count(required)==1,("RED original author hook missing",required)
    combined=patch(existing_swarm)
    for required in ("SpawnPacing.step(", "EncounterFair.chooseIndex(",
                     "EncounterFair.clear(", "h.Died:Connect(",
                     "ImpactFeedback.ko(", "local function credit(",
                     "local function addEnemy(", "local function liveMeleeVictims(",
                     "candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"):
        assert combined.count(required)==1,("RED duplicate authority",required)
    assert 'p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode' in combined
    assert 'local SPAWN_BATCH=5' not in combined
    assert combined!=existing_swarm
    generated=out.parent/"EGGRUMBLE_SwarmCombat.TRIPLE29_PRIVATE.luau"
    assert not generated.exists(),"RED mutable previous artifact"
    generated.write_text(combined,encoding="utf-8")

    project=copy.deepcopy(before)
    project["name"]="EGGRUMBLE_V3_GQ_494_501_533_29_SOURCE_ONLY"
    def remap(node,prefix=()):
        for name,spec in node.items():
            if name.startswith("$"):continue
            key=prefix+(name,)
            if "$path" in spec:
                assert key in originals
                spec["$path"]=os.path.relpath(originals[key],out.parent).replace(os.sep,"/")
            else:
                remap(spec,key)
    remap(project["tree"])
    server=project["tree"]["ServerScriptService"]
    server[ORIGINAL[-1]]={"$path":generated.name}
    server[POLICY[-1]]={"$path":os.path.relpath(melee_policy,out.parent).replace(os.sep,"/")}
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,now=flatten(out)
    assert len(now)==EXPECTED_CURRENT
    assert set(now)==set(originals)|{POLICY}
    for key in set(originals)-{ORIGINAL}:
        assert now[key].read_bytes()==originals[key].read_bytes(),("RED nonowner changed",key)
    assert now[POLICY].read_bytes()==melee_policy.read_bytes()
    assert sum(k[0]=="ServerScriptService" for k in now)==26
    assert sum(k[0]=="StarterPlayer" for k in now)==3
    receipt={
        "schema":"P0D_GQ_NEUTRAL_MELEE_TRIPLE29_V1",
        "status":"PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "source_original_swarm_blob":SOURCE_BLOB,
        "base28_receipt_sha256":digest(receipt_path),
        "base28_source_count":28,
        "preserved28_sources_exact":27,
        "changed_existing_sources":1,
        "new_policy_sources":1,
        "total_count":29,
        "swarm_before_sha256":digest(originals[ORIGINAL]),
        "swarm_after_sha256":digest(generated),
        "melee_policy_sha256":digest(melee_policy),
        "mapped_sha256":{"/".join(k):digest(path) for k,path in sorted(now.items())},
        "author_ack":False,"claim_granted":False,"official_rc_adopted":False,
        "studio_tested":False,"android_tested":False,"owner_accepted":False,
        "rollback":"Remove #533 generated single Swarm + melee policy; use original source-exact #501 dual28"
    }
    (out.parent/"TRIPLE29_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_ONE_SWARM_494_501_533_TRIPLE29_COMPOSE_PASS",len(now))
    return receipt

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for name in ("base28","original_swarm","out","melee_policy"):
        parser.add_argument("--"+name.replace("_","-"),required=True,type=Path)
    args=parser.parse_args()
    compose(args.base28,args.original_swarm,args.out,args.melee_policy)
