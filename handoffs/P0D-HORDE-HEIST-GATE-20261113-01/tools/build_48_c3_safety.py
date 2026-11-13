#!/usr/bin/env python3
"""C3: strict source-locked private C2→C3 runtime safety fix, no 2nd Game.
Keeps original all B42+V7+C1+C2 sources from pinned independent builders.
Three exactly allowed changes: Game, visual door adapter, solo epoch policy.
"""
from __future__ import annotations
import argparse,collections,difflib,hashlib,json,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_HEAD_C2="9bacd0b9b904d121f192f579047a97bd1e4f8b3a"
ORIGINAL_V7="70714a081a555d716832bb6a640611e05a1f3eca"
ORIGINAL_VISUAL_BLOB="f94b495725dc7c53e35e35b4e05e753a9a9dd794"
ORIGINAL_SOLO_BLOB="a0576d25c78d3c6341e8119853d646c36b42345e"
EXPECTED_TOTAL=48

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def scripts(path:Path):
    return {p.relative_to(path/"src").as_posix():p.read_bytes()
            for p in sorted((path/"src").rglob("*.luau"))}
def replace_once(src:str,find:str,repl:str)->str:
    n=src.count(find)
    assert n==1,("C3_FROZEN_GAME_DRIFT",find[:120],n)
    return src.replace(find,repl,1)

def upgrade_game(game:str)->str:
    g=replace_once(game,
        'local match = {\n    serial = 0,',
        'local match = {\n    serial = 0,\n'
        '    studioSolo = false, -- C3: original 2-team match never changes to solo mid-round')
    g=replace_once(g,
        '    match.serial += 1\n    if RunService:IsStudio() then',
        '    match.serial += 1\n'
        '    match.studioSolo = StudioSoloGateRules.isPractice(\n'
        '        RunService:IsStudio(),#Players:GetPlayers(),\n'
        '        teamCount("RED"),teamCount("BLUE"))\n'
        '    if RunService:IsStudio() then')
    g=replace_once(g,
        'local singlePractice=StudioSoloGateRules.isPractice(RunService:IsStudio(),count,\n'
        '            teamCount("RED"),teamCount("BLUE"))',
        'local singlePractice=StudioSoloGateRules.activePractice(\n'
        '            RunService:IsStudio(),match.studioSolo,count,\n'
        '            teamCount("RED"),teamCount("BLUE"))')
    g=replace_once(g,
        '            match.phase = "LOBBY"\n            match.winner = ""',
        '            match.phase = "LOBBY"\n'
        '            match.studioSolo = false\n'
        '            match.winner = ""')
    assert g.count("match.studioSolo = StudioSoloGateRules.isPractice(")==1
    assert g.count("StudioSoloGateRules.activePractice(")==1
    assert g.count("match.studioSolo = false")==1
    assert g.count("studioSolo = false,")==1
    assert g.count("StudioSoloGateRules.canStart(")==2
    assert g.count("s2HeistGate:beforeHit(horde)")==2
    assert g.count("s2HeistGate:afterHit(horde,beforeElite,")==2
    assert g.count("s2HeistGate:startRound(")==1
    assert g.count("s2HeistGate:tick(")==1
    assert g.count("remote.OnServerEvent:Connect(")==1
    assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
    return g

def main(original_repo:Path,dest:Path):
    assert not dest.exists(),"C3_DO_NOT_OVERWRITE_FINAL_PLACE"
    base=dest.parent/"_C2_IMMUTABLE_BUILD_BEFORE_C3"
    assert not base.exists(),"C3_DO_NOT_OVERWRITE_BASE_C2"
    cmd=[sys.executable,"-B",str(ROOT/"tools/build_48_studio_solo.py"),
         "--original-v7-repo",str(original_repo),"--output",str(base)]
    subprocess.run(cmd,check=True)
    old=scripts(base)
    assert len(old)==EXPECTED_TOTAL,len(old)
    assert blob(old["server/GateVisual.luau"])==ORIGINAL_VISUAL_BLOB
    assert blob(old["server/StudioSoloGateRules.luau"])==ORIGINAL_SOLO_BLOB
    assert 'local singlePractice=StudioSoloGateRules.isPractice(' in old["server/Game.server.luau"].decode()
    shutil.copytree(base,dest)
    updated=upgrade_game(old["server/Game.server.luau"].decode("utf-8"))
    (dest/"src/server/Game.server.luau").write_text(updated,encoding="utf-8")
    visual=(ROOT/"src/GateVisualRaySafeC3.luau").read_bytes()
    solo=(ROOT/"src/StudioSoloLatchRulesC3.luau").read_bytes()
    assert 'door.CanCollide = false\n        door.CanQuery = false' in visual.decode()
    assert 'door.CanQuery = true\n        door.CanCollide = true' in visual.decode()
    assert 'function Solo.activePractice(' in solo.decode()
    (dest/"src/server/GateVisual.luau").write_bytes(visual)
    (dest/"src/server/StudioSoloGateRules.luau").write_bytes(solo)
    new=scripts(dest)
    assert len(new)==EXPECTED_TOTAL
    assert set(old)==set(new)
    changed=[p for p in old if old[p]!=new[p]]
    assert changed==["server/Game.server.luau","server/GateVisual.luau",
                     "server/StudioSoloGateRules.luau"],changed
    assert sum(p.endswith(".server.luau") for p in new)==2
    assert sum(p.endswith(".client.luau") for p in new)==5
    assert sum(p.endswith("/Game.server.luau") for p in new)==1
    assert len([p for p in new if p.endswith(".luau")])==48
    proj=dest/"default.project.json"
    o=json.loads(proj.read_text("utf-8"))
    assert o["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    o["name"]="P0D_C3_B42_V7_GATE_SOLO_LATCH_RAY_SAFE_PRIVATE"
    proj.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt={
      "name":"C3_SAFE_REAL_ELITE_GATE_PRIVATE_STUDIO",
      "original_immutable_B42_V7":ORIGINAL_V7,
      "previous_C2_source_head":SOURCE_HEAD_C2,
      "total_scripts":48,
      "original_C2_sources_byte_identical":45,
      "only_3_changed":changed,
      "single_Game":True,"single_Remote":True,
      "studioSoloRoundLatched":True,
      "no_public_solo":True,
      "openDoorPassableAndRaycastClear":True,
      "private_unpublished":True,
      "roblox_engine_studio":"NOT_TESTED","two_client":"NOT_TESTED",
      "android":"NOT_TESTED","human_fun":"NOT_TESTED",
      "official_rc_adopted":False,"paid":False,
      "git_blobs":{k:blob(v) for k,v in sorted(new.items())},
    }
    (dest/"SOURCE_LOCK.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    gdiff="".join(difflib.unified_diff(
        old["server/Game.server.luau"].decode().splitlines(True),
        updated.splitlines(True),
        fromfile="C2_Game",tofile="C3_Game"))
    (dest/"C2_TO_C3_ONLY_GAME.diff").write_text(gdiff,encoding="utf-8")
    print("P0D_C3_48_LUAU_45_OF_48_BYTE_EXACT_3_SAFE_CHANGED_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-v7-repo",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    a=parser.parse_args()
    main(a.original_v7_repo.resolve(),a.output.resolve())
