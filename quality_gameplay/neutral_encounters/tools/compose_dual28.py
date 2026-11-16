#!/usr/bin/env python3
"""Integrate original #494 pacing patch with own #501 fairness into ONE private V3 Swarm.
Never changes #482/#484/#494 source, official RC, main, or user-facing experience.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ORIGINAL_NAME="EGGRUMBLE_SwarmCombat"
FAIR_NAME="EGGRUMBLE_NeutralEncounterFairness"
PACING_NAME="EGGRUMBLE_NeutralSpawnPacing"
NATIVE_CAP=110
EXPECTED_COUNT=28

def replace_once(data, before, after, label):
    count=data.count(before)
    assert count==1,(f"STALE_{label}",count,before)
    return data.replace(before,after,1)

def patch_fair_on_paced(source):
    """Only #501 target-location fairness hook; #494 owns all pacing/KO diff."""
    assert source.count('SpawnPacing.step(')==1
    assert source.count('and session.rules.castles[id].alive then')==1
    assert 'local SPAWN_BATCH=5' not in source
    assert source.count('local LIMIT=110')==1
    source=replace_once(source,
        'local SpawnPacing=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralSpawnPacing"))',
        'local SpawnPacing=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralSpawnPacing"))\n'
        'local EncounterFair=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralEncounterFairness"))',
        "own_require")
    source=replace_once(source,
        'local lastBotHit:{[string]:number}={}',
        'local lastBotHit:{[string]:number}={}\n'
        '  local encounterFairState={}',
        "own_state")
    source=replace_once(source,
        'local function aliveTargets():{Vector3}\n  local a={}',
        'local function aliveTargets():({Vector3},{string})\n  local a={}\n'
        '  local kinds:{string}={}',
        "own_targets")
    source=replace_once(source,
        'if root then table.insert(a,root.Position) end',
        'local hum=ch and ch:FindFirstChildOfClass("Humanoid")\n'
        '     if root and hum and hum.Health>0 then\n'
        '      table.insert(a,root.Position)\n'
        '      table.insert(kinds,"HUMAN")\n'
        '     end',
        "own_human")
    source=replace_once(source,
        'if c and c.alive and m.Parent and m.PrimaryPart then table.insert(a,m.PrimaryPart.Position) end',
        'local hum=m and m:FindFirstChildOfClass("Humanoid")\n'
        '    if c and c.alive and m.Parent and m.PrimaryPart and hum and hum.Health>0 then\n'
        '     table.insert(a,m.PrimaryPart.Position)\n'
        '     table.insert(kinds,"BOT")\n'
        '    end',
        "own_bot")
    source=replace_once(source,
        'return a\n end\n -- Area skills',
        'return a,kinds\n end\n -- Area skills',
        "own_pair")
    source=replace_once(source,
        'local candidates=aliveTargets()\n   local now=os.clock()',
        'local candidates,kinds=aliveTargets()\n   local now=os.clock()',
        "own_candidate_kinds")
    source=replace_once(source,
        'local target=candidates[math.random(1,#candidates)]',
        'local selected=EncounterFair.chooseIndex(encounterFairState,session,kinds)\n'
        '      if selected==nil then break end\n'
        '      local target=candidates[selected]',
        "own_index")
    source=replace_once(source,
        'ended=true\n end)',
        'EncounterFair.clear(encounterFairState)\n'
        '  ended=true\n end)',
        "own_cleanup")
    for key,n in [
      ("SpawnPacing.step(",1),("EncounterFair.chooseIndex(",1),
      ('local function credit(',1),('h.Died:Connect(',1),
      ('ImpactFeedback.ko(',1),('local function addEnemy(',1),
      ('local function aliveTargets(',1),
      ('SpawnPacing.new(',1),('and session.rules.castles[id].alive then',1),
    ]:
        assert source.count(key)==n,("ONLY_ONE_AUTHORITY",key,source.count(key))
    assert 'local SPAWN_BATCH=5' not in source
    assert 'MAX_LOS_RAYS_PER_ATTACK=48' in source
    assert 'EncounterFair.clear(encounterFairState)' in source
    assert source.count('math.random(1,#candidates)')==0
    return source

