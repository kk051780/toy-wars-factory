#!/usr/bin/env python3
"""Add this lane's *only* new identity gate to #494's single original Swarm.

Inputs: #494's latest27 private assembly, generated using the *existing* #482
Game, #484 composer, #485 ART, #487 SCORE. Never changes author branches.
No parallel death connection, no new horde, no duplicate KO/score authority.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE_NAME = "EGGRUMBLE_NeutralKoDeathFence"
SWARM_NAME = "EGGRUMBLE_SwarmCombat"
JOIN = 'local SpawnPacing=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralSpawnPacing"))\n'
OLD = ('   if type(id)=="string" and session.rules.phase=="ACTIVE"\n'
       '    and session.rules.castles[id] and session.rules.castles[id].alive then\n')
NEW = ('   if type(id)=="string" and session.rules.phase=="ACTIVE"\n'
       '    and session.rules.castles[id] and session.rules.castles[id].alive\n'
       '    and KoFence.mayCredit(session,id,m,all) then\n')

def mapping(project):
    out = {}
    def walk(node, here=()):
        for name, child in node.items():
            if name.startswith("$"): continue
            if "$path" in child:
                key = here+(name,)
                assert key not in out
                out[key] = child["$path"]
            else: walk(child,here+(name,))
    walk(project["tree"])
    return out

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def replace_once(s, before, after):
    assert s.count(before) == 1, ("upstream author drift / duplicate", before, s.count(before))
    return s.replace(before, after, 1)

def overlay(base27: Path, dest: Path):
    assert not dest.exists(), "never overwrite an existing source-exact candidate"
    base27 = base27.resolve(strict=True)
    base = json.loads(base27.read_text(encoding="utf-8"))
    assert base["tree"]["$className"] == "DataModel"
    src_map = mapping(base)
    assert len(src_map)==27, "must use owner's exact #494 27 mapped scripts"
    swarm_key=("ServerScriptService",SWARM_NAME)
    assert swarm_key in src_map
    server=base["tree"]["ServerScriptService"]
    assert FENCE_NAME not in server
    original={}
    all_hash={}
    for key,path in src_map.items():
        file=(base27.parent/path).resolve(strict=True)
        original[key]=file
        all_hash["/".join(key)] = sha(file)
    old=original[swarm_key].read_text(encoding="utf-8")
    assert old.count("h.Died:Connect(")==1
    assert old.count("local function credit(")==1
    assert old.count("ImpactFeedback.ko(")==1
    assert old.count("SpawnPacing.step(")==1
    assert old.count("EGGRUMBLE_NeutralSpawnPacing")==1
    patched=replace_once(old,JOIN,JOIN+'local KoFence=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralKoDeathFence"))\n')
    patched=replace_once(patched,OLD,NEW)
    assert patched.count("KoFence.mayCredit(")==1
    assert patched.count("h.Died:Connect(")==1
    assert patched.count("local function credit(")==1
    assert patched.count("ImpactFeedback.ko(")==1
    dest=dest.resolve()
    dest.mkdir(parents=True)
    host=dest/"EGGRUMBLE_SwarmCombat_Combined.luau"
    host.write_text(patched,encoding="utf-8")
    fence=(ROOT/"EGGRUMBLE_NeutralKoDeathFence.luau").resolve(strict=True)
    generated=copy.deepcopy(base)
    generated["name"]="EGGRUMBLE_GQ_494_PACING_PLUS_508_HORDE_IDENTITY_PRIVATE28_NOT_RC"
    def rewrite(node,key=()):
        for name, child in node.items():
            if name.startswith("$"):continue
            next_key=key+(name,)
            if "$path" in child:
                file=host if next_key==swarm_key else original[next_key]
                child["$path"]=os.path.relpath(file,dest).replace(os.sep,"/")
            else:rewrite(child,next_key)
    rewrite(generated["tree"])
    generated["tree"]["ServerScriptService"][FENCE_NAME]={"$path":os.path.relpath(fence,dest).replace(os.sep,"/")}
    manifest=dest/"EGGRUMBLE_GQ_NEUTRAL28.project.json"
    manifest.write_text(json.dumps(generated,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    new_map=mapping(generated)
    assert len(new_map)==28
    for key,path in new_map.items():
        if key == swarm_key or key == ("ServerScriptService",FENCE_NAME):continue
        assert sha((dest/path).resolve(strict=True)) == all_hash["/".join(key)], key
    receipt={
        "schema":"EGGRUMBLE_GQ494_PLUS_GQ508_IDENTITY_V1",
        "private_candidate":True,"official_rc_adopted":False,
        "original_27_mapped":27,"candidate_28_mapped":28,
        "unchanged_26_sources":26,"one_existing_swarm_source_selected":True,
        "one_new_fence_module":True,
        "original_source_sha256":all_hash,
        "combined_swarm_sha256":sha(host),"fence_sha256":sha(fence),
        "source_parent_494":"af8cd79f4217d187429270d29e6d44eb01725ff2",
        "source_parent_482":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
        "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NOT_ACCEPTED",
        "rollback":"discard this overlay and reuse #494 unchanged source27"
    }
    (dest/"SOURCE28_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NEUTRAL494_AND_508_SOURCE_SELECTIVE28_PREP_PASS 26 unchanged, one Swarm combined, one new identity helper")
    return manifest

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base27",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    overlay(args.base27,args.out)
