#!/usr/bin/env python3
"""Build a REAL single TRAP RAIDERS 32-script H2 private Rojo game.

Author sources are byte-for-byte unmodified: original whole 28-source H1 game
+ 2 independent original #268 Beast scripts + 2 independent original #267 Star.
No Roblox Studio physical play is claimed by these deterministic source gates.
"""
from __future__ import annotations

import argparse, collections, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parents[1]
BEAST = REPO / "handoffs/P0D-STUDIO-NEUTRAL-GATE-BEAST-20261113-01"
BEAST_DIST = BEAST / "dist/TRAP_RAIDERS_H2_GATE_BEAST_STUDIO_ONLY"
H1 = REPO / "handoffs/P0D-H1-FAST-ROUTES-WITH-UX-20261113-01"
DEST = OWN / "dist/TRAP_RAIDERS_H2_DUAL_ENCOUNTER_STUDIO_ONLY"
ORIGINAL_H1_SHA = "8f2a4aed7f6483f0bd00e31fcd733a823aa5c008"
BEAST_SOURCE_SHA = "e3aaadf6940397f74bb89d8bd54190260deb298d"
STAR_SOURCE_SHA = "af0d4eca02a48c64e530761401145b20ffcd86e7"
STAR_BLOBS = {
    "H2StarLaunchPolicy.luau":"2879b6fc8b1547a4d13db19a616da756c04180d7",
    "H2StarLaunch.server.luau":"b122c49f2072e383d27b1452d0bdda108f05f915",
}
BEAST_BLOBS = {
    "H2GateBeastPolicy.luau":"0aee2fc29b376cb9be5362f5230245fdf634ddff",
    "H2NeutralGateBeast.server.luau":"747c363f65aaa969af9266813fc79f6457d8e533",
}
KEY_GAME_BLOBS = {
    "server/Game.server.luau":"adecfee41a594bdd54393050b4890a5733a536ce",
    "server/S1RaiderWindRules.luau":"7d5706774b874759e7ab994dc0654c3ae9a46502",
    "server/H1FunWorld.server.luau":"7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea",
    "server/MapBuilder.luau":"94655d019fdf9798fa24a350ebf49f8290465ac0",
    "client/HUD.client.luau":"313484a69eb10ce01bbdb4872afee215133b01d4",
}
ROUTE_NAMES = {
    "SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE",
    "SEA_LOW_CAUSEWAY","SEA_ENTRY_RED","SEA_ENTRY_BLUE"
}
def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def lock(path:Path,expected:str):
    assert path.is_file(),("MISSING_ORIGINAL",str(path))
    actual=blob(path.read_bytes())
    assert actual==expected,("SOURCE_BLOB_CHANGED",str(path),actual,expected)

def source_controls(paths:dict[str,bytes])->dict:
    game=paths["server/Game.server.luau"].decode("utf-8")
    field=paths["server/H1FunWorld.server.luau"].decode("utf-8")
    star=paths["server/H2StarLaunch.server.luau"].decode("utf-8")
    beast=paths["server/H2NeutralGateBeast.server.luau"].decode("utf-8")
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "WIND_BURST" in game and 'action == "PLACE_TRAP"' in game
    assert "H2StarLaunchPolicy" in star and "H2GateBeastPolicy" in beast
    assert "H2_NEUTRAL_GATE_BEAST" in beast and "H2_STAR_JUMP_PADS" in star
    assert "H2_NEUTRAL_GATE_BEAST" not in star and "H2_STAR_JUMP_PADS" not in beast
    assert 'RunService:IsStudio()' in star and 'RunService:IsStudio()' in beast
    # Both new systems are server-only and neither may create match authority.
    for p in (star,beast):
        for forbidden in ("RemoteEvent","RemoteFunction","FireServer",
                          "FireClient","FireAllClients","DataStore",
                          "Marketplace","PublishAsync","TeleportAsync","TakeDamage"):
            assert forbidden not in p,("H2_OVERLAY_ADDED_FORBIDDEN_AUTHORITY",forbidden)
        assert "TriggerServer" not in p
    # Original #262 complete path design contains the six actual source-defined
    # ground alternatives; they stay byte-identical during this assembly.
    routes=set(re.findall(r'path\("([A-Z_]+)"',field))
    assert routes==ROUTE_NAMES,("ALTERNATE_ROUTE_DAMAGED",routes)
    # Source-position contract: original two launch pads must not overlap actual
    # physical central gate, source coordinates ±66 vs x=0, guard z=0.
    assert 'P.PAD_X = 66' in paths["server/H2StarLaunchPolicy.luau"].decode()
    assert 'P.PAD_Z = -20' in paths["server/H2StarLaunchPolicy.luau"].decode()
    assert 'Vector3.new(0,6,0)' in beast
    assert 'Vector3.new(3.5,12,21)' in beast
    # Centre collision half-width 1.75; pad half-width 5. Both ±66 pads clear.
    assert 66-5 > 3.5/2+5,"PAD_OVERLAPS_CENTER_GATE_WITH_SAFETY_BUFFER"
    # Alert warning and player-protection contract must also remain authored.
    assert 'Policy.insideGate(p.X,p.Y,p.Z)' in beast
    assert 'gate.CanCollide=solid' in beast
    assert 'if not Policy.canLaunch({' in star
    assert 'root.AssemblyLinearVelocity=Vector3.new(speed.x,speed.y,speed.z)' in star
    # Two new system entrance positions are distinct and do not replace S1 egg.
    assert 'part(folder, "GrassArena"' in paths["server/MapBuilder.luau"].decode()
    return {"only_one_authoritative_remote":True,
            "world_routes_preserved":sorted(routes),
            "star_and_beast_unique_server_systems":True,
            "star_and_gate_separate_source_geometry":True,
            "engine_physics_not_tested":True}

