#!/usr/bin/env python3
"""Source-selective 4-author COMBAT union, one original Game; private only."""
import argparse
import hashlib
import importlib.util
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
ORIGINAL_COMBAT = ROOT / "EGGRUMBLE_SevenRoleCombat.luau"
PROJECT = ROOT / "EGGRUMBLE_V3_STUDIO.project.json"
PINNED_HEADS = {
    "_gq_mage": "0338bd13f9d3d199972bd4cd30e467443083dffa",
    "_gq_dot": "8f0275692c54874f823d66748d470fb849607df5",
    "_gq_warp": "f90875e14446ba86b1c668ba43efa37fbc74be20",
}
PINNED_BLOBS = {
    "_gq_mage/quality_gameplay/v3_mage_heal_los_20261116/build_candidate.py": "86d757b83057bc370ce8b51c459420af462e86eb",
    "_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/tools/compose_with_mage_author.py": "13604c5f2cd67fe06e79322ee5ff359cd4469c1b",
    "_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_SevenRoleCombat.patched.luau": "34e6ec6e314eb36de657bd89a48bc1d07d74dcca",
    "_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_StatusTickFence.luau": "40bb3bc47c07fe27f82a28c97f82529d10788a8a",
    "_gq_warp/quality_gameplay/v3_safe_warp_landing_20261116/patch_safe_warp.py": "f608fd7748186f07307d0b0264f1d3c873dd4344",
}
DOT_FILE = Path("_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_StatusTickFence.luau")
STATUS_IMPORT = 'local StatusTickFence=require(script.Parent:WaitForChild("EGGRUMBLE_StatusTickFence"))'

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def load(path: str, ident: str):
    spec = importlib.util.spec_from_file_location(ident, str(Path(path).resolve(strict=True)))
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def sha_guard():
    for path, want in PINNED_BLOBS.items():
        got = git_blob(Path(path).read_bytes())
        assert got == want, ("RED author file changed", path, want, got)
    source = ORIGINAL_COMBAT.read_bytes()
    assert git_blob(source) == "66e666418b7c23d41f87faa5d61eb6e2770a463e"
    for root in PINNED_HEADS:
        assert (Path(root)/ORIGINAL_COMBAT).read_bytes() == source, ("RED different author original", root)
    return source

def build_union():
    raw = sha_guard()
    origin=raw.decode("utf-8")
    magepath=Path("_gq_mage/quality_gameplay/v3_mage_heal_los_20261116/build_candidate.py")
    statuspath="_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/tools/compose_with_mage_author.py"
    warpfile="_gq_warp/quality_gameplay/v3_safe_warp_landing_20261116/patch_safe_warp.py"
    ownfile="quality_gameplay/v3_human_stealth_pvp_20261116/build_candidate.py"
    mage=load(str(magepath),"actual_mage_author")
    status=load(statuspath,"actual_dot_author")
    warp=load(warpfile,"actual_warp_author")
    own=load(ownfile,"actual_human_pvp_author")
    assert mage.SOURCE_BLOB == own.SOURCE_BLOB == warp.EXPECTED_GIT_BLOB
    assert status.ORIG_GIT_BLOB==own.SOURCE_BLOB

    # Existing status author's proven SAME-source composer is the ONLY mage+DOT composition.
    both=status.compose(magepath)
    assert both.count(STATUS_IMPORT)==1
    assert both.count("StatusTickFence.canTick(")==1

    # Warp author patch() must first prove the ORIGINAL source, not trust a fuzzy diff.
    warp_orig=warp.patch(raw).decode("utf-8")
    warp_expected=origin.replace(warp.OLD,warp.NEW,1)
    warp_expected=warp_expected.replace(warp.OLD_NINJA,warp.NEW_NINJA,1)
    warp_expected=warp_expected.replace(warp.OLD_ESPER,warp.NEW_ESPER,1)
    assert warp_orig==warp_expected, "RED warp-only author drift"
    for before in (warp.OLD,warp.OLD_NINJA,warp.OLD_ESPER):
        assert both.count(before)==1, ("RED incompatible warp anchor",before[:60])
    with_warp=both.replace(warp.OLD,warp.NEW,1)
    with_warp=with_warp.replace(warp.OLD_NINJA,warp.NEW_NINJA,1)
    with_warp=with_warp.replace(warp.OLD_ESPER,warp.NEW_ESPER,1)

    # Our human PvP patch intentionally only touches direct-hit and debuff target loops.
    four=own.patch(with_warp)
    assert four.count("humanCombatTargetable(")==3
    assert four.count("StatusTickFence.canTick(")==1
    assert four.count(STATUS_IMPORT)==1
    assert four.count("local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean")==1
    assert four.count("botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)")==1
    assert four.count("local function hitHumanHeroes(")==1
    assert four.count("local function secondaryEffect(")==1
    assert four.count("function HeroCombat.equip(")==1
    assert four.count("function HeroCombat.clear(")==1
    assert len(four)>len(origin) and four!=own.patch(origin)

    # Strict round-trip to the exact #510+#516 author union when unique hooks removed.
    without_own = four.replace(own.HELPER,"",1).replace(own.HIT_NEW,own.HIT_OLD,1)
    without_own = without_own.replace(own.STATUS_NEW,own.STATUS_OLD,1)
    assert without_own==with_warp, "RED own patch changed other authors"
    without_warp = without_own.replace(warp.NEW,warp.OLD,1)
    without_warp = without_warp.replace(warp.NEW_NINJA,warp.OLD_NINJA,1)
    without_warp = without_warp.replace(warp.NEW_ESPER,warp.OLD_ESPER,1)
    assert without_warp==both, "RED warp patch changed other authors"
    return four,{"original_482":own.SOURCE_BLOB,
                 "mage_510":PINNED_HEADS["_gq_mage"],
                 "status_516":PINNED_HEADS["_gq_dot"],
                 "warp_524":PINNED_HEADS["_gq_warp"],
                 "human_pvp_529":"SAME_BRANCH_EXACT_HEAD_FROM_ACTIONS",
                 "combat_four_author_sha256":hashlib.sha256(four.encode()).hexdigest()}

