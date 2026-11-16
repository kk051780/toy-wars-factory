#!/usr/bin/env python3
"""SOURCE-selective optional castle-defense overlay on existing #484 26-source build.

This is not another V3 game or a production RC writer. It reuses the author,
artist, score, and quality composer and changes precisely the private host.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

BASE_COUNT = 26
ROOT = Path(__file__).resolve().parent
ADDED = ("EGGRUMBLE_CastleDefenseLive", "EGGRUMBLE_CastleDefensePolicy")
HOST = "EGGRUMBLE_LobbyCastleModesPreview"

def mapped(project_path, tree):
    def walk(node, parts):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            assert set(node) == {"$path"}, (parts, node)
            yield parts, (project_path.parent / node["$path"]).resolve(strict=True)
        else:
            for key, child in node.items():
                if not key.startswith("$"):
                    yield from walk(child, parts + (key,))
    yield from walk(tree, ())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def patch_host(src):
    required = (
        'local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))',
        'BotActors.start(session,Rules)',
        'if session.world.Parent then session.world:Destroy() end',
        'session.closeRound=function(abandoned:boolean?)',
        'SwarmCombat.start(session)',
        'SevenRoleCombat.equip(session,p,role)',
        'RaidItemIntake.start(session,root,FieldItems)',
        'NeutralStoneGiant.spawn(session.world,',
    )
    for token in required:
        assert src.count(token) == 1, ("V3 author host drift, reject unreviewed patch", token, src.count(token))
    assert "EGGRUMBLE_CastleDefenseLive" not in src, "already hooked; reject duplicate authority"
    src = src.replace(
        required[0],
        required[0] + '\nlocal CastleDefense=require(script.Parent:WaitForChild("EGGRUMBLE_CastleDefenseLive"))',
    )
    src = src.replace(
        required[1],
        required[1] + """
 -- Optional only; malformed cosmetics/defense must not abort the egg/castle match.
 -- OFF is immediate source-level rollback. Runtime never adds a second Game.
 local DEFENSE_V1_ENABLED=true
 if DEFENSE_V1_ENABLED then
  local defenseOK,defenseError=pcall(function() CastleDefense.start(session) end)
  if not defenseOK then
   if session.castleDefenseStop then session.castleDefenseStop() end
   warn("[EGGRUMBLE CASTLE DEFENSE] YELLOW_OPTIONAL source fail:",defenseError)
  end
 end""",
    )
    src = src.replace(
        required[2],
        'if session.castleDefenseStop then session.castleDefenseStop() end\n  ' + required[2],
    )
    assert src.count("CastleDefense.start(session)") == 1
    assert src.count("session.castleDefenseStop()") == 2
    assert src.count("BotActors.start(session,Rules)") == 1
    assert src.count("SevenRoleCombat.equip(session,p,role)") == 1
    return src

def build(base_project, out_project):
    base_project = base_project.resolve(strict=True)
    out_project = out_project.resolve()
    out_project.parent.mkdir(parents=True, exist_ok=True)
    assert out_project != base_project, "must never rewrite author/quality source"
    assert out_project.parent != ROOT, "outputs must stay private artifacts"
    baseline = json.loads(base_project.read_text(encoding="utf-8"))
    base_paths = list(mapped(base_project, baseline["tree"]))
    assert len(base_paths) == BASE_COUNT, ("expected existing official-author composite", len(base_paths))
    before = {}
    for parts, path in base_paths:
        label = parts[-1]
        assert label not in before, ("duplicate script name", label)
        before[label] = (path, digest(path))
    assert HOST in before
    server = baseline["tree"]["ServerScriptService"]
    client = baseline["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert len(server) == 24 and len(client) == 4, ("not 23 server + 3 client", len(server), len(client))
    for name in ADDED:
        assert name not in before and name not in server, ("duplicate defense module", name)
    original = before[HOST][0].read_text(encoding="utf-8")
    revised = patch_host(original)
    host_path = out_project.parent / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    host_path.write_text(revised, encoding="utf-8")
    result = copy.deepcopy(baseline)
    result["name"] = "EGGRUMBLE_V3_GQ_CURRENT28_CASTLE_DEFENSE_PRIVATE_NO_RC"
    result_server = result["tree"]["ServerScriptService"]
    result_server[HOST] = {"$path": os.path.relpath(host_path, out_project.parent).replace(os.sep, "/")}
    for name in ADDED:
        owner_file = (ROOT / (name + ".luau")).resolve(strict=True)
        result_server[name] = {"$path": os.path.relpath(owner_file, out_project.parent).replace(os.sep, "/")}
    out_project.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fresh = list(mapped(out_project, result["tree"]))
    assert len(fresh) == 28
    after = {}
    for parts, path in fresh:
        label = parts[-1]
        assert label not in after, ("duplicate across Services", label)
        after[label] = (path, digest(path))
    assert set(after) == set(before) | set(ADDED)
    changed = [n for n in before if before[n][1] != after[n][1]]
    assert changed == [HOST], ("non-owner file mutated", changed)
    assert len([n for n in before if before[n][1] == after[n][1]]) == 25
    # Verify every sibling import resolves in the same ServerScriptService.
    for parts, path in fresh:
        if parts[0] != "ServerScriptService": continue
        code = path.read_text(encoding="utf-8")
        for dep in re.findall(r'script\.Parent:WaitForChild\("([^"]+)"\)', code):
            assert dep in result_server, ("missing runtime dependency", parts, dep)
    for name in ("EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_BotActors",
                 "EGGRUMBLE_SwarmCombat","EGGRUMBLE_RaidItemIntake",
                 "EGGRUMBLE_MatchResultService","EGGRUMBLE_ProceduralSkills",
                 "EGGRUMBLE_FlagshipFieldArt","EGGRUMBLE_ArtDistanceLOD",
                 "EGGRUMBLE_NeutralStoneGiant"):
        assert name in after, ("gameplay domain lost", name)
    receipt = {
        "status":"PRIVATE_SOURCE_ONLY_NOT_AUTHENTICATED_RC",
        "official_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
        "owner_accepted":False,"pinned_baseline_project":str(base_project),
        "original_26_exact":True,"unaltered_existing":25,
        "host_overlay_only":HOST,"added_server_modules":list(ADDED),
        "script_count":28,"server_count":25,"client_count":3,
        "source_sha256":{name:value[1] for name,value in sorted(after.items())},
        "unchanged_baseline_sha256":{name:value[1] for name,value in sorted(before.items())
                                    if name != HOST},
        "rollback":"omit the optional defense hook and two modules; no save changes",
    }
    (out_project.parent / "CASTLE_DEFENSE_28_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("EGGRUMBLE_CASTLE_DEFENSE_PRIVATE28_SOURCE_EXACT_25_PLUS_HOST2_PASS")
    return receipt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-project", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    build(args.base_project, args.out)

if __name__ == "__main__":
    main()
