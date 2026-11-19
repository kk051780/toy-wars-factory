#!/usr/bin/env python3
"""SOURCE-selective PRIVATE V3 26->27 script composer. Existing 26 original author
game, ART, SCORE and quality fix scripts are never edited on disk.
Do not use this as an authorization for official RC, main, or Roblox Publish.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

SCRIPT = "EGGRUMBLE_DeadlinePolicy"
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
RESULT = "EGGRUMBLE_MatchResultService"
ITEM = "EGGRUMBLE_FieldItemPickups"

HOST_REQUIRE_ANCHOR = 'local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))'
HOST_START_ANCHOR = ' Rules.start(session.rules)\n'
RESULT_STATUS_ANCHOR = 'local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"'
HOST_REQUIRE_ADDITION = 'local DeadlinePolicy=require(script.Parent:WaitForChild("EGGRUMBLE_DeadlinePolicy"))'
HOST_START_ADDITION = """ Rules.start(session.rules)
 -- GQ #499: Same server-authoritative V3 round; no second Game, Remote, queue or score.
 -- Weak-table epoch ID is an identity token, never accepted from a client.
 local deadlineId=mode..":"..tostring(session)
 local deadlineLease=DeadlinePolicy.new(os.clock(),deadlineId)
 session.deadlineLease=deadlineLease
 task.spawn(function()
  while sessions[mode]==session and session.rules.phase=="ACTIVE" and session.world.Parent do
   local expired=DeadlinePolicy.expire(session.rules,deadlineLease,os.clock(),deadlineId)
   if expired then
    -- Existing result + replay flow; keep score, egg, KO and castle authors intact.
    session.refresh()
    break
   end
   task.wait(.5)
  end
 end)
