#!/usr/bin/env python3
"""Fail-closed proof: optional32 = exact current GQ81 31 scripts + pinned spectator only.
Source/Place check, not Roblox Studio or child-FUN certification.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, xml.etree.ElementTree as ET
from pathlib import Path

EXTRA="EGGRUMBLE_EliminatedSpectate"
TARGET="EGGRUMBLE_CombatFeel"
MARKERS=('hitToast.Name="ConfirmedHit042"','task.delay(.42,function()')
IMPACT_LISTENER='player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")'
AUDIO_BEGIN="GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117"
AUDIO_END="GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117"
AUDIO_LISTENER='local onHit=player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)'
def require(ok,msg):
    if not ok:raise ValueError("RED_GQ470_HIT042_INHERIT_"+msg)
def certify(base,optional):
    require(len(base)==31 and len(optional)==32,"SOURCE_COUNTS")
    require(set(optional)==set(base)|{EXTRA},"SPECTATOR_ONLY_EXTRA")
    for name,(source,clazz) in base.items():
        require(name in optional,"SOURCE_MISSING_"+name)
        actual,actual_clazz=optional[name]
        require(actual==source and actual_clazz==clazz,"SOURCE_OR_CLASS_DRIFT_"+name)
    source,clazz=optional[TARGET]
    require(clazz=="LocalScript","COMBATFEEL_WRONG_CLASS")
    content=source.decode("utf-8")
    for marker in MARKERS:
        require(content.count(marker)==1,"MISSING_CURRENT_HIT042_"+marker[:18])
    # Existing HIT042 already listens for confirmed impact. Original #504 audio
    # intentionally adds one *additional* client listener, not a second writer.
    audio=AUDIO_BEGIN in content or AUDIO_END in content
    require(content.count(IMPACT_LISTENER)==(2 if audio else 1),"HIT_AND_AUDIO_LISTENER_COUNT")
    if audio:
        require(content.count(AUDIO_BEGIN)==1 and content.count(AUDIO_END)==1,
                "AUDIO_AUTHOR_BLOCK_BRACKETS")
        require(content.count(AUDIO_LISTENER)==1,"AUDIO_EXACT_CONFIRMED_LISTENER")
        require(content.count('local GROUP="EGGRUMBLE_GQ_ConfirmedHitAudio"')==1,
                "AUDIO_DUPLICATE_SOUND_GROUP")
    require('task.delay(.17,function()' in content,"OLD_RETICLE_LOST")
    require(optional[EXTRA][1]=="LocalScript","SPECTATE_CLASS")
    return {"existing_source_and_class_byte_exact":"31/31",
            "optional_script_count":32,"new_script":EXTRA,
            "current_hit042_present_in_optional":True}
def source_map(path,selector):
    spec=importlib.util.spec_from_file_location("pinned_spectate634",str(selector))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    doc=json.loads(path.read_text(encoding="utf-8"))
    found=mod.source_map(doc,path)
    return {name:(file.read_bytes(),clazz) for name,(file,clazz) in found.items()}
def prove_place(place,source):
    found=[]
    for item in ET.parse(place).getroot().iter("Item"):
        clazz=item.get("class")
        if clazz not in ("Script","LocalScript","ModuleScript"):continue
        p=item.find("Properties")
        require(p is not None,"NO_PROPERTIES")
        name=p.findtext("string[@name='Name']")
        code=p.findtext("ProtectedString[@name='Source']")
        if code is None:code=p.findtext("string[@name='Source']")
        require(name is not None and code is not None,"PLACE_SCRIPT_SOURCE")
        found.append((name,clazz,code.replace("\r\n","\n")))
    require(len(found)==32 and len({n for n,_,_ in found})==32,"PLACE_COUNT")
    hit=[(clazz,content) for n,clazz,content in found if n==TARGET]
    require(len(hit)==1 and hit[0][0]=="LocalScript","PLACE_HIT_SOURCE_CLASS")
    require(hit[0][1]==source.decode("utf-8").replace("\r\n","\n"),
            "PLACE_HIT_NOT_CURRENT")
def main():
    p=argparse.ArgumentParser()
    for n in ("base","optional","place","selector","out"):
        p.add_argument("--"+n,required=True,type=Path)
    a=p.parse_args()
    baseline=source_map(a.base,a.selector)
    current=source_map(a.optional,a.selector)
    receipt=certify(baseline,current)
    prove_place(a.place,current[TARGET][0])
    receipt.update({"place_bytes":a.place.stat().st_size,
                    "place_sha256":hashlib.sha256(a.place.read_bytes()).hexdigest(),
                    "new_runtime_game_authorities":0,
                    "roblox_studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
                    "owner_accepted":False})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ470_HIT042_CURRENT31_PLUS_SPECTATOR_ONE_PLACE_TRUE_SOURCE_PASS")
if __name__=="__main__":main()
