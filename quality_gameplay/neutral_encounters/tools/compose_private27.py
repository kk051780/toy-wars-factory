#!/usr/bin/env python3
"""Prepare a private 27-source *overlay* from #484's exact original 26-source composite.
No modifications to owner branches, no production RC write and no second Swarm.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

GAME = "EGGRUMBLE_SwarmCombat"
POLICY = "EGGRUMBLE_NeutralEncounterFairness"

def replace_one(source: str, before: str, after: str, note: str) -> str:
    occurrences = source.count(before)
    if occurrences != 1:
        raise ValueError(f"STALE_SOURCE_{note}: expected 1 anchor, got {occurrences}")
    return source.replace(before, after, 1)

def patch_swarm(source: str) -> str:
    """Exact minimal, reviewable changes to the *generated private copy* only."""
    assert "EGGRUMBLE V3: standalone lightweight neutral-horde combat controller." in source
    assert 'require(script.Parent:WaitForChild("EGGRUMBLE_NeutralEncounterFairness"))' not in source
    source = replace_one(source,
        'local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))',
        'local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))\n'
        'local EncounterFair=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralEncounterFairness"))',
        "require")
    source = replace_one(source,
        'local lastBotHit:{[string]:number}={}',
        'local lastBotHit:{[string]:number}={}\n'
        '  local encounterFairState={}',
        "session_state")
    source = replace_one(source,
        'local function aliveTargets():{Vector3}\n  local a={}',
        'local function aliveTargets():({Vector3},{string})\n  local a={}\n'
        '   local kinds:{string}={}',
        "target_interface")
    source = replace_one(source,
        'if root then table.insert(a,root.Position) end',
        'local hum=ch and ch:FindFirstChildOfClass("Humanoid")\n'
        '     if root and hum and hum.Health>0 then\n'
        '      table.insert(a,root.Position)\n'
        '      table.insert(kinds,"HUMAN")\n'
        '     end',
        "alive_human")
    source = replace_one(source,
        'if c and c.alive and m.Parent and m.PrimaryPart then table.insert(a,m.PrimaryPart.Position) end',
        'local hum=m and m:FindFirstChildOfClass("Humanoid")\n'
        '    if c and c.alive and m.Parent and m.PrimaryPart and hum and hum.Health>0 then\n'
        '     table.insert(a,m.PrimaryPart.Position)\n'
        '     table.insert(kinds,"BOT")\n'
        '    end',
        "alive_bot")
    source = replace_one(source,
        'return a\n end\n -- Area skills',
        'return a,kinds\n end\n -- Area skills',
        "paired_return")
    source = replace_one(source,
        'local candidates=aliveTargets()\n   if #candidates>0 then\n    local n=api.getAliveCount()',
        'local candidates,kinds=aliveTargets()\n'
        '    if #candidates>0 then\n     local n=api.getAliveCount()',
        "spawn_candidates")
    source = replace_one(source,
        'local target=candidates[math.random(1,#candidates)]',
        'local selected=EncounterFair.chooseIndex(encounterFairState,session,kinds)\n'
        '      if selected==nil then break end\n'
        '      local target=candidates[selected]',
        "target_pick")
    source = replace_one(source,
        'ended=true\n end)',
        'EncounterFair.clear(encounterFairState)\n'
        '   ended=true\n  end)',
        "round_cleanup")
    assert "local LIMIT=110" in source and "local SPAWN_BATCH=5" in source
    assert "local SPAWN_TICK=.18" in source and "ImpactFeedback.ko(" in source
    assert source.count("EncounterFair.chooseIndex(") == 1
    return source

def mapped(project_path, data):
    def recur(node, path):
        if not isinstance(node, dict): return
        if "$path" in node:
            yield path[-1], (project_path.parent / node["$path"]).resolve(strict=True), path
        else:
            for key,val in node.items():
                if not key.startswith("$"):
                    yield from recur(val,path+(key,))
    yield from recur(data["tree"],())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-project",type=Path,required=True)
    ap.add_argument("--author-swarm",type=Path,required=True)
    ap.add_argument("--policy",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    base=args.base_project.resolve(strict=True)
    author=args.author_swarm.resolve(strict=True)
    policy=args.policy.resolve(strict=True)
    out=args.out.resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    assert base.parent!=out.parent or base.name!=out.name
    raw=json.loads(base.read_text(encoding="utf-8"))
    original=list(mapped(base,raw))
    assert len(original)==26 and len({name for name,_,_ in original})==26
    originals={name:p for name,p,_ in original}
    assert originals[GAME].read_bytes()==author.read_bytes(), "BASE_ORIGINAL_SWARM_DRIFT"
    assert POLICY not in originals
    game_mods=raw["tree"]["ServerScriptService"]
    assert set(game_mods[GAME])=={"$path"}
    assert game_mods["$className"]=="ServerScriptService"
    assert all(len(nodes)>1 for _,_,nodes in original)
    expected_receipt=json.loads((base.parent/"SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    assert expected_receipt["script_count"]==26
    assert {n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p,_ in original} == expected_receipt["source_sha256"],"BASE_26_HASH_DRIFT"
    policy_src=policy.read_text(encoding="utf-8")
    assert "function Fair.chooseIndex(" in policy_src
    assert "return Fair" in policy_src
    patched=patch_swarm(author.read_text(encoding="utf-8"))
    patched_path=out.parent/"EGGRUMBLE_SwarmCombat.encounter_private.luau"
    patched_path.write_text(patched,encoding="utf-8")
    raw=copy.deepcopy(raw)
    game_mods=raw["tree"]["ServerScriptService"]
    game_mods[GAME]={"$path":os.path.relpath(patched_path,out.parent).replace(os.sep,"/")}
    game_mods[POLICY]={"$path":os.path.relpath(policy,out.parent).replace(os.sep,"/")}
    raw["name"]="EGGRUMBLE_V3_GQ_27_ENCOUNTER_PREVIEW_NOT_OFFICIAL_RC"
    out.write_text(json.dumps(raw,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    new=list(mapped(out,raw))
    assert len(new)==27 and len({n for n,_,_ in new})==27
    now={n:p for n,p,_ in new}
    assert set(now)-set(originals)=={POLICY}
    for n in set(originals)-{GAME}:
        assert now[n].read_bytes()==originals[n].read_bytes(),f"NONOWNER_MUTATION:{n}"
    assert sum(1 for n,_,nodes in new if nodes[0]=="ServerScriptService") == 24
    assert sum(1 for n,_,nodes in new if nodes[0]=="StarterPlayer") == 3
    assert all("DataStore" not in p.read_text(encoding="utf-8") for n,p,_ in new if n==POLICY)
    receipt={
     "release_status":"PRIVATE_SOURCE_PREVIEW_NO_RC_CAS",
     "original_source_count":26,
     "candidate_count":27,
     "original_scripts_exact_unchanged":25,
     "only_private_host_overlay":GAME,
     "only_new_sibling_module":POLICY,
     "author_original_sha256":hashlib.sha256(author.read_bytes()).hexdigest(),
     "host_overlay_sha256":hashlib.sha256(patched_path.read_bytes()).hexdigest(),
     "source_sha256":{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p,_ in sorted(new)},
     "original_author_wiring":"NOT_MERGED", "official_rc":"NOT_ADOPTED",
     "studio":"NOT_TESTED", "android":"NOT_TESTED","owner":"NOT_ACCEPTED",
    }
    (out.parent/"ENCOUNTER_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EGGRUMBLE_GQ_ENCOUNTER_COMPOSE_27_PASS",receipt["original_scripts_exact_unchanged"])
if __name__=="__main__":
    main()