"""
RESULT_STATUS_ADDITION = 'local status=if session.rules.winner=="DRAW" then "引き分け" elseif won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"'

def exact_once(s: str, before: str, after: str, label: str) -> str:
    assert s.count(before) == 1, f"{label}: source drift, expected exactly one anchor"
    assert after not in s, f"{label}: patch already applied"
    return s.replace(before, after, 1)

def mapped_source(manifest: Path, item: dict) -> Path:
    assert set(item) == {"$path"}
    p = (manifest.parent / item["$path"]).resolve(strict=True)
    assert p.is_file() and p.suffix == ".luau", p
    return p

def manifest_path(out: Path, src: Path) -> dict[str, str]:
    return {"$path": os.path.relpath(src, out.parent).replace(os.sep, "/")}

def patch_host(source: str) -> str:
    assert source.count('local function startSession(mode:string)') == 1
    assert source.count('session.refresh=function()') == 1
    assert source.count(HOST_START_ANCHOR)==1, 'start() source drift'
    assert source.index('session.refresh=function()') < source.index(HOST_START_ANCHOR)
    assert source.count('session.closeRound=function(') == 1
    assert 'RoundReplay.schedule(session,session.closeRound)' in source
    assert 'ResultService.showIfFinished(session,queue,mode)' in source
    assert 'EGGRUMBLE_BossSessionFence' in source
    patched = exact_once(source, HOST_REQUIRE_ANCHOR,
                         HOST_REQUIRE_ANCHOR + "\n" + HOST_REQUIRE_ADDITION, "deadline import")
    return exact_once(patched, HOST_START_ANCHOR, HOST_START_ADDITION, "deadline lifecycle")

def patch_result(source: str) -> str:
    assert 'local ranking=ScoreBalance.build(' in source, "must retain actual #487 SCORE"
    assert 'if session.resultsDelivered' in source, "must retain one-shot original result"
    return exact_once(source, RESULT_STATUS_ANCHOR, RESULT_STATUS_ADDITION, "draw result")

def enumerate_scripts(node: dict, chain: tuple[str, ...] = ()):
    for key, item in node.items():
        if key.startswith("$"): continue
        if isinstance(item, dict) and "$path" in item:
            yield chain+(key,), item
        elif isinstance(item, dict):
            yield from enumerate_scripts(item, chain+(key,))

def compose(base_project: Path, policy: Path, out: Path, item: Path | None = None) -> dict:
    assert out.resolve() != base_project.resolve()
    assert out.parent.is_dir(), "output directory must exist"
    base = json.loads(base_project.read_text(encoding="utf-8"))
    project = copy.deepcopy(base)
    tree = project["tree"]
    server = tree["ServerScriptService"]
    client = tree["StarterPlayer"]["StarterPlayerScripts"]
    assert len(server)-1 == 23 and len(client)-1 == 3
    assert SCRIPT not in server
    assert HOST in server and RESULT in server
    assert "EGGRUMBLE_BossSessionFence" in server
    assert "EGGRUMBLE_ProceduralSkills" in client
    assert "EGGRUMBLE_ArtDistanceLOD" in client
    old_paths = {k:mapped_source(base_project,v) for k,v in server.items() if k!="$className"}
    old_client = {k:mapped_source(base_project,v) for k,v in client.items() if k!="$className"}
    assert len(old_paths)==23 and len(old_client)==3
    host = old_paths[HOST].read_text(encoding="utf-8")
    result = old_paths[RESULT].read_text(encoding="utf-8")
    modified_host=patch_host(host)
    modified_result=patch_result(result)
    # Source-select the dedicated #489 ITEM author's original bytes, never
    # reimplement HEAL/DASH/SHIELD, guard, or 35-second respawn here.
    item_bytes=None
    item_original=old_paths[ITEM].read_bytes()
    if item is not None:
        item=item.resolve(strict=True)
        assert item.name==ITEM+".luau", "wrong item author source"
        item_bytes=item.read_bytes()
        assert item_bytes!=item_original, "ITEM overlay not applied"
        item_source=item_bytes.decode("utf-8")
        assert 'carryingEnemyEggs(' in item_source and 'cancelBuffIfCarrier(' in item_source
        assert 'interactionGuard.allow(player,part,"拾う",part.Name)' in item_source
        assert 'local RESPAWN_SECONDS=35' in item_source
        assert 'local DEFINITIONS=' in item_source
        assert 'return Items' in item_source
    policy = policy.resolve(strict=True)
    assert "function Deadline.expire" in policy.read_text(encoding="utf-8")
    # Never overwrite the #484 composer\'s existing 26-source host in artifacts/.
    h_path=out.parent/(HOST+"_Deadline27.server.luau")
    r_path=out.parent/(RESULT+"_Deadline27.luau")
    assert h_path != old_paths[HOST] and r_path != old_paths[RESULT]
    h_path.write_text(modified_host,encoding="utf-8")
    r_path.write_text(modified_result,encoding="utf-8")
    server[HOST]=manifest_path(out,h_path)
    server[RESULT]=manifest_path(out,r_path)
    server[SCRIPT]=manifest_path(out,policy)
    if item is not None:
        server[ITEM]=manifest_path(out,item)
    project["name"]="EGGRUMBLE_V3_27SOURCE_DEADLINE_PRIVATE_NOT_OFFICIAL"
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    mapped = list(enumerate_scripts(tree))
    assert len(mapped)==27
    actual={nodes[-1]:(nodes,mapped_source(out,item)) for nodes,item in mapped}
    assert len(actual)==27, "Duplicate source names"
    unchanged_excludes={HOST, RESULT}
    if item is not None: unchanged_excludes.add(ITEM)
    for name,p in old_paths.items():
        if name in unchanged_excludes: continue
        assert actual[name][1].read_bytes()==p.read_bytes(), f"Original game/ART/SCORE modified: {name}"
    for name,p in old_client.items():
        assert actual[name][1].read_bytes()==p.read_bytes(), f"Original client modified: {name}"
    for nodes,item in mapped:
        if nodes[0]=="ServerScriptService":
            text=mapped_source(out,item).read_text(encoding="utf-8")
            import re
            for dep in re.findall(r'script\.Parent:WaitForChild\("([^"]+)"\)',text):
                assert dep in server, f"Unmapped original sibling {nodes[-1]}->{dep}"
    receipt={
        "status":"PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "source_count":27,"server_count":24,"client_count":3,
        "unchanged_original_sources":26-len(unchanged_excludes),
        "private_modified_original_sources":sorted(unchanged_excludes),
        "item_author_byte_exact":item_bytes is not None,
        "item_author_sha256":hashlib.sha256(item_bytes).hexdigest() if item_bytes is not None else None,
        "original_item_sha256":hashlib.sha256(item_original).hexdigest(),
        "new_pure_source":SCRIPT,
        "changes_only_in_generated_place":True,
        "studio":"NOT_TESTED","android":"NOT_TESTED","owner_accepted":False,
        "source_sha256":{name:hashlib.sha256(p.read_bytes()).hexdigest()
                         for name,(_,p) in sorted(actual.items())},
        "original_host_sha256":hashlib.sha256(host.encode("utf-8")).hexdigest(),
        "original_score_result_sha256":hashlib.sha256(result.encode("utf-8")).hexdigest(),
    }
    (out.parent/"DEADLINE27_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--policy",required=True,type=Path)
    ap.add_argument("--item",type=Path,help="read-only fixed original #489 ITEM author source")
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    r=compose(a.base.resolve(strict=True),a.policy.resolve(strict=True),a.out.resolve(),a.item)
    print("EGGRUMBLE_DEADLINE_ACTUAL_GAME_27_COMPOSE_PASS",r["source_count"])

if __name__=="__main__":
    main()