def flat(project):
    def walk(node,prefix=()):
        if isinstance(node,dict):
            if "$path" in node:
                assert len(node)==1
                yield prefix,(project.parent/node["$path"]).resolve(strict=True)
            else:
                for key,child in node.items():
                    if not key.startswith("$"):yield from walk(child,prefix+(key,))
    data=json.loads(project.read_text(encoding="utf-8"))
    return data,dict(walk(data["tree"]))

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def compose(base26,original_swarm,pacing_composer,pacing_policy,fair_policy,out):
    base26=base26.resolve(strict=True)
    original_swarm=original_swarm.resolve(strict=True)
    pacing_composer=pacing_composer.resolve(strict=True)
    pacing_policy=pacing_policy.resolve(strict=True)
    fair_policy=fair_policy.resolve(strict=True)
    out=out.resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    assert base26!=out and not out.exists(),"PRIVATE_OUT_MUST_BE_NEW"
    original, old=flat(base26)
    assert len(old)==26 and len({p[-1] for p in old})==26
    key=("ServerScriptService",ORIGINAL_NAME)
    assert key in old and old[key].read_bytes()==original_swarm.read_bytes()
    assert ("ServerScriptService",FAIR_NAME) not in old
    assert ("ServerScriptService",PACING_NAME) not in old
    old_receipt=json.loads((base26.parent/"SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    assert old_receipt["script_count"]==26
    for old_key,path in old.items():
        assert old_receipt["source_sha256"][old_key[-1]]==digest(path),old_key
    spec=importlib.util.spec_from_file_location("p0d_orig_pacing_494",pacing_composer)
    pacing=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pacing)
    assert pacing.git_blob(original_swarm)==pacing.AUTHOR_SWARM_BLOB
    assert pacing.AUTHOR_HEAD=="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
    assert "function Pacing.step(" in pacing_policy.read_text(encoding="utf-8")
    assert "function Fair.chooseIndex(" in fair_policy.read_text(encoding="utf-8")
    assert NATIVE_CAP==110
    before=original_swarm.read_text(encoding="utf-8")
    paced=pacing.patch_swarm(before)
    combined=patch_fair_on_paced(paced)
    assert combined!=paced and paced!=before
    generated=out.parent/"EGGRUMBLE_SwarmCombat.DUAL28_PRIVATE.luau"
    assert not generated.exists(),"NEVER_OVERWRITE_PRIOR_PRIVATE_OVERLAY"
    generated.write_text(combined,encoding="utf-8")
    current=copy.deepcopy(original)
    current["name"]="EGGRUMBLE_V3_GQ_NEUTRAL_PACING_AND_FAIRNESS_28_PRIVATE"
    # Original #484 26-source project paths are relative to its artifacts folder.
    # The #501 private overlay may be generated in a different folder: remap
    # file references, never rewrite the original 25 source bytes.
    def remap(node,prefix=()):
        for name,part in node.items():
            if name.startswith("$"):continue
            key=prefix+(name,)
            if "$path" in part:
                assert set(part)=={"$path"} and key in old
                part["$path"]=os.path.relpath(old[key],out.parent).replace(os.sep,"/")
            else:remap(part,key)
    remap(current["tree"])
    tree=current["tree"]
    server=tree["ServerScriptService"]
    client=tree["StarterPlayer"]["StarterPlayerScripts"]
    assert len(server)-1==23 and len(client)-1==3
    server[ORIGINAL_NAME]={"$path":os.path.relpath(generated,out.parent).replace(os.sep,"/")}
    server[PACING_NAME]={"$path":os.path.relpath(pacing_policy,out.parent).replace(os.sep,"/")}
    server[FAIR_NAME]={"$path":os.path.relpath(fair_policy,out.parent).replace(os.sep,"/")}
    out.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,new=flat(out)
    assert len(new)==EXPECTED_COUNT and len(set(new))==EXPECTED_COUNT
    assert set(new)==set(old)|{("ServerScriptService",PACING_NAME),("ServerScriptService",FAIR_NAME)}
    for old_key in set(old)-{key}:
        assert new[old_key].read_bytes()==old[old_key].read_bytes(),("NONOWNER_SOURCE_DRIFT",old_key)
    assert new[("ServerScriptService",PACING_NAME)].read_bytes()==pacing_policy.read_bytes()
    assert new[("ServerScriptService",FAIR_NAME)].read_bytes()==fair_policy.read_bytes()
    assert sum(k[0]=="ServerScriptService" for k in new)==25
    assert sum(k[0]=="StarterPlayer" for k in new)==3
    receipt={
      "schema":"P0D_501_PLUS_494_PRIVATE_DUAL28_COMPOSITE_V1",
      "stage":"PRIVATE_NON_RELEASE_ONLY",
      "unchanged_original26":25,
      "overlaid_original26":1,
      "originals":26,
      "extra_original_author_policies":[PACING_NAME,FAIR_NAME],
      "total_mapped":EXPECTED_COUNT,
      "original_swarm_sha256":digest(original_swarm),
      "pacing_only_swarm_sha256":hashlib.sha256(paced.encode()).hexdigest(),
      "dual_swarm_sha256":digest(generated),
      "pacing_policy_sha256":digest(pacing_policy),
      "fair_policy_sha256":digest(fair_policy),
      "mapped_sha256":{"/".join(k):digest(p) for k,p in sorted(new.items())},
      "official_rc":"NOT_ADOPTED","original_author_approval":"PENDING",
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner_fun":"NOT_ACCEPTED",
      "rollback":"use byte exact source #484 26, omitting both new modules"
    }
    (out.parent/"DUAL28_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ_DUAL28_ORIGINAL26_25_EXACT_ONE_SWARM_TWO_POLICIES_PASS")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("base26","original_swarm","pacing_composer","pacing_policy","fair_policy","out"):
        p.add_argument("--"+a.replace("_","-"),required=True,type=Path)
    x=p.parse_args()
    compose(x.base26,x.original_swarm,x.pacing_composer,x.pacing_policy,x.fair_policy,x.out)
