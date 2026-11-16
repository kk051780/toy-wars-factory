#!/usr/bin/env python3
"""Evidence: ALL 27 original+quality+ART+SCORE+carrier Luau sources are exact in a private Place."""
from __future__ import annotations
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def walk(node: dict, project_path: Path, out: dict) -> None:
    for name, child in node.items():
        if name.startswith("$") or not isinstance(child,dict): continue
        if "$path" in child:
            assert set(child) == {"$path"},name
            assert name not in out,("duplicate module",name)
            path = (project_path.parent / child["$path"]).resolve(strict=True)
            cl = ("Script" if path.name.endswith(".server.luau") else
                  ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript"))
            out[name]=(cl,path,path.read_text(encoding="utf-8").replace("\r\n","\n"))
        else:
            walk(child, project_path, out)

def verify(project_path: Path, place: Path, receipt_path: Path) -> dict:
    project_path=project_path.resolve(strict=True)
    project=json.loads(project_path.read_text(encoding="utf-8"))
    data=json.loads(receipt_path.read_text(encoding="utf-8"))
    source={}
    walk(project["tree"],project_path,source)
    assert len(source)==27 and data["script_count"]==27
    assert data["server_count"]==24 and data["client_count"]==3
    assert not data["official_rc_adopted"]
    assert source["EGGRUMBLE_CarrierBotTargeting"][0]=="ModuleScript"
    bot=source["EGGRUMBLE_BotActors"][2]
    assert bot.count('CarrierBotTargeting.canStrike(pc.heldEggs,')==1
    assert bot.count('local CarrierBotTargeting=require(')==1
    assert 'clearHeroStrike(actor,character,' in bot
    assert 'BOT_ATTACK_INTERVAL' in bot
    assert 'h:TakeDamage(BOT_HERO_DAMAGE)' in bot
    for name in ("EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_CastleMatchRules",
                 "EGGRUMBLE_SwarmCombat","EGGRUMBLE_FieldItemPickups",
                 "EGGRUMBLE_RaidItemIntake","EGGRUMBLE_NeutralStoneGiant",
                 "EGGRUMBLE_LobbyCastleModesPreview",
                 "EGGRUMBLE_ScoreBalance","EGGRUMBLE_MatchResultService",
                 "EGGRUMBLE_FlagshipFieldArt","EGGRUMBLE_ArtDistanceLOD"):
        assert name in source,("missing cross-domain runtime",name)
    assert sum(1 for k in source if k.endswith("BotActors"))==1
    assert sum(1 for k in source if k.endswith("MatchResultService"))==1
    for name,(_,path,_) in source.items():
        assert data["source_sha256"][name]==hashlib.sha256(path.read_bytes()).hexdigest(),name
    actual={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        if item.attrib.get("class") not in ("ModuleScript","Script","LocalScript"): continue
        prop=item.find("Properties")
        if prop is None:continue
        name=prop.findtext("string[@name='Name']")
        assert name not in actual,("duplicate embedded script",name)
        content=prop.findtext("ProtectedString[@name='Source']")
        if content is None:content=prop.findtext("string[@name='Source']")
        assert content is not None,name
        actual[name]=(item.attrib["class"],content.replace("\r\n","\n"))
    expected={name:(cls,source_text) for name,(cls,_,source_text) in source.items()}
    assert expected==actual,{"missing":sorted(set(expected)-set(actual)),
                             "extra":sorted(set(actual)-set(expected)),
                             "content_mismatch":[name for name in set(expected)&set(actual)
                                                 if expected[name]!=actual[name]]}
    data["place_bytes"]=place.stat().st_size
    data["place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    data["source_exact_count"]=len(expected)
    data["official_rc_adopted"]=False
    receipt_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EGGRUMBLE_27_OF_27_EXACT_GQ_CARRIER_ART_SCORE_PASS",len(expected))
    print("PRIVATE_PLACE_BYTES",data["place_bytes"],"SHA256",data["place_sha256"])
    return data

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--place",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    args=ap.parse_args()
    verify(args.project,args.place,args.receipt)
