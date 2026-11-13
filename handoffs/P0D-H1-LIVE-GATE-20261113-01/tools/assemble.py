#!/usr/bin/env python3
"""Stage an UNPUBLISHED H1 29-source future live gate candidate from #255 exact fixed source.
Do not edit original #255 builder or any game sources, official RC, main or GitHub publish state.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve()
REPO=HERE.parents[3]
OWN=HERE.parents[1]
ORIG=REPO/"handoffs/P0D-H1-WOW-4WAY-20261113-01"
ORIG_BUILD=ORIG/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
DEST=OWN/"dist/TRAP_RAIDERS_H1_LIVE_GATE_OFF_STUDIO_ONLY"
IN=OWN/"inputs"
NEW={
    "server/H1FunWorld.server.luau":"e344cbe67ab6a67f9382982c3a463569389dc49d",
    "client/D18MascotGuide.client.luau":"b0962b63867eef42d2657d6ad7c0302e4d637f7f",
    "shared/H1ReleaseGate.luau":"9c73d5b7da194077d268d727a2ddc5adf81aaef4"
}
OLD={
    "server/H1FunWorld.server.luau":"cc764b9caaa293ff747489e02e607af4502ddca4",
    "client/D18MascotGuide.client.luau":"39a2e35e4b2e8635d6d87359cd86f783aedf8756"
}
def blob(b:bytes):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def require_blob(p:Path,expected:str):
    assert p.is_file(),p
    got=blob(p.read_bytes())
    assert got==expected,(p,got,expected)
    return got

def build():
    # Re-execute the actual pinned original 28-game assembly; no approximation/merging source roots.
    subprocess.run([sys.executable,"-B",str(ORIG/"tools/assemble.py"),"--verify"],check=True,cwd=REPO)
    subprocess.run([sys.executable,"-B",str(ORIG/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
    original_src=ORIG_BUILD/"src"
    source_paths=sorted(p.relative_to(original_src) for p in original_src.rglob("*.luau"))
    assert len(source_paths)==28,len(source_paths)
    for rel,h in OLD.items():require_blob(original_src/rel,h)
    for rel,h in NEW.items():require_blob(IN/Path(rel).name,h)
    # Deliberately do not alter original authored H1 source/CI/protected RC.
    if DEST.exists():shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    shutil.copytree(original_src,DEST/"src")
    project=json.loads((ORIG_BUILD/"default.project.json").read_text(encoding="utf-8"))
    project["name"]="TRAP_RAIDERS_H1_LIVE_GATE_OFF_STUDIO_ONLY"
    assert project["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"]=="src/shared"
    for rel in NEW:
        target=DEST/"src"/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(IN/Path(rel).name,target)
    (DEST/"default.project.json").write_text(
        json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    built_paths=sorted(p.relative_to(DEST/"src") for p in (DEST/"src").rglob("*.luau"))
    assert len(built_paths)==29,len(built_paths)
    assert len([p for p in built_paths if p.name=="Game.server.luau"])==1
    assert len([p for p in built_paths if p.name=="H1ReleaseGate.luau"])==1
    assert len([p for p in built_paths if p.name=="H1FunWorld.server.luau"])==1
    assert len([p for p in built_paths if p.name=="D18MascotGuide.client.luau"])==1
    modified=[rel.as_posix() for rel in source_paths
              if (original_src/rel).read_bytes()!=(DEST/"src"/rel).read_bytes()]
    assert modified==sorted(OLD),modified
    for rel in source_paths:
        if rel.as_posix() not in OLD:
            assert (original_src/rel).read_bytes()==(DEST/"src"/rel).read_bytes(),rel
    for rel,h in NEW.items():require_blob(DEST/"src"/rel,h)
    gate=(DEST/"src/shared/H1ReleaseGate.luau").read_text(encoding="utf-8")
    assert "local LIVE_ENABLE = false" in gate
    assert "local APPROVED_GAME_ID = 0" in gate
    assert "local APPROVED_PLACE_ID = 0" in gate
    assert "if isStudio == true then return true end" in gate
    assert "and gameId == APPROVED_GAME_ID and placeId == APPROVED_PLACE_ID" in gate
    for rel in OLD:
        s=(DEST/"src"/rel).read_text(encoding="utf-8")
        assert "ReleaseGate.canRun(RunService:IsStudio(),game.GameId,game.PlaceId)" in s
        assert 'WaitForChild("H1ReleaseGate",30)' in s
        assert 'SetAttribute("PreviewOnly",RunService:IsStudio())' in s
        assert "FireServer" not in s and "MarketplaceService" not in s
    receipt={
        "game_id":"TRAP_RAIDERS","adoption_id":"P0D-FUN-H1-001",
        "source":"#255 immutable original H1 whole game",
        "original_h1_sha":"1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b",
        "source_count":29,"unchanged_original_h1_scripts":26,
        "only_replaced_h1_scripts":sorted(OLD),
        "new_h1_shared_module":"shared/H1ReleaseGate.luau",
        "module_live_enable":False,
        "approved_game_id":0,"approved_place_id":0,
        "developer_Studio_only_enabled":True,
        "non_Studio_life_enabled":False,
        "owner_Studio_2client_tested":False,"human_FUN_GO":False,
        "official_RC_adopted":False,"published":False,
        "script_expected_git_blobs":NEW
    }
    (DEST/"SOURCE_LOCK.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("H1_RELEASE_GATE_ACTUAL_29_SCRIPT_FULL_GAME_SOURCE_BUILT_LIVE_DISABLED")
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true")
    a=p.parse_args()
    if not a.assemble:p.error("--assemble required")
    build()
if __name__=="__main__":main()
