#!/usr/bin/env python3
"""Fail-closed, source-selective V3 private Place composer.

Authoritative gameplay remains with #482. This creates a separate, *nonpublic*
22-source build, preserving 20 original Luau files, changing only original
SwarmCombat's scheduling hookup, adding one independently tested planner.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
AUTHOR_PROJECT_BLOB = "1d3e5bdc9ac2ac3fb6e70110ff3c6636d70fc714"
AUTHOR_SWARM_BLOB = "fea147ac51411e626b410d172aad5cd72615bd45"
ORIGINAL_COUNT = 21
NEW_COUNT = 22
ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "EGGRUMBLE_NeutralSpawnPacing.luau"

def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()

def replace_once(data: str, before: str, after: str) -> str:
    assert data.count(before) == 1, ("source drift; wrong splice count", before, data.count(before))
    return data.replace(before, after, 1)

def patch_swarm(source: str) -> str:
    """Replace only spawn rate scheduling while keeping the original Horde authority."""
    assert "local LIMIT=110" in source
    source = replace_once(source, "local SPAWN_BATCH=5\n", "")
    source = replace_once(
        source,
        'local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))\n',
        'local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))\n'
        'local SpawnPacing=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralSpawnPacing"))\n',
    )
    source = replace_once(
        source,
        " local ended=false\n",
        ' local ended=false\n'
        ' assert(LIMIT==SpawnPacing.MAX_ALIVE,"horde/planner live cap drift")\n'
        ' local planner=SpawnPacing.new(session.world.Name..":"..tostring(os.clock()))\n',
    )
    source = replace_once(
        source,
        ' session.swarm=api\n task.spawn(function()\n  while all.Parent and session.rules.phase=="ACTIVE" do\n',
        ' session.swarm=api\n local lastSpawnAt=os.clock()\n task.spawn(function()\n'
        '  while all.Parent and session.rules.phase=="ACTIVE" do\n',
    )
    source = replace_once(
        source,
        '   local candidates=aliveTargets()\n'
        '   if #candidates>0 then\n'
        '    local n=api.getAliveCount()\n'
        '    for _=1,math.min(SPAWN_BATCH,LIMIT-n) do\n',
        '   local candidates=aliveTargets()\n'
        '   local now=os.clock()\n'
        '   local elapsed=now-lastSpawnAt\n'
        '   lastSpawnAt=now\n'
        '   local batch=SpawnPacing.step(planner,{\n'
        '    matchId=planner.matchId,phase=session.rules.phase,dt=elapsed,\n'
        '    live=api.getAliveCount(),activeHeroes=#candidates,\n'
        '    tickMs=math.max(0,(elapsed-SPAWN_TICK)*1000),\n'
        '   })\n'
        '   if batch>0 then\n'
        '    for _=1,batch do\n',
    )
    # A real Humanoid.Died callback may arrive after a castle falls or after
    # the match has ended. Never credit a dead/evicted participant for stale KO.
    # This is still the SAME original neutral Died callback; no parallel scorer.
    source = replace_once(
        source,
        '   if type(id)=="string" and session.rules.castles[id] then\n',
        '   if type(id)=="string" and session.rules.phase=="ACTIVE"\n'
        '    and session.rules.castles[id] and session.rules.castles[id].alive then\n',
    )
    assert source.count('session.rules.phase=="ACTIVE"') >= 3
    assert source.count('and session.rules.castles[id].alive then') == 1
    assert source.count("SpawnPacing.step(") == 1
    assert source.count("local function credit(") == 1
    assert source.count("ImpactFeedback.ko(") == 1
    assert source.count("h.Died:Connect(") == 1
    assert "MAX_LOS_RAYS_PER_ATTACK=48" in source
    assert "local SPAWN_BATCH=5" not in source
    return source

def entries(project: dict):
    root = project["tree"]
    assert root["$className"] == "DataModel"
    out = {}
    def rec(node, prefix=()):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            assert isinstance(value, dict), key
            if "$path" in value:
                assert set(value) == {"$path"}, "no conflicting source alias"
                k = prefix + (key,)
                assert k not in out
                out[k] = value["$path"]
            else:
                rec(value, prefix+(key,))
    rec(root)
    return out

def compose(author_dir: Path, author_checkout: Path, stage: Path) -> dict:
    author_dir = author_dir.resolve(strict=True)
    author_checkout = author_checkout.resolve(strict=True)
    stage = stage.resolve()
    actual_commit = subprocess.check_output(
        ["git","-C",str(author_checkout),"rev-parse","HEAD"],text=True).strip()
    assert actual_commit == AUTHOR_HEAD, ("author HEAD drift", actual_commit)
    base = author_dir/"EGGRUMBLE_V3_STUDIO.project.json"
    assert git_blob(base)==AUTHOR_PROJECT_BLOB, "author Rojo project changed"
    original = json.loads(base.read_text(encoding="utf-8"))
    mapped = entries(original)
    assert len(mapped)==ORIGINAL_COUNT, ("not original 21-source project", len(mapped))
    assert sum(k[0]=="ServerScriptService" for k in mapped)==19
    assert sum(k[0]=="StarterPlayer" for k in mapped)==2
    assert ("ServerScriptService","EGGRUMBLE_SwarmCombat") in mapped
    assert ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview") in mapped
    assert ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFeel") in mapped
    assert "Game" not in {k[-1] for k in mapped}

    dest_source = stage/"source"
    assert not stage.exists(), "output must be a fresh, not-overwritten stage"
    dest_source.mkdir(parents=True)
    originals = {}
    paths_seen = set()
    src_root = author_dir.resolve()
    for key, relative in mapped.items():
        source = (author_dir / relative).resolve(strict=True)
        assert source.is_relative_to(src_root), "project path escapes trusted original author"
        assert source.suffix == ".luau", "no asset or non-Luau shadow mapping"
        assert source.name not in paths_seen, "duplicate source filename"
        paths_seen.add(source.name)
        old = source.read_text(encoding="utf-8")
        if key[-1] == "EGGRUMBLE_SwarmCombat":
            assert git_blob(source)==AUTHOR_SWARM_BLOB, "swarm author changed"
            new = patch_swarm(old)
        else:
            new = old
        (dest_source/source.name).write_text(new,encoding="utf-8")
        originals["/".join(key)] = {
            "file": source.name,
            "original_git_blob":git_blob(source),
            "original_sha256":hashlib.sha256(old.encode()).hexdigest(),
            "built_sha256":hashlib.sha256(new.encode()).hexdigest(),
            "changed":old!=new,
        }
    assert sum(x["changed"] for x in originals.values())==1
    shutil.copyfile(PLANNER, dest_source/PLANNER.name)

    new_project = json.loads(json.dumps(original))
    def rewrite(node):
        for name, part in node.items():
            if name.startswith("$"):
                continue
            if "$path" in part:
                part["$path"] = "source/" + Path(part["$path"]).name
            else:
                rewrite(part)
    rewrite(new_project["tree"])
    server = new_project["tree"]["ServerScriptService"]
    assert "EGGRUMBLE_NeutralSpawnPacing" not in server
    server["EGGRUMBLE_NeutralSpawnPacing"]={"$path":"source/"+PLANNER.name}
    new_project["name"]="EGGRUMBLE_V3_PRIVATE_NEUTRAL_PACING_22_NO_PUBLISH"
    assert len(entries(new_project))==NEW_COUNT
    project_path=stage/"EGGRUMBLE_V3_NEUTRAL_PACING.project.json"
    project_path.write_text(json.dumps(new_project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt = {
        "schema":"P0D_PQG_NEUTRAL_PACING_SOURCE_V1",
        "author_head":AUTHOR_HEAD,"author_project_git_blob":AUTHOR_PROJECT_BLOB,
        "author_swarm_git_blob":AUTHOR_SWARM_BLOB,
        "previous_author_sources":ORIGINAL_COUNT,"new_total_sources":NEW_COUNT,
        "original_sources_byte_exact":20,"original_sources_surgical_change":1,
        "new_original_policy_sources":1,
        "originals":originals,
        "new_policy_sha256":hashlib.sha256(PLANNER.read_bytes()).hexdigest(),
        "source_stage":"PRIVATE_BUILD_ONLY",
        "official_rc":"NOT_INTEGRATED","engine_studio":"NOT_RUN",
        "android":"NOT_RUN","owner_fun":"NOT_ACCEPTED",
        "rollback":"Discard private composer overlay; retain canonical SwarmCombat",
    }
    (stage/"SOURCE_LOCK_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PINNED_AUTHOR_V3_SOURCE_EXACT_INTAKE",ORIGINAL_COUNT)
    print("SWARM_ONLY_DELTA_WITH_NEW_PACING_22_SOURCE_PASS")
    return receipt

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--author-root",type=Path,required=True)
    parser.add_argument("--author-checkout",type=Path,required=True)
    parser.add_argument("--stage",type=Path,required=True)
    args=parser.parse_args()
    compose(args.author_root,args.author_checkout,args.stage)
