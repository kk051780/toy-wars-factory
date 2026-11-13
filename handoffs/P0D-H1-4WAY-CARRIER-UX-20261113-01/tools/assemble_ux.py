#!/usr/bin/env python3
"""Overlay ONLY #251 child-friendly HUD into #255 original full 28-Luau private H1 game."""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,collections
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
OWN=Path(__file__).resolve().parents[1]
BASE=REPO/"handoffs/P0D-H1-WOW-4WAY-20261113-01"
BASE_DIST=BASE/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
DST=OWN/"dist/TRAP_RAIDERS_H1_WOW_4WAY_CARRIER_UX_STUDIO_ONLY"
HUD_INPUT=OWN/"input/HUD.client.luau"
NEW_HUD_BLOB="313484a69eb10ce01bbdb4872afee215133b01d4"
OLD_HUD_BLOB="6d273404800e1d25fb1405bc52249b3ab47c1b41"
GITHUB_BASE_SHA="1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b"
GITHUB_HUD_SHA="4606a74dcebdf4d8a51de4e69b930a15ac788180"

def git_blob(raw: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def source_tree(root):
    result={}
    for f in sorted((root/"src").rglob("*.luau")):
        p=f.relative_to(root/"src").as_posix()
        result[p]=f.read_bytes()
    assert len(result)==28,len(result)
    return result

def assemble():
    assert git_blob(HUD_INPUT.read_bytes())==NEW_HUD_BLOB,"HUD_CANONICAL_INPUT_MISMATCH"
    subprocess.run([sys.executable,str(BASE/"tools/assemble.py"),"--verify"],check=True,cwd=REPO)
    subprocess.run([sys.executable,str(BASE/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
    before=source_tree(BASE_DIST)
    assert git_blob(before["client/HUD.client.luau"])==OLD_HUD_BLOB,"HUD_BASE_MISMATCH"
    assert any(k=="server/Game.server.luau" for k in before)
    assert any(k=="server/H1FunWorld.server.luau" for k in before)
    assert any(k=="server/S1RaiderWindRules.luau" for k in before)
    assert any(k=="client/D18MascotGuide.client.luau" for k in before)
    if DST.exists():shutil.rmtree(DST)
    shutil.copytree(BASE_DIST,DST)
    (DST/"src/client/HUD.client.luau").write_bytes(HUD_INPUT.read_bytes())
    after=source_tree(DST)
    delta=[n for n in before if before[n]!=after[n]]
    assert delta==["client/HUD.client.luau"],delta
    assert len(after)==28 and set(after)==set(before)
    assert git_blob(after["client/HUD.client.luau"])==NEW_HUD_BLOB
    assert "🪤" in after["client/HUD.client.luau"].decode("utf8")
    new_hud=after["client/HUD.client.luau"].decode("utf8")
    required=[
      'trapButton.Active = s.phase == "ACTIVE" and s.role == "GUARDIAN"',
      'not carryingEgg and trapCooldown == 0',
      'windButton.Active = s.phase == "ACTIVE" and s.role == "RAIDER"',
      'not carryingEgg and windCooldown == 0 and s.windActive ~= true',
      '🥚 卵運搬中','風走り不可'
    ]
    for token in required:assert token in new_hud,token
    assert 'remote:FireServer' not in new_hud,"HUD direct remote authority changed"
    assert 'action("WIND_BURST", nil)' in new_hud
    assert 'action("PLACE_TRAP", nil)' in new_hud
    assert "MarketplaceService" not in new_hud and "DataStoreService" not in new_hud
    assert before["server/Game.server.luau"]==after["server/Game.server.luau"]
    assert before["server/H1FunWorld.server.luau"]==after["server/H1FunWorld.server.luau"]
    assert before["client/D18MascotGuide.client.luau"]==after["client/D18MascotGuide.client.luau"]
    original_project=json.loads((BASE_DIST/"default.project.json").read_text())
    project=json.loads((DST/"default.project.json").read_text())
    original_project["name"]="TRAP_RAIDERS_H1_WOW_4WAY_CARRIER_UX_STUDIO_ONLY"
    project["name"]=original_project["name"]
    assert original_project==project,"PROTECTED_PROJECT_MAP_CHANGED"
    (DST/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    receipt={
      "game":"TRAP_RAIDERS",
      "stage":"PRELAUNCH_PRIVATE_STUDIO_ONLY",
      "adoption_id":"P0D-FUN-H1-001",
      "owner_source_SHA":GITHUB_BASE_SHA,
      "owner_role_HUD_SHA":GITHUB_HUD_SHA,
      "old_HUD_GitBlob":OLD_HUD_BLOB,
      "new_HUD_GitBlob":NEW_HUD_BLOB,
      "script_count":28,
      "exact_other_original_script_count":27,
      "changed_only":delta,
      "all_other_game_scripts_sha256":{n:hashlib.sha256(raw).hexdigest() for n,raw in after.items() if n!="client/HUD.client.luau"},
      "not_tested":{"studio_2client":True,"physical_mobile":True,"owner_fun":True},
      "not_authorized":{"official_RC":True,"public_release":True,"paid":True},
    }
    (DST/"CARRIER_UX_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("P0D_H1_CHILD_CARRIER_UX_28_OF_28_SOURCE_EXACT_ONLY_HUD_CHANGED_27_BYTE_MATCH_PASS")
    print(json.dumps({"source_dir":str(DST.relative_to(REPO)), "changed_only":delta,
                      "Studio":"NOT_TESTED","owner_FUN_GATE":"NO_GO"},ensure_ascii=False))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true",required=True)
    p.parse_args()
    assemble()
