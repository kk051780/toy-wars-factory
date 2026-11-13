#!/usr/bin/env python3
"""Optional H2 original neutral beast: actual H1 real 28 game scripts, exactly 2 new Luau.

Build isolation and fail-closed source/XML proofs. Actual Studio physics unknown.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[3]
OWN=Path(__file__).resolve().parents[1]
UP=REPO/"handoffs/P0D-H1-FAST-ROUTES-WITH-UX-20261113-01"
BASE=UP/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
DEST=OWN/"dist/TRAP_RAIDERS_H2_GATE_BEAST_STUDIO_ONLY"
INPUTS={
    "H2GateBeastPolicy.luau":"0aee2fc29b376cb9be5362f5230245fdf634ddff",
    "H2NeutralGateBeast.server.luau":"747c363f65aaa969af9266813fc79f6457d8e533",
}
EXPECTED_GAME={
    "server/Game.server.luau":"adecfee41a594bdd54393050b4890a5733a536ce",
    "server/S1RaiderWindRules.luau":"7d5706774b874759e7ab994dc0654c3ae9a46502",
    "server/MapBuilder.luau":"94655d019fdf9798fa24a350ebf49f8290465ac0",
    "server/H1FunWorld.server.luau":"7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea",
    "client/HUD.client.luau":"313484a69eb10ce01bbdb4872afee215133b01d4",
}
BAD=("RemoteEvent","FireServer","FireClient","FireAllClients","DataStore","Marketplace","TeleportService","TakeDamage","LoadCharacter","AssemblyLinearVelocity")
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def pin(path:Path,sha:str):
    assert path.is_file(),("PINNED_FILE_MISSING",str(path))
    got=blob(path.read_bytes())
    assert got==sha,("SHA_MISMATCH",str(path),got,sha)

def inputs():
    for k,sha in INPUTS.items():pin(OWN/"src/server"/k,sha)
    ctrl=(OWN/"src/server/H2NeutralGateBeast.server.luau").read_text(encoding="utf-8")
    pol=(OWN/"src/server/H2GateBeastPolicy.luau").read_text(encoding="utf-8")
    must=(
      'if not RunService:IsStudio() then return end',
      'local Policy=require(script.Parent:WaitForChild("H2GateBeastPolicy"))',
      'gate.CanCollide=solid',
      'gate.CanQuery=solid',
      'Policy.insideGate(p.X,p.Y,p.Z)',
      'Policy.nearBeast(p.X,p.Y,p.Z,team,hum.Health>0)',
      'Policy.advance(status,os.clock(),near,clear)',
      'if nextStatus and nextStatus~=status then',
      'if beat then beat:Disconnect() end',
      'gate.CanCollide=false; gate.CanQuery=false',
      'world:SetAttribute("NeutralBothTeams",true)',
      'world:SetAttribute("TwoClientPhysicsMobileAndFun","NOT_TESTED")',
    )
    for needle in must:assert needle in ctrl,("BEAST_GUARD_MISSING",needle)
    assert 'gate.CanCollide=true' not in ctrl, "GATE_CANNOT_FORCE_SOLID_ARBITRARILY"
    assert ctrl.count("RunService.Heartbeat:Connect(")==1
    assert ctrl.count('Instance.new("Part")')==1
    assert pol.count('function P.advance(')==1 and pol.count('function P.insideGate(')==1
    assert 'if laneClear then' in pol and 'P.MAX_WARNING_SECONDS = 5' in pol
    for word in BAD:
        assert word not in ctrl and word not in pol,("FORBIDDEN_AUTHORITY",word)
    assert "H2_ORIGINAL" not in ctrl or "ORIGINAL" in ctrl
    return {"original_script_count":28,"new_script_count":2,
            "server_ownership":"original_Game_only",
            "physical_gate_controlled_by_original_pure_rule":True}

def assemble():
    evidence=inputs()
    subprocess.run([sys.executable,str(UP/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,timeout=60,check=True)
    originals=sorted((BASE/"src").rglob("*.luau"))
    assert len(originals)==28,("ORIGINAL_H1_SOURCE_COUNT",len(originals))
    for rel,sha in EXPECTED_GAME.items():pin(BASE/"src"/rel,sha)
    before={x.relative_to(BASE/"src").as_posix():x.read_bytes() for x in originals}
    if DEST.exists():shutil.rmtree(DEST)
    shutil.copytree(BASE,DEST)
    for fn in INPUTS:
        shutil.copyfile(OWN/"src/server"/fn,DEST/"src/server"/fn)
    after={x.relative_to(DEST/"src").as_posix():x.read_bytes()
           for x in (DEST/"src").rglob("*.luau")}
    assert len(after)==30,("EXPECTED_30_FULL_GAME_SCRIPTS",len(after))
    assert all(after.get(k)==v for k,v in before.items()),"ORIGINAL_GAME_28_SCRIPTS_CHANGED"
    assert set(after)-set(before)=={"server/"+k for k in INPUTS},"UNEXPECTED_GAME_SCRIPT"
    project=DEST/"default.project.json"
    metadata=json.loads(project.read_text(encoding="utf-8"))
    metadata["name"]="TRAP_RAIDERS_H2_NEUTRAL_GATE_BEAST_UNPUBLISHED_STUDIO"
    project.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lock={"id":"P0D-STUDIO-TACTICS-BEAST-001","release_status":"S2_OPTIONAL_PRIVATE_ONLY",
          "original_full_real_H1_source_commit":"8f2a4aed7f6483f0bd00e31fcd733a823aa5c008",
          "original_28_source_byte_exact":True,
          "original_authoritative_game_blob":"adecfee41a594bdd54393050b4890a5733a536ce",
          "new_scripts":INPUTS,"total_scripts":30,
          "source_integration":evidence,
          "studio_two_client":"NOT_TESTED","mobile":"NOT_TESTED",
          "human_fun":"NO_GO_PENDING","rc_adopted":False,"published":False}
    (DEST/"SOURCE_LOCK.json").write_text(
       json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("H2_BEAST_FULL_ORIGINAL_H1_28_OF_28_SOURCE_BYTES_PRESERVED")
    print("H2_BEAST_REAL_COMPLETE_GAME_30_SOURCES_CREATED")
    return lock

def verify_xml(place:Path,receipt:Path):
    source=sorted((DEST/"src").rglob("*.luau"))
    assert len(source)==30,"SOURCE_30_MISSING"
    expected=collections.Counter(p.read_text(encoding="utf-8") for p in source)
    actual=collections.Counter()
    classes=collections.Counter()
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","LocalScript","ModuleScript"}:continue
        body=item.find("./Properties/string[@name='Source']")
        if body is not None:
            actual[body.text or ""]+=1
            classes[cls]+=1
    assert actual==expected,("REAL_ROJO_SOURCE_BYTES_NOT_30_OF_30",len(actual))
    assert classes=={"Script":3,"LocalScript":4,"ModuleScript":23},classes
    source_lock=json.loads((DEST/"SOURCE_LOCK.json").read_text())
    source_lock.update({"original_real_30_scripts_xml_byte_exact":True,
       "real_Rojo_Place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
       "real_Rojo_Place_bytes":place.stat().st_size,"classes":dict(classes)})
    receipt.write_text(json.dumps(source_lock,ensure_ascii=False,indent=2)+"\n")
    print("H2_BEAST_REAL_ROJO_FULL_30_OF_30_SOURCE_XML_EXACT_PASS")
    print("H2_BEAST_REAL_PRIVATE_PLACE_SHA256="+source_lock["real_Rojo_Place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true")
    p.add_argument("--check-input",action="store_true")
    p.add_argument("--verify-xml",type=Path)
    p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    if a.assemble:assemble()
    elif a.check_input:print(inputs())
    elif a.verify_xml:
        assert a.receipt
        verify_xml(a.verify_xml,a.receipt)
    else:p.error("choose --assemble or --check-input or --verify-xml")
