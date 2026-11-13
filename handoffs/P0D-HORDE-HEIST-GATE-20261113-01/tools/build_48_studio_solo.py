#!/usr/bin/env python3
"""Standalone C2 PRIVATE Studio SOLO trial built from exact C1 full-game author.
Never overwrites C1 or original owner B42/V7 source/RC. Solo only IsStudio().
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_BASE_GAME="a09b6ea4d9a2b21d" # ignored: actual C1 sha verified by builder lock comparison
EXPECTED_ORIGINAL=47

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def sources(root:Path):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
        for p in sorted((root/"src").rglob("*.luau"))}
def replace_once(source:str,before:str,after:str)->str:
    assert source.count(before)==1,("ORIGINAL_GAME_DRIFT",before[:90],source.count(before))
    return source.replace(before,after,1)

def patch_game(source:str)->str:
    g=source
    g=replace_once(g,
        'local GateLiveRuntime = require(script.Parent:WaitForChild("GateLiveRuntime")) -- PRIVATE S2 overlay only',
        'local GateLiveRuntime = require(script.Parent:WaitForChild("GateLiveRuntime")) -- PRIVATE S2 overlay only\n'
        'local StudioSoloGateRules = require(script.Parent:WaitForChild("StudioSoloGateRules")) -- private one-client QA')
    g=replace_once(g,
        'if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then',
        'if StudioSoloGateRules.canStart(RunService:IsStudio(),count,Config.MinPlayers,\n'
        '            teamCount("RED"),teamCount("BLUE")) then')
    g=replace_once(g,
        'if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then',
        'if not StudioSoloGateRules.canStart(RunService:IsStudio(),count,Config.MinPlayers,\n'
        '            teamCount("RED"),teamCount("BLUE")) then')
    g=replace_once(g,
        'if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")\n'
        '        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")',
        'local singlePractice=StudioSoloGateRules.isPractice(RunService:IsStudio(),count,\n'
        '            teamCount("RED"),teamCount("BLUE"))\n'
        '        if not singlePractice and teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")\n'
        '        elseif not singlePractice and teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")')
    g=replace_once(g,
        'match.phase = "ACTIVE"\n    match.startedAt = serverNow()',
        'match.phase = "ACTIVE"\n'
        '    if StudioSoloGateRules.isPractice(RunService:IsStudio(),#Players:GetPlayers(),\n'
        '            teamCount("RED"),teamCount("BLUE")) then\n'
        '        warn("P0D_STUDIO_SOLO_PRACTICE_ONLY_NO_PVP_NO_OFFICIAL_FUN_PASS")\n'
        '    end\n'
        '    match.startedAt = serverNow()')
    assert g.count('StudioSoloGateRules.canStart(')==2
    assert g.count('StudioSoloGateRules.isPractice(')==2
    assert 'P0D_STUDIO_SOLO_PRACTICE_ONLY_NO_PVP_NO_OFFICIAL_FUN_PASS' in g
    assert g.count('s2HeistGate:beforeHit(horde)')==2
    assert g.count('s2HeistGate:startRound(')==1
    assert g.count('s2HeistGate:tick(')==1
    assert g.count('remote.OnServerEvent:Connect(')==1
    assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
    return g

def main(v7_repo:Path,private_dir:Path)->None:
    assert not private_dir.exists(),"C2_FAIL_CLOSED_NO_OVERWRITE"
    c1_dir=private_dir.parent/"_S2_PREVIOUS_C1_EXACT_47"
    assert not c1_dir.exists(),"C1_FAIL_CLOSED_NO_OVERWRITE"
    c1_builder=ROOT/"tools/build_47_private_gate.py"
    assert c1_builder.is_file()
    subprocess.run([sys.executable,"-B",str(c1_builder),
        "--original-v7-repo",str(v7_repo),"--output",str(c1_dir)],check=True)
    original=sources(c1_dir)
    assert len(original)==EXPECTED_ORIGINAL
    assert "server/StudioSoloGateRules.luau" not in original
    game_original=original["server/Game.server.luau"].decode("utf-8")
    game_new=patch_game(game_original)
    shutil.copytree(c1_dir,private_dir)
    (private_dir/"src/server/Game.server.luau").write_text(game_new,encoding="utf-8")
    solo=(ROOT/"src/StudioSoloGateRules.luau").read_bytes()
    assert "Studio" in solo.decode("utf-8") and b"players==1" in solo
    (private_dir/"src/server/StudioSoloGateRules.luau").write_bytes(solo)
    all_new=sources(private_dir)
    assert len(all_new)==48
    assert set(all_new)-set(original)=={"server/StudioSoloGateRules.luau"}
    assert [k for k in original if all_new[k]!=original[k]]==["server/Game.server.luau"]
    assert sum(k.endswith(".server.luau") for k in all_new)==2
    assert sum(k.endswith(".client.luau") for k in all_new)==5
    assert sum(k.endswith("/Game.server.luau") for k in all_new)==1
    assert all(all_new[k]==original[k] for k in original if k!="server/Game.server.luau")
    project=private_dir/"default.project.json"
    proj=json.loads(project.read_text(encoding="utf-8"))
    assert proj["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    proj["name"]="P0D_C2_B42_V7_GATE_STUDIO_SOLO_48_PRIVATE"
    project.write_text(json.dumps(proj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lock={
        "packet_id":"P0D-S2-C2-PRIVATE-STUDIO-SOLO-20261113",
        "parent_original_v7":"70714a081a555d716832bb6a640611e05a1f3eca",
        "base_c1_original_47_game_gitblob":gitblob(original["server/Game.server.luau"]),
        "studio_solo_policy_gitblob":gitblob(solo),
        "new_luau":48,"only_new_module":"server/StudioSoloGateRules.luau",
        "only_changed_original":"server/Game.server.luau",
        "47_previous_sources_other_than_Game_byte_exact":46,
        "server_game":1,"remote":1,
        "private_studio_solo_allowed":True,
        "public_or_live_solo_allowed":False,
        "two_client_original_rules_preserved":True,
        "android":"NOT_TESTED","studio_play":"NOT_TESTED","fun":"NOT_TESTED",
        "official_rc_adopted":False,"published":False,"paid":False,
        "source_git_blob_sha1":{k:gitblob(v) for k,v in sorted(all_new.items())}
    }
    (private_dir/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    diff="".join(difflib.unified_diff(
        game_original.splitlines(keepends=True),game_new.splitlines(keepends=True),
        fromfile="C1_Game.server.luau",tofile="C2_StudioSolo_Game.server.luau"))
    (private_dir/"C2_SOURCE_DIFF.diff").write_text(diff,encoding="utf-8")
    print("P0D_S2_C2_SOLO_48_ORIGINAL_ONE_GAME_SOURCE_LOCK_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-v7-repo",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    main(args.original_v7_repo.resolve(),args.output.resolve())