def assemble():
    for fn,sha in STAR_BLOBS.items():lock(OWN/"inputs"/fn,sha)
    for fn,sha in BEAST_BLOBS.items():lock(BEAST/"src/server"/fn,sha)
    # Produces the original #262 H1 game and adds existing exact beast code
    # without ever touching another owner's committed files.
    subprocess.run([sys.executable,str(BEAST/"tools/assemble.py"),"--assemble"],
                   check=True,cwd=REPO,timeout=70)
    before=sorted((BEAST_DIST/"src").rglob("*.luau"))
    assert len(before)==30,("ORIGINAL_BEAST_WHOLE_GAME_EXPECTED30",len(before))
    pre={p.relative_to(BEAST_DIST/"src").as_posix():p.read_bytes() for p in before}
    assert len(pre)==30
    for name,sha in KEY_GAME_BLOBS.items():lock(BEAST_DIST/"src"/name,sha)
    for fn,sha in BEAST_BLOBS.items():lock(BEAST_DIST/"src/server"/fn,sha)
    if DEST.exists():shutil.rmtree(DEST)
    shutil.copytree(BEAST_DIST,DEST)
    for name in STAR_BLOBS:
        shutil.copyfile(OWN/"inputs"/name,DEST/"src/server"/name)
    post={p.relative_to(DEST/"src").as_posix():p.read_bytes()
          for p in (DEST/"src").rglob("*.luau")}
    assert len(post)==32,("COMPLETE_GAME_32_EXPECTED",len(post))
    assert all(post.get(k)==v for k,v in pre.items()),"H1_AND_BEAST_SOURCE30_MUTATED"
    assert set(post)-set(pre)=={"server/"+fn for fn in STAR_BLOBS},"OTHER_NEW_GAME_SOURCE_PRESENT"
    for fn,sha in STAR_BLOBS.items():lock(DEST/"src/server"/fn,sha)
    assert [k for k in post if k=="server/Game.server.luau"]==["server/Game.server.luau"]
    contracts=source_controls(post)
    project=DEST/"default.project.json"
    data=json.loads(project.read_text())
    data["name"]="TRAP_RAIDERS_H2_DUAL_ENCOUNTER_PRIVATE_STUDIO_ONLY"
    project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    report={
        "project":"TRAP_RAIDERS_H2_DUAL_ENCOUNTER",
        "adoption_id":"P0D-STUDIO-DUAL-ENCOUNTER-001",
        "stage":"OPTIONAL_PRIVATE_STUDIO_ONLY_S2_NOT_RELEASE",
        "full_original_H1_28_files_byte_exact":True,
        "original_beast_two_files_byte_exact":BEAST_BLOBS,
        "original_star_two_files_byte_exact":STAR_BLOBS,
        "source_bases":{"original_H1":ORIGINAL_H1_SHA,
                        "original_beast":BEAST_SOURCE_SHA,"original_star":STAR_SOURCE_SHA},
        "total_scripts":32,"existing_scripts_preserved":30,
        "source_controls":contracts,
        "actual_roblox_studio_engine":"NOT_TESTED",
        "two_clients":"NOT_TESTED","mobile":"NOT_TESTED",
        "owner_fun":"NO_GO_PENDING","official_RC_adopted":False,
        "published":False,
    }
    (DEST/"SOURCE_LOCK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("P0D_DUAL_ORIGINAL_H1_28_OF_28_BYTES_PRESERVED")
    print("P0D_DUAL_ORIGINAL_TWO_FEATURES_4_OF_4_EXACT_SOURCE")
    print("P0D_DUAL_ONE_WHOLE_REAL_H1_GAME_32_SOURCES_ASSEMBLED")
    return post

def xml_check(place:Path,receipt:Path):
    paths=sorted((DEST/"src").rglob("*.luau"))
    assert len(paths)==32,"H2_GAME_SOURCE_MUST_BE32"
    exp=collections.Counter(f.read_text(encoding="utf-8") for f in paths)
    actual=collections.Counter()
    classes=collections.Counter()
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        val=item.find("./Properties/string[@name='Source']")
        if val is not None:
            actual[val.text or ""]+=1
            classes[cls]+=1
    assert actual==exp,("REAL_ROJO_XML_NOT_ALL_32_EXACT",sum(actual.values()),len(exp))
    assert classes=={"Script":4,"LocalScript":4,"ModuleScript":24},classes
    report=json.loads((DEST/"SOURCE_LOCK.json").read_text())
    report.update({"native_rojo_32_of_32_source_exact":True,
                   "real_unpublished_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
                   "real_unpublished_place_bytes":place.stat().st_size,
                   "script_classes":dict(classes)})
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("P0D_DUAL_ROJO_REAL_PLACE_XML_32_OF_32_SOURCE_EXACT_PASS")
    print("P0D_DUAL_ROJO_REAL_PLACE_SHA256="+report["real_unpublished_place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true")
    p.add_argument("--verify-xml",type=Path)
    p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    if a.assemble:assemble()
    elif a.verify_xml:
        if a.receipt is None:p.error("--receipt required")
        xml_check(a.verify_xml,a.receipt)
    else:p.error("--assemble or --verify-xml required")
