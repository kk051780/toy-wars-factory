#!/usr/bin/env python3
"""Rebuild ORIGINAL RC57 -> isolated 58 source Egg Relay (classic + H2).
Read-only on the sole official RC; never publishes or writes main/RC.
No fake claim of native Luau, Rojo or Studio execution.
"""
from pathlib import Path
import argparse, hashlib, subprocess, tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PATCH_GAME = ROOT / "rc54_candidate" / "Game.patch"
PATCH_H2 = ROOT / "h2_complement" / "H2OnlyRelayV2.patch"
POLICY = ROOT / "src" / "EggRelayPolicy.luau"
EXPECTED_PLACE_SHA256 = "15521b7dadbd96c0ef1ed12367b5fcf2f3738c4428ebf2fb8c43532b39b8b1a8"
EXPECTED_GAME_BLOB = "9edc39a681eeefb6ec4178b8bbeabf744cac567b"
EXPECTED_H2_BLOB = "0999d69391c176b9b95b04c5444d822e63d7ce04"
LOCKED = {
    "Game.patch": "a20a1f2599af5ec9f62c5b05206b89886341906b",
    "H2OnlyRelayV2.patch": "68f3df613ad548ab56e755adf91d797a979e8552",
    "EggRelayPolicy.luau": "ef9b65bd6520231f299f21c5cfe2aa250798c8d0",
}
EXPECTED_GAME_SHA256 = "9dd0c163b86b6a9a5c9affa5920bf4489ff7e528a83130621d508cdad26d797d"
EXPECTED_H2_SHA256 = "89e2f07e0000bb6338e44ad41ee812b054226718161136443e64382028558b00"
EXPECTED_OUTPUT_SHA256 = "ab502740b40a2e62344304461d26d89a91a8bc7ec657091ecc5cf7a9b2bfc5d3"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def prop(item, name):
    return item.find("./Properties/string[@name='%s']" % name)

def scan(root):
    scripts = {}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):
            continue
        n,s = prop(item,"Name"),prop(item,"Source")
        if n is None or s is None:
            continue
        assert n.text not in scripts, ("DUPLICATE_SCRIPT",n.text)
        scripts[n.text] = (item,s.text or "")
    return scripts

def apply_patch(dir_path, path):
    for opts in (["--dry-run"], []):
        r = subprocess.run([
            "patch","-p1","--fuzz=0","--batch","--forward","--reject-file=-",
            "-d",str(dir_path),"-i",str(path),*opts
        ], capture_output=True,text=True)
        assert r.returncode == 0, ("EXACT_PATCH_FAILED",path.name,opts,r.stdout,r.stderr)

def replace_once(s, before, after):
    assert s.count(before)==1, ("ANCHOR_NOT_UNIQUE",before)
    return s.replace(before, after, 1)

def rebuild(input_place, out):
    input_bytes = input_place.read_bytes()
    assert sha(input_bytes) == EXPECTED_PLACE_SHA256, "WRONG_REAL_RC57_PLACE"
    assert blob(PATCH_GAME.read_bytes()) == LOCKED["Game.patch"]
    assert blob(PATCH_H2.read_bytes()) == LOCKED["H2OnlyRelayV2.patch"]
    assert blob(POLICY.read_bytes()) == LOCKED["EggRelayPolicy.luau"]
    root = ET.fromstring(input_bytes)
    before = scan(root)
    assert len(before)==57 and "EggRelayPolicy" not in before, "WRONG_BASE_INVENTORY"
    assert before["Game"][0].get("class")=="Script"
    assert before["H2FiveEggRules"][0].get("class")=="ModuleScript"
    assert blob(before["Game"][1].encode("utf8"))==EXPECTED_GAME_BLOB
    assert blob(before["H2FiveEggRules"][1].encode("utf8"))==EXPECTED_H2_BLOB
    with tempfile.TemporaryDirectory() as scratch:
        d=Path(scratch)
        (d/"Game.luau").write_text(before["Game"][1],encoding="utf8")
        (d/"H2FiveEggRules.luau").write_text(before["H2FiveEggRules"][1],encoding="utf8")
        apply_patch(d,PATCH_GAME)
        apply_patch(d,PATCH_H2)
        game=(d/"Game.luau").read_text(encoding="utf8")
        h2=(d/"H2FiveEggRules.luau").read_text(encoding="utf8")
    game=replace_once(game,
        "H2Score.relay(h2ScoreState,fromId,toId,team)",
        "H2Score.relayWithVersion(h2ScoreState,eggId,actualVersion,fromId,toId,team)")
    game=replace_once(game,
        'ServerStorage:GetAttribute("P0D_RC_ENABLE_EGG_RELAY") == false',
        'ServerStorage:GetAttribute("P0D_RC_ENABLE_EGG_RELAY") ~= true')
    game=replace_once(game,
        'ServerStorage:GetAttribute("P0D_RC_ENABLE_EGG_RELAY")==false',
        'ServerStorage:GetAttribute("P0D_RC_ENABLE_EGG_RELAY")~=true')
    assert sha(game.encode("utf8"))==EXPECTED_GAME_SHA256, "NEW_GAME_SOURCE_DRIFT"
    assert sha(h2.encode("utf8"))==EXPECTED_H2_SHA256, "H2_SOURCE_DRIFT"
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    for marker in ("SavedPveMasteryPolicy","SavedBeastEvolutionPolicy","ScoutSpeciesPolicy",
                   "H2Score.relayWithVersion(", 'P0D_RC_ENABLE_EGG_RELAY'):
        assert marker in game, ("MISSING_ACCEPTED_GAME_FEATURE",marker)
    for key, src in (("Game",game),("H2FiveEggRules",h2)):
        prop(before[key][0],"Source").text=src
    parents = {child:parent for parent in root.iter() for child in parent}
    holder = parents[before["Game"][0]]
    item=ET.SubElement(holder,"Item",{
        "class":"ModuleScript","referent":"P0D_EGG_RELAY_UNIFIED_RC57_ISOLATED"
    })
    properties=ET.SubElement(item,"Properties")
    ET.SubElement(properties,"string",{"name":"Name"}).text="EggRelayPolicy"
    ET.SubElement(properties,"string",{"name":"Source"}).text=POLICY.read_text("utf8")
    out.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(out,encoding="utf8",xml_declaration=True)
    after=scan(ET.parse(out).getroot())
    assert len(after)==58 and set(after)==set(before)|{"EggRelayPolicy"}
    changed=sorted(k for k in before if after[k][1]!=before[k][1])
    assert changed==["Game","H2FiveEggRules"], changed
    assert sum(before[k][1]==after[k][1] for k in before)==55
    for unchanged in ("PersistentHatchStore","SavedPveMasteryPolicy",
                      "SavedBeastEvolutionPolicy","ScoutSpeciesPolicy"):
        assert after[unchanged][1]==before[unchanged][1], unchanged
    assert sha(out.read_bytes())==EXPECTED_OUTPUT_SHA256, "REPRODUCIBILITY_FAIL"
    print("P0D_RC57_TO_RC58_EGG_RELAY_SOURCE_ONLY_REBUILD_PASS", EXPECTED_OUTPUT_SHA256)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-place",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    opts=parser.parse_args()
    rebuild(opts.original_place,opts.output)