def scripts(source_json: dict, basedir: Path):
    out={}
    def walk(obj):
        for name,v in obj.items():
            if name.startswith("$") or not isinstance(v,dict):continue
            if "$path" in v:
                assert name not in out,("duplicate script",name)
                file=(basedir/v["$path"]).resolve(strict=True)
                kind=("LocalScript" if file.name.endswith(".client.luau")
                      else "Script" if file.name.endswith(".server.luau")
                      else "ModuleScript")
                out[name]=(kind,file)
            else:walk(v)
    walk(source_json["tree"])
    return out

def compose_private(combat:Path,project_out:Path,receipt:Path,heads:dict):
    original_project=PROJECT.resolve(strict=True)
    original_json=json.loads(original_project.read_text(encoding="utf-8"))
    originals=scripts(original_json,original_project.parent)
    assert len(originals)==21
    target=json.loads(json.dumps(original_json))
    target["name"]="EGGRUMBLE_GQ_4_AUTHOR_COMBAT_PRIVATE22_NOT_RC"
    project_out=project_out.resolve()
    project_out.parent.mkdir(parents=True,exist_ok=True)
    combat=combat.resolve(strict=True)
    def rewrite(obj):
        for name,v in obj.items():
            if name.startswith("$") or not isinstance(v,dict):continue
            if "$path" in v:
                selected=combat if name=="EGGRUMBLE_SevenRoleCombat" else originals[name][1]
                v["$path"]=os.path.relpath(selected,project_out.parent).replace(os.sep,"/")
            else:rewrite(v)
    rewrite(target["tree"])
    server=target["tree"]["ServerScriptService"]
    assert "EGGRUMBLE_StatusTickFence" not in server
    server["EGGRUMBLE_StatusTickFence"]={
        "$path":os.path.relpath(DOT_FILE.resolve(strict=True),project_out.parent).replace(os.sep,"/")
    }
    observed=scripts(target,project_out.parent)
    assert len(observed)==22
    assert set(observed)==set(originals)|{"EGGRUMBLE_StatusTickFence"}
    for name,(_,path) in originals.items():
        expected=combat if name=="EGGRUMBLE_SevenRoleCombat" else path
        assert observed[name][1]==expected,("RED source unexpectedly replaced",name)
    project_out.write_text(json.dumps(target,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report={**heads,"status":"PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC",
            "original_count":21,"private_source_count":22,
            "original_modules_byte_identical":20,"combat_source_overlays":1,
            "new_modules":["EGGRUMBLE_StatusTickFence"],
            "official_adopted":False,
            "source_sha256":{name:hashlib.sha256(src.read_bytes()).hexdigest() for name,(_,src) in observed.items()},
            "rollback":"omit optional helper/status module; use #482 original 21 source scripts"}
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_FOUR_AUTHOR_22_SOURCE_PRIVATE_MAP_PASS")

def verify_place(project:Path,place:Path,receipt:Path):
    project=project.resolve(strict=True)
    expected=scripts(json.loads(project.read_text(encoding="utf-8")),project.parent)
    receipt_json=json.loads(receipt.read_text(encoding="utf-8"))
    actual={}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        kind=node.attrib.get("class")
        if kind not in ("LocalScript","ModuleScript","Script"):continue
        props=node.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        assert name not in actual,("duplicate",name)
        body=props.findtext("ProtectedString[@name='Source']")
        if body is None:body=props.findtext("string[@name='Source']")
        assert body is not None,name
        actual[name]=(kind,body.replace("\r\n","\n"))
    assert set(actual)==set(expected),("missing/extra",sorted(set(expected)-set(actual)),sorted(set(actual)-set(expected)))
    for name,(kind,source) in expected.items():
        assert actual[name][0]==kind,name
        assert actual[name][1]==source.read_text(encoding="utf-8").replace("\r\n","\n"),name
        assert hashlib.sha256(source.read_bytes()).hexdigest()==receipt_json["source_sha256"][name],name
    assert len(actual)==22
    receipt_json["private_place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    receipt_json["place_size_bytes"]=place.stat().st_size
    receipt_json["rojo_exact_22_of_22"]=True
    receipt.write_text(json.dumps(receipt_json,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_FOUR_AUTHOR_22_ROJO_SOURCE_CLASS_EXACT_PASS",place.stat().st_size)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--combat",type=Path)
    parser.add_argument("--project",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--verify-place",type=Path)
    args=parser.parse_args()
    if args.verify_place:verify_place(args.project,args.verify_place,args.receipt)
    else:
        assert args.combat
        merged,heads=build_union()
        args.combat.parent.mkdir(parents=True,exist_ok=True)
        args.combat.write_text(merged,encoding="utf-8")
        compose_private(args.combat,args.project,args.receipt,heads)
        print("GQ_FOUR_AUTHOR_REAL_SINGLE_COMBAT_SOURCE_UNION_PASS",heads["combat_four_author_sha256"])

if __name__=="__main__":main()
