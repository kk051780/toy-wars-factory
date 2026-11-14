#!/usr/bin/env python3
"""Source-exact 80/80 real Rojo Studio Place check for isolated #405 Bot patch."""
import argparse, collections, hashlib, json, xml.etree.ElementTree as ET
from pathlib import Path
from apply_rc80_bot405 import read, blob, BOT, GAME, KEY, AUTHOR405

def verify(dist:Path,place:Path,receipt:Path):
    data=read(dist)
    assert len(data)==80 and BOT in data and GAME in data
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(data.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    info=sl[KEY]
    assert info==fl[KEY] and info["author_commit"]==AUTHOR405
    assert pins[BOT]==info["updated_bot_gitblob"]
    assert info["only_existing_bot_changed"] and info["other79_sources_byte_exact"]
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"]
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"]
    bot=data[BOT].decode("utf8")
    for marker in ("MAX_PENDING_PATH_TASKS=10",
                   "P0D_BOT_PATH_RESULT_FAILED",
                   "P0D_BOT_EGG_DROP_FAILED",
                   "P0D_BOT_FOLDER_TEARDOWN_FAILED",
                   "bot.lastProgressDistance=nil",
                   "bot.detourGoal=nil",
                   "if (position-goal).Magnitude<=4.5 then"):
        assert marker in bot,marker
    want=collections.Counter(v.decode("utf8") for v in data.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        prop=item.find("Properties")
        if prop is None:continue
        src=prop.find("string[@name='Source']")
        nm=prop.find("string[@name='Name']")
        if src is not None:actual[src.text or ""]+=1
        if nm is not None:names[(item.get("class"),nm.text)]+=1
    assert actual==want and sum(actual.values())==80
    assert names[("Script","Game")]==1
    assert names[("ModuleScript","SoloTeamBots")]==1
    assert names[("LocalScript","BattleHUDGovernor")]==1
    result={"stage":"PREP_NOT_OFFICIAL","source_author":AUTHOR405,
            "all_80_embedded_sources_exact":True,
            "single_game":True,"new_game_authorities":0,
            "studio_engine":"NOT_TESTED","android":"NOT_TESTED",
            "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
            "place_bytes":place.stat().st_size,
            "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()}
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_RC80_AUTHOR405_ALL80_ROJO_SOURCE_EXACT_PASS",result["place_bytes"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
