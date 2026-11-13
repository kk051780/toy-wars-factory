#!/usr/bin/env python3
"""Produce two complete ACTUAL H1 score-mode private Rojo builds, H0 OFF / H2 ON.

Uses entire frozen child-friendly H1 #270 (30 scripts), overlays SINGLE original
Game-server script via pinned anchor transform, reuses original native-verified
#273 score module as a ModuleScript, adds server-only trusted 5-egg adapter and
one READ-ONLY client HUD, total 33 executable Luau scripts (not 32).
Does NOT touch official RC, main, or another author's immutable original source.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from patch_game import inject,blob,SOURCE_SHA

REPO=Path(__file__).resolve().parents[3]
OWN=Path(__file__).resolve().parents[1]
BASE=REPO/"handoffs/P0D-H1-FAST-JOY-COMBINED-20261113-01"
OLD=BASE/"dist/TRAP_RAIDERS_H1_FAST_SEA_SKY_JOY_STUDIO_ONLY"
DIST=OWN/"dist"
MODES={"OFF":False,"ON":True}
INPUTS={
  "server/H2ScoreRules.luau":("inputs/H2ScoreRules.luau","ab35825cfcbf14315eecfae954318b4d92e0a592"),
  "server/H2ScoreIntegration.luau":("server/H2ScoreIntegration.luau","fbb58f9e4cc49fc520f5767b3796ee556b60864a"),
  "client/H2ScoreHUD.client.luau":("client/H2ScoreHUD.client.luau","f371e01965606d56383599f7434e9b428795a888"),
}
ORIGINAL_SHA={
  "server/Game.server.luau":"adecfee41a594bdd54393050b4890a5733a536ce",
  "client/HUD.client.luau":"313484a69eb10ce01bbdb4872afee215133b01d4",
  "server/MapBuilder.luau":"94655d019fdf9798fa24a350ebf49f8290465ac0",
  "server/H1FunWorld.server.luau":"7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea",
  "server/S1RaiderWindRules.luau":"7d5706774b874759e7ab994dc0654c3ae9a46502",
}
def scripts(place):
    return {p.relative_to(place/"src").as_posix():p.read_bytes()
       for p in (place/"src").rglob("*.luau")}
def guard(name,data,expected):
    got=blob(data)
    assert got==expected,("ACTUAL_AUTHOR_GITBLOB_CHANGED",name,got,expected)

def build():
    for name,(file,sha) in INPUTS.items():
        guard(name,(OWN/file).read_bytes(),sha)
    subprocess.run([sys.executable,str(BASE/"tools/assemble.py"),"--assemble"],
       cwd=REPO,timeout=90,check=True)
    original=scripts(OLD)
    assert len(original)==30,("MISSING_FULL_EXISTING_H1_30",len(original))
    for name,sha in ORIGINAL_SHA.items():guard(name,original[name],sha)
    assert original["server/Game.server.luau"] and len(original)>20
    artifacts={}
    for mode,enabled in MODES.items():
        dst=DIST/("TRAP_RAIDERS_H2_MULTI_EGG_"+mode+"_PRIVATE_STUDIO")
        if dst.exists():shutil.rmtree(dst)
        shutil.copytree(OLD,dst)
        patched=inject(original["server/Game.server.luau"],enabled)
        (dst/"src/server/Game.server.luau").write_bytes(patched)
        for name,(src,_) in INPUTS.items():
            p=dst/"src"/name
            p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(OWN/src,p)
        src=scripts(dst)
        assert len(src)==33,("H1_PLUS3_SHOULD_BE33",len(src))
        assert all(src[k]==v for k,v in original.items() if k!="server/Game.server.luau"),"ORIGINAL_GAME_SIDE_EFFECT"
        assert set(src)-set(original)==set(INPUTS),"EXTRA_SERVER_OR_CLIENT_SCRIPT"
        assert len([p for p in src if p=="server/Game.server.luau"])==1
        assert src["server/Game.server.luau"].count(b'remote.Name = "TrapRaidersS1Remote"')==1
        assert src["server/Game.server.luau"].count(b'Instance.new("RemoteEvent")')==1
        assert src["server/Game.server.luau"].count(b'if h2Mode then return end')==2
        assert b'local H2_SCORE_MODE = game:GetService("RunService"):IsStudio() and '+(
           b'true' if enabled else b'false') in src["server/Game.server.luau"]
        assert all(b'Instance.new("RemoteEvent")' not in src[p] for p in INPUTS)
        assert b'local H2ScoreIntegration = if H2_SCORE_MODE then require' in patched
        data=json.loads((dst/"default.project.json").read_text())
        data["name"]="TRAP_RAIDERS_H2_FIVE_EGGS_"+mode+"_OWNER_PRIVATE_DO_NOT_PUBLISH"
        clients=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        assert "H2ScoreHUD" not in clients
        clients["H2ScoreHUD"]={"$path":"src/client/H2ScoreHUD.client.luau"}
        (dst/"default.project.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
        artifacts[mode]=src
        report={
            "adoption_id":"P0D-STUDIO-RULE-MULTI-EGG-SCORE-001",
            "scope":"PRIVATE_ONE_EXISTING_H1_GAME_MODE_INTEGRATION",
            "mode":mode,"mode_active_only_if_studio":True,
            "original_full_H1_30_sha":"1f63a529dc512487145cea86557d38cec7f19e03",
            "original_H1_base_scripts":30,
            "original_other_29_scripts_byte_exact":True,
            "only_original_game_source_changed":True,
            "original_server_remote_count":1,
            "new_score_rule_adapter_and_read_only_client":list(INPUTS),
            "score_engine_original_sha":"ab35825cfcbf14315eecfae954318b4d92e0a592",
            "Luau_sources":33,
            "Game_source_sha256":hashlib.sha256(src["server/Game.server.luau"]).hexdigest(),
            "real_studio_2_clients":"NOT_TESTED",
            "android_mobile":"NOT_TESTED",
            "real_multiplayer_physics":"NOT_TESTED",
            "human_fun":"NOT_TESTED",
            "official_RC_adopted":False,"published":False}
        (dst/"SOURCE_LOCK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        print("P0D_H2_FULL_H1_SCORE_MODE_"+mode+"_33_SCRIPTS_BUILT")
    off=artifacts["OFF"]["server/Game.server.luau"].decode()
    on=artifacts["ON"]["server/Game.server.luau"].decode()
    prefix='local H2_SCORE_MODE = game:GetService("RunService"):IsStudio() and '
    assert off.replace(prefix+'false',prefix+'true',1)==on,("H0_H2_GAME_SOURCE_MODE_DIFF_NOT_ONE_BOOLEAN")
    for key in artifacts["OFF"]:
        if key!="server/Game.server.luau":
            assert artifacts["OFF"][key]==artifacts["ON"][key],("MODE_CHANGED_OTHER_GAME_SCRIPT",key)
    print("P0D_H2_FULL_H1_OFF_ON_DIFF_ONLY_ONE_SERVER_MODE_FLAG_PASS")
    return True

def verify_xml(place,receipt,mode):
    dst=DIST/("TRAP_RAIDERS_H2_MULTI_EGG_"+mode+"_PRIVATE_STUDIO")
    source=scripts(dst)
    assert len(source)==33
    expected=collections.Counter(p.decode("utf-8") for p in source.values())
    actual=collections.Counter()
    classes=collections.Counter()
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        sourceItem=item.find("./Properties/string[@name='Source']")
        if sourceItem is not None:
            actual[sourceItem.text or ""]+=1
            classes[cls]+=1
    assert expected==actual,("REAL_SCORE_MODE_ROJO_XML_SOURCE_MISMATCH",len(expected),len(actual))
    assert classes=={"Script":2,"ModuleScript":25,"LocalScript":6},classes
    data=json.loads((dst/"SOURCE_LOCK.json").read_text())
    data.update({"rojo_file_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
            "rojo_file_bytes":place.stat().st_size,"actual_rojo_xml_33_of_33_source_exact":True,
            "actual_script_classes":dict(classes)})
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("P0D_H2_FULL_H1_"+mode+"_ACTUAL_ROJO_SOURCE_33_OF_33_EXACT_PASS")
    print("P0D_H2_FULL_H1_"+mode+"_ROJO_SHA256="+data["rojo_file_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true")
    p.add_argument("--verify-xml",type=Path)
    p.add_argument("--mode",choices=("OFF","ON"))
    p.add_argument("--receipt",type=Path)
    args=p.parse_args()
    if args.assemble:build()
    elif args.verify_xml and args.mode and args.receipt:
        verify_xml(args.verify_xml,args.receipt,args.mode)
    else:p.error("--assemble or --verify-xml --mode OFF|ON --receipt file")
