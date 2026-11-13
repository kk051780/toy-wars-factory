#!/usr/bin/env python3
"""Reproducible extra H2 action pad experiment, keeping all #262 H1 game source byte exact."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
REPO=Path(__file__).resolve().parents[3]
OWN=Path(__file__).resolve().parents[1]
UP=REPO/"handoffs/P0D-H1-FAST-ROUTES-WITH-UX-20261113-01"
BASE=UP/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
DEST=OWN/"dist/TRAP_RAIDERS_H2_STAR_JUMP_STUDIO_ONLY"
INPUTS={
    "H2StarLaunchPolicy.luau":"2879b6fc8b1547a4d13db19a616da756c04180d7",
    "H2StarLaunch.server.luau":"b122c49f2072e383d27b1452d0bdda108f05f915",
}
EXPECTED_GAME={
    "server/Game.server.luau":"adecfee41a594bdd54393050b4890a5733a536ce",
    "server/S1RaiderWindRules.luau":"7d5706774b874759e7ab994dc0654c3ae9a46502",
    "server/MapBuilder.luau":"94655d019fdf9798fa24a350ebf49f8290465ac0",
    "server/H1FunWorld.server.luau":"7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea",
    "client/HUD.client.luau":"313484a69eb10ce01bbdb4872afee215133b01d4",
}
BAD=["RemoteEvent","FireServer","FireClient","FireAllClients","DataStore","Marketplace","Robux","TeleportService","TakeDamage","LoadCharacter"]
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def pin(path:Path,sha:str):
    assert path.exists(),("PINNED_FILE_MISSING",str(path))
    got=blob(path.read_bytes())
    assert got==sha,("SHA_MISMATCH",str(path),got,sha)
def inputs():
    for k,sha in INPUTS.items():pin(OWN/"src/server"/k,sha)
    src=(OWN/"src/server/H2StarLaunch.server.luau").read_text()
    pol=(OWN/"src/server/H2StarLaunchPolicy.luau").read_text()
    assert 'if not RunService:IsStudio() then return end' in src
    assert 'local Policy = require(script.Parent:WaitForChild("H2StarLaunchPolicy"))' in src
    assert 'if not Policy.canLaunch({' in src
    assert 'root.AssemblyLinearVelocity=Vector3.new(speed.x,speed.y,speed.z)' in src
    assert 'if not player or player.Parent~=Players then return end' in src
    assert 'lastUse[player]=now' in src
    assert src.count('wire("RED")')==1 and src.count('wire("BLUE")')==1
    assert src.count('prompt.Triggered:Connect')==1
    for word in BAD:
        assert word not in src and word not in pol,("FORBIDDEN_AUTHORITY",word)
    assert len(re.findall(r'Instance\.new\("ProximityPrompt"\)',src))==1
    assert len(re.findall(r'Instance\.new\("Part"\)',src))==1
    assert len(re.findall(r'local function wire\(side:string\)',src))==1
    assert 'P.COOLDOWN = 12' in pol and 'P.MAX_DISTANCE = 10' in pol
    return {"original_script_count":28,"new_script_count":2,"server_checks":True}

def assemble():
    evidence=inputs()
    subprocess.run([sys.executable,str(UP/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,timeout=60,check=True)
    original_files=sorted((BASE/"src").rglob("*.luau"))
    assert len(original_files)==28,("ORIGINAL_H1_SOURCE_COUNT_NOT28",len(original_files))
    for k,sha in EXPECTED_GAME.items():pin(BASE/"src"/k,sha)
    source={x.relative_to(BASE/"src").as_posix():x.read_bytes() for x in original_files}
    assert len(source)==28 and len([x for x in source if x=="server/Game.server.luau"])==1
    if DEST.exists():shutil.rmtree(DEST)
    shutil.copytree(BASE,DEST)
    for key in INPUTS:
        shutil.copyfile(OWN/"src/server"/key,DEST/"src/server"/key)
    output={x.relative_to(DEST/"src").as_posix():x.read_bytes()
            for x in (DEST/"src").rglob("*.luau")}
    assert len(output)==30,("EXPECTED_FULL_REAL_GAME_30",len(output))
    assert all(output.get(path)==raw for path,raw in source.items()),"ORIGINAL_28_SCRIPTS_MODIFIED"
    assert set(output)-set(source)=={"server/"+key for key in INPUTS},"UNEXPECTED_SCRIPT_ADDED"
    project=DEST/"default.project.json"
    data=json.loads(project.read_text())
    data["name"]="TRAP_RAIDERS_H2_STAR_JUMP_UNPUBLISHED_STUDIO_ONLY"
    project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    receipt={"feature_id":"P0D-STUDIO-ACTION-STAR-JUMP-001",
        "release_status":"S2_OPTIONAL_OWNER_PRIVATE_STUDIO_TEST_DO_NOT_PUBLISH",
        "game_base":"#262 8f2a4aed7f6483f0bd00e31fcd733a823aa5c008",
        "original_game_all_28_byte_exact":True,"new_Studio_only_scripts":INPUTS,
        "source_count":30,"subsystem":"FIXED_SERVER_IMPULSE_TWO_TEAMS_NO_NEW_REMOTE",
        "underlying_original":EXPECTED_GAME,"static_source_contract":evidence,
        "not_tested":{"owner_two_client_Studio":True,"actual_physics":True,
          "Android_touch":True,"human_fun":True,"publishing":True,
          "official_rc_integration":True}}
    (DEST/"SOURCE_LOCK.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("H2_STAR_JUMP_ORIGINAL_GAME_28_OF_28_BYTES_PRESERVED")
    print("H2_STAR_JUMP_NEW_ACTUAL_SCRIPTS_2_AND_FULL_GAME_30")
    return output

def verify_xml(place:Path,receipt:Path):
    source=sorted((DEST/"src").rglob("*.luau"))
    assert len(source)==30,"SOURCE_30_REQUIRED"
    actual=collections.Counter()
    classes=collections.Counter()
    xml=ET.fromstring(place.read_bytes())
    for item in xml.iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","LocalScript","ModuleScript"}:continue
        body=item.find("./Properties/string[@name='Source']")
        if body is not None:
            classes[cls]+=1
            actual[body.text or ""]+=1
    expected=collections.Counter(p.read_text(encoding="utf-8") for p in source)
    assert actual==expected,("XML_SCRIPTS_NOT_SAME_EXACT_REAL_SOURCE",sum(actual.values()),len(source))
    assert classes=={"Script":3,"LocalScript":4,"ModuleScript":23},classes
    proof=json.loads((DEST/"SOURCE_LOCK.json").read_text())
    proof["real_Rojo_30_of_30_exact_source"]=True
    proof["actual_studio_file_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    proof["actual_studio_file_bytes"]=place.stat().st_size
    proof["classes"]=dict(classes)
    receipt.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
    print("H2_STAR_JUMP_ROJO_FULL_REAL_PLACE_30_OF_30_SOURCE_EXACT_PASS")
    print("H2_STAR_JUMP_ROJO_PRIVATE_PLACE_SHA256="+proof["actual_studio_file_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true")
    p.add_argument("--check-input",action="store_true")
    p.add_argument("--verify-xml",type=Path)
    p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    if a.check_input:print(inputs())
    elif a.assemble:assemble()
    elif a.verify_xml:
        assert a.receipt is not None
        verify_xml(a.verify_xml,a.receipt)
    else:p.error("choose one")
