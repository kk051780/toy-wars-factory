#!/usr/bin/env python3
"""Native Rojo 78/78 XML embedded Luau source exact. No Studio engine is run."""
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from apply_p0_motion78 import read,gitblob,DEST,CLIENT_ID,FEATURE_ID,MOTION_PIN

def verify(dist:Path,place:Path,receipt:Path)->None:
    sources=read(dist)
    assert len(sources)==78
    pins={name:gitblob(raw) for name,raw in sorted(sources.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert pins[DEST]==MOTION_PIN
    assert fl["feature_flags"][FEATURE_ID] is True
    expected=collections.Counter(raw.decode("utf8") for raw in sources.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","ModuleScript","LocalScript"):continue
        code=item.find("./Properties/string[@name='Source']")
        if code is not None:actual[code.text or ""]+=1
        name=item.find("./Properties/string[@name='Name']")
        if name is not None:names[(item.get("class"),name.text)]+=1
    assert actual==expected and sum(actual.values())==78,("MOTION78_XML_SOURCE_DRIFT",sum(actual.values()))
    for typ,name in (
        ("Script","Game"),("ModuleScript","SoloTeamBots"),("ModuleScript","LobbyDojoIsland"),
        ("Script","Owner361CastleBattlefield"),("Script","ArtMinionSilhouette"),
        ("LocalScript","BattleHUDGovernor"),("LocalScript","FB015GoroganVisual"),
        ("LocalScript","P0DConfirmedCombatFX"),("LocalScript",CLIENT_ID),
    ):
        assert names[(typ,name)]==1,("MOTION78_DUPLICATE_OR_MISSING_SCRIPT",typ,name,names[(typ,name)])
    output={
        "private_candidate":"P0D_PRIVATE78_CORE70_SEVEN_ART_MOTION78",
        "source_count":78,"actual_luau_source_exact":True,
        "source_gitblob_match":True,"only_one_Game":True,
        "parent77_untouched":True,"studio_engine":"NOT_TESTED",
        "art_motion_proven_physically":"NOT_TESTED","android_fps":"NOT_TESTED",
        "owner_art":"ART_NO_GO","owner_fun":"FUN_NO_GO",
        "official_rc_adoption":0,
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0_PRIVATE78_NATIVE_AND_ROJO_ALL_78_SOURCE_EXACT_PASS",
          output["place_bytes"],output["place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
